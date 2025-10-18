import logging
from time import time
from typing import TYPE_CHECKING, cast

import pyvisa

from msms.connectivity.devices.common.register_device import device_registry, find_device_for_idn

if TYPE_CHECKING:
    from pyvisa.resources import MessageBasedResource as Resource

    from msms.connectivity.devices.common.device_base import DeviceBase

logger = logging.getLogger(__name__)


class DataCollector:
    def __init__(self, visa_library: str = "") -> None:
        self.visa_library = visa_library
        self.resource_manager: pyvisa.ResourceManager | None = None
        self.devices: list[DeviceBase] = []

    def initialize_visa(self) -> None:
        try:
            self.resource_manager = pyvisa.ResourceManager(self.visa_library)
            resources = self.resource_manager.list_resources()
            logger.info("Available VISA resources: %s", repr(resources))

            if not resources:
                logger.warning("No VISA resources found")

        except Exception:
            logger.exception("Failed to initialize VISA resource manager")
            raise

    def discover_devices(self) -> None:
        if self.resource_manager is None:
            msg = "VISA resource manager not initialized"
            raise RuntimeError(msg)

        resources = list(self.resource_manager.list_resources())
        print(f"Available resources: {resources}")

        registered_devices = [device.short_display_name for device in device_registry]
        logger.info("Registered device types: %s", repr(registered_devices))

        for resource_name in resources:
            resource = cast("Resource", self.resource_manager.open_resource(resource_name))
            idn: str | None = None

            try:
                idn = resource.query("*IDN?")
            except pyvisa.errors.VisaIOError:
                # Assume it is Lock-In SR-830 that could respond on wrong interface
                resource.write("OUTX 1")
                try:
                    idn = resource.query("*IDN?")
                    logger.info("IDN worked after changing interface")
                except pyvisa.errors.VisaIOError:
                    logger.exception("Try restarting/reconnecting the device at address %s", resource_name)
                    idn = None

            logger.info("Discovered device: (%s, %s)", resource_name, repr(idn))

            device_class = find_device_for_idn(idn)
            device_instance = None if device_class is None else device_class(resource)

            if device_instance:
                logger.info(
                    "Created device instance: %s (%s, %s)", device_instance.short_display_name, resource_name, repr(idn)
                )
                self.devices.append(device_instance)
            else:
                logger.warning("Unknown device (%s, %s)", resource_name, repr(idn))
                resource.close()

    def initialize_devices(self) -> None:
        for device in self.devices:
            logger.info("Initializing device: %s", device.short_display_name)
            try:
                device.initialize()
            except Exception:
                logger.exception("Failed to initialize device: %s", device.short_display_name)

    def collect_data(self) -> dict[str, str]:
        logger.info("Starting data collection loop iteration")
        t0 = time()
        results: dict[str, str] = {}
        for device in self.devices:
            try:
                results.update(device.update())
            except Exception:
                logger.exception("Failed to update device: %s", device.short_display_name)
        return {"timestamp": str(time()), "dt": f"{1000 * (time() - t0):.1f}", **results}

    def cleanup(self) -> None:
        for device in self.devices:
            try:
                device.close()
                logger.info("Closed device: %s", device.short_display_name)
            except Exception:
                logger.exception("Failed to close device: %s", device.short_display_name)

        self.devices.clear()
