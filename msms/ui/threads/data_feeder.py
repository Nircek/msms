import logging
import threading
import time

import numpy as np

from msms.connectivity.data_collector import DataCollector
from msms.connectivity.visa import get_visa_library

logger = logging.getLogger(__name__)


class StopExecution(Exception):  # noqa: N818
    pass


class ThreadedGrowingDataHolder:
    # only one thread can write to it
    def __init__(self) -> None:
        self._data = np.ndarray([])
        self.capacity = 0
        self.size = 0
        self.columns: list[str] = []
        self.lock = threading.Lock()

    @property
    def data(self) -> np.ndarray:
        if self.capacity == 0:
            return np.ndarray([])
        with self.lock:
            return self._data[: self.size, :]

    def initialize(self, columns: list[str], capacity: int = 1024) -> None:
        data = np.ndarray((capacity, len(columns)), dtype=float)
        self.columns = columns
        with self.lock:
            self.capacity = capacity
            self.size = 0
            self._data = data

    def append(self, row: list[float]) -> None:
        if self.size >= self.capacity:
            self.grow()
        self._data[self.size] = row
        self.size += 1

    def grow(self) -> None:
        new_capacity = max(2 * self.capacity, 1024)
        new_data = np.ndarray((new_capacity, self._data.shape[1]), dtype=float)
        new_data[: self.size, :] = self._data[: self.size, :]
        with self.lock:
            self.capacity = new_capacity
            self._data = new_data


class DataFeeder(threading.Thread):
    def __init__(
        self,
        interval: float = 0.5,
        stop_event: threading.Event | None = None,
    ) -> None:
        super().__init__(daemon=True)
        self._interval = interval
        self._interval_lock = threading.Lock()
        self._stop_event = stop_event or threading.Event()
        self._last_cycle_time = 0.0
        self.data_holder = ThreadedGrowingDataHolder()

    @property
    def interval(self) -> float:
        with self._interval_lock:
            return self._interval

    @interval.setter
    def interval(self, value: float) -> None:
        with self._interval_lock:
            self._interval = value

    def wait_for_next_cycle(self) -> None:
        while True:
            if self._stop_event.is_set():
                raise StopExecution()
            time_to_next_cycle = self._last_cycle_time + self.interval - time.time()
            if time_to_next_cycle <= 0:
                self._last_cycle_time = time.time()
                return
            time.sleep(min(1.0, time_to_next_cycle))

    def run(self) -> None:
        visa_library = get_visa_library()
        logger.info("Using VISA library: %s", visa_library)

        collector = DataCollector(visa_library)

        collector.initialize_visa()
        try:
            collector.discover_devices()
            collector.initialize_devices()
            data = collector.collect_data()
            self.data_holder.initialize(list(data.keys()))
            while True:
                self.wait_for_next_cycle()
                logger.info("Generating new data sample")
                data = collector.collect_data()
                self.data_holder.append([v if isinstance(v, float) else float("nan") for v in data.values()])
                # TODO: just throw it into disk  # noqa: FIX002
        except StopExecution:
            logger.info("Data feeder stopped")
        finally:
            collector.cleanup()

    def stop(self) -> None:
        self._stop_event.set()
