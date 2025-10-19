"""Coordinate data transformation and persistence for acquisition system."""

import logging
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from PyQt6 import QtCore

from msms.ui.managers import CsvPersistenceService

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

from msms.logging_config import get_logs_file_path

logger = logging.getLogger(__name__)


def to_float(s: str) -> str | float:
    """Convert a trimmed string to float when possible.

    Args:
        s: String representation of a value.

    Returns:
        Either ``float`` when the string represents a numeric value or the original
        string when conversion fails.
    """

    s = s.strip()
    try:
        return float(s)
    except ValueError:
        return s


def float_or_nan(v: str | float) -> float:
    """Return numeric input unchanged or ``np.nan`` for strings.

    Args:
        v: Value that may already be numeric.

    Returns:
        ``float``: either the supplied float value or ``np.nan``.
    """

    return np.nan if isinstance(v, str) else v


class DataRepository:
    """Thread-safe container storing streaming numeric data.

    Only one thread can append or grow it, but multiple threads can read data property.
    """

    def __init__(self) -> None:
        self._data = np.ndarray([])
        self.capacity = 0
        self.size = 0
        self._columns: list[str] | None = None
        self._mutex = QtCore.QMutex()

    @property
    def data(self) -> np.ndarray:
        """Return currently populated rows as a numpy array view."""

        if self.capacity == 0:
            return np.ndarray([])
        self._mutex.lock()
        view = self._data[: self.size, :]
        self._mutex.unlock()
        return view

    @property
    def columns(self) -> tuple[str, ...] | None:
        """Return configured numeric column names."""

        return None if self._columns is None else tuple(self._columns)

    def initialize(self, columns: list[str], *, capacity: int = 1024) -> None:
        """Allocate internal storage and remember column ordering.

        Args:
            columns: Ordered list of numeric column names.
            capacity: Initial capacity to allocate.
        """

        assert self._columns is None, "DataRepository is already initialized"
        self._columns = columns
        self._grow(capacity)

    def from_dataframe(self, df: pd.DataFrame) -> None:
        """Populate storage from an existing dataframe snapshot.

        Args:
            df: Dataframe containing historical numeric samples.
        """

        assert self._columns is None, "DataRepository is already initialized"
        self._columns = list(df.columns)
        data = df.to_numpy(dtype=float)
        self._mutex.lock()
        self._data = data
        self.size = data.shape[0]
        self.capacity = data.shape[0]
        self._mutex.unlock()

    def append(self, row: list[float]) -> None:
        """Append a numeric row, growing storage if necessary.

        Args:
            row: Numeric values aligned with configured columns.
        """

        if self.size >= self.capacity:
            self._grow()
        self._mutex.lock()
        self._data[self.size] = row
        self.size += 1
        self._mutex.unlock()

    def _grow(self, new_capacity: int | None = None) -> None:
        """Double storage or grow to ``new_capacity`` while preserving data."""

        assert self._columns is not None, "DataRepository is not initialized"
        if new_capacity is None:
            new_capacity = max(2 * self.capacity, 1024)
        if new_capacity <= self.capacity:
            return
        new_data = np.ndarray((new_capacity, len(self._columns)), dtype=float)
        if self._data.shape != ():
            new_data[: self.size, :] = self._data[: self.size, :]
        self._mutex.lock()
        self.capacity = new_capacity
        self._data = new_data
        self._mutex.unlock()


class StorageManager(QtCore.QObject):
    """Coordinate data transformation, persistence, and UI signals."""

    new_data_row = QtCore.pyqtSignal(object)
    columns_changed = QtCore.pyqtSignal(object)

    def __init__(self) -> None:
        super().__init__()
        self._is_running = False
        self.data_repository = DataRepository()
        self.csv_persistence = CsvPersistenceService()
        self.row_number = 1
        self.t0 = 0.0
        self.columns: list[str] = []
        self.number_columns: list[str] = []

    def setup(self) -> None:
        """Start a new acquisition session."""
        self._is_running = True
        self.csv_persistence.start_session()

    def stop(self) -> None:
        """Stop recording and close resources."""
        self._is_running = False
        self.csv_persistence.stop_session()

    def get_last_used_file(self) -> Path | None:
        """Return the most recently completed CSV file if it exists.

        Returns:
            Path to the previous CSV file or None when unavailable.
        """
        return self.csv_persistence.get_last_used_file()

    def load_old_file(self, file_path: Path) -> None:
        """Load previously recorded data and emit refresh signals for the UI."""
        file_stem = file_path.stem
        csv_file_path = get_logs_file_path(self.csv_persistence.data_suffix, file_stem)
        description_path = get_logs_file_path(self.csv_persistence.description_suffix, file_stem)
        assert file_path.exists(), f"Data file {file_path} does not exist"
        assert description_path.exists(), f"Description file {description_path} does not exist"

        self.stop()
        self.csv_persistence.csv_file_path = csv_file_path
        self._is_running = True

        df = pd.read_csv(file_path, comment="#")
        self.columns = list(df.columns)
        self.row_number = len(df)
        timestamp_val = df.loc[0, "timestamp"]
        self.t0 = float(timestamp_val) if pd.notna(timestamp_val) else 0.0  # type: ignore[arg-type]
        last_row = df.iloc[-1].astype("string").to_dict()
        logger.info("Loaded %d rows from %s", self.row_number, file_path)
        self.new_data_row.emit(self.transform_data(last_row)[0])

        df = df.apply(pd.to_numeric, errors="coerce").astype("float64")
        df = df.loc[:, df.notna().any()]
        self.data_repository.from_dataframe(df)
        self.number_columns = list(self.data_repository.columns or [])

        with description_path.open("r", encoding="utf-8") as desc_file:
            self.csv_persistence.description = desc_file.read()
        self.columns_changed.emit(self.number_columns)

    def export_to_csv(self, export_path: Path, columns: list[str] | None = None) -> None:
        """Export currently stored data into a user-provided CSV path."""
        self.csv_persistence.export_to_csv(export_path, columns)

    def set_description(self, description: str) -> None:
        """Persist the textual experiment description alongside the CSV file."""
        self.csv_persistence.set_description(description)

    def set_header(self, initial_data: Mapping[str, str]) -> None:
        """Configure CSV header and emit column information for the UI."""
        if not self.csv_persistence.is_active:
            logger.error("Cannot set header: persistence not active")
            return

        base_columns = list(initial_data.keys())
        additional_columns = [col for col in self.transform_data({})[0] if col not in base_columns]
        self.columns = base_columns + additional_columns
        self.number_columns = [col for col in self.columns if not col.startswith("_")]
        self.data_repository.initialize(self.number_columns)
        self.csv_persistence.write_header(self.columns)
        self.columns_changed.emit(self.number_columns)

    def on_data_append(self, data: dict[str, str]) -> None:
        """Handle new acquisition payload and update caches and CSV."""
        if not self._is_running:
            return

        parsed_data, row, number_row = self.transform_data(data)
        self.new_data_row.emit(parsed_data)
        self.data_repository.append(number_row)
        self.csv_persistence.write_row(row)
        self.row_number += 1

    def transform_data(self, data: Mapping[str, str]) -> tuple[dict[str, str | float], list[str | float], list[float]]:
        """Convert a string payload into miscellaneous and numeric representations.

        Args:
            data: Raw mapping with string values produced by the devices.

        Returns:
            A tuple consisting of the parsed dictionary, a CSV row ready for writing,
            and a numeric-only list suitable for the in-memory holder.
        """

        transformed: dict[str, str | float] = {k: to_float(v) for k, v in data.items()}
        if self.t0 == 0.0 and "timestamp" in transformed and isinstance(t0 := transformed.get("timestamp"), float):
            self.t0 = t0
        transformed["time"] = float(transformed.get("timestamp", 0)) - self.t0
        transformed["row_number"] = float(self.row_number)
        row = [transformed.get(col, "<empty>") for col in self.columns]
        number_row = [float_or_nan(transformed.get(col, np.nan)) for col in self.number_columns]
        return transformed, row, number_row
