import logging
from pathlib import Path

import pyqtgraph as pg  # type: ignore
from git import Repo
from PySide6 import QtCore, QtGui, QtWidgets

from msms.ui.controllers.app_controller import ApplicationController
from msms.ui.controllers.automation_controller import AutomationController
from msms.ui.controllers.comment_controller import CommentController
from msms.ui.controllers.display_controller import DisplayController, DisplayWidgets
from msms.ui.controllers.plot_controller import PlotController
from msms.ui.dialogs import (
    AutomationDialog,
    DeviceCommandDialog,
    DeviceSelectionDialog,
    MarkdownViewerDialog,
)
from msms.ui.ui_main_window import Ui_MainWindow

logger = logging.getLogger(__name__)

# Interval constants in milliseconds
INTERVAL_0_1S_MS = 100
INTERVAL_0_5S_MS = 500
INTERVAL_1_0S_MS = 1000
INTERVAL_2_0S_MS = 2000
INTERVAL_5_0S_MS = 5000


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
        self.display_controller = DisplayController(
            DisplayWidgets(
                time_label=self.timeValue,
                number_label=self.numberValue,
                sample_label=self.sampleValue,
                control_label=self.controlValue,
                set_point_label=self.setPointValue,
                ramp_label=self.rampValue,
                variables_text=self.variablesTextEdit,
                status_layout=self.automationStatusLayoutWidget,
            )
        )
        self.automation_controller = AutomationController(
            automation_plan_text=self.automationPlanTextEdit,
            app_controller=self.app_controller,
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

        self.comment_controller.description_changed.connect(self.storage_description_change_requested.emit)

        pg.setConfigOptions(antialias=True)

        # Connect interval actions
        self.actionInterval_0_1s.triggered.connect(lambda: self._set_interval(INTERVAL_0_1S_MS))
        self.actionInterval_0_5s.triggered.connect(lambda: self._set_interval(INTERVAL_0_5S_MS))
        self.actionInterval_1_0s.triggered.connect(lambda: self._set_interval(INTERVAL_1_0S_MS))
        self.actionInterval_2_0s.triggered.connect(lambda: self._set_interval(INTERVAL_2_0S_MS))
        self.actionInterval_5_0s.triggered.connect(lambda: self._set_interval(INTERVAL_5_0S_MS))

        self._update_interval_checks()

    @QtCore.Slot()
    def on_actionRestoreLastFile_triggered(self) -> None:
        """Restore the last recorded session from disk if available."""
        last_file = self.app_controller.managers.storage.get_last_used_file()
        if last_file is not None and last_file.exists():
            self.storage_restore_requested.emit(last_file)
        else:
            self.storage_restore_requested.emit(None)

    @QtCore.Slot()
    def on_actionSelectDevices_triggered(self) -> None:
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

    @QtCore.Slot()
    def on_actionExport_triggered(self) -> None:
        """Export current data to CSV file."""
        dialog = QtWidgets.QFileDialog(self)
        dialog.setWindowTitle("Export Data to CSV")
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptMode.AcceptSave)
        dialog.setNameFilter("CSV Files (*.csv)")
        dialog.setDefaultSuffix("csv")
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            export_path = Path(dialog.selectedFiles()[0])
            logger.info("Exporting data to CSV file: %s", export_path)
            self.storage_export_requested.emit((export_path, None))

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
    def on_actionStartAcquisition_triggered(self) -> None:
        """Start device acquisition."""
        if not self._selected_device_addresses:
            QtWidgets.QMessageBox.warning(
                self,
                "Select Devices",
                "Select at least one device before starting acquisition.",
            )
            return

        logger.info("Starting device manager with interval %d ms", self.app_controller.current_interval_ms)
        self.device_interval_change_requested.emit(self.app_controller.current_interval_ms)
        self.device_selection_requested.emit(self._selected_device_addresses)
        self.device_acquisition_start_requested.emit()

    @QtCore.Slot()
    def on_actionStopAcquisition_triggered(self) -> None:
        """Stop device acquisition."""
        logger.info("Stopping device manager")
        self.device_acquisition_stop_requested.emit()
        # Also stop automation if running
        if self.app_controller.managers.automation.is_running:
            self.automation_stop_requested.emit()

    @QtCore.Slot()
    def on_actionSendDeviceCommand_triggered(self) -> None:
        """Open device command dialog."""
        dialog = DeviceCommandDialog(self, self.app_controller)
        dialog.exec()

    def _set_interval(self, value_ms: int) -> None:
        """Change acquisition interval."""
        logger.info("Changing device manager interval to %d ms", value_ms)
        self.app_controller.current_interval_ms = value_ms
        self.device_interval_change_requested.emit(value_ms)
        self._update_interval_checks()

    def _update_interval_checks(self) -> None:
        """Update checkmarks on interval menu items."""
        current = self.app_controller.current_interval_ms
        self.actionInterval_0_1s.setChecked(current == INTERVAL_0_1S_MS)
        self.actionInterval_0_5s.setChecked(current == INTERVAL_0_5S_MS)
        self.actionInterval_1_0s.setChecked(current == INTERVAL_1_0S_MS)
        self.actionInterval_2_0s.setChecked(current == INTERVAL_2_0S_MS)
        self.actionInterval_5_0s.setChecked(current == INTERVAL_5_0S_MS)

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
    def on_actionStartAutomation_triggered(self) -> None:
        """Start automation execution."""
        # Check if automation plan exists by checking execution log
        if not self.app_controller.managers.automation.get_execution_log():
            QtWidgets.QMessageBox.warning(
                self,
                "No Automation Plan",
                "Please create an automation plan first using Automation → Manage Automation.",
            )
            return
        self.automation_start_requested.emit()
        logger.info("Automation started")

    @QtCore.Slot()
    def on_actionStopAutomation_triggered(self) -> None:
        """Stop automation execution."""
        self.automation_stop_requested.emit()
        logger.info("Automation stopped")

    @QtCore.Slot()
    def on_actionSkipToNext_triggered(self) -> None:
        """Skip to next step in automation."""
        self.automation_skip_forward_requested.emit()
        logger.info("Skipped to next step")

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
