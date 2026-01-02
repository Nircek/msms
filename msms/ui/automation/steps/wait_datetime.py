"""Wait for datetime step implementation."""

import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from msms.ui.automation.register_step import register_step
from msms.ui.automation.step_base import Step
from msms.ui.dialogs.step_config_dialogs import WaitForDatetimeDialog

if TYPE_CHECKING:
    from msms.ui.controllers.app_controller import ApplicationController
    from msms.ui.managers.automation_manager import AutomationManager

logger = logging.getLogger(__name__)


@register_step("Wait for Datetime")
class WaitForDatetimeStep(Step):
    """Wait until a specific datetime is reached."""

    def __init__(self, step_id: str) -> None:
        """Initialize step with default parameters.

        Args:
            step_id: Unique identifier for this step.
        """
        super().__init__(step_id)
        self.target_datetime = datetime.now(UTC) + timedelta(minutes=5)

    def get_label(self) -> str:
        """Get human-readable label."""
        return f"Wait until {self.target_datetime.isoformat()}"

    def exec_edit_dialog(self, parent: QtWidgets.QWidget | None, _app_controller: ApplicationController) -> bool:
        """Open dialog to edit step parameters.

        Args:
            parent: Parent widget for the dialog.

        Returns:
            True if parameters were modified, False if cancelled.
        """
        dialog = WaitForDatetimeDialog(parent)
        dialog.datetime_edit.setText(self.target_datetime.isoformat())

        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return False

        self.target_datetime = dialog.get_datetime()
        return True

    def evaluate(self, _runner: AutomationManager) -> bool:
        """Check if current time has reached target."""
        return datetime.now(UTC) >= self.target_datetime
