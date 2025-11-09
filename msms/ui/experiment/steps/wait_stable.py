"""Wait for stable condition step implementation."""

import logging
from collections import deque
from typing import TYPE_CHECKING

import numpy as np
from PyQt6 import QtWidgets

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

    def __init__(
        self,
        step_id: str,
        column_name: str,
        max_slope: float = 0.1,
        num_points: int = 10,
    ) -> None:
        """Initialize step to wait for stable condition.

        Args:
            step_id: Unique identifier for this step.
            column_name: Name of data column to monitor.
            max_slope: Maximum absolute slope for stability (default 0.1).
            num_points: Number of recent points to check (default 10).
        """
        super().__init__(
            step_id,
            f"Wait for {column_name} stable (|slope| <= {max_slope})",
        )
        self.column_name = column_name
        self.max_slope = max_slope
        self.num_points = num_points
        self._recent_values: deque[float] = deque(maxlen=num_points)

    @classmethod
    def create_config_dialog(
        cls,
        _parent: QtWidgets.QWidget | None,
    ) -> QtWidgets.QDialog | None:
        """Create configuration dialog."""
        return None  # Use QInputDialog directly

    @classmethod
    def create_from_dialog(cls, _dialog: QtWidgets.QDialog | None, step_id: str) -> Step | None:
        """Create step from dialog inputs."""
        column, ok = QtWidgets.QInputDialog.getText(
            _dialog,  # type: ignore[arg-type]
            "Wait for Stable",
            "Column name:",
            text="control",
        )
        if not ok:
            return None

        max_slope, ok = QtWidgets.QInputDialog.getDouble(
            _dialog,  # type: ignore[arg-type]
            "Wait for Stable",
            "Maximum absolute slope:",
            0.1,
            0.0,
            1000.0,
            2,
        )
        if not ok:
            return None

        num_points, ok = QtWidgets.QInputDialog.getInt(
            _dialog,  # type: ignore[arg-type]
            "Wait for Stable",
            "Number of points to check:",
            10,
            3,
            100,
        )
        if ok:
            return cls(step_id, column, max_slope, num_points)
        return None

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
