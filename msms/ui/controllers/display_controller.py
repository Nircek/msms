"""Controller for managing display labels and variable text views.

Note: If you see strange comments appearing in this file during pre-commit runs
(like "hey, can you hear me?" or suggestions to refactor), those are NOT from
the linter tools. They appear to be added manually or by an external process.
The actual ruff/mypy tools don't add conversational comments to code.
"""

import logging
from datetime import timedelta
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from PyQt6 import QtWidgets

logger = logging.getLogger(__name__)


class DisplayWidgets(NamedTuple):
    """Container for all UI widgets managed by the display controller."""

    time_label: QtWidgets.QLabel
    number_label: QtWidgets.QLabel
    sample_label: QtWidgets.QLabel
    control_label: QtWidgets.QLabel
    set_point_label: QtWidgets.QLabel
    ramp_label: QtWidgets.QLabel
    variables_text: QtWidgets.QTextEdit
    status_layout: QtWidgets.QWidget


class DisplayController:
    """Manage UI labels and text displays for experiment status."""

    def __init__(self, widgets: DisplayWidgets) -> None:
        """Initialize the display controller with UI widgets."""
        self.widgets = widgets

        # Initialize with default values
        self.update_labels({})

    def update_labels(self, data: dict[str, float | str]) -> None:
        """Update all display widgets with the latest data payload."""
        # Time and row number
        time = str(timedelta(seconds=int(data.get("time", 0))))
        no = f"#{data.get('row_number', 0):.0f}"
        self.widgets.time_label.setText(time)
        self.widgets.number_label.setText(no)

        # Temperature readings
        sample, control = data.get("sample", "N/A"), data.get("control", "N/A")
        sample = f"{sample:.2f}K" if isinstance(sample, float) else str(sample).strip()
        control = f"{control:.2f}K" if isinstance(control, float) else str(control).strip()
        self.widgets.sample_label.setText(sample)
        self.widgets.control_label.setText(control)

        # Set point with unit
        set_point, set_point_unit = data.get("set_point", "N/A"), data.get("set_point_unit", "")
        set_point = f"{set_point:.2f} {set_point_unit}" if isinstance(set_point, float) else str(set_point).strip()
        self.widgets.set_point_label.setText(set_point)

        # Ramp rate
        ramp_rate = data.get("ramp_rate") or "-"
        ramp_rate = f"{ramp_rate:.1f}K/s" if isinstance(ramp_rate, float) else str(ramp_rate).strip()
        self.widgets.ramp_label.setText(ramp_rate)

        # Update layout width if needed for proper label display
        self.widgets.status_layout.setMinimumWidth(
            max(self.widgets.status_layout.minimumWidth(), self.widgets.status_layout.sizeHint().width())
        )

        # Variables debug view
        self.widgets.variables_text.setPlainText("\n\n".join(f"{k}:\n{v!r}" for k, v in data.items()))

        logger.debug("Display updated with %d data fields", len(data))
