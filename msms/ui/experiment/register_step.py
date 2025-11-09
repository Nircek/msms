"""Step registration system."""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from msms.ui.experiment.step_base import Step

logger = logging.getLogger(__name__)

step_registry: list[type[Step]] = []
"""Globally registered step classes."""


def register_step(
    display_name: str,
) -> Callable[[type[Step]], type[Step]]:
    """Decorator to register step class in global registry.

    Args:
        display_name: Human-readable name shown in step selection dialog.

    Returns:
        Decorator function.
    """

    def decorator(cls: type[Step]) -> type[Step]:
        cls.display_name = display_name
        step_registry.append(cls)
        logger.debug("Registered step: %s (%s)", display_name, cls.__name__)
        return cls

    return decorator
