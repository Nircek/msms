"""Experiment orchestration manager (Step Runner)."""

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from PyQt6 import QtCore

if TYPE_CHECKING:
    from msms.ui.experiment.step_base import Step

logger = logging.getLogger(__name__)


class ExperimentManager(QtCore.QObject):
    """Manage execution of procedural experiment steps.

    Runs in separate thread, evaluates current step every second
    and on new data arrival. Maintains ordered list of steps and
    records start timestamp for each executed step.
    """

    current_step_changed = QtCore.pyqtSignal(object)
    experiment_completed = QtCore.pyqtSignal()
    experiment_started = QtCore.pyqtSignal()
    experiment_stopped = QtCore.pyqtSignal()
    experiment_log_updated = QtCore.pyqtSignal(object)
    device_command_requested = QtCore.pyqtSignal(object, object)

    def __init__(self) -> None:
        """Initialize experiment manager with empty plan."""
        super().__init__()
        self._steps: list[Step] = []
        self._current_index = 0
        self._is_running = False
        self._timer: QtCore.QTimer | None = None
        self._latest_data: dict[str, str | float] = {}

    @property
    def is_running(self) -> bool:
        """Check if experiment is currently running."""
        return self._is_running

    @property
    def current_step(self) -> Step | None:
        """Get currently executing step or None if no active step."""
        if 0 <= self._current_index < len(self._steps):
            return self._steps[self._current_index]
        return None

    @property
    def next_step(self) -> Step | None:
        """Get next step to execute or None if at end."""
        next_index = self._current_index + 1
        if 0 <= next_index < len(self._steps):
            return self._steps[next_index]
        return None

    def get_latest_data(self) -> dict[str, str | float]:
        """Provide access to latest measurement data for step evaluation."""
        return self._latest_data.copy()

    def send_device_command(self, device_address: str, command: str) -> None:
        """Send command to device via signal.

        Args:
            device_address: VISA address of target device.
            command: SCPI command string to send.
        """
        self.device_command_requested.emit(device_address, command)

    @QtCore.pyqtSlot(object)
    def on_set_steps(self, steps: list[Step]) -> None:
        """Replace experiment plan with new steps.

        Args:
            steps: New list of step instances to execute.
        """
        self._steps = steps
        self._current_index = 0
        logger.info("Experiment plan updated with %d steps", len(steps))

    @QtCore.pyqtSlot(object)
    def on_add_step(self, step: Step) -> None:
        """Add step to end of experiment plan.

        Args:
            step: Step instance to append.
        """
        self._steps.append(step)
        logger.info("Added step: %s", step.label)

    @QtCore.pyqtSlot(object)
    def on_insert_step(self, params: tuple[int, Step]) -> None:
        """Insert step at specific position.

        Args:
            params: Tuple of (index, step) where index is insertion position.
        """
        index, step = params
        if 0 <= index <= len(self._steps):
            self._steps.insert(index, step)
            logger.info("Inserted step at index %d: %s", index, step.label)

    @QtCore.pyqtSlot(object)
    def on_remove_step(self, index: int) -> None:
        """Remove step at specific position.

        Args:
            index: Position of step to remove.
        """
        if 0 <= index < len(self._steps) and index > self._current_index:
            removed = self._steps.pop(index)
            logger.info("Removed step at index %d: %s", index, removed.label)

    @QtCore.pyqtSlot()
    def on_start_request(self) -> None:
        """Start experiment execution."""
        if self._is_running:
            logger.warning("Experiment already running")
            return

        if not self._steps:
            logger.error("Cannot start experiment with empty plan")
            return

        self._is_running = True
        self._current_index = 0

        if self._timer is None:
            self._timer = QtCore.QTimer(self)
            self._timer.timeout.connect(self._evaluate_step)

        self._timer.setInterval(1000)
        self._timer.start()

        logger.info("Experiment started with %d steps", len(self._steps))
        self.experiment_started.emit()
        self._start_current_step()

    @QtCore.pyqtSlot()
    def on_stop_request(self) -> None:
        """Stop experiment execution."""
        if not self._is_running:
            return

        self._is_running = False
        if self._timer is not None:
            self._timer.stop()

        logger.info("Experiment stopped at step %d", self._current_index)
        self.experiment_stopped.emit()

    @QtCore.pyqtSlot()
    def on_skip_forward_request(self) -> None:
        """Skip to next step immediately."""
        if not self._is_running:
            logger.warning("Cannot skip when experiment is not running")
            return

        current = self.current_step
        if current is not None:
            logger.info("Skipping step: %s", current.label)
            current.on_finish(self)

        self._advance_to_next_step()

    @QtCore.pyqtSlot(object)
    def on_data_update(self, data: dict[str, str | float]) -> None:
        """Receive new measurement data and trigger evaluation.

        Args:
            data: Latest measurement data from StorageManager.
        """
        self._latest_data = data
        if self._is_running:
            self._evaluate_step()

    def _start_current_step(self) -> None:
        """Initialize current step and record start timestamp."""
        current = self.current_step
        if current is None:
            self._complete_experiment()
            return

        current.start_timestamp = datetime.now(UTC)
        logger.info("Starting step %d: %s", self._current_index, current.label)

        try:
            current.on_start(self)
        except Exception:
            logger.exception("Error in on_start for step: %s", current.label)

        self.current_step_changed.emit(current)
        self.experiment_log_updated.emit(self.get_execution_log())

    def _evaluate_step(self) -> None:
        """Check if current step is complete and advance if needed."""
        if not self._is_running:
            return

        current = self.current_step
        if current is None:
            self._complete_experiment()
            return

        try:
            is_complete = current.evaluate(self)
        except Exception:
            logger.exception("Error evaluating step: %s", current.label)
            is_complete = False

        if is_complete:
            logger.info("Step %d completed: %s", self._current_index, current.label)
            try:
                current.on_finish(self)
            except Exception:
                logger.exception("Error in on_finish for step: %s", current.label)

            self._advance_to_next_step()

    def _advance_to_next_step(self) -> None:
        """Move to next step in experiment plan."""
        self._current_index += 1

        if self._current_index >= len(self._steps):
            self._complete_experiment()
        else:
            self._start_current_step()

    def _complete_experiment(self) -> None:
        """Finalize experiment execution."""
        self._is_running = False
        if self._timer is not None:
            self._timer.stop()

        logger.info("Experiment completed")
        self.experiment_completed.emit()
        self.current_step_changed.emit(None)

    def get_execution_log(self) -> list[tuple[str, str, datetime | None]]:
        """Get execution history with step labels and timestamps.

        Returns:
            List of tuples (step_id, label, start_timestamp) for all steps.
        """
        return [
            (step.step_id, step.label, step.start_timestamp)
            for step in self._steps
        ]
