"""Wait for condition step implementation."""

import logging
from collections import deque
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from msms.ui.automation.register_step import register_step
from msms.ui.automation.step_base import Step, StepEvaluationSource
from msms.ui.dialogs.step_config_dialogs import WaitForConditionDialog

if TYPE_CHECKING:
    from msms.ui.controllers import ApplicationController
    from msms.ui.managers.automation_manager import AutomationManager

logger = logging.getLogger(__name__)


@register_step("Wait for Condition")
class WaitForConditionStep(Step):
    """Wait until a data column meets a threshold condition.

    Checks the last 3 measurements to account for noise.
    """

    TEST_MEASUREMENTS_COUNT = 3

    def __init__(self, step_id: str) -> None:
        """Initialize step with default parameters.

        Args:
            step_id: Unique identifier for this step.
        """
        super().__init__(step_id)
        self.column_name = "control"
        self.threshold = 100.0
        self.comparison = ">="
        self._recent_values: deque[float] = deque(maxlen=self.TEST_MEASUREMENTS_COUNT)

    def get_label(self) -> str:
        """Get human-readable label."""
        return f"Wait for {self.column_name} {self.comparison} {self.threshold}"

    def exec_edit_dialog(self, parent: QtWidgets.QWidget | None, app_controller: ApplicationController) -> bool:
        """Open dialog to edit step parameters.

        Args:
            parent: Parent widget for the dialog.
            app_controller: Application controller for accessing devices and data.

        Returns:
            True if parameters were modified, False if cancelled.
        """
        # Get available column names from app_controller
        columns = app_controller.data_repository.columns
        column_names = list(columns) if columns else None

        dialog = WaitForConditionDialog(parent, column_names=column_names)
        dialog.set_column_name(self.column_name)
        dialog.threshold_spinbox.setValue(self.threshold)
        dialog.comparison_combo.setCurrentText(self.comparison)

        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return False

        column_name = dialog.get_column_name()
        if not column_name:
            QtWidgets.QMessageBox.warning(
                dialog,
                "Invalid Input",
                "Column name cannot be empty.",
            )
            return False

        self.column_name = column_name
        self.threshold = dialog.get_threshold()
        self.comparison = dialog.get_comparison()
        return True

    def evaluate(self, runner: AutomationManager, source: StepEvaluationSource) -> bool:
        """Check if latest data meets threshold condition.

        Returns True only if last 3 measurements all meet the condition
        to account for noise.
        """
        if source is not StepEvaluationSource.NEW_DATA:
            return False

        latest_data = runner.get_latest_data()
        if not latest_data or self.column_name not in latest_data:
            return False

        value = latest_data[self.column_name]
        if isinstance(value, str):
            return False

        # Add to recent values
        self._recent_values.append(value)

        # Need at least 3 measurements
        if len(self._recent_values) < self.TEST_MEASUREMENTS_COUNT:
            return False

        # Check if all last 3 values meet condition
        if self.comparison == ">=":
            return all(v >= self.threshold for v in self._recent_values)
        # <=
        return all(v <= self.threshold for v in self._recent_values)
