import logging
from contextlib import suppress
from dataclasses import dataclass
from time import time
from typing import TYPE_CHECKING, cast

import pyvisa

from msms.connectivity.devices.common.register_device import device_registry, find_device_for_idn
from msms.connectivity.visa import get_visa_library

if TYPE_CHECKING:
    from pyvisa.resources import MessageBasedResource as Resource

    from msms.connectivity.devices.common.device_base import DeviceBase

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredDevice:
    """Summary of a device discovered on the VISA bus."""

    address: str
    idn: str | None
    device_name: str | None


class DeviceRepository:
    """Repository for discovering and managing VISA-connected device life cycle management."""

    def __init__(self, visa_library: str | None = None) -> None:
        self._visa_library = visa_library or get_visa_library()
        self._resource_manager: pyvisa.ResourceManager | None = None
        self._devices: list[DeviceBase] = []
        self._selected_addresses: set[str] = set()
        self._devices_info: dict[str, DiscoveredDevice] = {}

    def initialize_visa(self) -> None:
        """Initialise the VISA resource manager if it is not ready yet."""

        if self._resource_manager is not None:
            return

        try:
            self._resource_manager = pyvisa.ResourceManager(self._visa_library)
            resources = self._resource_manager.list_resources()
            logger.info("Available VISA resources: %r", resources)
            if not resources:
                logger.warning("No VISA resources found")
        except Exception:
            logger.exception("Failed to initialise VISA resource manager")
            raise

    def discover_devices(self) -> list[DiscoveredDevice]:
        """Discover VISA resources and return device summaries.

        Returns:
            List of discovered devices, including address, raw IDN string, and
            a resolved short display name when available.
        """

        if self._resource_manager is None:
            self.initialize_visa()
        assert self._resource_manager is not None

        resources = list(self._resource_manager.list_resources())
        logger.debug("Discovered VISA resources: %s", resources)

        registered_devices = [device.short_display_name for device in device_registry]
        logger.info("Registered device types: %r", registered_devices)

        discovered: list[DiscoveredDevice] = []

        for resource_name in resources:
            idn: str | None = None
            device_name: str | None = None
            resource: Resource | None = None

            try:
                resource = cast("Resource", self._resource_manager.open_resource(resource_name))
                try:
                    idn = resource.query("*IDN?")
                except pyvisa.errors.VisaIOError:
                    resource.write("OUTX 1")
                    try:
                        idn = resource.query("*IDN?")
                        logger.info("IDN worked after changing interface for %s", resource_name)
                    except pyvisa.errors.VisaIOError:
                        logger.debug("Could not query IDN for %s", resource_name)
                        idn = None

                device_class = find_device_for_idn(idn)
                device_name = device_class.short_display_name if device_class else None
            except Exception:
                logger.exception("Error querying device %s", resource_name)
            finally:
                if resource is not None:
                    with suppress(Exception):
                        resource.close()

            discovered.append(DiscoveredDevice(resource_name, idn, device_name))

        self._devices_info = {dev.address: dev for dev in discovered}

        return discovered

    def set_selected_addresses(self, addresses: list[str]) -> None:
        """Persist the currently selected VISA addresses."""
        self._selected_addresses = set(addresses)

    def prepare_devices(self) -> None:
        """Instantiate device drivers for the selected VISA resources.

        Raises:
            RuntimeError: If no device addresses have been selected.
        """

        if self._resource_manager is None:
            self.initialize_visa()
        assert self._resource_manager is not None

        if not self._selected_addresses:
            msg = "No device addresses selected"
            raise RuntimeError(msg)

        self.shutdown_devices()

        resources = list(self._resource_manager.list_resources())
        missing_addresses = self._selected_addresses - set(resources)
        if missing_addresses:
            logger.warning("Selected addresses no longer available: %s", sorted(missing_addresses))
            msg = "Some selected device addresses are not available"
            raise RuntimeError(msg)

        device_info_to_delete = set(self._devices_info.keys()) - self._selected_addresses
        for addr in device_info_to_delete:
            del self._devices_info[addr]

        for resource_name in resources:
            if resource_name not in self._selected_addresses:
                continue

            resource = cast("Resource", self._resource_manager.open_resource(resource_name))
            idn: str | None = None

            try:
                idn = resource.query("*IDN?")
            except pyvisa.errors.VisaIOError:
                resource.write("OUTX 1")
                try:
                    idn = resource.query("*IDN?")
                    logger.info("IDN worked after changing interface for %s", resource_name)
                except pyvisa.errors.VisaIOError:
                    logger.exception("Try restarting/reconnecting the device at address %s", resource_name)
                    idn = None

            device_class = find_device_for_idn(idn)
            device_instance = None if device_class is None else device_class(resource)

            if device_instance is None:
                logger.warning("Unknown device (%s, %r)", resource_name, idn)
                resource.close()
                continue

            logger.info(
                "Created device instance: %s (%s, %r)",
                device_instance.short_display_name,
                resource_name,
                idn,
            )
            self._devices.append(device_instance)

    def get_devices_info(self) -> dict[str, DiscoveredDevice]:
        """Return discovered device info keyed by address."""
        return self._devices_info

    def initialize_devices(self) -> None:
        """Run device-specific initialization hooks."""

        for device in self._devices:
            logger.info("Initializing device: %s", device.short_display_name)
            try:
                device.initialize()
            except Exception:
                logger.exception("Failed to initialize device: %s", device.short_display_name)

    def collect_data(self) -> dict[str, str]:
        """Collect a single data snapshot from the selected devices.

        Returns:
            Mapping of collected fields per devices combined into one payload.
        """

        logger.info("Starting data collection loop iteration")
        t0 = time()
        results: dict[str, str] = {}
        for device in self._devices:
            try:
                results.update(device.update())
            except Exception:
                logger.exception("Failed to update device: %s", device.short_display_name)
        return {"timestamp": str(time()), "dt": f"{1000 * (time() - t0):.1f}", **results}

    def send_command(self, device_address: str, command: str) -> None:
        """Send a command to a specific device.

        Args:
            device_address: VISA address of the target device.
            command: Command string to send.
        """

        for device in self._devices:
            if device.resource_address == device_address:
                logger.info("Sending command to %s: %s", device.short_display_name, command)
                device.command_resource(command, force=True)
                return

        logger.warning("No device found with address %s to send command: %s", device_address, command)

    def shutdown_devices(self) -> None:
        """Close all instantiated devices and clear internal state."""

        for device in self._devices:
            try:
                device.close()
                logger.info("Closed device: %s", device.short_display_name)
            except Exception:
                logger.exception("Failed to close device: %s", device.short_display_name)
        self._devices.clear()

    def close(self) -> None:
        """Release VISA resources entirely."""

        self.shutdown_devices()
        if self._resource_manager is not None:
            try:
                self._resource_manager.close()
            except Exception:
                logger.exception("Failed to close VISA resource manager")
            finally:
                self._resource_manager = None
                logger.info("VISA resource manager closed")
