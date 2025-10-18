import logging
import time

from PyQt6 import QtCore

from msms.connectivity.data_collector import DataCollector
from msms.connectivity.visa import get_visa_library

logger = logging.getLogger(__name__)


class StopExecution(Exception):  # noqa: N818
    pass


class DeviceManager(QtCore.QObject):
    initiated = QtCore.pyqtSignal(object)
    updated = QtCore.pyqtSignal(object)

    def __init__(self, interval: float = 0.5) -> None:
        super().__init__()
        self._is_running = False
        self.interval = interval  # atomic, do not perform arithmetics on it
        self._last_cycle_time = 0.0

    def wait_for_next_cycle(self) -> None:
        while True:
            if not self._is_running:
                raise StopExecution()
            time_to_next_cycle = self._last_cycle_time + self.interval - time.time()
            if time_to_next_cycle <= 0:
                self._last_cycle_time = time.time()
                return
            time.sleep(min(1.0, time_to_next_cycle))

    def run(self) -> None:
        self._is_running = True
        visa_library = get_visa_library()
        logger.info("Using VISA library: %s", visa_library)

        collector = DataCollector(visa_library)

        collector.initialize_visa()
        try:
            collector.discover_devices()
            collector.initialize_devices()
            data = collector.collect_data()
            self.initiated.emit(list(data.keys()))
            while True:
                self.wait_for_next_cycle()
                logger.info("Generating new data sample")
                data = collector.collect_data()
                self.updated.emit(data)
        except StopExecution:
            logger.info("Device manager stopped")
        finally:
            collector.cleanup()

    def stop(self) -> None:
        self._is_running = False
