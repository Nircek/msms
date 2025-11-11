import logging
from pathlib import Path

import pyqtgraph as pg  # type: ignore
from PyQt6 import QtCore, QtGui, QtWidgets, uic

from msms.ui.controllers.app_controller import ApplicationController
from msms.ui.controllers.display_controller import DisplayController, DisplayWidgets
from msms.ui.controllers.experiment_controller import ExperimentController
from msms.ui.controllers.plot_controller import PlotController
from msms.ui.dialogs import (
    DescriptionDialog,
    DeviceCommandDialog,
    DeviceSelectionDialog,
    ExperimentDialog,
    MarkdownViewerDialog,
)

logger = logging.getLogger(__name__)

# Interval constants in milliseconds
INTERVAL_0_1S_MS = 100
INTERVAL_0_5S_MS = 500
INTERVAL_1_0S_MS = 1000
INTERVAL_2_0S_MS = 2000
INTERVAL_5_0S_MS = 5000


class MainWindowUic(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        ui_file = Path(__file__).parent / "main_window.ui"
        uic.loadUi(str(ui_file), self)
        self.center_on_screen()
        self.autoFollowCheckBox: QtWidgets.QCheckBox
        self.chartConfigPushButton: QtWidgets.QPushButton
        self.plotWidget: pg.PlotWidget
        self.experimentStatusLayoutWidget: QtWidgets.QWidget
        self.timeValue: QtWidgets.QLabel
        self.numberValue: QtWidgets.QLabel
        self.sampleValue: QtWidgets.QLabel
        self.controlValue: QtWidgets.QLabel
        self.setPointValue: QtWidgets.QLabel
        self.rampValue: QtWidgets.QLabel
        self.experimentPlanTextEdit: QtWidgets.QTextEdit
        self.commentPlainTextEdit: QtWidgets.QPlainTextEdit
        self.variablesTextEdit: QtWidgets.QTextEdit
        self.menuFile: QtWidgets.QMenu
        self.menuDevices: QtWidgets.QMenu
        self.menuAcquisition: QtWidgets.QMenu
        self.menuExperiment: QtWidgets.QMenu
        self.menuHelp: QtWidgets.QMenu
        self.menuSetInterval: QtWidgets.QMenu
        self.actionSelectDevices: QtGui.QAction
        self.actionManageExperiment: QtGui.QAction
        self.actionDescribe: QtGui.QAction
        self.actionExport: QtGui.QAction
        self.actionRestoreLastFile: QtGui.QAction
        self.actionAbout: QtGui.QAction
        self.actionHelp: QtGui.QAction
        self.actionStartAcquisition: QtGui.QAction
        self.actionStopAcquisition: QtGui.QAction
        self.actionSendDeviceCommand: QtGui.QAction
        self.actionInterval_0_1s: QtGui.QAction
        self.actionInterval_0_5s: QtGui.QAction
        self.actionInterval_1_0s: QtGui.QAction
        self.actionInterval_2_0s: QtGui.QAction
        self.actionInterval_5_0s: QtGui.QAction
        self.actionStartExperiment: QtGui.QAction
        self.actionStopExperiment: QtGui.QAction
        self.actionSkipToNext: QtGui.QAction
        self.actionQuit: QtGui.QAction

    def center_on_screen(self) -> None:
        """Move the window to the center of the primary screen."""

        screen = QtWidgets.QApplication.primaryScreen()
        assert screen is not None
        screen_geometry = screen.availableGeometry()
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(screen_geometry.center())
        self.move(window_geometry.topLeft())


class MainWindow(MainWindowUic):  # noqa: PLR0904
    # Device signals
    device_acquisition_start_requested = QtCore.pyqtSignal()
    device_acquisition_stop_requested = QtCore.pyqtSignal()
    device_selection_requested = QtCore.pyqtSignal(object)
    device_interval_change_requested = QtCore.pyqtSignal(object)

    # Storage signals
    storage_restore_requested = QtCore.pyqtSignal(object)
    storage_export_requested = QtCore.pyqtSignal(object)
    storage_description_change_requested = QtCore.pyqtSignal(object)
    storage_session_start_requested = QtCore.pyqtSignal()
    storage_stop_requested = QtCore.pyqtSignal()

    # Experiment signals
    experiment_start_requested = QtCore.pyqtSignal()
    experiment_stop_requested = QtCore.pyqtSignal()
    experiment_skip_forward_requested = QtCore.pyqtSignal()

    def __init__(self) -> None:
        super().__init__()

        self.chart_columns = ["time", "number", "dt"]
        self.current_chart_column = "timestamp"

        self.app_controller = ApplicationController(interval_ms=500)
        self._selected_device_addresses: list[str] = []

        # Connect MainWindow signals to managers
        self.app_controller.connect_main_window_signals(self)

        storage_manager = self.app_controller.managers.storage
        storage_manager.new_data_row.connect(self.on_update_data_labels)
        storage_manager.new_data_row.connect(lambda _data: self.refresh_plot())
        storage_manager.columns_changed.connect(self.on_columns_change)
        storage_manager.description_changed.connect(self._on_description_changed)
        storage_manager.restore_failed.connect(self._on_restore_failed)
        storage_manager.export_completed.connect(self._on_export_completed)
        storage_manager.export_failed.connect(self._on_export_failed)

        pg.setConfigOptions(antialias=True)
        self.plot_controller = PlotController(self.plotWidget, self.autoFollowCheckBox)
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
        self.experiment_controller = ExperimentController(
            experiment_plan_text=self.experimentPlanTextEdit,
            app_controller=self.app_controller,
        )

        # Connect interval actions
        self.actionInterval_0_1s.triggered.connect(lambda: self._set_interval(INTERVAL_0_1S_MS))
        self.actionInterval_0_5s.triggered.connect(lambda: self._set_interval(INTERVAL_0_5S_MS))
        self.actionInterval_1_0s.triggered.connect(lambda: self._set_interval(INTERVAL_1_0S_MS))
        self.actionInterval_2_0s.triggered.connect(lambda: self._set_interval(INTERVAL_2_0S_MS))
        self.actionInterval_5_0s.triggered.connect(lambda: self._set_interval(INTERVAL_5_0S_MS))

        self._update_interval_checks()

    def refresh_plot(self) -> None:
        """Update plot with latest data from repository."""
        self.plot_controller.refresh_from_repository(self.app_controller.data_repository)

    @QtCore.pyqtSlot()
    def on_actionRestoreLastFile_triggered(self) -> None:
        """Restore the last recorded session from disk if available."""
        last_file = self.app_controller.managers.storage.get_last_used_file()
        if last_file is not None and last_file.exists():
            self.storage_restore_requested.emit(last_file)
        else:
            self.storage_restore_requested.emit(None)

    @QtCore.pyqtSlot()
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

    @QtCore.pyqtSlot()
    def on_actionManageExperiment_triggered(self) -> None:
        """Show experiment management dialog."""
        if not self._selected_device_addresses:
            QtWidgets.QMessageBox.warning(
                self,
                "No Devices Selected",
                "Please select devices first using Devices → Select Devices before managing experiments.",
            )
            return

        # Check if acquisition has started (which initializes columns)
        if not self.app_controller.data_repository.columns:
            QtWidgets.QMessageBox.warning(
                self,
                "No Data Columns Available",
                "Please start acquisition first to initialize data columns before managing experiments.",
            )
            return

        dialog = ExperimentDialog(self, app_controller=self.app_controller)
        dialog.exec()

    @QtCore.pyqtSlot()
    def on_actionDescribe_triggered(self) -> None:
        """Show dialog for editing the experiment description."""
        current_description = self.commentPlainTextEdit.toPlainText()
        dialog = DescriptionDialog(self, current_description)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            description = dialog.get_description()
            self.commentPlainTextEdit.setPlainText(description)
            self.storage_description_change_requested.emit(description)

    @QtCore.pyqtSlot()
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

    @QtCore.pyqtSlot()
    def on_actionHelp_triggered(self) -> None:
        """Show help dialog with README content."""
        readme_path = Path(__file__).parent.parent.parent / "README.md"
        dialog = MarkdownViewerDialog.from_file(self, readme_path, "MSMS - Help")
        dialog.exec()

    @QtCore.pyqtSlot()
    def on_actionAbout_triggered(self) -> None:
        """Show about dialog."""
        about_text = """
        <h2>MSMS</h2>
        <p>Measurement System Management Software</p>
        <p>Version 1.0</p>
        <p>A PyQt6-based application for managing laboratory measurement devices.</p>
        """
        QtWidgets.QMessageBox.about(self, "About MSMS", about_text)

    @QtCore.pyqtSlot()
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

    @QtCore.pyqtSlot()
    def on_actionStopAcquisition_triggered(self) -> None:
        """Stop device acquisition."""
        logger.info("Stopping device manager")
        self.device_acquisition_stop_requested.emit()
        # Also stop experiment if running
        if self.app_controller.managers.experiment.is_running:
            self.experiment_stop_requested.emit()

    @QtCore.pyqtSlot()
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

    @QtCore.pyqtSlot()
    def on_chartConfigPushButton_clicked(self) -> None:
        """Display column selection menu for the main chart."""

        menu = QtWidgets.QMenu(self)
        for column in self.chart_columns:
            action = menu.addAction(column)
            assert action is not None
            action.setCheckable(True)
            action.setChecked(column == self.current_chart_column)
            action.triggered.connect(lambda _checked=None, col=column: self.set_chart_column(col))
        menu.exec(QtGui.QCursor.pos())

    @QtCore.pyqtSlot(object)
    def set_chart_column(self, column: str) -> None:
        self.current_chart_column = column
        self.chartConfigPushButton.setText(f"CHART: {column}")
        self.plot_controller.set_column(column)
        self.refresh_plot()

    @QtCore.pyqtSlot(object)
    def on_columns_change(self, columns: list[str]) -> None:
        """Handle notification that numeric chart columns have changed."""
        self.chart_columns = columns
        if self.current_chart_column not in self.chart_columns and self.chart_columns:
            self.current_chart_column = self.chart_columns[0]
            self.chartConfigPushButton.setText(f"CHART: {self.current_chart_column}")

    @QtCore.pyqtSlot(object)
    def on_update_data_labels(self, data: dict[str, float | str]) -> None:
        """Update UI labels and all relevant views with the latest data payload."""
        self.display_controller.update_labels(data)

    @QtCore.pyqtSlot()
    def on_commentPlainTextEdit_textChanged(self) -> None:
        """Persist experiment comments as they change."""

        comment = self.commentPlainTextEdit.toPlainText()
        self.storage_description_change_requested.emit(comment)

    @QtCore.pyqtSlot(object)
    def _on_description_changed(self, description: str) -> None:
        previously_blocked = self.commentPlainTextEdit.blockSignals(True)
        self.commentPlainTextEdit.setPlainText(description)
        self.commentPlainTextEdit.blockSignals(previously_blocked)

    @QtCore.pyqtSlot(object)
    def _on_restore_failed(self, message: str) -> None:
        QtWidgets.QMessageBox.information(self, "Restore Session", message)

    @QtCore.pyqtSlot(object)
    def _on_export_completed(self, path: str) -> None:
        QtWidgets.QMessageBox.information(self, "Export Completed", f"Data exported to {path}")

    @QtCore.pyqtSlot(object)
    def _on_export_failed(self, message: str) -> None:
        QtWidgets.QMessageBox.warning(self, "Export Failed", message)

    @QtCore.pyqtSlot()
    def on_actionStartExperiment_triggered(self) -> None:
        """Start experiment execution."""
        # Check if experiment plan exists by checking execution log
        if not self.app_controller.managers.experiment.get_execution_log():
            QtWidgets.QMessageBox.warning(
                self,
                "No Experiment Plan",
                "Please create an experiment plan first using Experiment → Manage Experiment.",
            )
            return
        self.experiment_start_requested.emit()
        logger.info("Experiment started")

    @QtCore.pyqtSlot()
    def on_actionStopExperiment_triggered(self) -> None:
        """Stop experiment execution."""
        self.experiment_stop_requested.emit()
        logger.info("Experiment stopped")

    @QtCore.pyqtSlot()
    def on_actionSkipToNext_triggered(self) -> None:
        """Skip to next step in experiment."""
        self.experiment_skip_forward_requested.emit()
        logger.info("Skipped to next step")

    @QtCore.pyqtSlot()
    def on_actionQuit_triggered(self) -> None:
        """Quit the application."""
        self.close()

    def closeEvent(self, event: QtGui.QCloseEvent | None) -> None:
        """Ensure worker threads are stopped before window closes."""

        self.app_controller.shutdown()
        logger.info("Shutdown complete, accepting close event")
        if event:
            event.accept()
