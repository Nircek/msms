"""Automation orchestration components."""

# Import steps to trigger registration
import msms.ui.automation.steps  # noqa: F401
from msms.ui.automation.register_step import register_step, step_registry
from msms.ui.automation.step_base import Step

__all__ = [
    "Step",
    "register_step",
    "step_registry",
]
