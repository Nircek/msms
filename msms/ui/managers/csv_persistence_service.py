import csv
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from msms.logging_config import get_logs_file_path

if TYPE_CHECKING:
    from _csv import _writer
    from io import TextIOWrapper

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SessionSnapshot:
    """Container storing parsed CSV session data."""

    csv_path: Path
    description_path: Path
    columns: list[str]
    numeric_columns: list[str]
    numeric_rows: list[list[float]]
    last_row: dict[str, str]
    description: str
    timestamp_zero: float
    row_count: int


class CsvPersistenceService:
    """Handle CSV file writing and metadata persistence."""

    data_suffix = ".csv"
    description_suffix = ".txt"

    def __init__(self) -> None:
        """Initialize the persistence service."""
        self.csv_file_path = get_logs_file_path(self.data_suffix)
        self.csv_file: TextIOWrapper | None = None
        self.csv_file_writer: _writer | None = None
        self._is_active = False
        self.description = ""

    @property
    def is_active(self) -> bool:
        """Check if persistence is currently active."""
        return self._is_active

    @property
    def description_path(self) -> Path:
        """Get the path to the description text file."""
        return get_logs_file_path(self.description_suffix, self.csv_file_path.stem)

    def start_session(self) -> None:
        """Open CSV file for writing a new acquisition session."""
        if self._is_active:
            logger.warning("Persistence session already active")
            return

        self.csv_file = Path(self.csv_file_path).open("w", buffering=1, newline="", encoding="utf-8")  # noqa: SIM115
        self.csv_file_writer = csv.writer(self.csv_file)
        self.description_path.touch()
        self._is_active = True
        logger.info("Started CSV persistence to %s", self.csv_file_path)

    def reactivate_session(self) -> None:
        """Mark session as active without opening files (for restored sessions)."""
        self._is_active = True
        logger.debug("Reactivated persistence session for %s", self.csv_file_path)

    def stop_session(self) -> None:
        """Close CSV file and clean up empty files."""
        if not self._is_active:
            return

        self._is_active = False
        if self.csv_file:
            self.csv_file_writer = None
            self.csv_file.close()
            file_size = self.csv_file_path.stat().st_size if self.csv_file_path.exists() else 0

            # Clean up empty files
            if self.csv_file_path.exists() and file_size == 0:
                self.csv_file_path.unlink()
                if self.description_path.exists():
                    self.description_path.unlink()
                logger.info(
                    "Removed empty CSV and description files: %s, %s", self.csv_file_path, self.description_path
                )

            self.csv_file = None
            logger.info("Stopped CSV persistence")

    def write_header(self, columns: list[str]) -> None:
        if not self._is_active or self.csv_file_writer is None:
            logger.error("Cannot write header: persistence not active")
            return

        self.csv_file_writer.writerow(col.removeprefix("_") for col in columns)
        logger.debug("Wrote CSV header: %s", columns)

    def write_row(self, row: list[str | float]) -> None:
        """Write data row to CSV file."""
        if not self._is_active or self.csv_file_writer is None:
            logger.error("Cannot write row: persistence not active")
            return

        self.csv_file_writer.writerow(row)

    def set_description(self, description: str) -> None:
        """Persist experiment description to a text file."""
        if not self._is_active:
            logger.error("Cannot set description: persistence not active")
            return

        self.description = description
        with self.description_path.open("w", encoding="utf-8") as desc_file:
            desc_file.write(self.description)
        logger.debug("Saved description to %s", self.description_path)

    def get_last_used_file(self) -> Path | None:
        """Return the most recently completed CSV file if it exists.

        Returns:
            The path to the previous CSV file or ``None`` when unavailable.
        """
        log_dir = self.csv_file_path.parent
        csv_files = sorted(file.stem for file in log_dir.glob(f"*{self.data_suffix}"))
        try:
            index = csv_files.index(self.csv_file_path.stem)
        except ValueError:
            return None
        if index > 0:
            last_file_stem = csv_files[index - 1]
            return get_logs_file_path(self.data_suffix, last_file_stem)
        return None

    def resolve_restore_target(self, candidate: Path | None) -> Path | None:
        """Resolve the path that should be used for restoring a session.

        Returns:
            ``Path`` pointing to the session that should be restored or ``None``
            when no historic session is available.
        """

        if candidate is not None:
            return candidate
        return self.get_last_used_file()

    def load_snapshot(self, csv_path: Path) -> SessionSnapshot:
        """Parse CSV data and description for a stored session.

        Returns:
            ``SessionSnapshot`` containing parsed CSV data alongside metadata.

        Raises:
            FileNotFoundError: When either CSV or description file is missing.
        """

        if not csv_path.exists():
            raise FileNotFoundError(csv_path)

        description_path = get_logs_file_path(self.description_suffix, csv_path.stem)
        if not description_path.exists():
            raise FileNotFoundError(description_path)

        dataframe = pd.read_csv(csv_path, comment="#")
        columns = list(dataframe.columns)
        last_row = dataframe.iloc[-1].astype("string").to_dict() if not dataframe.empty else {}
        timestamp_value = 0.0
        if not dataframe.empty and "timestamp" in dataframe.columns:
            first_row_value = dataframe.iloc[0]["timestamp"]
            if pd.notna(first_row_value):
                timestamp_value = float(first_row_value)
        row_count = len(dataframe)

        numeric_frame = dataframe.apply(pd.to_numeric, errors="coerce").astype("float64", copy=False)
        numeric_frame = numeric_frame.loc[:, numeric_frame.notna().any()]
        numeric_columns = list(numeric_frame.columns)
        numeric_rows = numeric_frame.to_numpy(dtype=float, copy=True).tolist()

        description_text = description_path.read_text(encoding="utf-8")

        return SessionSnapshot(
            csv_path=csv_path,
            description_path=description_path,
            columns=columns,
            numeric_columns=numeric_columns,
            numeric_rows=numeric_rows,
            last_row=last_row,
            description=description_text,
            timestamp_zero=timestamp_value,
            row_count=row_count,
        )

    def export_to_csv(
        self,
        export_path: Path,
        columns: list[str] | None = None,
        experiment_log: list[tuple[str, str, datetime | None]] | None = None,
    ) -> None:
        """Export current CSV data to a user-provided path.

        Args:
            export_path: Destination path for export.
            columns: Optional column filter.
            experiment_log: Optional experiment log entries (step_id, label, timestamp).
        """
        if self.csv_file is not None:
            self.csv_file.flush()

        if not self.csv_file_path.exists():
            logger.error("Cannot export data: source CSV file does not exist")
            return

        with (
            self.csv_file_path.open(newline="", encoding="utf-8") as infile,
            export_path.open("w", newline="", encoding="utf-8") as outfile,
        ):
            reader = csv.DictReader(infile)
            if columns is None:
                columns = list(reader.fieldnames or [])

            # Write description
            outfile.write("\n".join(f"# {line}" for line in self.description.splitlines()) + "\n")

            # Write experiment log if provided
            if experiment_log:
                outfile.write("#\n# Experiment Log:\n")
                for step_id, label, timestamp in experiment_log:
                    if timestamp is not None:
                        ts_str = timestamp.isoformat() if isinstance(timestamp, datetime) else str(timestamp)
                        outfile.write(f"# {step_id}: {label} (started: {ts_str})\n")
                    else:
                        outfile.write(f"# {step_id}: {label} (not started)\n")

            writer = csv.DictWriter(outfile, fieldnames=columns)

            writer.writeheader()
            for row in reader:
                writer.writerow({col: row[col] for col in columns})

        logger.info("Exported data to %s", export_path)
