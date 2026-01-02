"""Stop program step implementation."""

import logging
from typing import TYPE_CHECKING

from msms.ui.automation.register_step import register_step
from msms.ui.automation.step_base import Step

if TYPE_CHECKING:
    from PySide6 import QtWidgets

    from msms.ui.controllers import ApplicationController
    from msms.ui.managers.automation_manager import AutomationManager

logger = logging.getLogger(__name__)


@register_step("Stop Program")
class StopProgramStep(Step):
    """Stop the automation program execution."""

    def __init__(self, step_id: str) -> None:
        """Initialize step to stop program execution.

        Args:
            step_id: Unique identifier for this step.
        """
        super().__init__(step_id)

    def get_label(self) -> str:  # noqa: PLR6301
        """Get human-readable label."""
        return "Stop program"

    def exec_edit_dialog(self, _parent: QtWidgets.QWidget | None, _app_controller: ApplicationController) -> bool:  # noqa: PLR6301
        """No configuration needed for stop step."""
        return True

    def on_start(self, _runner: AutomationManager) -> None:  # noqa: PLR6301
        """Request automation to stop."""
        logger.info("Stop program step activated")

    def evaluate(self, _runner: AutomationManager) -> bool:  # noqa: PLR6301
        """Complete immediately, triggering automation stop."""
        return True
