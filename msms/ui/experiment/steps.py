"""Concrete step implementations for experiments."""

from __future__ import annotations

import logging
import operator
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from msms.ui.experiment.step_base import Step

if TYPE_CHECKING:
    from collections.abc import Callable

    from msms.ui.managers.experiment_manager import ExperimentManager

logger = logging.getLogger(__name__)


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

    def evaluate(self, runner: ExperimentManager) -> bool:  # noqa: ARG002
        """Check if current time has reached target."""
        return datetime.now(UTC) >= self.target_datetime


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

    def evaluate(self, runner: ExperimentManager) -> bool:  # noqa: ARG002
        """Check if duration has elapsed since step start."""
        if self.start_timestamp is None:
            return False

        elapsed = (datetime.now(UTC) - self.start_timestamp).total_seconds()
        return elapsed >= self.duration_seconds


class WaitForConditionStep(Step):
    """Wait until a data column meets a threshold condition."""

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
            comparison: Comparison operator (>=, <=, >, <, ==, !=).
        """
        super().__init__(
            step_id,
            f"Wait for {column_name} {comparison} {threshold}",
        )
        self.column_name = column_name
        self.threshold = threshold
        self.comparison_op = self._get_comparison_op(comparison)

    @staticmethod
    def _get_comparison_op(comparison: str) -> Callable[[float, float], bool]:
        """Map comparison string to operator function."""
        ops: dict[str, Callable[[float, float], bool]] = {
            ">=": operator.ge,
            "<=": operator.le,
            ">": operator.gt,
            "<": operator.lt,
            "==": operator.eq,
            "!=": operator.ne,
        }
        return ops[comparison]

    def evaluate(self, runner: ExperimentManager) -> bool:
        """Check if latest data meets threshold condition."""
        latest_data = runner.get_latest_data()
        if not latest_data or self.column_name not in latest_data:
            return False

        value = latest_data[self.column_name]
        if isinstance(value, str):
            return False

        return self.comparison_op(value, self.threshold)


class SetSetpointStep(Step):
    """Set a device setpoint value."""

    def __init__(
        self,
        step_id: str,
        device_address: str,
        command: str,
    ) -> None:
        """Initialize step to set device setpoint.

        Args:
            step_id: Unique identifier for this step.
            device_address: VISA address of target device.
            command: SCPI command to send (e.g., "SETP 300").
        """
        super().__init__(step_id, f"Set {device_address}: {command}")
        self.device_address = device_address
        self.command = command

    def on_start(self, runner: ExperimentManager) -> None:
        """Send setpoint command when step starts."""
        try:
            runner.send_device_command(self.device_address, self.command)
            logger.info("Sent command to %s: %s", self.device_address, self.command)
        except Exception:
            logger.exception("Failed to send command to %s", self.device_address)

    def evaluate(self, runner: ExperimentManager) -> bool:  # noqa: ARG002, PLR6301
        """Complete immediately after sending command."""
        return True


class StopProgramStep(Step):
    """Stop the experiment program execution."""

    def __init__(self, step_id: str) -> None:
        """Initialize step to stop program execution.

        Args:
            step_id: Unique identifier for this step.
        """
        super().__init__(step_id, "Stop program")

    def on_start(self, runner: ExperimentManager) -> None:  # noqa: ARG002, PLR6301
        """Request experiment to stop."""
        logger.info("Stop program step activated")

    def evaluate(self, runner: ExperimentManager) -> bool:  # noqa: ARG002, PLR6301
        """Complete immediately, triggering experiment stop."""
        return True
