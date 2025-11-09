"""Stop program step implementation."""

import logging
from typing import TYPE_CHECKING

from PyQt6 import QtWidgets

from msms.ui.experiment.register_step import register_step
from msms.ui.experiment.step_base import Step

if TYPE_CHECKING:
    from msms.ui.managers.experiment_manager import ExperimentManager

logger = logging.getLogger(__name__)


@register_step("Stop Program")
class StopProgramStep(Step):
    """Stop the experiment program execution."""

    def __init__(self, step_id: str) -> None:
        """Initialize step to stop program execution.

        Args:
            step_id: Unique identifier for this step.
        """
        super().__init__(step_id, "Stop program")

    @classmethod
    def create_config_dialog(
        cls,
        _parent: QtWidgets.QWidget | None,
    ) -> QtWidgets.QDialog | None:
        """No configuration needed for stop step."""
        return None

    @classmethod
    def create_from_dialog(cls, __dialog: QtWidgets.QDialog | None, step_id: str) -> Step | None:
        """Create stop step (no configuration needed)."""
        return cls(step_id)

    def on_start(self, _runner: ExperimentManager) -> None:
        """Request experiment to stop."""
        logger.info("Stop program step activated")

    def evaluate(self, _runner: ExperimentManager) -> bool:
        """Complete immediately, triggering experiment stop."""
        return True
