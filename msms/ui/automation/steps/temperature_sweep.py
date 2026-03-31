"""Temperature sweep automation step implementation."""

import logging
from collections import deque
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import TYPE_CHECKING

import numpy as np
from PySide6 import QtWidgets

from msms.ui.automation.register_step import register_step
from msms.ui.automation.step_base import Step, StepEvaluationSource
from msms.ui.dialogs.step_config_dialogs import TemperatureSweepDialog

if TYPE_CHECKING:
    from msms.ui.controllers import ApplicationController
    from msms.ui.managers.automation_manager import AutomationManager

logger = logging.getLogger(__name__)

_TEMP_QUANT = Decimal("0.01")


def _q2(value: float | Decimal) -> Decimal:
    return Decimal(str(value)).quantize(_TEMP_QUANT, rounding=ROUND_HALF_UP)


@register_step("Temperature Sweep")
class TemperatureSweepStep(Step):
    """Perform a stepped no-ramp temperature sweep with significant captures."""

    requires_live_acquisition = True

    def __init__(self, step_id: str) -> None:
        super().__init__(step_id)
        self.device_address = ""
        self.t0 = 100.00
        self.t1 = 120.00
        self.dt = 0.50
        self.column_name = "T_control"
        self.max_slope = 0.1
        self.num_points = 10
        self.timeout_seconds = 0.0
        self.dwell_seconds = 0.0

        self._targets: list[Decimal] = []
        self._target_index = -1
        self._recent_values: deque[float] = deque(maxlen=self.num_points)
        self._target_command_sent_at: datetime | None = None
        self._target_result: str | None = None
        self._target_capture_requested_at: datetime | None = None
        self._awaiting_capture = False
        self._paused_for_acquisition = False

    def get_label(self) -> str:
        if not self.device_address:
            return "Temperature Sweep (not configured)"
        if self._paused_for_acquisition:
            return "Temperature Sweep (PAUSED: waiting for acquisition)"
        if not self._targets or self._target_index < 0 or self._target_index >= len(self._targets):
            return f"Temperature Sweep {self.t0:.2f}->{self.t1:.2f} dT={self.dt:.2f} on {self.device_address}"
        target = self._targets[self._target_index]
        return f"Temperature Sweep target {self._target_index + 1}/{len(self._targets)}: {target:.2f} K"

    def exec_edit_dialog(self, parent: QtWidgets.QWidget | None, app_controller: ApplicationController) -> bool:
        device_info_map: dict[str, tuple[str, str]] = {}
        for address, info in app_controller.device_info_cache.items():
            device_name = info.device_name or "Unknown"
            display_text = f"{device_name} ({address})"
            device_info_map[address] = (device_name, display_text)

        columns = app_controller.data_repository.columns
        column_names = list(columns) if columns else None

        dialog = TemperatureSweepDialog(parent, device_info=device_info_map, column_names=column_names)
        dialog.set_device_address(self.device_address)
        dialog.t0_spinbox.setValue(self.t0)
        dialog.t1_spinbox.setValue(self.t1)
        dialog.dt_spinbox.setValue(self.dt)
        dialog.set_column_name(self.column_name)
        dialog.slope_spinbox.setValue(self.max_slope)
        dialog.points_spinbox.setValue(self.num_points)
        dialog.timeout_spinbox.setValue(self.timeout_seconds)
        dialog.dwell_spinbox.setValue(self.dwell_seconds)

        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return False

        device_address = dialog.get_device_address()
        column_name = dialog.get_column_name()
        if not device_address:
            QtWidgets.QMessageBox.warning(dialog, "Invalid Input", "Device must be selected.")
            return False
        if not column_name or not column_name.startswith("T_"):
            QtWidgets.QMessageBox.warning(dialog, "Invalid Input", "Stabilization column must start with T_.")
            return False

        self.device_address = device_address
        self.t0 = dialog.t0_spinbox.value()
        self.t1 = dialog.t1_spinbox.value()
        self.dt = dialog.dt_spinbox.value()
        self.column_name = column_name
        self.max_slope = dialog.slope_spinbox.value()
        self.num_points = dialog.points_spinbox.value()
        self.timeout_seconds = dialog.timeout_spinbox.value()
        self.dwell_seconds = dialog.dwell_spinbox.value()
        self._recent_values = deque(maxlen=self.num_points)
        return True

    def on_start(self, runner: AutomationManager) -> None:
        self._targets = self._build_targets()
        self._target_index = -1
        self._recent_values = deque(maxlen=self.num_points)
        self._target_command_sent_at = None
        self._target_result = None
        self._target_capture_requested_at = None
        self._awaiting_capture = False

        if not runner.is_acquisition_running:
            self._paused_for_acquisition = True
            runner.active_step_status_changed.emit("Temperature Sweep PAUSED: start acquisition to continue")
            return

        self._paused_for_acquisition = False
        self._advance_target(runner)

    def evaluate(self, runner: AutomationManager, source: StepEvaluationSource) -> bool:
        if self._paused_for_acquisition:
            if runner.is_acquisition_running:
                self._paused_for_acquisition = False
                runner.active_step_status_changed.emit("Temperature Sweep resumed")
                self._advance_target(runner)
            else:
                if source is StepEvaluationSource.TICK:
                    runner.active_step_status_changed.emit("Temperature Sweep PAUSED: waiting for acquisition")
                return False

        if not self._targets or self._target_index >= len(self._targets):
            return True

        if self._awaiting_capture:
            if source is StepEvaluationSource.NEW_DATA and runner.is_significant_capture_event:
                self._finalize_target(runner)
            return False

        if source is StepEvaluationSource.NEW_DATA:
            self._on_new_data(runner)
            return False

        self._on_tick(runner)
        return False

    def _build_targets(self) -> list[Decimal]:
        t0 = _q2(self.t0)
        t1 = _q2(self.t1)
        dt = _q2(self.dt)
        if dt <= Decimal("0"):
            msg = "Temperature sweep dT must be > 0."
            raise ValueError(msg)

        step = dt if t1 >= t0 else -dt
        targets: list[Decimal] = []
        current = t0
        if step > 0:
            while current <= t1:
                targets.append(current)
                current = _q2(current + step)
        else:
            while current >= t1:
                targets.append(current)
                current = _q2(current + step)

        if not targets or targets[-1] != t1:
            targets.append(t1)
        return targets

    def _advance_target(self, runner: AutomationManager) -> None:
        self._target_index += 1
        self._recent_values = deque(maxlen=self.num_points)
        self._target_result = None
        self._target_capture_requested_at = None
        self._awaiting_capture = False

        if self._target_index >= len(self._targets):
            return

        target = self._targets[self._target_index]
        command = f"RAMP 0;SETP {target:.2f}"
        runner.send_device_command(self.device_address, command)
        self._target_command_sent_at = datetime.now(UTC)
        runner.active_step_status_changed.emit(
            f"Temperature Sweep target {self._target_index + 1}/{len(self._targets)}: {target:.2f} K (stabilizing)"
        )
        logger.info(
            "Temperature sweep sent no-ramp setpoint command: target=%s index=%d/%d",
            f"{target:.2f}",
            self._target_index + 1,
            len(self._targets),
        )

    def _elapsed_from_command(self) -> float:
        if self._target_command_sent_at is None:
            return 0.0
        return (datetime.now(UTC) - self._target_command_sent_at).total_seconds()

    def _dwell_reached(self) -> bool:
        return self._elapsed_from_command() >= self.dwell_seconds

    def _on_new_data(self, runner: AutomationManager) -> None:
        latest_data = runner.get_latest_data()
        value = latest_data.get(self.column_name)
        if isinstance(value, str) or value is None:
            return

        self._recent_values.append(value)
        if len(self._recent_values) < self.num_points or not self._dwell_reached():
            return

        x = np.arange(len(self._recent_values))
        y = np.array(self._recent_values)
        slope = float(np.polyfit(x, y, 1)[0])
        if abs(slope) <= self.max_slope:
            self._request_capture(runner, result="stable")

    def _on_tick(self, runner: AutomationManager) -> None:
        if self.timeout_seconds <= 0.0 or not self._dwell_reached():
            return
        if self._elapsed_from_command() >= self.timeout_seconds:
            self._request_capture(runner, result="timeout")

    def _request_capture(self, runner: AutomationManager, result: str) -> None:
        if self._awaiting_capture:
            return
        self._target_result = result
        self._target_capture_requested_at = datetime.now(UTC)
        self._awaiting_capture = True
        runner.active_step_status_changed.emit(
            f"Temperature Sweep target {self._target_index + 1}/{len(self._targets)}: capture requested ({result})"
        )
        runner.request_significant_measurement()

    def _finalize_target(self, runner: AutomationManager) -> None:
        target = self._targets[self._target_index]
        elapsed = self._elapsed_from_command()
        capture_delay = 0.0
        if self._target_capture_requested_at is not None:
            capture_delay = (datetime.now(UTC) - self._target_capture_requested_at).total_seconds()

        logger.info(
            "Temperature sweep target completed: target=%s status=%s elapsed_s=%.3f dwell_s=%.3f timeout_s=%.3f capture_delay_s=%.3f",
            f"{target:.2f}",
            self._target_result or "unknown",
            elapsed,
            self.dwell_seconds,
            self.timeout_seconds,
            capture_delay,
        )
        self._advance_target(runner)
