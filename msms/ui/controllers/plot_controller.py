import logging
from typing import TYPE_CHECKING, Any, cast

import numpy as np
import pyqtgraph as pg  # type: ignore
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication

if TYPE_CHECKING:
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
        x_axis_button: QtWidgets.QPushButton,
        y_axis_button: QtWidgets.QPushButton,
        data_repository: DataRepository,
    ) -> None:
        super().__init__()
        self.plot_widget = plot_widget
        self.auto_follow_checkbox = auto_follow_checkbox
        self.x_axis_button = x_axis_button
        self.y_axis_button = y_axis_button
        self.data_repository = data_repository

        # Column selection state
        self.chart_columns: list[str] = []
        self.x_column = "time"
        self.y_column = "timestamp"

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

        self.xs = np.array([])
        self.ys = np.array([])

        self._last_user_xrange: list[float] | None = None
        self._last_user_yrange: list[float] | None = None

        self.plot_widget.sigRangeChanged.connect(self._on_range_changed)
        self.auto_follow_checkbox.toggled.connect(self._on_auto_follow_toggled)
        self.x_axis_button.clicked.connect(self._on_x_axis_button_clicked)
        self.y_axis_button.clicked.connect(self._on_y_axis_button_clicked)

        self.on_columns_change([])

        # Connect to OS theme changes (Qt 6.5+)
        self._connect_theme_change_signal()

    def _configure_plot_options(self) -> None:
        """Set plot interaction options."""
        self.plot_widget.getViewBox().setLimits(minXRange=1e-20, minYRange=1e-20, maxXRange=1e20, maxYRange=1e20)
        self.plot_widget.getViewBox().setMouseMode(pg.ViewBox.RectMode)

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

        # Initial title and labels (will be updated when columns change)
        self._update_plot_labels(text_color)

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

    def refresh_data_from_repository(self) -> None:
        """Update plot data from repository."""
        columns = list(self.data_repository.columns or [])
        data = self.data_repository.data

        if data.shape == () or self.x_column not in columns or self.y_column not in columns:
            self.plot_item.setData([], [])
            return

        x_idx = columns.index(self.x_column)
        y_idx = columns.index(self.y_column)

        logger.debug("Refreshing plot with %d samples", data.shape[0])
        self.xs = data[:, x_idx]
        self.ys = data[:, y_idx]
        self.plot_item.setData(self.xs, self.ys)

    def _on_range_changed(self, *_args: list[Any]) -> None:
        if self.auto_follow_checkbox.isChecked() and not all(self.plot_widget.getViewBox().autoRangeEnabled()):
            self.auto_follow_checkbox.blockSignals(True)
            self.auto_follow_checkbox.setChecked(False)
            self.auto_follow_checkbox.blockSignals(False)

    def _on_auto_follow_toggled(self, checked: bool) -> None:
        self.plot_widget.getViewBox().enableAutoRange(enable=checked)

    @QtCore.Slot()
    def _on_x_axis_button_clicked(self) -> None:
        """Display X-axis column selection menu."""
        if not self.chart_columns:
            return
        menu = QtWidgets.QMenu()
        for column in self.chart_columns:
            action = menu.addAction(column)
            assert action is not None
            action.setCheckable(True)
            action.setChecked(column == self.x_column)
            action.triggered.connect(lambda _checked=None, col=column: self._set_x_column(col))
        menu.exec(QtGui.QCursor.pos())

    @QtCore.Slot()
    def _on_y_axis_button_clicked(self) -> None:
        """Display Y-axis column selection menu."""
        if not self.chart_columns:
            return
        menu = QtWidgets.QMenu()
        for column in self.chart_columns:
            action = menu.addAction(column)
            assert action is not None
            action.setCheckable(True)
            action.setChecked(column == self.y_column)
            action.triggered.connect(lambda _checked=None, col=column: self._set_y_column(col))
        menu.exec(QtGui.QCursor.pos())

    def _set_x_column(self, column: str) -> None:
        """Update X-axis column and refresh display."""
        self.x_column = column
        self._update_button_text()
        self._update_plot_labels()
        self.refresh_data_from_repository()

    def _set_y_column(self, column: str) -> None:
        """Update Y-axis column and refresh display."""
        self.y_column = column
        self._update_button_text()
        self._update_plot_labels()
        self.refresh_data_from_repository()

    def _update_button_text(self) -> None:
        """Update axis buttons with current selections."""
        self.x_axis_button.setText(f"X: {self.x_column}")
        self.y_axis_button.setText(f"Y: {self.y_column}")

    def _update_plot_labels(self, text_color: str | None = None) -> None:
        """Update plot title and axis labels based on selected columns."""
        if text_color is None:
            # Determine text color from current theme
            is_dark = self._is_dark_theme()
            text_color = "#e0e0e0" if is_dark else "#000000"

        # Update title
        self.plot_widget.setTitle(f"{self.y_column} vs {self.x_column}", color=text_color, size="14pt")

        # Update axis labels
        label_styles = {"color": text_color, "font-size": "12pt"}
        self.plot_widget.setLabel("left", self.y_column, **label_styles)
        self.plot_widget.setLabel("bottom", self.x_column, **label_styles)

    @QtCore.Slot(object)
    def on_columns_change(self, columns: list[str]) -> None:
        """Handle notification that numeric chart columns have changed."""
        self.chart_columns = columns
        columns_does_not_exist = not bool(self.chart_columns)
        self.x_axis_button.setDisabled(columns_does_not_exist)
        self.y_axis_button.setDisabled(columns_does_not_exist)
        if columns_does_not_exist:
            return

        if self.x_column not in self.chart_columns:
            self.x_column = "time"

        if self.y_column not in self.chart_columns:
            self.y_column = next((c for c in self.chart_columns if c != self.x_column), "time")

        self._update_button_text()
        self._update_plot_labels()
