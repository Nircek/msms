"""Wait for condition step implementation."""

import logging
from collections import deque
from typing import TYPE_CHECKING

from PyQt6 import QtWidgets

from msms.ui.experiment.register_step import register_step
from msms.ui.experiment.step_base import Step

if TYPE_CHECKING:
    from msms.ui.managers.experiment_manager import ExperimentManager

logger = logging.getLogger(__name__)


@register_step("Wait for Condition")
class WaitForConditionStep(Step):
    """Wait until a data column meets a threshold condition.

    Checks the last 3 measurements to account for noise.
    """

    def __init__(
        self,
        step_id: str,
        column_name: str,
        threshold: float,
        comparison: str = ">=",
    ) -> None:
        """Initialize step to wait for data condition.

        Args:
            step_id: Unique identifier for this step.
            column_name: Name of data column to monitor.
            threshold: Threshold value to compare against.
            comparison: Comparison operator (>= or <=).
        """
        super().__init__(
            step_id,
            f"Wait for {column_name} {comparison} {threshold}",
        )
        self.column_name = column_name
        self.threshold = threshold
        self.comparison = comparison
        self._recent_values: deque[float] = deque(maxlen=3)

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
            "Wait for Condition",
            "Column name:",
            text="control",
        )
        if not ok:
            return None

        threshold, ok = QtWidgets.QInputDialog.getDouble(
            _dialog,  # type: ignore[arg-type]
            "Wait for Condition",
            "Threshold value:",
            100.0,
            -1000000.0,
            1000000.0,
            2,
        )
        if not ok:
            return None

        comparison, ok = QtWidgets.QInputDialog.getItem(
            _dialog,  # type: ignore[arg-type]
            "Wait for Condition",
            "Comparison:",
            [">=", "<="],
            0,
            False,
        )
        if ok:
            return cls(step_id, column, threshold, comparison)
        return None

    def evaluate(self, runner: ExperimentManager) -> bool:
        """Check if latest data meets threshold condition.

        Returns True only if last 3 measurements all meet the condition
        to account for noise.
        """
        latest_data = runner.get_latest_data()
        if not latest_data or self.column_name not in latest_data:
            return False

        value = latest_data[self.column_name]
        if isinstance(value, str):
            return False

        # Add to recent values
        self._recent_values.append(value)

        # Need at least 3 measurements
        if len(self._recent_values) < 3:
            return False

        # Check if all last 3 values meet condition
        if self.comparison == ">=":
            return all(v >= self.threshold for v in self._recent_values)
        # <=
        return all(v <= self.threshold for v in self._recent_values)
