import logging
from pathlib import Path

import pyqtgraph as pg  # type: ignore
from PyQt6 import QtGui, QtWidgets, uic

from msms.ui.controllers.app_controller import ApplicationController
from msms.ui.controllers.display_controller import DisplayController, DisplayWidgets
from msms.ui.controllers.experiment_controller import ExperimentController
from msms.ui.controllers.plot_controller import PlotController
from msms.ui.dialogs import DescriptionDialog, DeviceSelectionDialog, MarkdownViewerDialog

logger = logging.getLogger(__name__)


class MainWindowUic(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        ui_file = Path(__file__).parent / "main_window.ui"
        uic.loadUi(str(ui_file), self)
        self.center_on_screen()
        self.fix_slot_signal("chartConfigPushButton", "clicked")
        self.fix_slot_signal("doActionPushButton", "clicked")
        self.fix_slot_signal("actionRestoreLastFile", "triggered")
        self.fix_slot_signal("actionSelectDevices", "triggered")
        self.fix_slot_signal("actionManageExperiment", "triggered")
        self.fix_slot_signal("actionDescribe", "triggered")
        self.fix_slot_signal("actionExport", "triggered")
        self.fix_slot_signal("actionHelp", "triggered")
        self.fix_slot_signal("actionAbout", "triggered")
        self.autoFollowCheckBox: QtWidgets.QCheckBox
        self.chartConfigPushButton: QtWidgets.QPushButton
        self.doActionPushButton: QtWidgets.QPushButton
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
        self.actionSelectDevices: QtGui.QAction
        self.actionManageExperiment: QtGui.QAction
        self.actionDescribe: QtGui.QAction
        self.actionExport: QtGui.QAction
        self.actionRestoreLastFile: QtGui.QAction
        self.actionAbout: QtGui.QAction
        self.actionHelp: QtGui.QAction

    def fix_slot_signal(self, widget_name: str, signal_name: str) -> None:
        """Disconnect UIC's auto-wired slots and reconnect the desired overload."""

        widget = self.findChild((QtWidgets.QPushButton, QtGui.QAction), widget_name)
        slot = getattr(self, f"on_{widget_name}_{signal_name}", None)
        widget_slot = getattr(widget, signal_name, None)
        assert widget is not None
        assert widget_slot is not None
        assert widget.receivers(widget_slot) > 1
        assert slot is not None
        # UIC keeps connecting `clicked` and `clicked(bool)` and we need to disconnect all of them
        widget_slot.disconnect()
        widget_slot.connect(slot)

    def center_on_screen(self) -> None:
        """Move the window to the center of the primary screen."""

        screen = QtWidgets.QApplication.primaryScreen()
        assert screen is not None
        screen_geometry = screen.availableGeometry()
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(screen_geometry.center())
        self.move(window_geometry.topLeft())


class MainWindow(MainWindowUic):
    def __init__(self) -> None:
        super().__init__()

        self.chart_columns = ["time", "number", "dt"]
        self.current_chart_column = "timestamp"

        self.app_controller = ApplicationController(interval_ms=500)
        self._selected_device_addresses: list[str] = []

        storage_manager = self.app_controller.storage_manager
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
            parent=self,
            button=self.doActionPushButton,
            app_controller=self.app_controller,
        )

    def refresh_plot(self) -> None:
        self.plot_controller.refresh_from_repository(self.app_controller.storage_manager.data_repository)

    def on_actionRestoreLastFile_triggered(self) -> None:
        """Restore the last recorded session from disk if available."""
        logger.info("Restoring last used file...")
        last_file = self.app_controller.storage_manager.get_last_used_file()
        if last_file is not None and last_file.exists():
            self.app_controller.request_restore_session(last_file)
        else:
            self.app_controller.request_restore_session()

    def on_actionSelectDevices_triggered(self) -> None:
        """Show dialog for selecting devices to poll."""
        logger.info("Opening device selection dialog...")
        if self._selected_device_addresses:
            logger.error("Device selection dialog was already open.")
            return

        dialog = DeviceSelectionDialog(self, app_controller=self.app_controller)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            selected_addresses = dialog.get_selected_addresses()
            logger.info("Selected devices: %s", selected_addresses)
            self._selected_device_addresses = selected_addresses
            self.app_controller.update_selected_devices(selected_addresses)
            self.experiment_controller.set_selected_devices(selected_addresses)
        else:
            logger.info("Device selection cancelled")

    def on_actionManageExperiment_triggered(self) -> None:
        """Show dialog for managing the experiment plan."""
        logger.info("Opening experiment management dialog...")
        QtWidgets.QMessageBox.information(
            self,
            "Manage Experiment",
            "Experiment management functionality is not yet implemented.",
        )

    def on_actionDescribe_triggered(self) -> None:
        """Show dialog for editing the experiment description."""
        logger.info("Opening description dialog...")
        current_description = self.commentPlainTextEdit.toPlainText()
        dialog = DescriptionDialog(self, current_description)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            description = dialog.get_description()
            self.commentPlainTextEdit.setPlainText(description)
            self.app_controller.update_description(description)
            logger.info("Description updated")

    def on_actionExport_triggered(self) -> None:
        """Export current data to CSV file."""
        self.experiment_controller.export_data_to_csv()

    def on_actionHelp_triggered(self) -> None:
        """Show help dialog with README content."""
        logger.info("Opening help dialog...")
        readme_path = Path(__file__).parent.parent.parent / "README.md"
        dialog = MarkdownViewerDialog.from_file(self, readme_path, "MSMS - Help")
        dialog.exec()

    def on_actionAbout_triggered(self) -> None:
        """Show about dialog."""
        logger.info("Opening about dialog...")
        about_text = """
        <h2>MSMS</h2>
        <p>Measurement System Management Software</p>
        <p>Version 1.0</p>
        <p>A PyQt6-based application for managing laboratory measurement devices.</p>
        """
        QtWidgets.QMessageBox.about(self, "About MSMS", about_text)

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

    def set_chart_column(self, column: str) -> None:
        logger.info("Chart column changed to: %s", column)
        self.current_chart_column = column
        self.chartConfigPushButton.setText(f"CHART: {column}")
        self.plot_controller.set_column(column)
        self.refresh_plot()

    def on_doActionPushButton_clicked(self) -> None:
        """Show the action menu for controlling acquisition and exports."""
        self.experiment_controller.show_action_menu()

    def on_columns_change(self, columns: list[str]) -> None:
        """Handle notification that numeric chart columns have changed."""

        logger.info("Device manager initiated with columns: %s", columns)
        self.chart_columns = columns
        if self.current_chart_column not in self.chart_columns and self.chart_columns:
            self.current_chart_column = self.chart_columns[0]
            self.chartConfigPushButton.setText(f"CHART: {self.current_chart_column}")

    def on_update_data_labels(self, data: dict[str, float | str]) -> None:
        """Update UI labels and all relevant views with the latest data payload."""
        self.display_controller.update_labels(data)

    def on_commentPlainTextEdit_textChanged(self) -> None:
        """Persist experiment comments as they change."""

        comment = self.commentPlainTextEdit.toPlainText()
        self.app_controller.update_description(comment)

    def _on_description_changed(self, description: object) -> None:
        if not isinstance(description, str):
            return
        previously_blocked = self.commentPlainTextEdit.blockSignals(True)
        self.commentPlainTextEdit.setPlainText(description)
        self.commentPlainTextEdit.blockSignals(previously_blocked)

    def _on_restore_failed(self, message: object) -> None:
        if isinstance(message, str):
            QtWidgets.QMessageBox.information(self, "Restore Session", message)

    def _on_export_completed(self, path: object) -> None:
        if isinstance(path, str):
            QtWidgets.QMessageBox.information(self, "Export Completed", f"Data exported to {path}")

    def _on_export_failed(self, message: object) -> None:
        if isinstance(message, str):
            QtWidgets.QMessageBox.warning(self, "Export Failed", message)

    def closeEvent(self, event: QtGui.QCloseEvent | None) -> None:
        """Ensure worker threads are stopped before window closes."""
        app = QtWidgets.QApplication.instance()
        current_thread = app.thread() if app else None
        thread_id = int(current_thread.currentThreadId()) if current_thread else 0  # type: ignore[arg-type]
        logger.info("closeEvent called from thread %s (id: %s)", current_thread, thread_id)

        self.app_controller.shutdown()
        logger.info("Shutdown complete, accepting close event")
        if event:
            event.accept()
