import logging

from msms.connectivity.devices.common.device_base import DeviceBase
from msms.connectivity.devices.common.register_device import GpibIdnParts, register_device

logger = logging.getLogger(__name__)


@register_device(
    initials="MM",
    short_display_name="Multi-Meter RSDM3055A",
    full_display_name="RS Pro Digital Multi-Meter RSDM3055A",
)
class RSDM3055A(DeviceBase):
    """RS Pro digital multimeter RSDM3055A driver."""

    @classmethod
    def can_handle(cls, idn_parts: GpibIdnParts) -> bool:
        _vendor, _model, serial, _version = idn_parts
        return serial.startswith("SDM35")

    def initialize(self) -> None:
        self.command_resource("*RST")

        measurement_types = ["CURR:DC", "CURR:AC", "RES", "FRES", "VOLT:DC", "VOLT:AC"]
        cmds = []

        for measurement_type in measurement_types:
            cmds.extend([
                f"CONF:{measurement_type};:SAMP:COUN 1;:TRIG:COUN 1;:CONF?",
                "READ?",
                "READ?",
                "READ?",
            ])

        for cmd in cmds:
            self.query_resource(cmd)
        # MEAS:...? takes about a second
        # CONF takes about a second but then it is pretty fast to get one READ?

    def update(self) -> dict[str, str]:
        return {"volt:dc": self.query_resource("READ?")}
