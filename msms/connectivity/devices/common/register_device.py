import logging
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from collections.abc import Callable

    from msms.connectivity.devices.common.device_base import DeviceBase

logger = logging.getLogger(__name__)

GPIB_IDN_PARTS_COUNT = 4
GpibIdnParts = tuple[str, str, str, str]
"""(vendor, model, serial, version)"""

device_registry: list[type[DeviceBase]] = []
"""Globally registered device classes."""


def register_device(
    initials: str, short_display_name: str, full_display_name: str | None = None
) -> Callable[[type[DeviceBase]], type[DeviceBase]]:
    """Decorator to register device class in global registry."""

    def decorator(cls: type[DeviceBase]) -> type[DeviceBase]:
        cls.initials = initials
        cls.short_display_name = short_display_name
        cls.full_display_name = full_display_name or short_display_name

        device_registry.append(cls)
        logger.debug("Registered device: %s (%s)", cls.short_display_name, cls.__name__)

        return cls

    return decorator


def find_device_for_idn(idn: str | None) -> type[DeviceBase] | None:
    """Find registered device class that can handle given IDN string."""
    if idn is None:
        return None

    idn_parts = tuple(idn.split(","))
    if len(idn_parts) != GPIB_IDN_PARTS_COUNT:
        return None
    idn_parts = cast("GpibIdnParts", idn_parts)

    can_be_handled_by = [device_class for device_class in device_registry if device_class.can_handle(idn_parts)]
    if len(can_be_handled_by) > 1:
        logger.warning("Multiple device classes can handle IDN %r: %r", idn, can_be_handled_by)

    if can_be_handled_by:
        return can_be_handled_by[0]
    return None
