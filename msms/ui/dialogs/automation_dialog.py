"""Dialog for managing automation plans."""

import logging
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtWidgets

from msms.ui.automation import step_registry

if TYPE_CHECKING:
    from msms.ui.automation.step_base import Step
    from msms.ui.controllers import ApplicationController

logger = logging.getLogger(__name__)


class AutomationDialog(QtWidgets.QDialog):
    """Dialog for creating and editing automation plans."""

    # Automation management signals
    automation_get_steps_requested = QtCore.Signal()
    automation_set_steps_requested = QtCore.Signal(object)

    def __init__(
        self,
        parent: QtWidgets.QWidget | None,
        app_controller: ApplicationController,
    ) -> None:
        """Initialize automation dialog.

        Args:
            parent: Parent widget.
            app_controller: Application controller reference.
        """
        super().__init__(parent)
        self.app_controller = app_controller
        self.steps: list[Step] = []

        self.setWindowTitle("Automation Plan")
        self.setMinimumSize(600, 400)

        self._setup_ui()

        # Connect to signals before requesting data

        self.automation_get_steps_requested.connect(self.app_controller.managers.automation.on_get_steps_request)
        self.automation_set_steps_requested.connect(self.app_controller.managers.automation.on_set_steps)
        self.app_controller.managers.automation.steps_changed.connect(self._on_steps_changed)
        self.app_controller.managers.automation.current_step_changed.connect(self._on_current_step_changed)

        # Request current steps
        self.automation_get_steps_requested.emit()

    def _setup_ui(self) -> None:
        """Create dialog UI elements."""
        layout = QtWidgets.QVBoxLayout(self)

        # Step list
        list_label = QtWidgets.QLabel("Automation Steps:")
        layout.addWidget(list_label)

        self.step_list = QtWidgets.QListWidget()
        layout.addWidget(self.step_list)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()

        add_button = QtWidgets.QPushButton("Add Step")
        add_button.clicked.connect(self._add_step)
        button_layout.addWidget(add_button)

        edit_button = QtWidgets.QPushButton("Edit Step")
        edit_button.clicked.connect(self._edit_step)
        button_layout.addWidget(edit_button)

        remove_button = QtWidgets.QPushButton("Remove Step")
        remove_button.clicked.connect(self._remove_step)
        button_layout.addWidget(remove_button)

        move_up_button = QtWidgets.QPushButton("Move Up")
        move_up_button.clicked.connect(self._move_step_up)
        button_layout.addWidget(move_up_button)

        move_down_button = QtWidgets.QPushButton("Move Down")
        move_down_button.clicked.connect(self._move_step_down)
        button_layout.addWidget(move_down_button)

        layout.addLayout(button_layout)

        # Dialog buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    @QtCore.Slot(object)
    def _on_steps_changed(self, steps: list[Step]) -> None:
        """Handle steps changed signal from manager.

        Args:
            steps: Updated list of automation steps.
        """
        self.steps = steps
        self._refresh_step_list()

    @QtCore.Slot(object)
    def _on_current_step_changed(self, _current_step: Step | None) -> None:
        """Handle current step changed signal.

        Args:
            _current_step: Currently executing step or None.
        """
        self._refresh_step_list()

    def _refresh_step_list(self) -> None:
        """Update step list display."""
        self.step_list.clear()
        for i, step in enumerate(self.steps):
            status = ""
            if step.start_timestamp is not None:
                status = f" [Started: {step.start_timestamp.strftime('%H:%M:%S')}]"
            self.step_list.addItem(f"{i + 1}. {step.label}{status}")

    def _add_step(self) -> None:
        """Show dialog to add a new step."""
        # Get list of registered step types
        step_types = [step_class.display_name for step_class in step_registry]

        if not step_types:
            QtWidgets.QMessageBox.warning(
                self,
                "No Steps Available",
                "No step types are registered.",
            )
            return

        # Create step type selection dialog
        selection_dialog = QtWidgets.QDialog(self)
        selection_dialog.setWindowTitle("Select Step Type")
        selection_dialog.setMinimumWidth(300)

        layout = QtWidgets.QVBoxLayout(selection_dialog)

        label = QtWidgets.QLabel("Select step type:")
        layout.addWidget(label)

        step_list = QtWidgets.QListWidget()
        step_list.addItems(step_types)
        step_list.setCurrentRow(0)
        layout.addWidget(step_list)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(selection_dialog.accept)
        button_box.rejected.connect(selection_dialog.reject)
        layout.addWidget(button_box)

        if selection_dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        step_type = step_list.currentItem()
        if step_type is None:
            return

        # Find the step class
        step_class = None
        for cls in step_registry:
            if cls.display_name == step_type.text():
                step_class = cls
                break

        if step_class is None:
            return

        # Generate unique step ID using thread-safe counter
        step_id = f"step_{self.app_controller.managers.automation.threaded_new_step_id()}"

        # Create step instance with default parameters
        step_instance = step_class(step_id)

        # Open edit dialog
        if step_instance.exec_edit_dialog(self, self.app_controller):
            # Request manager to add the step
            updated_steps = [*self.steps, step_instance]
            self.automation_set_steps_requested.emit(updated_steps)

    def _edit_step(self) -> None:
        """Edit selected step parameters."""
        current_row = self.step_list.currentRow()
        if current_row < 0:
            return

        step = self.steps[current_row]
        if step.exec_edit_dialog(self, self.app_controller):
            # Request manager to update the steps (to trigger refresh)
            self.automation_set_steps_requested.emit(list(self.steps))

    def _remove_step(self) -> None:
        """Remove selected step from plan."""
        current_row = self.step_list.currentRow()
        if current_row >= 0:
            # Request manager to remove the step
            updated_steps = [step for i, step in enumerate(self.steps) if i != current_row]
            self.automation_set_steps_requested.emit(updated_steps)

    def _move_step_up(self) -> None:
        """Move selected step up in list."""
        current_row = self.step_list.currentRow()
        if current_row > 0:
            # Request manager to reorder steps
            updated_steps = list(self.steps)
            updated_steps[current_row], updated_steps[current_row - 1] = (
                updated_steps[current_row - 1],
                updated_steps[current_row],
            )
            self.automation_set_steps_requested.emit(updated_steps)
            # Update selection after refresh
            self.step_list.setCurrentRow(current_row - 1)

    def _move_step_down(self) -> None:
        """Move selected step down in list."""
        current_row = self.step_list.currentRow()
        if 0 <= current_row < len(self.steps) - 1:
            # Request manager to reorder steps
            updated_steps = list(self.steps)
            updated_steps[current_row], updated_steps[current_row + 1] = (
                updated_steps[current_row + 1],
                updated_steps[current_row],
            )
            self.automation_set_steps_requested.emit(updated_steps)
            # Update selection after refresh
            self.step_list.setCurrentRow(current_row + 1)

    def get_steps(self) -> list[Step]:
        """Get configured automation steps."""
        return self.steps
