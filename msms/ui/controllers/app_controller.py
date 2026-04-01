import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtWidgets

from msms.ui.managers import AutomationManager, DeviceManager, StorageManager

if TYPE_CHECKING:
    from msms.connectivity.device_repository import DiscoveredDevice
    from msms.ui.main_window import MainWindow
    from msms.ui.managers.storage_manager import DataRepository


logger = logging.getLogger(__name__)


@dataclass
class AppManagers:
    """Container for all application managers.

    Provides structured access to device, storage, and automation managers.
    """

    device: DeviceManager
    storage: StorageManager
    automation: AutomationManager


class ApplicationController(QtCore.QObject):
    """Coordinates threads and connects signals between components and managers.

    This controller's sole responsibility is thread management and signal routing.
    It owns minimal internal signals only for shutdown coordination - all other
    signals are owned by UI components and connected by this controller.
    """

    # Internal signals for shutdown coordination
    _device_shutdown_requested = QtCore.Signal()
    _storage_shutdown_requested = QtCore.Signal()
    _automation_shutdown_requested = QtCore.Signal()

    def __init__(self, interval_ms: int = 3000) -> None:
        super().__init__()

        self.current_interval_ms = interval_ms

        # Create managers
        device_manager = DeviceManager(interval_ms=interval_ms)
        storage_manager = StorageManager()
        automation_manager = AutomationManager()

        self.managers = AppManagers(
            device=device_manager,
            storage=storage_manager,
            automation=automation_manager,
        )

        # Create threads
        self.device_manager_thread = QtCore.QThread()
        self.storage_manager_thread = QtCore.QThread()
        self.automation_manager_thread = QtCore.QThread()

        # Move managers to threads
        self.managers.device.moveToThread(self.device_manager_thread)
        self.managers.storage.moveToThread(self.storage_manager_thread)
        self.managers.automation.moveToThread(self.automation_manager_thread)

        # Connect thread started signals to on_setup methods
        self.device_manager_thread.started.connect(self.managers.device.on_setup)
        self.storage_manager_thread.started.connect(self.managers.storage.on_setup)
        self.automation_manager_thread.started.connect(self.managers.automation.on_setup)

        # Connect manager-to-manager signals
        self._connect_device_to_storage()
        self._connect_storage_to_automation()
        self._connect_automation_to_device()

        # Start threads
        self.storage_manager_thread.start()
        self.device_manager_thread.start()
        self.automation_manager_thread.start()

        self._device_info_cache: dict[str, DiscoveredDevice] = {}
        self.managers.device.device_info_collected.connect(self._on_device_info_collected)

        # Connect internal shutdown signals
        self._device_shutdown_requested.connect(self.managers.device.on_shutdown)
        self._storage_shutdown_requested.connect(self.managers.storage.on_stop_request)
        self._automation_shutdown_requested.connect(self.managers.automation.on_stop_request)

    def connect_main_window_signals(self, main_window: MainWindow) -> None:
        """Connect MainWindow signals to manager slots.

        Args:
            main_window: MainWindow instance with signals to connect.
        """
        # Device signals
        main_window.device_acquisition_start_requested.connect(self.managers.device.on_acquisition_start_request)
        main_window.device_acquisition_stop_requested.connect(self.managers.device.on_acquisition_stop_request)
        main_window.device_selection_requested.connect(self.managers.device.on_device_select_request)
        main_window.device_interval_change_requested.connect(self.managers.device.on_interval_change_request)

        # Storage signals
        main_window.storage_restore_requested.connect(self.managers.storage.on_session_restore_request)
        main_window.storage_export_requested.connect(self.managers.storage.on_export_request)
        main_window.storage_description_change_requested.connect(self.managers.storage.on_description_change_request)
        main_window.storage_stop_requested.connect(self.managers.storage.on_stop_request)
        main_window.storage_session_start_requested.connect(self.managers.storage.on_session_start_request)

        # Automation signals
        main_window.automation_start_requested.connect(self.managers.automation.on_start_request)
        main_window.automation_stop_requested.connect(self.managers.automation.on_stop_request)
        main_window.automation_skip_forward_requested.connect(self.managers.automation.on_skip_step_request)

    def _connect_device_to_storage(self) -> None:
        """Connect device manager signals to storage manager slots."""
        self.managers.device.data_initialized.connect(self.managers.storage.on_header_set_request)
        self.managers.device.data_collected.connect(self.managers.storage.on_data_append_request)

    def _connect_storage_to_automation(self) -> None:
        """Connect storage manager signals to automation manager slots."""
        self.managers.storage.new_data_row.connect(self.managers.automation.on_data_update)

    def _connect_automation_to_device(self) -> None:
        """Connect automation manager signals to device manager slots."""
        self.managers.automation.automation_log_changed.connect(self.managers.storage.on_automation_log_update)
        self.managers.automation.device_command_requested.connect(self.managers.device.on_device_command_request)
        self.managers.automation.device_acquisition_start_requested.connect(self.managers.device.on_acquisition_start_request)
        self.managers.automation.device_acquisition_stop_requested.connect(self.managers.device.on_acquisition_stop_request)

    @property
    def data_repository(self) -> DataRepository:
        """Provide controlled read access to storage manager's data repository."""
        return self.managers.storage._data_repository  # noqa: SLF001

    @property
    def device_info_cache(self) -> dict[str, DiscoveredDevice]:
        """Provide read access to cached device info."""
        return self._device_info_cache

    @QtCore.Slot(object)
    def _on_device_info_collected(self, info: dict[str, DiscoveredDevice]) -> None:
        """Cache latest device info collected from device manager."""
        self._device_info_cache = info

    def shutdown(self) -> None:
        """Clean up threads and resources."""
        logger.info("Shutting down application controller")

        self._device_shutdown_requested.emit()
        self._storage_shutdown_requested.emit()
        self._automation_shutdown_requested.emit()

        QtWidgets.QApplication.processEvents()

        # Quit threads
        self.device_manager_thread.quit()
        self.storage_manager_thread.quit()
        self.automation_manager_thread.quit()

        # Wait for threads to finish
        device_finished = self.device_manager_thread.wait(500)
        if not device_finished:
            logger.warning("Device manager thread did not finish within timeout")

        storage_finished = self.storage_manager_thread.wait(500)
        if not storage_finished:
            logger.warning("Storage manager thread did not finish within timeout")

        automation_finished = self.automation_manager_thread.wait(500)
        if not automation_finished:
            logger.warning("Automation manager thread did not finish within timeout")
