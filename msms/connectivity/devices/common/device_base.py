import logging
from abc import ABC, abstractmethod
from contextlib import contextmanager
from time import time
from typing import TYPE_CHECKING

import pyvisa

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pyvisa.resources import MessageBasedResource as Resource

    from msms.connectivity.devices.common.register_device import GpibIdnParts


DEVICE_NOT_INITIALIZED_ERROR = "Device not initialized"


class DeviceBase(ABC):
    initials: str = ""
    short_display_name: str = ""
    full_display_name: str = ""
    idn: GpibIdnParts
    error_cool_down_period: float = 5.0

    def __init__(self, resource: Resource) -> None:
        self._resource = resource
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._last_command_time = time()
        self._last_read_time = time()
        self._error_cool_down_time = 0.0
        self._error_cool_down_cause: str | None = None

    @property
    def resource_address(self) -> str:
        """Get the VISA resource address of this device."""
        return self._resource.resource_name

    @classmethod
    @abstractmethod
    def can_handle(cls, idn_parts: GpibIdnParts) -> bool:
        """Check if this device class can handle the given IDN response."""

    @abstractmethod
    def initialize(self) -> None:
        """Perform device-specific initialization after connection."""

    @abstractmethod
    def update(self) -> dict[str, str]:
        """Query device and return current readings as string dict."""

    @contextmanager
    def error_cool_down_context_manager(
        self, *, bypass: bool = False, can_be_executed_after: bool = True
    ) -> Iterator[None]:
        """Prevent repeated operations on failing devices via cool-down period."""
        if not hasattr(self, "_resource"):
            raise RuntimeError(DEVICE_NOT_INITIALIZED_ERROR)
        if not bypass:
            if self._error_cool_down_time >= time():
                self._logger.warning("Error cool down period active")
                return
            if self._error_cool_down_cause and not can_be_executed_after:
                self._logger.warning("Error cool down state active")
                return
        try:
            yield
        except pyvisa.errors.VisaIOError as e:
            self._logger.exception("VISA IO Error during device operation")
            self._error_cool_down_cause = e.abbreviation
            self._error_cool_down_time = time() + self.error_cool_down_period
        else:
            self._error_cool_down_cause = None

    def close(self) -> None:
        """Close VISA resource connection."""
        with self.error_cool_down_context_manager(bypass=True):
            self._resource.close()
        del self._resource

    def command_resource(self, cmd: str, force: bool = False) -> None:
        """Send SCPI command to device."""
        self._last_command_time = self._last_read_time = time()
        with self.error_cool_down_context_manager(bypass=force):
            self._resource.write(cmd)
        t1 = time()
        print(f"{self.initials}: {cmd!r} -- [{t1 - self._last_command_time:.1f}ms, T0]")

    def query_resource(self, cmd: str) -> str:
        """Send SCPI query and return response."""
        response, t0 = None, time()
        with self.error_cool_down_context_manager():
            response = self._resource.query(cmd)
        if response is None:
            response = self._error_cool_down_cause

        t1 = time()
        print(f"{self.initials}: {cmd!r} : {response!r} -- {1000 * (t1 - t0):.1f}ms")
        return response

    def read_resource(self) -> str:
        """Read buffered response from device."""
        response = self._error_cool_down_cause
        with self.error_cool_down_context_manager(can_be_executed_after=False):
            response = self._resource.read()
        t1 = time()
        accumulated_time = 1000 * (t1 - self._last_command_time)
        last_time = 1000 * (t1 - self._last_read_time)
        self._last_read_time = t1
        print(f"{self.initials}: [READ] : {response!r} -- [{last_time:.1f}ms, {accumulated_time:.1f}ms]")
        return response
