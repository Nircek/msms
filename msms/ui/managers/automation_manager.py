"""Automation orchestration manager (Step Runner)."""

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from PySide6 import QtCore

if TYPE_CHECKING:
    from msms.ui.automation.step_base import Step

logger = logging.getLogger(__name__)


class AutomationManager(QtCore.QObject):
    """Manage execution of procedural automation steps.

    Runs in separate thread, evaluates current step every second
    and on new data arrival. Maintains ordered list of steps and
    records start timestamp for each executed step.
    """

    automation_started = QtCore.Signal()
    automation_stopped = QtCore.Signal()
    automation_completed = QtCore.Signal()
    current_step_changed = QtCore.Signal(object)
    automation_log_changed = QtCore.Signal(object)
    device_command_requested = QtCore.Signal(object, object)
    steps_changed = QtCore.Signal(object)

    def __init__(self) -> None:
        """Initialize automation manager with empty plan."""
        super().__init__()
        self._steps: list[Step] = []
        self._current_index = 0
        self._is_running = False
        self._timer: QtCore.QTimer | None = None
        self._latest_data: dict[str, str | float] = {}
        self._step_id_counter = 0
        self._step_id_mutex = QtCore.QMutex()

    @QtCore.Slot()
    def on_setup(self) -> None:  # noqa: PLR6301
        """Initialize automation manager in thread context."""
        QtCore.QCoreApplication.processEvents()

    def threaded_new_step_id(self) -> int:
        """Generate unique step ID in thread-safe manner.

        Returns:
            Next sequential step ID.
        """
        self._step_id_mutex.lock()
        try:
            self._step_id_counter += 1
            return self._step_id_counter
        finally:
            self._step_id_mutex.unlock()

    @property
    def is_running(self) -> bool:
        """Check if automation is currently running."""
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

    @QtCore.Slot(object)
    def on_set_steps(self, steps: list[Step]) -> None:
        """Replace automation plan with new steps.

        Args:
            steps: New list of step instances to execute.
        """
        # Remember current step ID to restore position
        current_step_id = None
        if self.current_step is not None:
            current_step_id = self.current_step.step_id

        self._steps = steps

        # Restore position to step with same ID if exists
        if current_step_id is not None:
            for index, step in enumerate(self._steps):
                if step.step_id == current_step_id:
                    self._current_index = index
                    logger.info("Restored position to step %d (ID: %s)", index, current_step_id)
                    break
        else:
            self._current_index = 0

        logger.info("Automation plan updated with %d steps", len(steps))
        self.steps_changed.emit(self._steps)

    @QtCore.Slot()
    def on_get_steps_request(self) -> None:
        """Emit current steps list."""
        self.steps_changed.emit(self._steps)

    @QtCore.Slot()
    def on_start_request(self) -> None:
        """Start automation execution."""
        if self._is_running:
            logger.warning("Automation already running")
            return

        if not self._steps:
            logger.error("Cannot start automation with empty plan")
            return

        self._is_running = True
        self._current_index = 0

        if self._timer is None:
            self._timer = QtCore.QTimer(self)
            self._timer.timeout.connect(self._evaluate_step)

        self._timer.setInterval(1000)
        self.automation_started.emit()

        self._timer.start()
        logger.info("Automation started with %d steps", len(self._steps))
        self._start_current_step()

    @QtCore.Slot()
    def on_stop_request(self) -> None:
        """Stop automation execution."""
        if not self._is_running:
            return

        self._is_running = False
        if self._timer is not None:
            self._timer.stop()

        logger.info("Automation stopped at step %d", self._current_index)
        self.automation_stopped.emit()

    @QtCore.Slot()
    def on_skip_step_request(self) -> None:
        """Skip to next step immediately."""
        if not self._is_running:
            logger.warning("Cannot skip when automation is not running")
            return

        current = self.current_step
        if current is not None:
            logger.info("Skipping step: %s", current.label)
            current.on_finish(self)

        self._advance_to_next_step()

    @QtCore.Slot(object)
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
            self._complete_automation()
            return

        current.start_timestamp = datetime.now(UTC)
        logger.info("Starting step %d: %s", self._current_index, current.label)

        try:
            current.on_start(self)
        except Exception:
            logger.exception("Error in on_start for step: %s", current.label)

        self.current_step_changed.emit(current)
        self.automation_log_changed.emit(self.get_execution_log())

    def _evaluate_step(self) -> None:
        """Check if current step is complete and advance if needed."""
        if not self._is_running:
            return

        current = self.current_step
        if current is None:
            self._complete_automation()
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
        """Move to next step in automation plan."""
        self._current_index += 1

        if self._current_index >= len(self._steps):
            self._complete_automation()
        else:
            self._start_current_step()

    def _complete_automation(self) -> None:
        """Finalize automation execution."""
        self._is_running = False
        if self._timer is not None:
            self._timer.stop()

        logger.info("Automation completed")
        self.current_step_changed.emit(None)
        self.automation_completed.emit()

    def get_execution_log(self) -> list[tuple[str, str, datetime | None]]:
        """Get execution history with step labels and timestamps.

        Returns:
            List of tuples (step_id, label, start_timestamp) for all steps.
        """
        return [(step.step_id, step.label, step.start_timestamp) for step in self._steps]
