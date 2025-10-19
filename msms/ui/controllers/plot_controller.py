"""Controller for managing plot visualization and interaction."""

import logging
from typing import TYPE_CHECKING

import numpy as np
import pyqtgraph as pg  # type: ignore
from PyQt6 import QtCore, QtWidgets

if TYPE_CHECKING:
    from pyqtgraph.graphicsItems.ViewBox.ViewBox import ViewBox  # type: ignore

    from msms.ui.managers import DataRepository

logger = logging.getLogger(__name__)


class PlotController(QtCore.QObject):
    """Manage plot widget state, auto-follow, and user interaction."""

    def __init__(self, plot_widget: pg.PlotWidget, auto_follow_checkbox: QtWidgets.QCheckBox) -> None:
        """Initialize the plot controller."""
        super().__init__()
        self.plot_widget = plot_widget
        self.auto_follow_checkbox = auto_follow_checkbox
        self.plot_item = plot_widget.plot(
            [], [], pen=pg.mkPen("y", width=1), symbol="+", symbolSize=20, symbolBrush="b"
        )

        self.current_column = "timestamp"
        self.xs = np.array([])
        self.ys = np.array([])

        self._last_user_xrange: list[float] | None = None
        self._last_user_yrange: list[float] | None = None
        self._programmatic_update = False

        self.plot_widget.sigXRangeChanged.connect(self._on_x_range_changed)
        self.plot_widget.sigYRangeChanged.connect(self._on_y_range_changed)
        self.auto_follow_checkbox.toggled.connect(self._on_auto_follow_toggled)

        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setTitle("Temperature vs Time", color="b", size="20pt")
        styles = {"color": "red", "font-size": "18px"}
        self.plot_widget.setLabel("left", "Temperature (°C)", **styles)
        self.plot_widget.setLabel("bottom", "Time (s)", **styles)

    def set_column(self, column: str) -> None:
        """Change the Y-axis column being plotted."""
        logger.info("Plot column changed to: %s", column)
        self.current_column = column

    def refresh_from_repository(self, data_repository: DataRepository) -> None:
        """Update plot data from the data repository."""
        columns = list(data_repository.columns or [])
        data = data_repository.data

        if data.shape == ():
            return
        if "time" not in columns or self.current_column not in columns:
            return

        x_idx = columns.index("time")
        y_idx = columns.index(self.current_column)

        logger.debug("Refreshing plot with %d samples", data.shape[0])
        self.xs = data[:, x_idx]
        self.ys = data[:, y_idx]
        self.plot_item.setData(self.xs, self.ys)

        if self.auto_follow_checkbox.isChecked() and self.xs.size > 0:
            self._update_auto_follow_view()
        else:
            self._restore_user_view()

    def _update_auto_follow_view(self) -> None:
        """Pan the chart to show the latest samples when auto-follow is on."""
        if self.xs.size > 0:
            new_xrange = [self.xs[0], self.xs[-1]]

            self._programmatic_update = True
            self.plot_widget.setXRange(new_xrange[0], new_xrange[1], padding=0)
            self._last_user_xrange = new_xrange

            self.plot_widget.enableAutoRange(axis=pg.ViewBox.YAxis, enable=True)
            # Keep _programmatic_update flag set briefly to catch Y auto-range changes
            QtCore.QTimer.singleShot(150, lambda: setattr(self, "_programmatic_update", False))

    def _restore_user_view(self) -> None:
        """Restore the user's manually set view range."""
        if self._last_user_xrange is not None:
            self._programmatic_update = True
            self.plot_widget.setXRange(self._last_user_xrange[0], self._last_user_xrange[1], padding=0)
            self._programmatic_update = False
        self.plot_widget.enableAutoRange(axis=pg.ViewBox.YAxis, enable=False)

    def _on_x_range_changed(self, _view_box: ViewBox, range_: list[float]) -> None:
        """Track manual X range changes to disable auto-follow."""
        if self._programmatic_update:
            return
        self.auto_follow_checkbox.setChecked(False)
        self._last_user_xrange = range_

    def _on_y_range_changed(self, _view_box: ViewBox, range_: list[float]) -> None:
        """Track manual Y range changes to disable auto-follow."""
        if self._programmatic_update:
            return
        self.auto_follow_checkbox.setChecked(False)
        self._last_user_yrange = range_

    def _on_auto_follow_toggled(self, checked: bool) -> None:
        """Enable or disable automatic chart panning."""
        logger.info("Auto-follow toggled: %s", checked)
        if checked and self.xs.size > 0:
            self._update_auto_follow_view()
