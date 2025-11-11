"""Wait for stable condition step implementation."""

import logging
from collections import deque
from typing import TYPE_CHECKING

import numpy as np
from PyQt6 import QtWidgets

from msms.ui.controllers.app_controller import ApplicationController
from msms.ui.dialogs.step_config_dialogs import WaitForStableDialog
from msms.ui.experiment.register_step import register_step
from msms.ui.experiment.step_base import Step

if TYPE_CHECKING:
    from msms.ui.managers.experiment_manager import ExperimentManager

logger = logging.getLogger(__name__)


@register_step("Wait for Stable")
class WaitForStableStep(Step):
    """Wait until a data column is stable (linear fit with |slope| <= threshold).

    Checks recent measurements to verify stability via linear regression.
    """

    def __init__(self, step_id: str) -> None:
        """Initialize step with default parameters.

        Args:
            step_id: Unique identifier for this step.
        """
        super().__init__(step_id)
        self.column_name = "control"
        self.max_slope = 0.1
        self.num_points = 10
        self._recent_values: deque[float] = deque(maxlen=self.num_points)

    def get_label(self) -> str:
        """Get human-readable label."""
        return f"Wait for {self.column_name} stable (|slope| <= {self.max_slope})"

    def exec_edit_dialog(self, parent: QtWidgets.QWidget | None, app_controller: object) -> bool:
        """Open dialog to edit step parameters.

        Args:
            parent: Parent widget for the dialog.
            app_controller: Application controller for accessing devices and data.

        Returns:
            True if parameters were modified, False if cancelled.
        """
        # Get available column names from app_controller
        column_names = None
        if isinstance(app_controller, ApplicationController):
            columns = app_controller.data_repository.columns
            column_names = list(columns) if columns else None

        dialog = WaitForStableDialog(parent, column_names=column_names)
        dialog.set_column_name(self.column_name)
        dialog.slope_spinbox.setValue(self.max_slope)
        dialog.points_spinbox.setValue(self.num_points)

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
        self.max_slope = dialog.get_max_slope()
        self.num_points = dialog.get_num_points()
        self._recent_values = deque(maxlen=self.num_points)
        return True

    def evaluate(self, runner: ExperimentManager) -> bool:
        """Check if column is stable via linear regression.

        Returns True only if recent measurements show |slope| <= max_slope.
        """
        latest_data = runner.get_latest_data()
        if not latest_data or self.column_name not in latest_data:
            return False

        value = latest_data[self.column_name]
        if isinstance(value, str):
            return False

        # Add to recent values
        self._recent_values.append(value)

        # Need enough measurements for linear fit
        if len(self._recent_values) < self.num_points:
            return False

        # Perform linear regression
        x = np.arange(len(self._recent_values))
        y = np.array(self._recent_values)

        # Calculate slope using least squares
        slope = np.polyfit(x, y, 1)[0]

        # Check if absolute slope is within threshold
        return abs(slope) <= self.max_slope
