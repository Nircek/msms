import logging
import threading
import time
from typing import TYPE_CHECKING

from msms.connectivity.data_collector import DataCollector
from msms.connectivity.visa import get_visa_library

if TYPE_CHECKING:
    from collections import deque

logger = logging.getLogger(__name__)


class StopExecution(Exception):  # noqa: N818
    pass


class DataFeeder(threading.Thread):
    def __init__(
        self, out_queue: deque[tuple[float, float]], interval: float = 0.5, stop_event: threading.Event | None = None
    ) -> None:
        super().__init__(daemon=True)
        self.out_queue = out_queue
        self._interval = interval
        self._interval_lock = threading.Lock()
        self._stop_event = stop_event or threading.Event()
        self._last_cycle_time = 0.0

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
            while True:
                self.wait_for_next_cycle()
                logger.info("Generating new data sample")
                data = collector.collect_data()
                assert isinstance(data["timestamp"], float)
                assert isinstance(data["dt"], float)
                self.out_queue.append((data["timestamp"], data["dt"]))
        except StopExecution:
            logger.info("Data feeder stopped")
        finally:
            collector.cleanup()

    def stop(self) -> None:
        self._stop_event.set()
