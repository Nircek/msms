import logging
from pathlib import Path

import pyqtgraph as pg  # type: ignore
from PyQt6 import QtGui, QtWidgets, uic

from msms.ui.controllers.app_controller import ApplicationController
from msms.ui.controllers.display_controller import DisplayController, DisplayWidgets
from msms.ui.controllers.experiment_controller import ExperimentController
from msms.ui.controllers.plot_controller import PlotController
from msms.ui.dialogs import DescriptionDialog, DeviceSelectionDialog, ExperimentDialog, MarkdownViewerDialog
from msms.ui.experiment.step_base import Step

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

        experiment_manager = self.app_controller.experiment_manager
        experiment_manager.current_step_changed.connect(self._on_experiment_step_changed)
        experiment_manager.experiment_completed.connect(self._on_experiment_completed)

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
        """Update plot with latest data from repository."""
        self.plot_controller.refresh_from_repository(self.app_controller.data_repository)

    def on_actionRestoreLastFile_triggered(self) -> None:
        """Restore the last recorded session from disk if available."""
        last_file = self.app_controller.get_last_used_file()
        if last_file is not None and last_file.exists():
            self.app_controller.request_restore_session(last_file)
        else:
            self.app_controller.request_restore_session()

    def on_actionSelectDevices_triggered(self) -> None:
        """Show dialog for selecting devices to poll."""
        if self._selected_device_addresses:
            return

        dialog = DeviceSelectionDialog(self, app_controller=self.app_controller)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            selected_addresses = dialog.get_selected_addresses()
            logger.info("Selected devices: %s", selected_addresses)
            self._selected_device_addresses = selected_addresses
            self.app_controller.update_selected_devices(selected_addresses)
            self.experiment_controller.set_selected_devices(selected_addresses)

    def on_actionManageExperiment_triggered(self) -> None:
        """Show dialog for managing the experiment plan."""
        if not self._selected_device_addresses:
            QtWidgets.QMessageBox.warning(
                self,
                "No Devices Selected",
                "Please select devices first using File → Select Devices before managing experiments.",
            )
            return

        dialog = ExperimentDialog(self, app_controller=self.app_controller)
        dialog.exec()

    def on_actionDescribe_triggered(self) -> None:
        """Show dialog for editing the experiment description."""
        current_description = self.commentPlainTextEdit.toPlainText()
        dialog = DescriptionDialog(self, current_description)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            description = dialog.get_description()
            self.commentPlainTextEdit.setPlainText(description)
            self.app_controller.update_description(description)

    def on_actionExport_triggered(self) -> None:
        """Export current data to CSV file."""
        self.experiment_controller.export_data_to_csv()

    def on_actionHelp_triggered(self) -> None:
        """Show help dialog with README content."""
        readme_path = Path(__file__).parent.parent.parent / "README.md"
        dialog = MarkdownViewerDialog.from_file(self, readme_path, "MSMS - Help")
        dialog.exec()

    def on_actionAbout_triggered(self) -> None:
        """Show about dialog."""
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
        self.current_chart_column = column
        self.chartConfigPushButton.setText(f"CHART: {column}")
        self.plot_controller.set_column(column)
        self.refresh_plot()

    def on_doActionPushButton_clicked(self) -> None:
        """Show the action menu for controlling acquisition and exports."""
        self.experiment_controller.show_action_menu()

    def on_columns_change(self, columns: list[str]) -> None:
        """Handle notification that numeric chart columns have changed."""
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

    def _on_description_changed(self, description: str) -> None:
        previously_blocked = self.commentPlainTextEdit.blockSignals(True)
        self.commentPlainTextEdit.setPlainText(description)
        self.commentPlainTextEdit.blockSignals(previously_blocked)

    def _on_restore_failed(self, message: str) -> None:
        QtWidgets.QMessageBox.information(self, "Restore Session", message)

    def _on_export_completed(self, path: str) -> None:
        QtWidgets.QMessageBox.information(self, "Export Completed", f"Data exported to {path}")

    def _on_export_failed(self, message: str) -> None:
        QtWidgets.QMessageBox.warning(self, "Export Failed", message)

    def _on_experiment_step_changed(self, step: object) -> None:
        """Update experiment plan display when current step changes."""
        current_step = step if isinstance(step, Step) else None
        next_step = self.app_controller.get_next_step()

        current_text = current_step.label if current_step else "No active step"
        next_text = next_step.label if next_step else "End of plan"

        html = (
            '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">'
            '<html><head><meta name="qrichtext" content="1" /><meta charset="utf-8" />'
            '<style type="text/css">p, li { white-space: pre-wrap; }'
            "hr { height: 1px; border-width: 0; }"
            'li.unchecked::marker { content: "\\2610"; }'
            'li.checked::marker { content: "\\2612"; }'
            "</style></head><body style=\" font-family:'.AppleSystemUIFont'; font-size:13pt; "
            'font-weight:400; font-style:normal;">'
            '<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; '
            f'-qt-block-indent:0; text-indent:0px;"><span style=" font-weight:700;">CURRENT: </span>{current_text}</p>'
            '<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; '
            f'-qt-block-indent:0; text-indent:0px;"><span style=" font-weight:700;">NEXT: '
            f"</span>{next_text}</p>"
            "</body></html>"
        )

        self.experimentPlanTextEdit.setHtml(html)

    def _on_experiment_completed(self) -> None:
        """Handle experiment completion."""
        logger.info("Experiment completed")
        self.experimentPlanTextEdit.setHtml(
            '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">'
            '<html><head><meta name="qrichtext" content="1" /><meta charset="utf-8" />'
            '<style type="text/css">p, li { white-space: pre-wrap; }hr { height: 1px; border-width: 0; }'
            'li.unchecked::marker { content: "\\2610"; }li.checked::marker { content: "\\2612"; }'
            "</style></head><body style=\" font-family:'.AppleSystemUIFont'; font-size:13pt; "
            'font-weight:400; font-style:normal;"><p style=" margin-top:0px; margin-bottom:0px; '
            'margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">'
            '<span style=" font-weight:700;">EXPERIMENT COMPLETED</span></p></body></html>'
        )

    def closeEvent(self, event: QtGui.QCloseEvent | None) -> None:
        """Ensure worker threads are stopped before window closes."""

        self.app_controller.shutdown()
        logger.info("Shutdown complete, accepting close event")
        if event:
            event.accept()
