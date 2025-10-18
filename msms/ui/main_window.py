import logging
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pyqtgraph as pg  # type: ignore
from PyQt6 import QtCore, QtGui, QtWidgets, uic

from msms.ui.threads.data_feeder import DataFeeder

if TYPE_CHECKING:
    from pyqtgraph.graphicsItems.ViewBox.ViewBox import ViewBox  # type: ignore

logger = logging.getLogger(__name__)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        ui_file = Path(__file__).parent / "main_window.ui"
        uic.loadUi(str(ui_file), self)
        self.center_on_screen()
        self.fix_clicked_signal("chartConfigPushButton")
        self.fix_clicked_signal("doActionPushButton")
        self.on_data_feeder_updated({})
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

        self.chart_columns = ["time", "number", "dt"]
        self.current_chart_column = "timestamp"

        self.data_feeder: DataFeeder | None = None
        self.current_interval = 0.5

        pg.setConfigOptions(antialias=True)

        self.plotWidget.showGrid(x=True, y=True)
        self.plot = self.plotWidget.plot([], [], pen=pg.mkPen("y", width=1), symbol="+", symbolSize=20, symbolBrush="b")
        self.plotWidget.setTitle("Temperature vs Time", color="b", size="20pt")
        styles = {"color": "red", "font-size": "18px"}
        self.plotWidget.setLabel("left", "Temperature (°C)", **styles)
        self.plotWidget.setLabel("bottom", "Time (s)", **styles)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.on_timer_timeout)
        self.timer.start(100)

        self.xs = np.array([])
        self.ys = np.array([])

        self.plotWidget.sigXRangeChanged.connect(self.on_plotWidget_sigXRangeChanged)
        self.plotWidget.sigYRangeChanged.connect(self.on_plotWidget_sigYRangeChanged)

        self._last_user_xrange: list[float] | None = None
        self._last_user_yrange: list[float] | None = None
        self._programmatic_update = False

    def fix_clicked_signal(self, push_button_name: str) -> None:
        push_button = self.findChild(QtWidgets.QPushButton, push_button_name)
        slot = getattr(self, f"on_{push_button_name}_clicked", None)
        assert push_button is not None
        assert push_button.receivers(push_button.clicked) > 1
        assert slot is not None
        # UIC keeps connecting `clicked` and `clicked(bool)` and we need to disconnect all of them
        push_button.clicked.disconnect()
        push_button.clicked.connect(slot)

    def center_on_screen(self) -> None:
        screen = QtWidgets.QApplication.primaryScreen()
        assert screen is not None
        screen_geometry = screen.availableGeometry()
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(screen_geometry.center())
        self.move(window_geometry.topLeft())

    def on_chartConfigPushButton_clicked(self) -> None:
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
        if not self.timer.isActive():
            self.on_timer_timeout()

    def on_doActionPushButton_clicked(self) -> None:
        menu = QtWidgets.QMenu(self)

        if self.data_feeder is not None:
            stop_action = QtGui.QAction("Stop", self)
            stop_action.triggered.connect(self._stop_data_feeder)
            menu.addAction(stop_action)
        else:
            start_action = QtGui.QAction("Start", self)
            start_action.triggered.connect(self._start_data_feeder)
            menu.addAction(start_action)

        menu.addSeparator()

        interval_menu = QtWidgets.QMenu("Set Interval", self)
        menu.addMenu(interval_menu)
        for interval in [0.1, 0.5, 1.0, 2.0, 5.0]:
            action = QtGui.QAction(f"{interval} s", self)
            action.setCheckable(True)
            action.setChecked(interval == self.current_interval)
            action.triggered.connect(lambda _, val=interval: self._set_interval(val))
            interval_menu.addAction(action)

        menu.exec(QtGui.QCursor.pos())

    def _start_data_feeder(self) -> None:
        logger.info("Starting data feeder with interval %.2f", self.current_interval)
        self.thread_data_feeder = QtCore.QThread()
        self.data_feeder = DataFeeder(interval=self.current_interval)
        self.data_feeder.moveToThread(self.thread_data_feeder)
        self.data_feeder.initiated.connect(self.on_data_feeder_initiated)
        self.data_feeder.updated.connect(self.on_data_feeder_updated)
        self.thread_data_feeder.started.connect(self.data_feeder.run)
        self.thread_data_feeder.start()
        self.doActionPushButton.setText("STOP")

    def _stop_data_feeder(self) -> None:
        logger.info("Stopping data feeder")
        if self.data_feeder is not None:
            self.data_feeder.stop()
            self.thread_data_feeder.quit()
        self.data_feeder = None
        self.doActionPushButton.setText("DO ACTION")

    def _set_interval(self, value: float) -> None:
        logger.info("Changing data feeder interval to %.2f", value)
        self.current_interval = value
        if self.data_feeder is not None:
            self.data_feeder.interval = value

    def on_data_feeder_initiated(self, columns: list[str]) -> None:
        logger.info("Data feeder initiated with columns: %s", columns)
        self.chart_columns = columns
        assert self.current_chart_column in self.chart_columns

    def on_data_feeder_updated(self, data: dict[str, float | str]) -> None:
        time = str(timedelta(seconds=int(data.get("time", 0))))
        no = f"#{data.get('number', 0):d}"
        self.timeValue.setText(time)
        self.numberValue.setText(no)

        sample, control = data.get("sample", "N/A"), data.get("control", "N/A")
        sample = f"{sample:.2f}K" if isinstance(sample, float) else sample.strip()
        control = f"{control:.2f}K" if isinstance(control, float) else control.strip()
        self.sampleValue.setText(sample)
        self.controlValue.setText(control)
        set_point, set_point_unit = data.get("set_point", "N/A"), data.get("set_point_unit", "")
        set_point = f"{set_point:.2f} {set_point_unit}" if isinstance(set_point, float) else set_point.strip()
        self.setPointValue.setText(set_point)
        ramp_rate = data.get("ramp_rate") or "-"
        ramp_rate = f"{ramp_rate:.1f}K/s" if isinstance(ramp_rate, float) else ramp_rate.strip()
        self.rampValue.setText(ramp_rate)

        # if the layout is too narrow to show all labels properly, expand it
        self.experimentStatusLayoutWidget.setMinimumWidth(
            max(self.experimentStatusLayoutWidget.minimumWidth(), self.experimentStatusLayoutWidget.sizeHint().width())
        )

    def on_plotWidget_sigXRangeChanged(self, _view_box: ViewBox, range_: list[float]) -> None:
        if self._programmatic_update:
            return
        self.autoFollowCheckBox.setChecked(False)
        self._last_user_xrange = range_

    def on_plotWidget_sigYRangeChanged(self, _view_box: ViewBox, range_: list[float]) -> None:
        if self._programmatic_update:
            return
        self.autoFollowCheckBox.setChecked(False)
        self._last_user_yrange = range_

    def on_autoFollowCheckBox_toggled(self, checked: bool) -> None:
        logger.info("Follow checkbox toggled: %s", checked)
        if checked and self.xs.size > 0:
            # Immediately update view to follow latest data
            self.update_auto_follow_view()

    def update_auto_follow_view(self) -> None:
        if self.xs.size > 0:
            new_xrange = [self.xs[0], self.xs[-1]]

            self._programmatic_update = True
            self.plotWidget.setXRange(new_xrange[0], new_xrange[1], padding=0)
            self._last_user_xrange = new_xrange

            self.plotWidget.enableAutoRange(axis=pg.ViewBox.YAxis, enable=True)
            # keep _programmatic_update flag set for a bit longer to catch Y auto-range changes
            QtCore.QTimer.singleShot(150, lambda: setattr(self, "_programmatic_update", False))

    def on_timer_timeout(self) -> None:
        if self.data_feeder is None:
            return
        data = self.data_feeder.data_holder.data
        if data.shape == ():
            return
        x_idx = self.data_feeder.data_holder.columns.index("time")
        y_idx = self.data_feeder.data_holder.columns.index(self.current_chart_column)
        size = data.shape[0]
        logger.info("Retrieved %d new samples.", size)
        self.xs = data[:, x_idx]
        self.ys = data[:, y_idx]
        self.plot.setData(self.xs, self.ys)

        if self.autoFollowCheckBox.isChecked() and self.xs.size > 0:
            self.update_auto_follow_view()
        else:  # if auto-follow is disabled, restore last user range
            if self._last_user_xrange is not None:
                self._programmatic_update = True
                self.plotWidget.setXRange(self._last_user_xrange[0], self._last_user_xrange[1], padding=0)
                self._programmatic_update = False
            self.plotWidget.enableAutoRange(axis=pg.ViewBox.YAxis, enable=False)

    def closeEvent(self, event: QtGui.QCloseEvent | None) -> None:
        if self.data_feeder is not None:
            logger.info("Stopping data feeder on exit")
            self.thread_data_feeder.quit()
            self.thread_data_feeder.wait(100)
        if event:
            event.accept()
