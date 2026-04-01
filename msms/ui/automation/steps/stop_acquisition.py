"""Stop acquisition step implementation."""

import logging
from typing import TYPE_CHECKING

from msms.ui.automation.register_step import register_step
from msms.ui.automation.step_base import Step

if TYPE_CHECKING:
    from PySide6 import QtWidgets

    from msms.ui.controllers import ApplicationController
    from msms.ui.managers.automation_manager import AutomationManager

logger = logging.getLogger(__name__)


@register_step("Stop Acquisition")
class StopAcquisitionStep(Step):
    """Stop device acquisition from automation."""

    def __init__(self, step_id: str) -> None:
        """Initialize stop-acquisition step.

        Args:
            step_id: Unique identifier for this step.
        """
        super().__init__(step_id)

    def get_label(self) -> str:  # noqa: PLR6301
        """Get human-readable label."""
        return "Stop acquisition"

    def exec_edit_dialog(self, _parent: QtWidgets.QWidget | None, _app_controller: ApplicationController) -> bool:  # noqa: PLR6301
        """No configuration needed for this step."""
        return True

    def on_start(self, runner: AutomationManager) -> None:
        """Request acquisition stop when this step begins."""
        logger.info("Stop acquisition step activated")
        runner.request_device_acquisition_stop()

    def evaluate(self, _runner: AutomationManager) -> bool:  # noqa: PLR6301
        """Complete immediately after emitting request."""
        return True
