import logging

from PyQt6 import QtCore

from msms.connectivity.device_repository import DeviceRepository, DiscoveredDevice

logger = logging.getLogger(__name__)


class DeviceManager(QtCore.QObject):
    """Coordinate device discovery and periodic data polling using QTimer."""

    data_initialized = QtCore.pyqtSignal(object)
    data_collected = QtCore.pyqtSignal(object)
    devices_discovered = QtCore.pyqtSignal(object)
    acquisition_state_changed = QtCore.pyqtSignal(object)

    def __init__(self, interval_ms: int = 500) -> None:
        """Initialize the manager with a QTimer-based polling mechanism.

        Args:
            interval_ms: Polling interval in milliseconds.
        """
        super().__init__()
        self._is_running = False
        self._timer: QtCore.QTimer | None = None
        self._interval_ms = interval_ms
        self._repository = DeviceRepository()
        self._selected_addresses: list[str] = []
        self._discovery_timer: QtCore.QTimer | None = None

    @property
    def interval_ms(self) -> int:
        return self._interval_ms

    @interval_ms.setter
    def interval_ms(self, value: int) -> None:
        self._interval_ms = value
        if self._is_running and self._timer is not None:
            self._timer.setInterval(value)
            logger.info("Polling interval changed to %d ms", value)

    def initialize_visa(self) -> None:
        """Initialise VISA resources once."""
        self._repository.initialize_visa()

    def discover_devices(self) -> list[DiscoveredDevice]:
        """Return the current set of discoverable devices.

        Returns:
            List of devices detected via the VISA repository.
        """
        return self._repository.discover_devices()

    @QtCore.pyqtSlot()
    def on_setup(self) -> None:
        self.initialize_visa()

    @QtCore.pyqtSlot()
    def on_acquisition_start_request(self) -> None:
        """Initialize devices and start timer-based polling."""
        if self._is_running:
            logger.warning("Acquisition already running, ignoring start request.")
            return

        if not self._selected_addresses:
            logger.error("No device addresses configured; cannot start acquisition.")
            return

        try:
            self.initialize_visa()
        except Exception:
            logger.exception("Unable to initialise VISA before acquisition")
            return

        if self._timer is None:
            current_thread = QtCore.QThread.currentThread()
            thread_id = int(current_thread.currentThreadId()) if current_thread else 0  # type: ignore[arg-type]
            logger.info("Creating timer on thread %s (id: %s)", current_thread, thread_id)
            self._timer = QtCore.QTimer(self)
            self._timer.timeout.connect(self._poll_devices)

        self._repository.set_selected_addresses(self._selected_addresses)

        try:
            self._repository.prepare_devices()
            self._repository.initialize_devices()
            initial_data = self._repository.collect_data()
        except Exception:
            logger.exception("Failed to start device acquisition")
            self._repository.shutdown_devices()
            return

        if not initial_data:
            logger.error("No devices returned data; aborting acquisition start.")
            self._repository.shutdown_devices()
            return

        self.data_initialized.emit(initial_data)
        logger.info("Initial data collected, starting acquisition.")
        self._is_running = True
        self._timer.setInterval(self._interval_ms)
        self._timer.start()
        self.acquisition_state_changed.emit(True)

    def _poll_devices(self) -> None:
        """Collect data from devices (called by timer)."""
        if not self._is_running:
            return

        logger.info("Collecting data sample")
        data = self._repository.collect_data()
        self.data_collected.emit(data)

    @QtCore.pyqtSlot()
    def on_acquisition_stop_request(self) -> None:
        """Stop polling and clean up device resources."""

        if not self._is_running:
            logger.info("Acquisition not running, nothing to stop")
            return

        self._is_running = False
        if self._timer is not None:
            self._timer.stop()

        self._repository.close()

        self.acquisition_state_changed.emit(False)
        logger.info("Device acquisition stopped")

    @QtCore.pyqtSlot(object)
    def on_device_select_request(self, addresses: list[str]) -> None:
        """Configure which device addresses should be polled."""

        self._selected_addresses = addresses
        self._repository.set_selected_addresses(addresses)
        logger.info("Selected device addresses updated: %s", addresses)
        if self._is_running:
            logger.warning("Updated device selection will apply on the next restart.")

    @QtCore.pyqtSlot(object)
    def on_interval_change_request(self, interval_ms: int) -> None:
        """Update polling interval from a queued signal."""

        self.interval_ms = interval_ms

    @QtCore.pyqtSlot(object)
    def on_discovery_start_request(self, interval_ms: int) -> None:
        if self._discovery_timer is not None and self._discovery_timer.isActive():
            logger.warning("Discovery already running, ignoring start request.")
            return

        try:
            self.initialize_visa()
        except Exception:
            logger.exception("Unable to initialize VISA before discovery")
            return

        if self._discovery_timer is None:
            self._discovery_timer = QtCore.QTimer(self)
            self._discovery_timer.timeout.connect(self._poll_discovered_devices)

        self._discovery_timer.setInterval(interval_ms)
        self._discovery_timer.start()
        logger.info("Device discovery started with interval %d ms", interval_ms)
        self._poll_discovered_devices()

    def _poll_discovered_devices(self) -> None:
        """Scan for devices and emit results (called by discovery timer)."""
        if not self._discovery_timer or not self._discovery_timer.isActive():
            return

        try:
            devices = self.discover_devices()
        except Exception:
            logger.exception("Device discovery failed")
            devices = []
        self.devices_discovered.emit(devices)

    @QtCore.pyqtSlot()
    def on_discovery_stop_request(self) -> None:
        """Stop periodic device discovery polling."""
        if self._discovery_timer is not None:
            self._discovery_timer.stop()

    @QtCore.pyqtSlot()
    def on_shutdown(self) -> None:
        """Release all VISA resources."""

        self.on_discovery_stop_request()
        self.on_acquisition_stop_request()
