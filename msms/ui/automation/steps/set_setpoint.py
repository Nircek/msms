"""Set setpoint step implementation."""

import logging
from typing import TYPE_CHECKING

from PySide6 import QtWidgets

from msms.ui.automation.register_step import register_step
from msms.ui.automation.step_base import Step
from msms.ui.dialogs.step_config_dialogs import SetSetpointDialog

if TYPE_CHECKING:
    from msms.ui.controllers import ApplicationController
    from msms.ui.managers.automation_manager import AutomationManager

logger = logging.getLogger(__name__)


@register_step("Set Setpoint")
class SetSetpointStep(Step):
    """Set a LakeShore device setpoint value."""

    def __init__(self, step_id: str) -> None:
        """Initialize step with default parameters.

        Args:
            step_id: Unique identifier for this step.
        """
        super().__init__(step_id)
        self.device_address = ""
        self.setpoint_value = 300.0
        self.ramp_rate_value = 0.0

    def get_label(self) -> str:
        """Get human-readable label."""
        if self.device_address:
            return f"Set SETP {self.setpoint_value} RAMPR {self.ramp_rate_value} on {self.device_address}"
        return "Set Setpoint (not configured)"

    def exec_edit_dialog(self, parent: QtWidgets.QWidget | None, app_controller: ApplicationController) -> bool:
        """Open dialog to edit step parameters.

        Args:
            parent: Parent widget for the dialog.
            app_controller: Application controller for accessing devices and data.

        Returns:
            True if parameters were modified, False if cancelled.
        """
        # Get device info from cached device info in app controller
        device_info_map: dict[str, tuple[str, str]] = {}

        # Build device info map from cached device info
        for address, info in app_controller.device_info_cache.items():
            device_name = info.device_name or "Unknown"
            display_text = f"{device_name} ({address})"
            device_info_map[address] = (device_name, display_text)

        dialog = SetSetpointDialog(parent, device_info=device_info_map)
        dialog.set_device_address(self.device_address)
        dialog.value_spinbox.setValue(self.setpoint_value)
        dialog.ramp_rate_spinbox.setValue(self.ramp_rate_value)

        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return False

        device_address = dialog.get_device_address()
        if not device_address:
            QtWidgets.QMessageBox.warning(
                dialog,
                "Invalid Input",
                "Device must be selected.",
            )
            return False

        self.device_address = device_address
        self.setpoint_value = dialog.get_setpoint_value()
        self.ramp_rate_value = dialog.get_ramp_rate_value()
        return True

    def on_start(self, runner: AutomationManager) -> None:
        """Send setpoint command when step starts."""
        command = f"SETP {self.setpoint_value}"
        try:
            runner.send_device_command(self.device_address, command)
            logger.info("Sent command to %s: %s", self.device_address, command)
        except Exception:
            logger.exception("Failed to send command to %s", self.device_address)

    def evaluate(self, _runner: AutomationManager) -> bool:  # noqa: PLR6301
        """Complete immediately after sending command."""
        return True
