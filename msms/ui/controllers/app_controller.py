import logging
from typing import TYPE_CHECKING

from PyQt6 import QtCore, QtWidgets

from msms.ui.managers import DeviceManager, StorageManager

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class ApplicationController(QtCore.QObject):
    device_acquisition_start_requested = QtCore.pyqtSignal()
    device_acquisition_stop_requested = QtCore.pyqtSignal()
    device_selection_requested = QtCore.pyqtSignal(object)
    device_discovery_start_requested = QtCore.pyqtSignal(object)
    device_discovery_stop_requested = QtCore.pyqtSignal()
    device_interval_change_requested = QtCore.pyqtSignal(object)
    device_shutdown_requested = QtCore.pyqtSignal()

    storage_restore_requested = QtCore.pyqtSignal(object)
    storage_export_requested = QtCore.pyqtSignal(object)
    storage_description_change_requested = QtCore.pyqtSignal(object)
    storage_session_start_requested = QtCore.pyqtSignal()
    storage_stop_requested = QtCore.pyqtSignal()

    def __init__(self, interval_ms: int = 500) -> None:
        super().__init__()

        self.current_interval_ms = interval_ms

        self.device_manager = DeviceManager(interval_ms=interval_ms)
        self.storage_manager = StorageManager()

        self.device_manager_thread = QtCore.QThread()
        self.storage_manager_thread = QtCore.QThread()
        self.device_manager.moveToThread(self.device_manager_thread)
        self.storage_manager.moveToThread(self.storage_manager_thread)

        self.storage_manager_thread.started.connect(self.storage_manager.on_session_start_request)
        self.device_manager_thread.started.connect(self.device_manager.on_setup)

        self.device_acquisition_start_requested.connect(self.device_manager.on_acquisition_start_request)
        self.device_acquisition_stop_requested.connect(self.device_manager.on_acquisition_stop_request)
        self.device_selection_requested.connect(self.device_manager.on_device_select_request)
        self.device_discovery_start_requested.connect(self.device_manager.on_discovery_start_request)
        self.device_discovery_stop_requested.connect(self.device_manager.on_discovery_stop_request)
        self.device_interval_change_requested.connect(self.device_manager.on_interval_change_request)
        self.device_shutdown_requested.connect(self.device_manager.on_shutdown)

        self.device_manager.devices_discovered.connect(self._on_devices_discovered)
        self.device_manager.acquisition_state_changed.connect(self._on_acquisition_state_changed)

        self.storage_restore_requested.connect(self.storage_manager.on_session_restore_request)
        self.storage_export_requested.connect(self.storage_manager.on_export_request)
        self.storage_description_change_requested.connect(self.storage_manager.on_description_change_request)
        self.storage_stop_requested.connect(self.storage_manager.on_stop_request)
        self.storage_session_start_requested.connect(self.storage_manager.on_session_start_request)

        self.device_manager.data_initialized.connect(self.storage_manager.on_header_set_request)
        self.device_manager.data_collected.connect(self.storage_manager.on_data_append_request)

        self.storage_manager_thread.start()
        self.device_manager_thread.start()

        self._selected_device_addresses: list[str] = []
        self._is_device_running = False

    @property
    def is_acquiring(self) -> bool:
        return self._is_device_running

    def start_discovery(self, interval_ms: int = 2000) -> None:
        """Start periodic device discovery polling.

        Args:
            interval_ms: Discovery polling interval in milliseconds.
        """
        logger.info("Starting device discovery with interval %d ms", interval_ms)
        self.device_discovery_start_requested.emit(interval_ms)

    def stop_discovery(self) -> None:
        """Stop periodic device discovery polling."""
        logger.info("Stopping device discovery")
        self.device_discovery_stop_requested.emit()

    def start_acquisition(self) -> None:
        """Start device acquisition."""
        if self.is_acquiring:
            logger.warning("Acquisition already running")
            return

        if not self._selected_device_addresses:
            logger.warning("Cannot start acquisition without selected devices")
            return

        logger.info("Starting acquisition with interval %d ms", self.current_interval_ms)
        self.device_interval_change_requested.emit(self.current_interval_ms)
        # self.storage_stop_requested.emit()
        # self.storage_session_start_requested.emit()
        self.device_selection_requested.emit(self._selected_device_addresses)
        self.device_acquisition_start_requested.emit()

    def stop_acquisition(self) -> None:
        """Stop device acquisition."""
        if not self.is_acquiring:
            logger.info("Device manager already stopped")
            return

        logger.info("Stopping acquisition")
        self.device_acquisition_stop_requested.emit()

    def set_interval(self, interval_ms: int) -> None:
        """Change the acquisition interval.

        Args:
            interval_ms: New polling interval in milliseconds.
        """
        logger.info("Changing interval to %d ms", interval_ms)
        self.current_interval_ms = interval_ms
        self.device_interval_change_requested.emit(interval_ms)

    def shutdown(self) -> None:
        """Clean up threads and resources."""
        current_thread = QtCore.QThread.currentThread()
        thread_id = int(current_thread.currentThreadId()) if current_thread else 0  # type: ignore[arg-type]
        logger.info("Shutting down application controller from thread %s (id: %s)", current_thread, thread_id)
        logger.info("Acquisition running: %s", self._is_device_running)

        self.device_shutdown_requested.emit()
        logger.info("Sent device shutdown signal")

        self.storage_stop_requested.emit()
        logger.info("Sent storage stop signal")

        # Process events briefly to ensure stop signals are delivered and processed
        # before we quit the threads
        QtWidgets.QApplication.processEvents()

        # logger.info("Quitting device manager thread")
        self.device_manager_thread.quit()
        # logger.info("Quitting storage manager thread")
        self.storage_manager_thread.quit()

        logger.info("Waiting for device manager thread (500ms)")
        device_finished = self.device_manager_thread.wait(500)
        if not device_finished:
            logger.warning("Device manager thread did not finish within timeout")

        logger.info("Waiting for storage manager thread (500ms)")
        storage_finished = self.storage_manager_thread.wait(500)
        if not storage_finished:
            logger.warning("Storage manager thread did not finish within timeout")

        logger.info("Shutdown complete")

    def update_selected_devices(self, addresses: list[str]) -> None:
        """Update the set of selected device VISA addresses."""

        self._selected_device_addresses = addresses
        logger.info("Selected devices updated: %s", addresses)
        self.device_selection_requested.emit(self._selected_device_addresses)

    def request_restore_session(self, path: Path | None = None) -> None:
        """Ask the storage manager to restore a historic session."""

        self.storage_restore_requested.emit(path)

    def request_export_to_csv(self, export_path: Path, columns: list[str] | None = None) -> None:
        """Request the current dataset to be exported to CSV."""

        self.storage_export_requested.emit((export_path, columns))

    def update_description(self, description: str) -> None:
        """Forward experiment description updates to storage manager."""

        self.storage_description_change_requested.emit(description)

    @QtCore.pyqtSlot(object)
    @staticmethod
    def _on_devices_discovered(devices: object) -> None:
        """Log discovered devices (currently unused)."""
        logger.debug("Devices discovered: %s", devices)

    @QtCore.pyqtSlot(object)
    def _on_acquisition_state_changed(self, running: bool) -> None:
        self._is_device_running = running
