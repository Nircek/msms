"""Dialog for managing experiment plans."""

import logging
from typing import TYPE_CHECKING

from PyQt6 import QtWidgets

from msms.ui.experiment import step_registry

if TYPE_CHECKING:
    from msms.ui.controllers.app_controller import ApplicationController
    from msms.ui.experiment.step_base import Step

logger = logging.getLogger(__name__)


class ExperimentDialog(QtWidgets.QDialog):
    """Dialog for creating and editing experiment plans."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None,
        app_controller: ApplicationController,
    ) -> None:
        """Initialize experiment dialog.

        Args:
            parent: Parent widget.
            app_controller: Application controller reference.
        """
        super().__init__(parent)
        self.app_controller = app_controller
        self.steps: list[Step] = []

        self.setWindowTitle("Experiment Plan")
        self.setMinimumSize(600, 400)

        self._setup_ui()
        self._load_current_steps()

    def _setup_ui(self) -> None:
        """Create dialog UI elements."""
        layout = QtWidgets.QVBoxLayout(self)

        # Step list
        list_label = QtWidgets.QLabel("Experiment Steps:")
        layout.addWidget(list_label)

        self.step_list = QtWidgets.QListWidget()
        layout.addWidget(self.step_list)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()

        add_button = QtWidgets.QPushButton("Add Step")
        add_button.clicked.connect(self._add_step)
        button_layout.addWidget(add_button)

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

        # Control buttons
        control_layout = QtWidgets.QHBoxLayout()

        start_button = QtWidgets.QPushButton("Start Experiment")
        start_button.clicked.connect(self._start_experiment)
        control_layout.addWidget(start_button)

        stop_button = QtWidgets.QPushButton("Stop Experiment")
        stop_button.clicked.connect(self._stop_experiment)
        control_layout.addWidget(stop_button)

        skip_button = QtWidgets.QPushButton("Skip to Next")
        skip_button.clicked.connect(self._skip_forward)
        control_layout.addWidget(skip_button)

        layout.addLayout(control_layout)

        # Status label
        self.status_label = QtWidgets.QLabel()
        layout.addWidget(self.status_label)

        # Dialog buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self._update_status()

    def _load_current_steps(self) -> None:
        """Load current experiment steps from manager."""
        self._refresh_step_list()

    def _refresh_step_list(self) -> None:
        """Update step list display."""
        self.step_list.clear()
        for i, step in enumerate(self.steps):
            status = ""
            if step.start_timestamp is not None:
                status = f" [Started: {step.start_timestamp.strftime('%H:%M:%S')}]"
            self.step_list.addItem(f"{i + 1}. {step.label}{status}")

    def _update_status(self) -> None:
        """Update status label with current experiment state."""
        is_running = self.app_controller.is_experiment_running()
        current_step = self.app_controller.get_current_step()

        if is_running and current_step:
            self.status_label.setText(f"Running: {current_step.label}")
        elif is_running:
            self.status_label.setText("Running")
        else:
            self.status_label.setText("Not running")

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

        step_type, ok = QtWidgets.QInputDialog.getItem(
            self,
            "Select Step Type",
            "Step type:",
            step_types,
            0,
            False,
        )

        if not ok:
            return

        # Find the step class
        step_class = None
        for cls in step_registry:
            if cls.display_name == step_type:
                step_class = cls
                break

        if step_class is None:
            return

        # Generate unique step ID
        step_id = f"step_{len(self.steps) + 1}"

        # Let the step class create its configuration dialog and instance
        dialog = step_class.create_config_dialog(self)
        step_instance = step_class.create_from_dialog(dialog, step_id)

        if step_instance is not None:
            self.steps.append(step_instance)
            self._refresh_step_list()
            # Immediately send steps to manager
            self.app_controller.set_experiment_steps(self.steps)

    def _remove_step(self) -> None:
        """Remove selected step from plan."""
        current_row = self.step_list.currentRow()
        if current_row >= 0:
            self.steps.pop(current_row)
            self._refresh_step_list()
            # Immediately send steps to manager
            self.app_controller.set_experiment_steps(self.steps)

    def _move_step_up(self) -> None:
        """Move selected step up in list."""
        current_row = self.step_list.currentRow()
        if current_row > 0:
            self.steps[current_row], self.steps[current_row - 1] = (
                self.steps[current_row - 1],
                self.steps[current_row],
            )
            self._refresh_step_list()
            self.step_list.setCurrentRow(current_row - 1)
            # Immediately send steps to manager
            self.app_controller.set_experiment_steps(self.steps)

    def _move_step_down(self) -> None:
        """Move selected step down in list."""
        current_row = self.step_list.currentRow()
        if 0 <= current_row < len(self.steps) - 1:
            self.steps[current_row], self.steps[current_row + 1] = (
                self.steps[current_row + 1],
                self.steps[current_row],
            )
            self._refresh_step_list()
            self.step_list.setCurrentRow(current_row + 1)
            # Immediately send steps to manager
            self.app_controller.set_experiment_steps(self.steps)

    def _start_experiment(self) -> None:
        """Start experiment with current plan."""
        if not self.steps:
            QtWidgets.QMessageBox.warning(self, "No Steps", "Add steps before starting experiment.")
            return

        self.app_controller.set_experiment_steps(self.steps)
        self.app_controller.start_experiment()
        self._update_status()
        logger.info("Experiment started with %d steps", len(self.steps))

    def _stop_experiment(self) -> None:
        """Stop running experiment."""
        self.app_controller.stop_experiment()
        self._update_status()
        logger.info("Experiment stopped")

    def _skip_forward(self) -> None:
        """Skip to next step in experiment."""
        self.app_controller.skip_experiment_forward()
        self._update_status()
        logger.info("Skipped to next step")

    def get_steps(self) -> list[Step]:
        """Get configured experiment steps."""
        return self.steps
