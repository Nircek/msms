import logging
from typing import TYPE_CHECKING, cast

import numpy as np
import pyqtgraph as pg  # type: ignore
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication

if TYPE_CHECKING:
    from pyqtgraph.graphicsItems.ViewBox.ViewBox import ViewBox  # type: ignore

    from msms.ui.managers import DataRepository

logger = logging.getLogger(__name__)


def clamp_to_float_precision(value: float) -> float:
    return max(-1e308, min(1e308, value))


class PlotController(QtCore.QObject):
    """Plot widget state, auto-follow, and user interaction."""

    def __init__(
        self,
        plot_widget: pg.PlotWidget,
        auto_follow_checkbox: QtWidgets.QCheckBox,
        chart_config_button: QtWidgets.QPushButton,
        data_repository: DataRepository,
    ) -> None:
        super().__init__()
        self.plot_widget = plot_widget
        self.auto_follow_checkbox = auto_follow_checkbox
        self.chart_config_button = chart_config_button
        self.data_repository = data_repository

        # Column selection state
        self.chart_columns = ["time", "number", "dt"]
        self.current_chart_column = "timestamp"

        # Detect system theme and configure colors
        is_dark_theme = self._is_dark_theme()
        self._configure_plot_style(is_dark_theme)
        self._configure_plot_options()

        # Create plot item with theme-appropriate colors
        line_color, marker_color = self._get_plot_colors(is_dark_theme)
        self.plot_item = plot_widget.plot(
            [],
            [],
            pen=pg.mkPen(line_color, width=2),
            symbol="o",
            symbolSize=8,
            symbolBrush=marker_color,
            symbolPen=None,
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
        self.chart_config_button.clicked.connect(self._on_chart_config_clicked)

        # Connect to OS theme changes (Qt 6.5+)
        self._connect_theme_change_signal()

    def _configure_plot_options(self) -> None:
        """Set plot interaction options."""
        self.plot_widget.setClipToView(True)
        self.plot_widget.getViewBox().setLimits(minXRange=1e-20, minYRange=1e-20, maxXRange=1e20, maxYRange=1e20)

    @staticmethod
    def _is_dark_theme() -> bool:
        """Detect if OS is using a dark theme (Qt 6.5+)."""
        gui_app = cast("QGuiApplication", QGuiApplication.instance())
        if gui_app is None:
            return False

        # Use Qt6's QStyleHints to detect color scheme
        style_hints = gui_app.styleHints()
        if style_hints is None:
            return False

        try:
            # Qt 6.5+ has colorScheme() method
            color_scheme = style_hints.colorScheme()
        except AttributeError as e:
            msg = "You need Qt6.5+"
            raise RuntimeError(msg) from e
            # Fallback for older Qt6 versions: analyze palette luminance
            palette = gui_app.palette()
            bg_color = palette.color(palette.ColorRole.Window)
            luminance_threshold = 0.5
            luminance = (0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue()) / 255
            return luminance < luminance_threshold
        else:
            return color_scheme == Qt.ColorScheme.Dark

    @staticmethod
    def _get_plot_colors(is_dark: bool) -> tuple[str, str]:
        """Get plot line and marker colors for theme."""
        if is_dark:
            # Dark theme: bright colors for visibility
            return "#00D4FF", "#00D4FF"  # Cyan for both line and markers
        # Light theme: darker colors for contrast
        return "#1f77b4", "#1f77b4"  # Professional blue

    def _configure_plot_style(self, is_dark: bool) -> None:
        """Configure plot background, grid, and labels for theme."""
        if is_dark:
            # Dark theme styling
            self.plot_widget.setBackground("#1e1e1e")
            text_color = "#e0e0e0"
        else:
            # Light theme styling
            self.plot_widget.setBackground("#ffffff")
            text_color = "#000000"

        # Configure grid
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.getPlotItem().getAxis("bottom").setPen(text_color)
        self.plot_widget.getPlotItem().getAxis("left").setPen(text_color)
        self.plot_widget.getPlotItem().getAxis("bottom").setTextPen(text_color)
        self.plot_widget.getPlotItem().getAxis("left").setTextPen(text_color)

        # Set title and labels with appropriate colors
        self.plot_widget.setTitle("Temperature vs Time", color=text_color, size="14pt")
        label_styles = {"color": text_color, "font-size": "12pt"}
        self.plot_widget.setLabel("left", "Temperature (°C)", **label_styles)
        self.plot_widget.setLabel("bottom", "Sample Index", color=text_color)

    def _connect_theme_change_signal(self) -> None:
        """Connect to OS theme change signal."""
        gui_app = cast("QGuiApplication", QGuiApplication.instance())
        if gui_app is None:
            return

        style_hints = gui_app.styleHints()
        if style_hints is None:
            return

        try:
            # Qt 6.5+ has colorSchemeChanged signal
            style_hints.colorSchemeChanged.connect(self._on_theme_changed)
            logger.info("Connected to OS theme change signal")
        except AttributeError:
            logger.debug("colorSchemeChanged signal not available (Qt < 6.5)")

    @QtCore.Slot(Qt.ColorScheme)
    def _on_theme_changed(self, color_scheme: Qt.ColorScheme) -> None:
        """Handle OS theme change and update plot styling."""
        is_dark = color_scheme == Qt.ColorScheme.Dark
        logger.info("OS theme changed, dark mode: %s", is_dark)

        # Update plot styling
        self._configure_plot_style(is_dark)

        # Update plot line and marker colors
        line_color, marker_color = self._get_plot_colors(is_dark)
        self.plot_item.setPen(pg.mkPen(line_color, width=2))
        self.plot_item.setSymbolBrush(marker_color)

        # Refresh the plot to apply changes
        self.plot_item.setData(self.xs, self.ys)

    def set_column(self, column: str) -> None:
        logger.info("Plot column changed to: %s", column)
        self.current_column = column

    def refresh_data_from_repository(self) -> None:
        """Update plot data from repository."""
        columns = list(self.data_repository.columns or [])
        data = self.data_repository.data

        if data.shape == () or "time" not in columns or self.current_column not in columns:
            self.plot_item.setData([], [])
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
        """Pan chart to show latest samples."""
        if self.xs.size > 0:
            new_xrange = [self.xs[0], self.xs[-1]]

            self._programmatic_update = True
            self.plot_widget.setXRange(new_xrange[0], new_xrange[1], padding=0)
            self._last_user_xrange = new_xrange

            self.plot_widget.enableAutoRange(axis=pg.ViewBox.YAxis, enable=True)
            # Keep _programmatic_update flag set briefly to catch Y auto-range changes
            QtCore.QTimer.singleShot(150, lambda: setattr(self, "_programmatic_update", False))

    def _restore_user_view(self) -> None:
        """Restore user's manual view range."""
        if self._last_user_xrange is not None:
            self._programmatic_update = True
            self.plot_widget.setXRange(self._last_user_xrange[0], self._last_user_xrange[1], padding=0)
            self._programmatic_update = False
        self.plot_widget.enableAutoRange(axis=pg.ViewBox.YAxis, enable=False)

    def _on_x_range_changed(self, _view_box: ViewBox, range_: list[float]) -> None:
        """Track manual X range changes."""
        if self._programmatic_update:
            return
        self.auto_follow_checkbox.setChecked(False)
        self._last_user_xrange = [clamp_to_float_precision(range_[0]), clamp_to_float_precision(range_[1])]

    def _on_y_range_changed(self, _view_box: ViewBox, range_: list[float]) -> None:
        """Track manual Y range changes."""
        if self._programmatic_update:
            return
        self.auto_follow_checkbox.setChecked(False)
        self._last_user_yrange = [clamp_to_float_precision(range_[0]), clamp_to_float_precision(range_[1])]

    def _on_auto_follow_toggled(self, checked: bool) -> None:
        logger.info("Auto-follow toggled: %s", checked)
        if checked and self.xs.size > 0:
            self._update_auto_follow_view()

    @QtCore.Slot()
    def _on_chart_config_clicked(self) -> None:
        """Display column selection menu for the main chart."""
        menu = QtWidgets.QMenu()
        for column in self.chart_columns:
            action = menu.addAction(column)
            assert action is not None
            action.setCheckable(True)
            action.setChecked(column == self.current_chart_column)
            action.triggered.connect(lambda _checked=None, col=column: self._set_chart_column(col))
        menu.exec(QtGui.QCursor.pos())

    def _set_chart_column(self, column: str) -> None:
        """Update selected chart column and refresh display."""
        self.current_chart_column = column
        self.chart_config_button.setText(f"CHART: {column}")
        self.set_column(column)
        self.refresh_data_from_repository()

    @QtCore.Slot(object)
    def on_columns_change(self, columns: list[str]) -> None:
        """Handle notification that numeric chart columns have changed."""
        self.chart_columns = columns
        if self.current_chart_column not in self.chart_columns and self.chart_columns:
            self.current_chart_column = self.chart_columns[0]
            self.chart_config_button.setText(f"CHART: {self.current_chart_column}")
