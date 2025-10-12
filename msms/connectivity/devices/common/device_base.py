import logging
from abc import ABC, abstractmethod
from time import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyvisa.resources import MessageBasedResource as Resource

    from msms.connectivity.devices.common.register_device import GpibIdnParts


DEVICE_NOT_INITIALIZED_ERROR = "Device not initialized"


def to_float(s: str) -> str | float:
    s = s.strip()
    try:
        return float(s)
    except ValueError:
        return s


class DeviceBase(ABC):
    initials: str = ""
    short_display_name: str = ""
    full_display_name: str = ""
    idn: GpibIdnParts

    def __init__(self, resource: Resource) -> None:
        self._resource = resource
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._last_command_time = time()
        self._last_read_time = time()

    @classmethod
    @abstractmethod
    def can_handle(cls, idn_parts: GpibIdnParts) -> bool:
        pass

    @abstractmethod
    def initialize(self) -> None:
        pass

    @abstractmethod
    def _update(self) -> dict[str, str]:
        pass

    def update(self) -> dict[str, str | float]:
        return {k: to_float(v) for k, v in self._update().items()}

    def command_resource(self, cmd: str) -> None:
        if not hasattr(self, "_resource"):
            raise RuntimeError(DEVICE_NOT_INITIALIZED_ERROR)
        self._last_command_time = self._last_read_time = time()
        self._resource.write(cmd)
        t1 = time()
        print(f"{self.initials}: {cmd!r} -- [{t1 - self._last_command_time:.1f}ms, T0]")

    def query_resource(self, cmd: str) -> str:
        if not hasattr(self, "_resource"):
            raise RuntimeError(DEVICE_NOT_INITIALIZED_ERROR)
        t0 = time()
        response = self._resource.query(cmd)
        t1 = time()
        print(f"{self.initials}: {cmd!r} : {response!r} -- {1000 * (t1 - t0):.1f}ms")
        return response

    def read_resource(self) -> str:
        if not hasattr(self, "_resource"):
            raise RuntimeError(DEVICE_NOT_INITIALIZED_ERROR)
        response = self._resource.read()
        t1 = time()
        accumulated_time = 1000 * (t1 - self._last_command_time)
        last_time = 1000 * (t1 - self._last_read_time)
        self._last_read_time = t1
        print(f"{self.initials}: [READ] : {response!r} -- [{last_time:.1f}ms, {accumulated_time:.1f}ms]")
        return response

    def close(self) -> None:
        if hasattr(self, "_resource"):
            self._resource.close()
            del self._resource
