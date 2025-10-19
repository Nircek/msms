import logging

from PyQt6 import QtCore

from msms.connectivity.device_repository import DeviceRepository, DiscoveredDevice

logger = logging.getLogger(__name__)


class DeviceManager(QtCore.QObject):
    """Coordinate device discovery and periodic data polling using QTimer."""

    data_initialized = QtCore.pyqtSignal(object)
    data_collected = QtCore.pyqtSignal(object)

    def __init__(self, device_repository: DeviceRepository | None = None, interval_ms: int = 500) -> None:
        """Initialize the manager with a QTimer-based polling mechanism.

        Args:
            interval_ms: Polling interval in milliseconds.
        """
        super().__init__()
        self._is_running = False
        self._timer: QtCore.QTimer | None = None
        self._interval_ms = interval_ms
        self._repository = device_repository or DeviceRepository()
        self._selected_addresses: tuple[str, ...] = ()
        self._visa_ready = False

    @property
    def is_running(self) -> bool:
        """Report whether the polling loop is currently active."""
        return self._is_running

    @property
    def interval_ms(self) -> int:
        """Get current polling interval in milliseconds."""
        return self._interval_ms

    @interval_ms.setter
    def interval_ms(self, value: int) -> None:
        """Set polling interval in milliseconds and update timer if running.

        Args:
            value: New interval in milliseconds.
        """
        self._interval_ms = value
        if self._is_running and self._timer is not None:
            self._timer.setInterval(value)
            logger.info("Polling interval changed to %d ms", value)

    def initialize_visa(self) -> None:
        """Initialise VISA resources once."""

        if self._visa_ready:
            return

        self._repository.initialize_visa()
        self._visa_ready = True

    def discover_devices(self) -> list[DiscoveredDevice]:
        """Return the current set of discoverable devices.

        Returns:
            A list of discovered device summaries sourced from the VISA bus.
        """

        self.initialize_visa()
        return self._repository.discover_devices()

    def start_acquisition(self) -> None:
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

        # Create timer in the correct thread (after moveToThread)
        if self._timer is None:
            self._timer = QtCore.QTimer(self)
            self._timer.timeout.connect(self._poll_devices)

        self._repository.set_selected_addresses(list(self._selected_addresses))

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

    def _poll_devices(self) -> None:
        """Collect data from devices (called by timer)."""
        if not self._is_running:
            return

        logger.info("Collecting data sample")
        data = self._repository.collect_data()
        self.data_collected.emit(data)

    def stop_acquisition(self) -> None:
        """Stop polling and clean up device resources."""
        if self._timer is not None and self._timer.isActive():
            self._timer.stop()

        self._repository.shutdown_devices()
        if self._visa_ready:
            self._repository.close()
            self._visa_ready = False

        if self._is_running:
            logger.info("Device acquisition stopped")
        self._is_running = False

    @QtCore.pyqtSlot(list)
    def set_selected_addresses(self, addresses: list[str]) -> None:
        """Configure which device addresses should be polled."""

        self._selected_addresses = tuple(addresses)
        self._repository.set_selected_addresses(list(addresses))
        logger.info("Selected device addresses updated: %s", addresses)
        if self._is_running:
            logger.warning("Updated device selection will apply on the next restart.")

    def shutdown(self) -> None:
        """Release all VISA resources."""

        self.stop_acquisition()
