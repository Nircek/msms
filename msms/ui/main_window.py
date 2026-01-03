import logging
from pathlib import Path

import pyqtgraph as pg  # type: ignore
from git import Repo
from PySide6 import QtCore, QtGui, QtWidgets

from msms.ui.controllers import (
    ApplicationController,
    CommentController,
    ControlsController,
    DisplayController,
    DisplayWidgets,
    PlotController,
)
from msms.ui.dialogs import (
    AutomationDialog,
    DeviceCommandDialog,
    DeviceSelectionDialog,
    ExportDialog,
    MarkdownViewerDialog,
)
from msms.ui.ui_main_window import Ui_MainWindow

logger = logging.getLogger(__name__)


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    # Device signals
    device_acquisition_start_requested = QtCore.Signal()
    device_acquisition_stop_requested = QtCore.Signal()
    device_selection_requested = QtCore.Signal(object)
    device_interval_change_requested = QtCore.Signal(object)

    # Storage signals
    storage_restore_requested = QtCore.Signal(object)
    storage_export_requested = QtCore.Signal(object)
    storage_description_change_requested = QtCore.Signal(object)
    storage_session_start_requested = QtCore.Signal()
    storage_stop_requested = QtCore.Signal()

    # Automation signals
    automation_start_requested = QtCore.Signal()
    automation_stop_requested = QtCore.Signal()
    automation_skip_forward_requested = QtCore.Signal()

    def center_on_screen(self) -> None:
        """Move the window to the center of the primary screen."""

        screen = QtWidgets.QApplication.primaryScreen()
        assert screen is not None
        screen_geometry = screen.availableGeometry()
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(screen_geometry.center())
        self.move(window_geometry.topLeft())

    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)
        self.center_on_screen()

        self.app_controller = ApplicationController(interval_ms=500)
        self._selected_device_addresses: list[str] = []

        self.plot_controller = PlotController(
            self.plotWidget,
            self.autoFollowCheckBox,
            self.xAxisPushButton,
            self.yAxisPushButton,
            self.app_controller.data_repository,
        )
        self.controls_controller = ControlsController(
            placeholder=self.controlsPlaceholder,
            app_controller=self.app_controller,
        )
        self.display_controller = DisplayController(
            DisplayWidgets(
                time_label=self.timeValue,
                number_label=self.numberValue,
                sample_label=self.sampleValue,
                control_label=self.controlValue,
                set_point_label=self.setPointValue,
                ramp_label=self.rampValue,
                variables_text=self.variablesTextEdit,
                status_layout=self.experimentStatusLayoutWidget,
            )
        )
        self.comment_controller = CommentController(
            comment_text_edit=self.commentPlainTextEdit,
            parent_window=self,
        )

        # Connect MainWindow signals to managers
        self.app_controller.connect_main_window_signals(self)

        storage_manager = self.app_controller.managers.storage
        storage_manager.new_data_row.connect(self.on_update_data_labels)
        storage_manager.new_data_row.connect(lambda _data: self.plot_controller.refresh_data_from_repository())
        storage_manager.columns_changed.connect(self.plot_controller.on_columns_change)
        storage_manager.description_changed.connect(self.comment_controller.on_description_changed)
        storage_manager.restore_failed.connect(self._on_restore_failed)
        storage_manager.export_completed.connect(self._on_export_completed)
        storage_manager.export_failed.connect(self._on_export_failed)

        # Connect controls controller signals
        self.controls_controller.device_selection_requested.connect(self._handle_device_selection)
        self.controls_controller.acquisition_start_requested.connect(self.device_acquisition_start_requested.emit)
        self.controls_controller.acquisition_stop_requested.connect(self.device_acquisition_stop_requested.emit)
        self.controls_controller.manual_measurement_requested.connect(
            self.app_controller.managers.device.on_devices_poll_request
        )
        self.controls_controller.interval_change_requested.connect(self._on_interval_change)
        self.controls_controller.automation_edit_requested.connect(self.on_actionManageAutomation_triggered)
        self.controls_controller.automation_start_requested.connect(self.automation_start_requested.emit)
        self.controls_controller.automation_stop_requested.connect(self.automation_stop_requested.emit)
        self.controls_controller.automation_skip_requested.connect(self.automation_skip_forward_requested.emit)

        self.comment_controller.description_changed.connect(self.storage_description_change_requested.emit)

        pg.setConfigOptions(antialias=True)

    @QtCore.Slot()
    def on_actionRestoreLastFile_triggered(self) -> None:
        """Restore the last recorded session from disk if available."""
        last_file = self.app_controller.managers.storage.get_last_used_file()
        if last_file is not None and last_file.exists():
            self.storage_restore_requested.emit(last_file)
        else:
            self.storage_restore_requested.emit(None)

    @QtCore.Slot()
    def _handle_device_selection(self) -> None:
        """Show dialog for selecting devices to poll."""
        if self._selected_device_addresses:
            return

        dialog = DeviceSelectionDialog(self, app_controller=self.app_controller)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            selected_addresses = dialog.get_selected_addresses()
            logger.info("Selected devices: %s", selected_addresses)
            self._selected_device_addresses = selected_addresses

            # Clear any restored session state - we're starting fresh acquisition
            # Stop any running managers and reset to clean state
            self.storage_stop_requested.emit()
            self.storage_session_start_requested.emit()

            self._selected_device_addresses = selected_addresses
            self.device_selection_requested.emit(selected_addresses)

            # Notify controls controller that devices were selected
            self.controls_controller.on_devices_selected()

    @QtCore.Slot()
    def on_actionManageAutomation_triggered(self) -> None:
        """Show automation management dialog."""
        if not self._selected_device_addresses:
            QtWidgets.QMessageBox.warning(
                self,
                "No Devices Selected",
                "Please select devices first using Devices → Select Devices before managing automation.",
            )
            return

        # Check if acquisition has started (which initializes columns)
        if not self.app_controller.data_repository.columns:
            QtWidgets.QMessageBox.warning(
                self,
                "No Data Columns Available",
                "Please start acquisition first to initialize data columns before managing automation.",
            )
            return

        dialog = AutomationDialog(self, app_controller=self.app_controller)
        dialog.exec()

    @QtCore.Slot(int)
    def _on_interval_change(self, interval_ms: int) -> None:
        """Handle interval change from controls controller."""
        logger.info("Changing device manager interval to %d ms", interval_ms)
        self.app_controller.current_interval_ms = interval_ms
        self.device_interval_change_requested.emit(interval_ms)

    @QtCore.Slot()
    def on_actionExport_triggered(self) -> None:
        """Export current data to CSV file with customizable options."""
        # Get available columns from storage manager
        columns = self.app_controller.data_repository.columns
        if not columns:
            QtWidgets.QMessageBox.information(
                self,
                "No Data Available",
                "No data available to export. Start acquisition first.",
            )
            return

        # Show export dialog
        dialog = ExportDialog(self, available_columns=list(columns))
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        export_path = dialog.get_selected_path()
        if not export_path:
            return

        selected_columns = dialog.get_selected_columns()
        include_comments = dialog.get_include_comments()
        include_automation_log = dialog.get_include_automation_log()

        logger.info(
            "Exporting data to %s (columns: %d, comments: %s, automation log: %s)",
            export_path,
            len(selected_columns),
            include_comments,
            include_automation_log,
        )
        self.storage_export_requested.emit((export_path, selected_columns, include_comments, include_automation_log))

    @QtCore.Slot()
    def on_actionHelp_triggered(self) -> None:
        """Show help dialog with README content."""
        readme_path = Path(__file__).parent.parent.parent / "README.md"
        dialog = MarkdownViewerDialog.from_file(self, readme_path, "MSMS - Help")
        dialog.exec()

    @QtCore.Slot()
    def on_actionAbout_triggered(self) -> None:
        """Show about dialog."""
        repo = Repo(Path(__file__).parent.parent.parent)
        commit = repo.head.commit
        date = commit.committed_datetime.strftime("%Y-%m-%dT%H:%M:%S%z")

        about_text = f"""
        <h2>MSMS</h2>
        <p>Measurement System Management Software</p>
        <p>Version {date} {commit.hexsha}</p>
        <p>A PyQt6-based application for managing laboratory measurement devices.</p>
        """
        QtWidgets.QMessageBox.about(self, "About MSMS", about_text)

    @QtCore.Slot()
    def on_actionSendDeviceCommand_triggered(self) -> None:
        """Open device command dialog."""
        dialog = DeviceCommandDialog(self, self.app_controller)
        dialog.exec()

    @QtCore.Slot(object)
    def on_update_data_labels(self, data: dict[str, float | str]) -> None:
        """Update UI labels and all relevant views with the latest data payload."""
        self.display_controller.update_labels(data)

    @QtCore.Slot(object)
    def _on_restore_failed(self, message: str) -> None:
        QtWidgets.QMessageBox.information(self, "Restore Session", message)

    @QtCore.Slot(object)
    def _on_export_completed(self, path: str) -> None:
        QtWidgets.QMessageBox.information(self, "Export Completed", f"Data exported to {path}")

    @QtCore.Slot(object)
    def _on_export_failed(self, message: str) -> None:
        QtWidgets.QMessageBox.warning(self, "Export Failed", message)

    @QtCore.Slot()
    def on_actionQuit_triggered(self) -> None:
        """Quit the application."""
        self.close()

    def closeEvent(self, event: QtGui.QCloseEvent | None) -> None:
        """Ensure worker threads are stopped before window closes."""

        self.app_controller.shutdown()
        logger.info("Shutdown complete, accepting close event")
        if event:
            event.accept()
