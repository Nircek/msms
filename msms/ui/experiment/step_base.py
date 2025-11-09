"""Base class for experiment steps."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt6 import QtWidgets

    from msms.ui.managers.experiment_manager import ExperimentManager


class Step(ABC):
    """Abstract base class for experiment steps.

    Steps define experimental actions or conditions. The Step Runner
    manages execution state (start timestamp, current index) globally.
    Each step implementation is stateless and queries services through
    the runner reference.
    """

    display_name: str = "Step"  # Set by @register_step decorator

    def __init__(self, step_id: str, label: str) -> None:
        """Initialize step with unique ID and human-readable label.

        Args:
            step_id: Unique identifier for this step instance.
            label: Human-readable description of the step.
        """
        self.step_id = step_id
        self.label = label
        self.start_timestamp: datetime | None = None

    @classmethod
    @abstractmethod
    def create_config_dialog(
        cls,
        parent: QtWidgets.QWidget | None,
    ) -> QtWidgets.QDialog | None:
        """Create configuration dialog for this step type.

        Args:
            parent: Parent widget for the dialog.

        Returns:
            Dialog instance or None if no configuration needed.
        """

    @classmethod
    @abstractmethod
    def create_from_dialog(cls, dialog: QtWidgets.QDialog, step_id: str) -> Step | None:
        """Create step instance from configuration dialog.

        Args:
            dialog: The configuration dialog returned by create_config_dialog.
            step_id: Unique identifier for this step instance.

        Returns:
            Step instance or None if cancelled/invalid.
        """

    @abstractmethod
    def evaluate(self, runner: ExperimentManager) -> bool:
        """Check if conditions for completing this step are met.

        Args:
            runner: Reference to the experiment manager providing
                   access to data, devices, and other services.

        Returns:
            True if step is complete and runner should advance,
            False if step should continue.
        """

    def on_start(self, runner: ExperimentManager) -> None:  # noqa: B027
        """Called once when this step becomes active.

        Override to issue commands to devices or perform
        initialization. Default implementation does nothing.

        Args:
            runner: Reference to the experiment manager.
        """

    def on_finish(self, runner: ExperimentManager) -> None:  # noqa: B027
        """Called once when step completes.

        Override for cleanup or finalization. Default implementation
        does nothing.

        Args:
            runner: Reference to the experiment manager.
        """
