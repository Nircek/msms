import logging
from datetime import timedelta
from pathlib import Path

import pyqtgraph as pg  # type: ignore
from PyQt6 import QtGui, QtWidgets, uic

from msms.ui.controllers.app_controller import ApplicationController
from msms.ui.controllers.plot_controller import PlotController
from msms.ui.dialogs import DeviceSelectionDialog

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

        self.on_update_data_labels({})  # initialize labels
        self.chart_columns = ["time", "number", "dt"]
        self.current_chart_column = "timestamp"

        self.app_controller = ApplicationController(interval_ms=500)
        self._selected_device_addresses: list[str] = []

        self.app_controller.storage_manager.new_data_row.connect(self.on_update_data_labels)
        self.app_controller.storage_manager.new_data_row.connect(lambda _data: self.refresh_plot())
        self.app_controller.storage_manager.columns_changed.connect(self.on_columns_change)

        pg.setConfigOptions(antialias=True)
        self.plot_controller = PlotController(self.plotWidget, self.autoFollowCheckBox)

    def refresh_plot(self) -> None:
        self.plot_controller.refresh_from_repository(self.app_controller.storage_manager.data_repository)

    def on_actionRestoreLastFile_triggered(self) -> None:
        """Restore the last recorded session from disk if available."""
        logger.info("Restoring last used file...")
        last_file = self.app_controller.storage_manager.get_last_used_file()
        if last_file is not None and last_file.exists():
            logger.info("Restoring last used file: %s", last_file)
            self.app_controller.storage_manager.load_old_file(last_file)
            comment = self.app_controller.storage_manager.csv_persistence.description
            self.commentPlainTextEdit.setPlainText(comment)
        else:
            logger.info("No last used file to restore.")

    def on_actionSelectDevices_triggered(self) -> None:
        """Show dialog for selecting devices to poll."""
        logger.info("Opening device selection dialog...")
        if self._selected_device_addresses:
            logger.error("Device selection dialog was already open.")
            return

        dialog = DeviceSelectionDialog(
            self,
            discover_devices=self.app_controller.discover_devices,
        )
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            selected_addresses = dialog.get_selected_addresses()
            logger.info("Selected devices: %s", selected_addresses)
            self._selected_device_addresses = selected_addresses
            self.app_controller.update_selected_devices(selected_addresses)
        else:
            logger.info("Device selection cancelled")

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

        menu = QtWidgets.QMenu(self)

        if self.app_controller.is_acquiring:
            stop_action = QtGui.QAction("Stop", self)
            stop_action.triggered.connect(self._stop_device_manager)
            menu.addAction(stop_action)
        else:
            start_action = QtGui.QAction("Start", self)
            start_action.triggered.connect(self._start_device_manager)
            menu.addAction(start_action)

        menu.addSeparator()
        export_action = QtGui.QAction("Export Data to CSV...", self)
        export_action.triggered.connect(self._export_data_to_csv)
        menu.addAction(export_action)
        menu.addSeparator()

        interval_menu = QtWidgets.QMenu("Set Interval", self)
        menu.addMenu(interval_menu)
        for interval_sec in [0.1, 0.5, 1.0, 2.0, 5.0]:
            interval_ms = int(interval_sec * 1000)
            action = QtGui.QAction(f"{interval_sec} s", self)
            action.setCheckable(True)
            action.setChecked(interval_ms == self.app_controller.current_interval_ms)
            action.triggered.connect(lambda _, val=interval_ms: self._set_interval(val))
            interval_menu.addAction(action)

        menu.exec(QtGui.QCursor.pos())

    def _start_device_manager(self) -> None:
        """Start asynchronous device data acquisition."""
        if not self._selected_device_addresses:
            QtWidgets.QMessageBox.warning(
                self,
                "Select Devices",
                "Select at least one device before starting acquisition.",
            )
            return

        logger.info("Starting device manager with interval %d ms", self.app_controller.current_interval_ms)
        self.app_controller.start_acquisition()

    def _stop_device_manager(self) -> None:
        """Stop acquisition thread and update button label."""
        logger.info("Stopping device manager")
        self.app_controller.stop_acquisition()

    def _export_data_to_csv(self) -> None:
        """Open a save dialog and export the current dataset."""

        dialog = QtWidgets.QFileDialog(self)
        dialog.setWindowTitle("Export Data to CSV")
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptMode.AcceptSave)
        dialog.setNameFilter("CSV Files (*.csv)")
        dialog.setDefaultSuffix("csv")
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            export_path = Path(dialog.selectedFiles()[0])
            logger.info("Exporting data to CSV file: %s", export_path)
            self.app_controller.storage_manager.export_to_csv(export_path)

    def _set_interval(self, value_ms: int) -> None:
        """Update device polling interval both in UI state and manager."""

        logger.info("Changing device manager interval to %d ms", value_ms)
        self.app_controller.set_interval(value_ms)

    def on_columns_change(self, columns: list[str]) -> None:
        """Handle notification that numeric chart columns have changed."""

        logger.info("Device manager initiated with columns: %s", columns)
        self.chart_columns = columns
        if self.current_chart_column not in self.chart_columns and self.chart_columns:
            self.current_chart_column = self.chart_columns[0]
            self.chartConfigPushButton.setText(f"CHART: {self.current_chart_column}")

    def on_update_data_labels(self, data: dict[str, float | str]) -> None:
        """Update UI labels and all relevant views with the latest data payload."""

        time = str(timedelta(seconds=int(data.get("time", 0))))
        no = f"#{data.get('row_number', 0):.0f}"
        self.timeValue.setText(time)
        self.numberValue.setText(no)

        sample, control = data.get("sample", "N/A"), data.get("control", "N/A")
        sample = f"{sample:.2f}K" if isinstance(sample, float) else str(sample).strip()
        control = f"{control:.2f}K" if isinstance(control, float) else str(control).strip()
        self.sampleValue.setText(sample)
        self.controlValue.setText(control)
        set_point, set_point_unit = data.get("set_point", "N/A"), data.get("set_point_unit", "")
        set_point = f"{set_point:.2f} {set_point_unit}" if isinstance(set_point, float) else str(set_point).strip()
        self.setPointValue.setText(set_point)
        ramp_rate = data.get("ramp_rate") or "-"
        ramp_rate = f"{ramp_rate:.1f}K/s" if isinstance(ramp_rate, float) else str(ramp_rate).strip()
        self.rampValue.setText(ramp_rate)

        # if the layout is too narrow to show all labels properly, expand it
        self.experimentStatusLayoutWidget.setMinimumWidth(
            max(self.experimentStatusLayoutWidget.minimumWidth(), self.experimentStatusLayoutWidget.sizeHint().width())
        )

        self.variablesTextEdit.setPlainText("\n\n".join(f"{k}:\n{v!r}" for k, v in data.items()))

    def on_commentPlainTextEdit_textChanged(self) -> None:
        """Persist experiment comments as they change."""

        comment = self.commentPlainTextEdit.toPlainText()
        self.app_controller.storage_manager.set_description(comment)

    def closeEvent(self, event: QtGui.QCloseEvent | None) -> None:
        """Ensure worker threads are stopped before window closes."""

        self.app_controller.shutdown()
        if event:
            event.accept()
