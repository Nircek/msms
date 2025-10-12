import logging
import threading
import time
from typing import TYPE_CHECKING

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
            print(self._interval)
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
        try:
            while True:
                self.wait_for_next_cycle()
                logger.info("Generating new data sample")
                self.out_queue.append((time.time(), time.time()))
        except StopExecution:
            logger.info("Data feeder stopped")

    def stop(self) -> None:
        self._stop_event.set()
