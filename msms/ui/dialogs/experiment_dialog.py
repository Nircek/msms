"""Dialog for managing experiment plans."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from PyQt6 import QtWidgets

from msms.ui.experiment import (
    SetSetpointStep,
    StopProgramStep,
    WaitForConditionStep,
    WaitForDatetimeStep,
    WaitForDurationStep,
)

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

    def _add_step(self) -> None:  # noqa: C901, PLR0912
        """Show dialog to add a new step."""
        step_types = [
            "Wait for Duration",
            "Wait for Datetime",
            "Wait for Condition",
            "Set Setpoint",
            "Stop Program",
        ]

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

        step_id = f"step_{len(self.steps) + 1}"

        if step_type == "Wait for Duration":
            duration, ok = QtWidgets.QInputDialog.getDouble(
                self,
                "Wait for Duration",
                "Duration (seconds):",
                10.0,
                0.1,
                86400.0,
                1,
            )
            if ok:
                self.steps.append(WaitForDurationStep(step_id, duration))

        elif step_type == "Wait for Datetime":
            future_time = datetime.now(UTC) + timedelta(minutes=5)
            datetime_str, ok = QtWidgets.QInputDialog.getText(
                self,
                "Wait for Datetime",
                "Datetime (ISO format, default +5min):",
                text=future_time.isoformat(),
            )
            if ok:
                try:
                    target_dt = datetime.fromisoformat(datetime_str)
                    self.steps.append(WaitForDatetimeStep(step_id, target_dt))
                except ValueError as e:
                    QtWidgets.QMessageBox.warning(self, "Invalid Datetime", str(e))
                    return

        elif step_type == "Wait for Condition":
            column, ok = QtWidgets.QInputDialog.getText(
                self,
                "Wait for Condition",
                "Column name:",
            )
            if not ok:
                return

            threshold, ok = QtWidgets.QInputDialog.getDouble(
                self,
                "Wait for Condition",
                "Threshold value:",
                100.0,
                -1000000.0,
                1000000.0,
                2,
            )
            if not ok:
                return

            comparison, ok = QtWidgets.QInputDialog.getItem(
                self,
                "Wait for Condition",
                "Comparison:",
                [">=", "<=", ">", "<", "==", "!="],
                0,
                False,
            )
            if ok:
                self.steps.append(WaitForConditionStep(step_id, column, threshold, comparison))

        elif step_type == "Set Setpoint":
            device, ok = QtWidgets.QInputDialog.getText(
                self,
                "Set Setpoint",
                "Device address:",
            )
            if not ok:
                return

            command, ok = QtWidgets.QInputDialog.getText(
                self,
                "Set Setpoint",
                "SCPI command:",
            )
            if ok:
                self.steps.append(SetSetpointStep(step_id, device, command))

        elif step_type == "Stop Program":
            self.steps.append(StopProgramStep(step_id))

        self._refresh_step_list()

    def _remove_step(self) -> None:
        """Remove selected step from plan."""
        current_row = self.step_list.currentRow()
        if current_row >= 0:
            self.steps.pop(current_row)
            self._refresh_step_list()

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
