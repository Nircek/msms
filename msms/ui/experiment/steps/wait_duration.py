"""Wait for duration step implementation."""

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from PyQt6 import QtWidgets

from msms.ui.experiment.register_step import register_step
from msms.ui.experiment.step_base import Step

if TYPE_CHECKING:
    from msms.ui.managers.experiment_manager import ExperimentManager

logger = logging.getLogger(__name__)


@register_step("Wait for Duration")
class WaitForDurationStep(Step):
    """Wait for a specified duration in seconds."""

    def __init__(self, step_id: str, duration_seconds: float) -> None:
        """Initialize step to wait for duration.

        Args:
            step_id: Unique identifier for this step.
            duration_seconds: Number of seconds to wait.
        """
        super().__init__(step_id, f"Wait for {duration_seconds}s")
        self.duration_seconds = duration_seconds

    @classmethod
    def create_config_dialog(
        cls,
        _parent: QtWidgets.QWidget | None,
    ) -> QtWidgets.QDialog | None:
        """Create configuration dialog for duration input."""
        return None  # Use QInputDialog directly

    @classmethod
    def create_from_dialog(cls, _dialog: QtWidgets.QDialog | None, step_id: str) -> Step | None:
        """Create step from dialog (uses QInputDialog instead)."""
        duration, ok = QtWidgets.QInputDialog.getDouble(
            _dialog,  # type: ignore[arg-type]
            "Wait for Duration",
            "Duration (seconds):",
            10.0,
            0.1,
            86400.0,
            1,
        )
        if ok:
            return cls(step_id, duration)
        return None

    def evaluate(self, _runner: ExperimentManager) -> bool:
        """Check if duration has elapsed since step start."""
        if self.start_timestamp is None:
            return False

        elapsed = (datetime.now(UTC) - self.start_timestamp).total_seconds()
        return elapsed >= self.duration_seconds
