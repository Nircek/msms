import csv
import logging
import threading
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from PyQt6 import QtCore

from msms.logging_config import get_logs_file_path

if TYPE_CHECKING:
    from _csv import _writer
    from io import TextIOWrapper

logger = logging.getLogger(__name__)


class StopExecution(Exception):  # noqa: N818
    pass


def to_float(s: str) -> str | float:
    s = s.strip()
    try:
        return float(s)
    except ValueError:
        return s


def float_or_nan(v: str | float) -> float:
    return np.nan if isinstance(v, str) else v


class ThreadedGrowingDataHolder:
    # only one thread can append or grow it
    # but multiple threads can read data property
    def __init__(self) -> None:
        self._data = np.ndarray([])
        self.capacity = 0
        self.size = 0
        self._columns: list[str] | None = None
        self._lock = threading.Lock()

    @property
    def data(self) -> np.ndarray:
        with self._lock:
            if self.capacity == 0:
                return np.ndarray([])
            return self._data[: self.size, :]

    def initialize(self, columns: list[str], *, capacity: int = 1024) -> None:
        assert self._columns is None, "DataHolder is already initialized"
        self._columns = columns
        self._grow(capacity)

    def from_dataframe(self, df: pd.DataFrame) -> None:
        assert self._columns is None, "DataHolder is already initialized"
        self._columns = list(df.columns)
        data = df.to_numpy(dtype=float)
        with self._lock:
            self._data = data
            self.size = data.shape[0]
            self.capacity = data.shape[0]

    def append(self, row: list[float]) -> None:
        if self.size >= self.capacity:
            self._grow()
        with self._lock:
            self._data[self.size] = row
        self.size += 1

    def _grow(self, new_capacity: int | None = None) -> None:
        assert self._columns is not None, "DataHolder is not initialized"
        if new_capacity is None:
            new_capacity = max(2 * self.capacity, 1024)
        if new_capacity <= self.capacity:
            return
        new_data = np.ndarray((new_capacity, len(self._columns)), dtype=float)
        if self._data.shape != ():
            new_data[: self.size, :] = self._data[: self.size, :]
        with self._lock:
            self.capacity = new_capacity
            self._data = new_data


class StorageManager(QtCore.QObject):
    data_suffix = ".csv"
    description_suffix = ".txt"
    new_data_row = QtCore.pyqtSignal(object)
    old_file_load = QtCore.pyqtSignal(object)

    def __init__(self) -> None:
        super().__init__()
        self._is_running = False
        self.data_holder = ThreadedGrowingDataHolder()
        self.csv_file_path = get_logs_file_path(self.data_suffix)
        self.csv_file: TextIOWrapper | None = None
        self.csv_file_writer: _writer | None = None
        self.row_number = 1
        self.t0 = 0.0
        self.columns: list[str] = []
        self.number_columns: list[str] = []
        self.description = ""

    def setup(self) -> None:
        self._is_running = True
        self.csv_file = Path(self.csv_file_path).open("w", buffering=1, encoding="utf-8")  # noqa: SIM115
        self.csv_file_writer = csv.writer(self.csv_file)
        self.set_description(self.description)

    def stop(self) -> None:
        self._is_running = False
        if self.csv_file:
            self.csv_file_writer = None
            self.csv_file.close()
            if self.csv_file_path.exists() and self.csv_file_path.stat().st_size == 0:
                self.csv_file_path.unlink()
                get_logs_file_path(self.description_suffix, self.csv_file_path.stem).unlink()
            self.csv_file = None

    def get_last_used_file(self) -> Path | None:
        log_dir = self.csv_file_path.parent
        csv_files = sorted(file.stem for file in log_dir.glob(f"*{self.data_suffix}"))
        index = csv_files.index(self.csv_file_path.stem)
        if index > 0:
            last_file_stem = csv_files[index - 1]
            return get_logs_file_path(self.data_suffix, last_file_stem)
        return None

    def load_old_file(self, file_path: Path) -> None:  # from file?
        file_stem = file_path.stem
        csv_file_path = get_logs_file_path(self.data_suffix, file_stem)
        description_path = get_logs_file_path(self.description_suffix, file_stem)
        assert file_path.exists(), f"Data file {file_path} does not exist"
        assert description_path.exists(), f"Description file {description_path} does not exist"
        self.stop()
        self.csv_file_path = csv_file_path
        self._is_running = True
        df = pd.read_csv(file_path, comment="#")
        self.columns = list(df.columns)
        self.row_number = len(df)
        last_row = df.iloc[-1].astype("string").to_dict()
        print(last_row)
        self.new_data_row.emit(self.transform_data(last_row)[0])
        df = df.apply(pd.to_numeric, errors="coerce").astype("float64")
        df.loc[:, df.notna().any()]
        self.data_holder.from_dataframe(df)
        with description_path.open("r", encoding="utf-8") as desc_file:
            self.description = desc_file.read()
            self.old_file_load.emit(self.data_holder._columns)

    def export_to_csv(self, export_path: Path, columns: list[str] | None = None) -> None:
        assert self.csv_file_path is not None, "StorageManager is not set up"
        if self.csv_file is not None:
            self.csv_file.flush()
        with (
            self.csv_file_path.open(newline="", encoding="utf-8") as infile,
            export_path.open("w", newline="", encoding="utf-8") as outfile,
        ):
            reader = csv.DictReader(infile)
            if columns is None:
                columns = list(reader.fieldnames or [])
            outfile.write("\n".join(f"# {line}" for line in self.description.splitlines()) + "\n")
            writer = csv.DictWriter(outfile, fieldnames=columns)

            writer.writeheader()
            for row in reader:
                writer.writerow({col: row[col] for col in columns})

    def set_description(self, description: str) -> None:
        self.description = description
        with get_logs_file_path(self.description_suffix, self.csv_file_path.stem).open(
            "w", encoding="utf-8"
        ) as desc_file:
            desc_file.write(self.description)

    def set_header(self, columns: list[str]) -> None:
        assert self.csv_file_writer is not None, "StorageManager is not set up"
        columns += self.transform_data({})[0].keys()
        print("\n\n\n\n", columns, "\n\n\n\n")
        self.number_columns = [col for col in columns if not col.startswith("_")]
        self.columns = columns
        self.data_holder.initialize(self.number_columns)
        self.csv_file_writer.writerow(col.removeprefix("_") for col in columns)

    def on_data_append(self, data: dict[str, str]) -> None:
        if not self._is_running:
            return
        assert self.csv_file_writer is not None, "StorageManager is not set up"
        parsed_data, row, number_row = self.transform_data(data)
        self.new_data_row.emit(parsed_data)
        self.data_holder.append(number_row)
        self.csv_file_writer.writerow(row)
        self.row_number += 1

    def transform_data(self, data: dict[str, str]) -> tuple[dict[str, str | float], list[str | float], list[float]]:
        transformed: dict[str, str | float] = {k: to_float(v) for k, v in data.items()}
        if self.t0 == 0.0 and "timestamp" in transformed and isinstance(t0 := transformed.get("timestamp"), float):
            self.t0 = t0
        transformed["time"] = float(transformed.get("timestamp", 0)) - self.t0
        transformed["row_number"] = float(self.row_number)
        row = [transformed.get(col, "<empty>") for col in self.columns]
        number_row = [float_or_nan(transformed.get(col, np.nan)) for col in self.number_columns]
        return transformed, row, number_row
