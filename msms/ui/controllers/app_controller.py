"""Controller for application-level coordination and lifecycle."""

import logging

from PyQt6 import QtCore

from msms.connectivity.device_repository import DeviceRepository, DiscoveredDevice
from msms.ui.managers import DeviceManager, StorageManager

logger = logging.getLogger(__name__)


class ApplicationController(QtCore.QObject):
    """Coordinate device manager and storage manager life cycles and connections."""

    device_start_requested = QtCore.pyqtSignal()
    device_stop_requested = QtCore.pyqtSignal()
    device_selection_changed = QtCore.pyqtSignal(list)

    def __init__(self, interval_ms: int = 500) -> None:
        """Initialize application controller with managers and threads.

        Args:
            interval_ms: Initial polling interval in milliseconds.
        """
        super().__init__()

        self.current_interval_ms = interval_ms

        # Create managers
        self.device_repository = DeviceRepository()
        self.device_manager = DeviceManager(device_repository=self.device_repository, interval_ms=interval_ms)
        self.storage_manager = StorageManager()

        # Create threads
        self.device_manager_thread = QtCore.QThread()
        self.storage_manager_thread = QtCore.QThread()

        # Move managers to threads
        self.device_manager.moveToThread(self.device_manager_thread)
        self.storage_manager.moveToThread(self.storage_manager_thread)

        # Connect thread lifecycle
        self.storage_manager_thread.started.connect(self.storage_manager.setup)

        self.device_start_requested.connect(self.device_manager.start_acquisition)
        self.device_stop_requested.connect(self.device_manager.stop_acquisition)
        self.device_selection_changed.connect(self.device_manager.set_selected_addresses)
        self._selected_device_addresses: list[str] = []

        # Connect data flow
        self.device_manager.data_initialized.connect(self.storage_manager.set_header)
        self.device_manager.data_collected.connect(self.storage_manager.on_data_append)

        # Start storage manager thread
        self.storage_manager_thread.start()

    @property
    def is_acquiring(self) -> bool:
        return self.device_manager_thread.isRunning() and self.device_manager.is_running

    def start_acquisition(self) -> None:
        """Start device acquisition."""
        if self.is_acquiring:
            logger.warning("Acquisition already running")
            return

        if not self._selected_device_addresses:
            logger.warning("Cannot start acquisition without selected devices")
            return

        logger.info("Starting acquisition with interval %d ms", self.current_interval_ms)
        self.device_manager.interval_ms = self.current_interval_ms

        if not self.device_manager_thread.isRunning():
            self.device_manager_thread.start()

        self.device_selection_changed.emit(self._selected_device_addresses)
        self.device_start_requested.emit()

    def stop_acquisition(self) -> None:
        """Stop device acquisition."""
        if not self.device_manager_thread.isRunning():
            return

        logger.info("Stopping acquisition")
        self.device_stop_requested.emit()
        self.device_manager_thread.quit()
        self.device_manager_thread.wait(100)

    def set_interval(self, interval_ms: int) -> None:
        """Change the acquisition interval.

        Args:
            interval_ms: New polling interval in milliseconds.
        """
        logger.info("Changing interval to %d ms", interval_ms)
        self.current_interval_ms = interval_ms
        self.device_manager.interval_ms = interval_ms

    def shutdown(self) -> None:
        """Clean up threads and resources."""
        logger.info("Shutting down application controller")
        self.stop_acquisition()
        self.storage_manager.stop()
        self.storage_manager_thread.quit()
        self.storage_manager_thread.wait(100)

    def update_selected_devices(self, addresses: list[str]) -> None:
        """Update the set of selected device VISA addresses."""

        self._selected_device_addresses = list(addresses)
        logger.info("Selected devices updated: %s", addresses)
        self.device_selection_changed.emit(self._selected_device_addresses)

    def discover_devices(self) -> list[DiscoveredDevice]:
        """Run a discovery pass across available VISA devices.

        Returns:
            List of device summaries obtained from the device manager.
        """

        return self.device_manager.discover_devices()
