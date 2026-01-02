"""Wait for duration step implementation."""

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from msms.ui.automation.register_step import register_step
from msms.ui.automation.step_base import Step
from msms.ui.dialogs.step_config_dialogs import WaitForDurationDialog

if TYPE_CHECKING:
    from msms.ui.controllers.app_controller import ApplicationController
    from msms.ui.managers.automation_manager import AutomationManager

logger = logging.getLogger(__name__)


@register_step("Wait for Duration")
class WaitForDurationStep(Step):
    """Wait for a specified duration in seconds."""

    def __init__(self, step_id: str) -> None:
        """Initialize step with default parameters.

        Args:
            step_id: Unique identifier for this step.
        """
        super().__init__(step_id)
        self.duration_seconds = 10.0

    def get_label(self) -> str:
        """Get human-readable label."""
        return f"Wait for {self.duration_seconds}s"

    def exec_edit_dialog(self, parent: QtWidgets.QWidget | None, _app_controller: ApplicationController) -> bool:
        """Open dialog to edit step parameters.

        Args:
            parent: Parent widget for the dialog.

        Returns:
            True if parameters were modified, False if cancelled.
        """
        dialog = WaitForDurationDialog(parent)
        dialog.duration_spinbox.setValue(self.duration_seconds)

        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return False

        self.duration_seconds = dialog.get_duration()
        return True

    def evaluate(self, _runner: AutomationManager) -> bool:
        """Check if duration has elapsed since step start."""
        if self.start_timestamp is None:
            return False

        elapsed = (datetime.now(UTC) - self.start_timestamp).total_seconds()
        return elapsed >= self.duration_seconds
