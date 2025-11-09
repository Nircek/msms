"""Wait for datetime step implementation."""

import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from PyQt6 import QtWidgets

from msms.ui.experiment.register_step import register_step
from msms.ui.experiment.step_base import Step

if TYPE_CHECKING:
    from msms.ui.managers.experiment_manager import ExperimentManager

logger = logging.getLogger(__name__)


@register_step("Wait for Datetime")
class WaitForDatetimeStep(Step):
    """Wait until a specific datetime is reached."""

    def __init__(self, step_id: str, target_datetime: datetime) -> None:
        """Initialize step to wait until target datetime.

        Args:
            step_id: Unique identifier for this step.
            target_datetime: Datetime to wait for (timezone-aware).
        """
        super().__init__(step_id, f"Wait until {target_datetime.isoformat()}")
        self.target_datetime = target_datetime

    @classmethod
    def create_config_dialog(
        cls,
        _parent: QtWidgets.QWidget | None,
    ) -> QtWidgets.QDialog | None:
        """Create configuration dialog."""
        return None  # Use QInputDialog directly

    @classmethod
    def create_from_dialog(cls, _dialog: QtWidgets.QDialog | None, step_id: str) -> Step | None:
        """Create step from dialog input."""
        future_time = datetime.now(UTC) + timedelta(minutes=5)
        datetime_str, ok = QtWidgets.QInputDialog.getText(
            _dialog,  # type: ignore[arg-type]
            "Wait for Datetime",
            "Datetime (ISO format, default +5min):",
            text=future_time.isoformat(),
        )
        if ok:
            try:
                target_dt = datetime.fromisoformat(datetime_str)
                return cls(step_id, target_dt)
            except ValueError as e:
                QtWidgets.QMessageBox.warning(
                    _dialog,  # type: ignore[arg-type]
                    "Invalid Datetime",
                    str(e),
                )
        return None

    def evaluate(self, _runner: ExperimentManager) -> bool:
        """Check if current time has reached target."""
        return datetime.now(UTC) >= self.target_datetime
