"""Configuration dialogs for automation steps."""

import logging
from datetime import UTC, datetime, timedelta

from PySide6 import QtWidgets

logger = logging.getLogger(__name__)


class SetSetpointDialog(QtWidgets.QDialog):
    """Dialog for configuring a Set Setpoint step."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        device_info: dict[str, tuple[str, str]] | None = None,
    ) -> None:
        """Initialize the dialog.

        Args:
            parent: Parent widget.
            device_info: Dictionary mapping addresses to (device_name, display_text) tuples.
        """
        super().__init__(parent)
        self.setWindowTitle("Set Setpoint Configuration")
        self.setMinimumWidth(400)

        layout = QtWidgets.QFormLayout(self)

        # Device selection combo box (required)
        self.device_combo = QtWidgets.QComboBox()
        self.device_combo.setEditable(False)
        if device_info:
            for address, (_device_name, display_text) in device_info.items():
                self.device_combo.addItem(display_text, address)
        layout.addRow("LakeShore Device:", self.device_combo)

        # Setpoint value input
        self.value_spinbox = QtWidgets.QDoubleSpinBox()
        self.value_spinbox.setRange(0.0, 1000.0)
        self.value_spinbox.setValue(300.0)
        self.value_spinbox.setDecimals(1)
        self.value_spinbox.setSuffix(" K")
        layout.addRow("Setpoint Value:", self.value_spinbox)

        # Buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def get_device_address(self) -> str:
        """Get the configured device address."""
        return self.device_combo.currentData() or ""

    def set_device_address(self, address: str) -> None:
        """Set the device address field."""
        # Find by data (address), not by text
        for i in range(self.device_combo.count()):
            if self.device_combo.itemData(i) == address:
                self.device_combo.setCurrentIndex(i)
                return

    def get_setpoint_value(self) -> float:
        """Get the configured setpoint value."""
        return self.value_spinbox.value()


class WaitForDurationDialog(QtWidgets.QDialog):
    """Dialog for configuring a Wait for Duration step."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Initialize the dialog.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Wait for Duration Configuration")
        self.setMinimumWidth(400)

        layout = QtWidgets.QFormLayout(self)

        # Duration input
        self.duration_spinbox = QtWidgets.QDoubleSpinBox()
        self.duration_spinbox.setRange(0.1, 86400.0)
        self.duration_spinbox.setValue(10.0)
        self.duration_spinbox.setDecimals(1)
        self.duration_spinbox.setSuffix(" seconds")
        layout.addRow("Duration:", self.duration_spinbox)

        # Buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def get_duration(self) -> float:
        """Get the configured duration in seconds."""
        return self.duration_spinbox.value()


class WaitForStableDialog(QtWidgets.QDialog):
    """Dialog for configuring a Wait for Stable step."""

    def __init__(self, parent: QtWidgets.QWidget | None = None, column_names: list[str] | None = None) -> None:
        """Initialize the dialog.

        Args:
            parent: Parent widget.
            column_names: List of available column names to populate combo box.
        """
        super().__init__(parent)
        self.setWindowTitle("Wait for Stable Configuration")
        self.setMinimumWidth(400)

        layout = QtWidgets.QFormLayout(self)

        # Column name combo box (required)
        self.column_combo = QtWidgets.QComboBox()
        self.column_combo.setEditable(False)
        if column_names:
            self.column_combo.addItems(column_names)
        layout.addRow("Column Name:", self.column_combo)

        # Max slope input
        self.slope_spinbox = QtWidgets.QDoubleSpinBox()
        self.slope_spinbox.setRange(0.0, 1000.0)
        self.slope_spinbox.setValue(0.1)
        self.slope_spinbox.setDecimals(2)
        layout.addRow("Maximum Absolute Slope:", self.slope_spinbox)

        # Number of points input
        self.points_spinbox = QtWidgets.QSpinBox()
        self.points_spinbox.setRange(3, 100)
        self.points_spinbox.setValue(10)
        layout.addRow("Number of Points to Check:", self.points_spinbox)

        # Buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def get_column_name(self) -> str:
        """Get the configured column name."""
        return self.column_combo.currentText().strip()

    def set_column_name(self, column_name: str) -> None:
        """Set the column name field."""
        # Find by text
        index = self.column_combo.findText(column_name)
        if index >= 0:
            self.column_combo.setCurrentIndex(index)

    def get_max_slope(self) -> float:
        """Get the configured maximum slope."""
        return self.slope_spinbox.value()

    def get_num_points(self) -> int:
        """Get the configured number of points."""
        return self.points_spinbox.value()


class WaitForConditionDialog(QtWidgets.QDialog):
    """Dialog for configuring a Wait for Condition step."""

    def __init__(self, parent: QtWidgets.QWidget | None = None, column_names: list[str] | None = None) -> None:
        """Initialize the dialog.

        Args:
            parent: Parent widget.
            column_names: List of available column names to populate combo box.
        """
        super().__init__(parent)
        self.setWindowTitle("Wait for Condition Configuration")
        self.setMinimumWidth(400)

        layout = QtWidgets.QFormLayout(self)

        # Column name combo box (required)
        self.column_combo = QtWidgets.QComboBox()
        self.column_combo.setEditable(False)
        if column_names:
            self.column_combo.addItems(column_names)
        layout.addRow("Column Name:", self.column_combo)

        # Threshold input
        self.threshold_spinbox = QtWidgets.QDoubleSpinBox()
        self.threshold_spinbox.setRange(-1000000.0, 1000000.0)
        self.threshold_spinbox.setValue(100.0)
        self.threshold_spinbox.setDecimals(2)
        layout.addRow("Threshold Value:", self.threshold_spinbox)

        # Comparison operator
        self.comparison_combo = QtWidgets.QComboBox()
        self.comparison_combo.addItems([">=", "<="])
        layout.addRow("Comparison:", self.comparison_combo)

        # Buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def get_column_name(self) -> str:
        """Get the configured column name."""
        return self.column_combo.currentText().strip()

    def set_column_name(self, column_name: str) -> None:
        """Set the column name field."""
        # Find by text
        index = self.column_combo.findText(column_name)
        if index >= 0:
            self.column_combo.setCurrentIndex(index)

    def get_threshold(self) -> float:
        """Get the configured threshold value."""
        return self.threshold_spinbox.value()

    def get_comparison(self) -> str:
        """Get the configured comparison operator."""
        return self.comparison_combo.currentText()


class WaitForDatetimeDialog(QtWidgets.QDialog):
    """Dialog for configuring a Wait for Datetime step."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        """Initialize the dialog.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Wait for Datetime Configuration")
        self.setMinimumWidth(400)

        layout = QtWidgets.QFormLayout(self)

        # Datetime input
        self.datetime_edit = QtWidgets.QLineEdit()
        future_time = datetime.now(UTC) + timedelta(minutes=5)
        self.datetime_edit.setText(future_time.isoformat())
        self.datetime_edit.setPlaceholderText("ISO format: YYYY-MM-DDTHH:MM:SS+00:00")
        layout.addRow("Target Datetime:", self.datetime_edit)

        # Help text
        help_label = QtWidgets.QLabel("Enter datetime in ISO format (default is +5 minutes)")
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addRow(help_label)

        # Buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def _validate_and_accept(self) -> None:
        """Validate datetime input before accepting."""
        try:
            datetime.fromisoformat(self.datetime_edit.text().strip())
            self.accept()
        except ValueError as e:
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid Datetime",
                f"Invalid datetime format: {e}",
            )

    def get_datetime(self) -> datetime:
        """Get the configured target datetime."""
        return datetime.fromisoformat(self.datetime_edit.text().strip())
