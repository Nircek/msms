"""Step implementations for automation orchestration."""

# Import all step implementations to trigger registration
from msms.ui.automation.steps.set_setpoint import SetSetpointStep
from msms.ui.automation.steps.start_acquisition import StartAcquisitionStep
from msms.ui.automation.steps.stop_acquisition import StopAcquisitionStep
from msms.ui.automation.steps.stop_program import StopProgramStep
from msms.ui.automation.steps.wait_condition import WaitForConditionStep
from msms.ui.automation.steps.wait_datetime import WaitForDatetimeStep
from msms.ui.automation.steps.wait_duration import WaitForDurationStep
from msms.ui.automation.steps.wait_stable import WaitForStableStep

__all__ = [
    "SetSetpointStep",
    "StartAcquisitionStep",
    "StopAcquisitionStep",
    "StopProgramStep",
    "WaitForConditionStep",
    "WaitForDatetimeStep",
    "WaitForDurationStep",
    "WaitForStableStep",
]
