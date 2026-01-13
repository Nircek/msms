import logging
from datetime import timedelta
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from PySide6 import QtWidgets

logger = logging.getLogger(__name__)


class DisplayWidgets(NamedTuple):
    """UI widgets for display controller."""

    time_label: QtWidgets.QLabel
    number_label: QtWidgets.QLabel
    sample_label: QtWidgets.QLabel
    control_label: QtWidgets.QLabel
    set_point_label: QtWidgets.QLabel
    ramp_label: QtWidgets.QLabel
    variables_text: QtWidgets.QTextEdit
    status_layout: QtWidgets.QWidget


class DisplayController:
    """UI labels and text displays for automation status."""

    def __init__(self, widgets: DisplayWidgets) -> None:
        self.widgets = widgets

        # Initialize with default values
        self.update_labels({})

    def update_labels(self, data: dict[str, float | str]) -> None:
        """Update display widgets with latest data."""
        # Time and row number
        time = str(timedelta(seconds=int(data.get("time", 0))))
        no = f"#{data.get('row_number', 0):.0f}"
        self.widgets.time_label.setText(time)
        self.widgets.number_label.setText(no)

        # Temperature readings
        sample, control = data.get("T_sample", "N/A"), data.get("T_control", "N/A")
        sample = f"{sample:.2f}K" if isinstance(sample, float) else truncate_text(sample.strip())
        control = f"{control:.2f}K" if isinstance(control, float) else truncate_text(control.strip())
        self.widgets.sample_label.setText(sample)
        self.widgets.control_label.setText(control)

        # Set point with unit
        set_point, set_point_unit = data.get("T_set_point", "N/A"), data.get("T_set_point_unit", "")
        set_point = (
            f"{set_point:.2f} {set_point_unit}" if isinstance(set_point, float) else truncate_text(set_point.strip())
        )
        self.widgets.set_point_label.setText(set_point)

        # Ramp rate
        ramp_rate = data.get("T_ramp_rate") or "-"
        ramp_rate = f"{ramp_rate:.1f}K/min" if isinstance(ramp_rate, float) else truncate_text(ramp_rate.strip())
        self.widgets.ramp_label.setText(ramp_rate)

        # Update layout width if needed for proper label display
        self.widgets.status_layout.setMinimumWidth(
            max(self.widgets.status_layout.minimumWidth(), self.widgets.status_layout.sizeHint().width())
        )

        # Variables debug view
        v_scroll_bar = self.widgets.variables_text.verticalScrollBar()
        v_scroll = v_scroll_bar.value() if v_scroll_bar is not None else 0
        self.widgets.variables_text.setPlainText("\n\n".join(f"{k}:\n{v!r}" for k, v in data.items()))
        if v_scroll_bar is not None:
            v_scroll_bar.setValue(v_scroll)

        logger.debug("Display updated with %d data fields", len(data))


def truncate_text(text: str, max_length: int = 10) -> str:
    """Truncate text to a maximum length, adding ellipsis if needed."""
    return text if len(text) <= max_length else text[: max_length - 1] + "…"
