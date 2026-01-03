import logging
from typing import TYPE_CHECKING

import numpy as np
from PySide6 import QtCore

from msms.ui.managers.csv_persistence_service import CsvPersistenceService, SessionSnapshot

if TYPE_CHECKING:
    from collections.abc import Mapping
    from datetime import datetime
    from pathlib import Path

logger = logging.getLogger(__name__)


def to_float(s: str) -> str | float:
    """Convert trimmed string to float or return original string."""
    s = s.strip()
    try:
        return float(s)
    except ValueError:
        return s


def float_or_nan(v: str | float) -> float:
    """Return float unchanged or np.nan for strings."""
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

    def clear(self) -> None:
        """Clear all stored data."""
        self._mutex.lock()
        self._data = np.ndarray([])
        self._columns = None
        self.capacity = 0
        self.size = 0
        self._mutex.unlock()

    @property
    def data(self) -> np.ndarray:
        """Return populated rows as numpy array view."""
        if self.capacity == 0:
            return np.ndarray([])
        self._mutex.lock()
        view = self._data[: self.size, :]
        self._mutex.unlock()
        return view

    @property
    def columns(self) -> tuple[str, ...] | None:
        """Return numeric column names."""
        return None if self._columns is None else tuple(self._columns)

    def initialize(self, columns: list[str], *, capacity: int = 1024) -> None:
        """Allocate internal storage and remember column ordering."""
        assert self._columns is None, "DataRepository is already initialized"
        self._columns = columns
        self._grow(capacity)

    def load_snapshot(self, columns: list[str], rows: list[list[float]]) -> None:
        """Populate storage from historical snapshot."""
        assert self._columns is None, "DataRepository is already initialized"
        row_count = len(rows)
        column_count = len(columns)
        if row_count == 0 or column_count == 0:
            data = np.zeros((0, column_count), dtype=float)
        else:
            data = np.asarray(rows, dtype=float).reshape(row_count, column_count)
        self._mutex.lock()
        self._columns = list(columns)
        self._data = data
        self.size = data.shape[0]
        self.capacity = data.shape[0]
        self._mutex.unlock()

    def append(self, row: list[float]) -> None:
        """Append numeric row, growing storage if necessary."""
        if self.size >= self.capacity:
            self._grow()
        self._mutex.lock()
        self._data[self.size] = row
        self.size += 1
        self._mutex.unlock()

    def _grow(self, new_capacity: int | None = None) -> None:
        """Double storage or grow to new_capacity, preserving data."""
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
    """Data transformation, persistence, and UI signals."""

    columns_changed = QtCore.Signal(object)
    new_data_row = QtCore.Signal(object)
    restore_completed = QtCore.Signal()
    restore_failed = QtCore.Signal(object)
    export_completed = QtCore.Signal(object)
    export_failed = QtCore.Signal(object)
    description_changed = QtCore.Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self._is_running = False
        self._data_repository = DataRepository()
        self.csv_persistence = CsvPersistenceService()
        self.row_number = 1
        self.t0 = 0.0
        self.columns: list[str] = []
        self.number_columns: list[str] = []
        self._automation_log: list[tuple[str, str, datetime | None]] = []

    @QtCore.Slot()
    def on_setup(self) -> None:
        """Initialize storage manager in thread context."""
        self.on_session_start_request()
        QtCore.QCoreApplication.processEvents()

    @QtCore.Slot()
    def on_session_start_request(self) -> None:
        """Start new acquisition session."""
        if self.csv_persistence.is_active:
            logger.warning("Persistence session already active")
            return

        self.csv_persistence = CsvPersistenceService()
        self._data_repository.clear()
        self.columns = []
        self.number_columns = []
        self.row_number = 1
        self.t0 = 0.0
        self._is_running = True
        self.csv_persistence.start_session()
        self.columns_changed.emit(self.number_columns)
        self.new_data_row.emit({})
        self.description_changed.emit("")

    @QtCore.Slot()
    def on_stop_request(self) -> None:
        self._is_running = False
        self.csv_persistence.stop_session()

    def get_last_used_file(self) -> Path | None:
        """Return most recent CSV file or None."""
        return self.csv_persistence.get_last_used_file()

    @QtCore.Slot(object)
    def on_session_restore_request(self, target: Path | None) -> None:
        """Restore a previously recorded session and notify the UI."""
        resolved = self.csv_persistence.resolve_restore_target(target)
        if resolved is None:
            message = "No previous session available to restore."
            logger.info(message)
            self.restore_failed.emit(message)
            return

        self.on_stop_request()

        try:
            snapshot = self.csv_persistence.load_snapshot(resolved)
        except FileNotFoundError as error:
            logger.info("Requested restore target missing: %s", error)
            self.restore_failed.emit(str(error))
            return
        except Exception:
            logger.exception("Unexpected error while restoring session from %s", resolved)
            self.restore_failed.emit(f"Failed to restore session from {resolved}")
            return

        self._apply_snapshot(snapshot)

    @QtCore.Slot(object)
    def on_export_request(self, request: tuple[Path, list[str] | None]) -> None:
        """Export data to CSV."""
        export_path, columns = request
        if export_path is None:
            message = "Export request missing path."
            logger.error(message)
            self.export_failed.emit(message)
            return

        try:
            self.csv_persistence.export_to_csv(export_path, columns, self._automation_log)
        except Exception:
            logger.exception("Failed to export data to %s", export_path)
            self.export_failed.emit(f"Failed to export data to {export_path}")
            return

        self.export_completed.emit(str(export_path))

    @QtCore.Slot(object)
    def on_automation_log_update(self, log: list[tuple[str, str, datetime | None]]) -> None:
        """Update cached automation log for export.

        Args:
            log: List of (step_id, label, timestamp) tuples.
        """
        self._automation_log = log

    @QtCore.Slot(object)
    def on_description_change_request(self, description: str) -> None:
        """Persist automation description to file."""
        description_text = "" if description is None else str(description)
        self.csv_persistence.set_description(description_text)
        # self.description_changed.emit(description_text) -- do not emit, UI already knows

    @QtCore.Slot(object)
    def on_header_set_request(self, initial_data: dict[str, str]) -> None:
        """Configure CSV header and emit columns to UI."""
        if not self.csv_persistence.is_active:
            logger.error("Cannot set header: persistence not active")
            return

        base_columns = list(initial_data.keys())
        additional_columns = [col for col in self.transform_data({})[0] if col not in base_columns]
        self.columns = base_columns + additional_columns
        self.number_columns = [col for col in self.columns if not col.startswith("_")]
        self._data_repository.initialize(self.number_columns)
        self.csv_persistence.write_header(self.columns)
        self.columns_changed.emit(self.number_columns)
        self._is_running = True

    @QtCore.Slot(object)
    def on_data_append_request(self, data: dict[str, str]) -> None:
        """Handle new acquisition payload."""
        if not self._is_running:
            return

        parsed_data, row, number_row = self.transform_data(data)
        self._data_repository.append(number_row)
        self.new_data_row.emit(parsed_data)
        self.csv_persistence.write_row(row)
        self.row_number += 1

    def _apply_snapshot(self, snapshot: SessionSnapshot) -> None:
        """Replace in-memory state with the supplied snapshot."""

        logger.info("Restoring session from %s", snapshot.csv_path)
        self._is_running = False
        self.csv_persistence.csv_file_path = snapshot.csv_path
        self.csv_persistence.description = snapshot.description
        self.csv_persistence.reactivate_session()  # Allow description updates for restored session
        self.columns = list(snapshot.columns)
        self.number_columns = list(snapshot.numeric_columns)

        self._data_repository.clear()
        self._data_repository.load_snapshot(snapshot.numeric_columns, snapshot.numeric_rows)

        last_row_index = snapshot.row_count
        self.row_number = last_row_index if last_row_index > 0 else 1
        self.t0 = snapshot.timestamp_zero

        if snapshot.last_row:
            parsed, _, _ = self.transform_data(snapshot.last_row)
            self.new_data_row.emit(parsed)
        self.row_number = last_row_index + 1 if last_row_index > 0 else 1

        self.columns_changed.emit(self.number_columns)
        self.description_changed.emit(snapshot.description)

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
