import logging
from typing import TYPE_CHECKING

from PyQt6 import QtCore, QtWidgets

from msms.ui.managers import DeviceManager, ExperimentManager, StorageManager

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path

    from msms.ui.experiment.step_base import Step
    from msms.ui.managers.storage_manager import DataRepository

logger = logging.getLogger(__name__)


class ApplicationController(QtCore.QObject):  # noqa: PLR0904
    device_acquisition_start_requested = QtCore.pyqtSignal()
    device_acquisition_stop_requested = QtCore.pyqtSignal()
    device_selection_requested = QtCore.pyqtSignal(object)
    device_discovery_start_requested = QtCore.pyqtSignal(object)
    device_discovery_stop_requested = QtCore.pyqtSignal()
    device_interval_change_requested = QtCore.pyqtSignal(object)
    device_shutdown_requested = QtCore.pyqtSignal()
    device_info_requested = QtCore.pyqtSignal()
    device_command_requested = QtCore.pyqtSignal(object, object)
    device_info_collected = QtCore.pyqtSignal(object)
    devices_discovered = QtCore.pyqtSignal(object)

    storage_restore_requested = QtCore.pyqtSignal(object)
    storage_export_requested = QtCore.pyqtSignal(object)
    storage_description_change_requested = QtCore.pyqtSignal(object)
    storage_session_start_requested = QtCore.pyqtSignal()
    storage_stop_requested = QtCore.pyqtSignal()

    experiment_start_requested = QtCore.pyqtSignal()
    experiment_stop_requested = QtCore.pyqtSignal()
    experiment_skip_forward_requested = QtCore.pyqtSignal()
    experiment_set_steps_requested = QtCore.pyqtSignal(object)
    experiment_get_steps_requested = QtCore.pyqtSignal()

    experiment_steps_changed = QtCore.pyqtSignal(object)
    experiment_current_step_changed = QtCore.pyqtSignal(object)

    def __init__(self, interval_ms: int = 500) -> None:
        super().__init__()

        self.current_interval_ms = interval_ms

        self.device_manager = DeviceManager(interval_ms=interval_ms)
        self.storage_manager = StorageManager()
        self.experiment_manager = ExperimentManager()

        self.device_manager_thread = QtCore.QThread()
        self.storage_manager_thread = QtCore.QThread()
        self.experiment_manager_thread = QtCore.QThread()
        self.device_manager.moveToThread(self.device_manager_thread)
        self.storage_manager.moveToThread(self.storage_manager_thread)
        self.experiment_manager.moveToThread(self.experiment_manager_thread)

        self.storage_manager_thread.started.connect(self.storage_manager.on_session_start_request)
        self.device_manager_thread.started.connect(self.device_manager.on_setup)

        self.device_acquisition_start_requested.connect(self.device_manager.on_acquisition_start_request)
        self.device_acquisition_stop_requested.connect(self.device_manager.on_acquisition_stop_request)
        self.device_selection_requested.connect(self.device_manager.on_device_select_request)
        self.device_discovery_start_requested.connect(self.device_manager.on_discovery_start_request)
        self.device_discovery_stop_requested.connect(self.device_manager.on_discovery_stop_request)
        self.device_interval_change_requested.connect(self.device_manager.on_interval_change_request)
        self.device_shutdown_requested.connect(self.device_manager.on_shutdown)
        self.device_info_requested.connect(self.device_manager.on_device_info_request)
        self.device_command_requested.connect(self.device_manager.on_device_command_request)

        self.device_manager.devices_discovered.connect(self.devices_discovered)
        self.device_manager.device_info_collected.connect(self.device_info_collected)
        self.device_manager.acquisition_state_changed.connect(self._on_acquisition_state_changed)

        self.storage_restore_requested.connect(self.storage_manager.on_session_restore_request)
        self.storage_export_requested.connect(self.storage_manager.on_export_request)
        self.storage_description_change_requested.connect(self.storage_manager.on_description_change_request)
        self.storage_stop_requested.connect(self.storage_manager.on_stop_request)
        self.storage_session_start_requested.connect(self.storage_manager.on_session_start_request)

        self.device_manager.data_initialized.connect(self.storage_manager.on_header_set_request)
        self.device_manager.data_collected.connect(self.storage_manager.on_data_append_request)

        self.experiment_start_requested.connect(self.experiment_manager.on_start_request)
        self.experiment_stop_requested.connect(self.experiment_manager.on_stop_request)
        self.experiment_skip_forward_requested.connect(self.experiment_manager.on_skip_forward_request)
        self.experiment_set_steps_requested.connect(self.experiment_manager.on_set_steps)
        self.experiment_get_steps_requested.connect(self.experiment_manager.on_get_steps_request)

        self.storage_manager.new_data_row.connect(self.experiment_manager.on_data_update)
        self.experiment_manager.experiment_log_updated.connect(self.storage_manager.on_experiment_log_update)
        self.experiment_manager.device_command_requested.connect(self.device_command_requested)
        self.experiment_manager.steps_changed.connect(self.experiment_steps_changed)
        self.experiment_manager.current_step_changed.connect(self.experiment_current_step_changed)

        self.storage_manager_thread.start()
        self.device_manager_thread.start()
        self.experiment_manager_thread.start()

        self._selected_device_addresses: list[str] = []
        self._is_device_running = False

    @property
    def is_acquiring(self) -> bool:
        return self._is_device_running

    @property
    def data_repository(self) -> DataRepository:
        """Provide controlled read access to storage manager's data repository."""
        return self.storage_manager._data_repository  # noqa: SLF001

    def get_last_used_file(self) -> Path | None:
        """Get the path to the last used session file.

        Returns:
            Path to last session file, or None if no session exists.
        """
        return self.storage_manager.get_last_used_file()

    def start_discovery(self, interval_ms: int = 2000) -> None:
        """Start periodic device discovery polling.

        Args:
            interval_ms: Discovery polling interval in milliseconds.
        """
        self.device_discovery_start_requested.emit(interval_ms)

    def stop_discovery(self) -> None:
        """Stop periodic device discovery polling."""
        self.device_discovery_stop_requested.emit()

    def start_acquisition(self) -> None:
        """Start device acquisition."""
        if self.is_acquiring:
            return

        if not self._selected_device_addresses:
            logger.warning("Cannot start acquisition without selected devices")
            return

        logger.info("Starting acquisition")
        self.device_interval_change_requested.emit(self.current_interval_ms)
        # self.storage_stop_requested.emit()
        # self.storage_session_start_requested.emit()
        self.device_selection_requested.emit(self._selected_device_addresses)
        self.device_acquisition_start_requested.emit()

    def stop_acquisition(self) -> None:
        """Stop device acquisition."""
        if not self.is_acquiring:
            return

        logger.info("Stopping acquisition")
        self.device_acquisition_stop_requested.emit()
        # Also stop experiment if running
        if self.experiment_manager.is_running:
            self.experiment_stop_requested.emit()

    def set_interval(self, interval_ms: int) -> None:
        """Change the acquisition interval.

        Args:
            interval_ms: New polling interval in milliseconds.
        """
        self.current_interval_ms = interval_ms
        self.device_interval_change_requested.emit(interval_ms)

    def shutdown(self) -> None:
        """Clean up threads and resources."""
        logger.info("Shutting down application controller")

        self.device_shutdown_requested.emit()
        self.storage_stop_requested.emit()

        QtWidgets.QApplication.processEvents()

        self.device_manager_thread.quit()
        self.storage_manager_thread.quit()
        self.experiment_manager_thread.quit()

        device_finished = self.device_manager_thread.wait(500)
        if not device_finished:
            logger.warning("Device manager thread did not finish within timeout")

        storage_finished = self.storage_manager_thread.wait(500)
        if not storage_finished:
            logger.warning("Storage manager thread did not finish within timeout")

        experiment_finished = self.experiment_manager_thread.wait(500)
        if not experiment_finished:
            logger.warning("Experiment manager thread did not finish within timeout")

    def update_selected_devices(self, addresses: list[str]) -> None:
        """Update the set of selected device VISA addresses."""

        self._selected_device_addresses = addresses
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

    def request_device_info(self) -> None:
        """Request device information from device manager."""

        self.device_info_requested.emit()

    def send_device_command(self, address: str, command: str) -> None:
        """Send command to specific device.

        Args:
            address: VISA resource address of target device.
            command: SCPI command to send.
        """

        self.device_command_requested.emit(address, command)

    @QtCore.pyqtSlot(object)
    def _on_acquisition_state_changed(self, running: bool) -> None:
        self._is_device_running = running

    def start_experiment(self) -> None:
        """Start experiment execution."""
        self.experiment_start_requested.emit()

    def stop_experiment(self) -> None:
        """Stop experiment execution."""
        self.experiment_stop_requested.emit()

    def skip_experiment_forward(self) -> None:
        """Skip to next step in experiment."""
        self.experiment_skip_forward_requested.emit()

    def set_experiment_steps(self, steps: list[Step]) -> None:
        """Replace experiment plan with new steps."""
        self.experiment_set_steps_requested.emit(steps)

    def get_current_step(self) -> Step | None:
        """Get currently executing step."""
        return self.experiment_manager.current_step

    def get_next_step(self) -> Step | None:
        """Get next step to execute."""
        return self.experiment_manager.next_step

    def is_experiment_running(self) -> bool:
        """Check if experiment is running."""
        return self.experiment_manager.is_running

    def get_experiment_log(self) -> list[tuple[str, str, datetime | None]]:
        """Get execution history with timestamps."""
        return self.experiment_manager.get_execution_log()

    def request_experiment_steps(self) -> None:
        """Request current experiment steps from manager."""
        self.experiment_get_steps_requested.emit()

    def generate_step_id(self) -> int:
        """Generate unique step ID using thread-safe counter.

        Returns:
            Next sequential step ID from experiment manager.
        """
        return self.experiment_manager.threaded_new_step_id()
