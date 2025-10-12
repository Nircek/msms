import contextlib
import logging
from collections import deque
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
        self.followCheckBox: QtWidgets.QCheckBox
        self.intervalSpinBox: QtWidgets.QDoubleSpinBox
        self.startStopButton: QtWidgets.QPushButton
        self.infoLabel: QtWidgets.QLabel
        self.plotWidget: pg.PlotWidget
        self.logTextBrowser: QtWidgets.QTextBrowser

        assert self.startStopButton.receivers(self.startStopButton.clicked) > 1
        # UIC keeps connecting `clicked` and `clicked(bool)` and we need to disconnect all of them
        self.startStopButton.clicked.disconnect()
        self.startStopButton.clicked.connect(self.on_startStopButton_clicked)

        self.buffer: deque[tuple[float, float]] = deque()

        self.data_feeder: DataFeeder | None = None

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

    def on_plotWidget_sigXRangeChanged(self, _view_box: ViewBox, range_: list[float]) -> None:
        if self._programmatic_update:
            return
        self.followCheckBox.setChecked(False)
        self._last_user_xrange = range_

    def on_plotWidget_sigYRangeChanged(self, _view_box: ViewBox, range_: list[float]) -> None:
        if self._programmatic_update:
            return
        self.followCheckBox.setChecked(False)
        self._last_user_yrange = range_

    def on_followCheckBox_toggled(self, checked: bool) -> None:
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
        if len(self.buffer) == 0:
            return
        items = []
        while True:
            try:
                items.append(self.buffer.popleft())  # popleft is thread-safe
            except IndexError:
                break
            except Exception:
                break
        if not items:
            return

        self.logTextBrowser.append(f"Retrieved {len(items)} new samples.")
        logger.info("Retrieved %d new samples.", len(items))

        ts = np.array([it[0] for it in items], dtype=float)
        vals = np.array([it[1] for it in items], dtype=float)

        if self.xs.size == 0:
            self.xs = ts
            self.ys = vals
        else:
            self.xs = np.concatenate((self.xs, ts))
            self.ys = np.concatenate((self.ys, vals))

        self.plot.setData(self.xs, self.ys)

        if self.followCheckBox.isChecked() and self.xs.size > 0:
            self.update_auto_follow_view()
        else:  # if auto-follow is disabled, restore last user range
            if self._last_user_xrange is not None:
                self._programmatic_update = True
                self.plotWidget.setXRange(self._last_user_xrange[0], self._last_user_xrange[1], padding=0)
                self._programmatic_update = False
            self.plotWidget.enableAutoRange(axis=pg.ViewBox.YAxis, enable=False)

        if self.xs.size > 0:
            self.infoLabel.setText(f"Samples stored: {self.xs.size}  Latest t={self.xs[-1]:.2f}  val={self.ys[-1]:.3f}")
        else:
            self.infoLabel.setText("No samples available")

    def on_startStopButton_clicked(self) -> None:
        if self.data_feeder is not None:
            logger.info("Stopping data feeder")
            self.data_feeder.stop()
            self.data_feeder = None
            self.startStopButton.setText("Start")
        else:
            interval = self.intervalSpinBox.value()
            logger.info("Starting data feeder with interval %.2f", interval)
            self.data_feeder = DataFeeder(self.buffer, interval=interval)
            self.data_feeder.start()
            self.startStopButton.setText("Stop")

    def on_intervalSpinBox_valueChanged(self, value: float) -> None:
        if self.data_feeder is not None:
            logger.info("Changing data feeder interval to %.2f", value)
            self.data_feeder.interval = value

    def closeEvent(self, event: QtGui.QCloseEvent | None) -> None:
        if self.data_feeder is not None:
            with contextlib.suppress(Exception):
                logger.info("Stopping data feeder on exit")
                self.data_feeder.stop()
        if event:
            event.accept()
