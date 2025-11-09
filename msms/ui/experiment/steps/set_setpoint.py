"""Set setpoint step implementation."""

import logging
from typing import TYPE_CHECKING

from PyQt6 import QtWidgets

from msms.ui.experiment.register_step import register_step
from msms.ui.experiment.step_base import Step

if TYPE_CHECKING:
    from msms.ui.managers.experiment_manager import ExperimentManager

logger = logging.getLogger(__name__)


@register_step("Set Setpoint")
class SetSetpointStep(Step):
    """Set a LakeShore device setpoint value."""

    def __init__(
        self,
        step_id: str,
        device_address: str,
        setpoint_value: float,
    ) -> None:
        """Initialize step to set device setpoint.

        Args:
            step_id: Unique identifier for this step.
            device_address: VISA address of LakeShore device.
            setpoint_value: Setpoint value to set.
        """
        super().__init__(step_id, f"Set {device_address}: SETP {setpoint_value}")
        self.device_address = device_address
        self.setpoint_value = setpoint_value

    @classmethod
    def create_config_dialog(
        cls,
        _parent: QtWidgets.QWidget | None,
    ) -> QtWidgets.QDialog | None:
        """Create configuration dialog."""
        return None  # Use QInputDialog directly

    @classmethod
    def create_from_dialog(cls, _dialog: QtWidgets.QDialog | None, step_id: str) -> Step | None:
        """Create step from dialog inputs.

        Note: In a full implementation, this should query the ApplicationController
        for available LakeShore devices and present them in a dropdown.
        For now, using text input.
        """
        device, ok = QtWidgets.QInputDialog.getText(
            _dialog,  # type: ignore[arg-type]
            "Set Setpoint",
            "LakeShore device address:",
        )
        if not ok:
            return None

        value, ok = QtWidgets.QInputDialog.getDouble(
            _dialog,  # type: ignore[arg-type]
            "Set Setpoint",
            "Setpoint value:",
            300.0,
            0.0,
            1000.0,
            1,
        )
        if ok:
            return cls(step_id, device, value)
        return None

    def on_start(self, runner: ExperimentManager) -> None:
        """Send setpoint command when step starts."""
        command = f"SETP {self.setpoint_value}"
        try:
            runner.send_device_command(self.device_address, command)
            logger.info("Sent command to %s: %s", self.device_address, command)
        except Exception:
            logger.exception("Failed to send command to %s", self.device_address)

    def evaluate(self, _runner: ExperimentManager) -> bool:
        """Complete immediately after sending command."""
        return True
