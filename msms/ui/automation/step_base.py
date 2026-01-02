"""Base class for automation steps."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from PySide6 import QtWidgets

    from msms.ui.controllers import ApplicationController
    from msms.ui.managers.automation_manager import AutomationManager


class Step(ABC):
    """Abstract base class for automation steps.

    Steps define automation actions or conditions. The Step Runner
    manages execution state (start timestamp, current index) globally.
    Each step implementation is stateless and queries services through
    the runner reference.
    """

    display_name: str = "Step"  # Set by @register_step decorator

    def __init__(self, step_id: str) -> None:
        """Initialize step with unique ID and default parameters.

        Args:
            step_id: Unique identifier for this step instance.
        """
        self.step_id = step_id
        self.start_timestamp: datetime | None = None

    @abstractmethod
    def get_label(self) -> str:
        """Get human-readable description of the step with current parameters.

        Returns:
            Human-readable label for this step.
        """

    @property
    def label(self) -> str:
        """Get current label (convenience property)."""
        return self.get_label()

    @abstractmethod
    def exec_edit_dialog(self, parent: QtWidgets.QWidget | None, app_controller: ApplicationController) -> bool:
        """Open dialog to edit step parameters.

        Args:
            parent: Parent widget for the dialog.
            app_controller: Application controller for accessing devices and data.

        Returns:
            True if parameters were modified, False if cancelled.
        """

    @abstractmethod
    def evaluate(self, runner: AutomationManager) -> bool:
        """Check if conditions for completing this step are met.

        Args:
            runner: Reference to the automation manager providing
                   access to data, devices, and other services.

        Returns:
            True if step is complete and runner should advance,
            False if step should continue.
        """

    def on_start(self, runner: AutomationManager) -> None:  # noqa: B027
        """Called once when this step becomes active.

        Override to issue commands to devices or perform
        initialization. Default implementation does nothing.

        Args:
            runner: Reference to the automation manager.
        """

    def on_finish(self, runner: AutomationManager) -> None:  # noqa: B027
        """Called once when step completes.

        Override for cleanup or finalization. Default implementation
        does nothing.

        Args:
            runner: Reference to the automation manager.
        """
