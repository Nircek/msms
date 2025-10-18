import logging

from msms.connectivity.devices.common.device_base import DeviceBase
from msms.connectivity.devices.common.register_device import GpibIdnParts, register_device

logger = logging.getLogger(__name__)


@register_device(
    initials="LS",
    short_display_name="LakeShore 330",
    full_display_name="LakeShore 330 Temperature Controller",
)
class LakeShore330(DeviceBase):
    @classmethod
    def can_handle(cls, idn_parts: GpibIdnParts) -> bool:
        vendor, model, _serial, _version = idn_parts
        return vendor == "LSCI" and model == "MODEL330"

    def initialize(self) -> None:
        self._logger.info("Initializing LakeShore 330")
        self.command_resource("*RST")

        cmds = [
            "CUNI K;CUNI?",  # set units to Kelvin
            "SUNI K;SUNI?",
            "TUNE 3;TUNE?",  # set PID auto-tune mode
            "ESE?",  # query Event Status Enable Register
            "ESR?",  # query Event Status Register
            "*SRE?",  # query Service Request Enable Register
            "*STB?",  # query Status Byte
            "*TST?",  # query Self-Test
            "CCHN?",  # which channel is control
            "SCHN?",  # which channel is sample
            "FILT?",  # query if screen shows average of 10 measurements
            "CDAT?",  # query control value
            "SDAT?",  # query sample value
            "CLIM?",  # query Control Limit Query
            "GAIN?",  # query P term
            "RSET?",  # query I term
            "RATE?",  # query D term
            "HEAT?",  # read-only, current heater power 0.5..100
            "RAMP?",  # query if ramping is enabled, 0|1
            "RAMPR?",  # query ramp rate 0..99.9; 0 is turned off
            "RAMPS?",  # query if it is ramping now, 0|1
            "RANG?",  # query heater range 0..3 off,low,medium,high
            "SETP?",  # query set point; resolution is 0.01 for temperatures below 200
        ]

        for cmd in cmds:
            self.query_resource(cmd)

        # For the setpoint parameter, enter a value from 0 to 999.9 for temperature or 0 to 2.4990 for voltage.
        # Commands can be concatenated with ';' but there must not be any command after the query
        # Do not combine channel, control unit, and setpoint changes. Allow one controller update cycle (half second)
        # '*WAI\r\n'?

    @staticmethod
    def how_many_digits_after_dot(s: str) -> int | None:
        s = s.strip()
        dot_index = s.find(".")
        if dot_index == -1:
            return None
        return len(s) - dot_index - 1

    def update(self) -> dict[str, str]:
        set_point = self.query_resource("SETP?")
        match LakeShore330.how_many_digits_after_dot(set_point):
            case None:
                set_point_unit = ""
            case 1 | 2:
                set_point_unit = "K"
            case _:
                set_point_unit = "V"
        ramps = self.query_resource("RAMPS?")
        ramp_rate = self.query_resource("RAMPR?") if ramps.strip() == "1" else "0"
        return {
            "sample": self.query_resource("SDAT?"),
            "control": self.query_resource("CDAT?"),
            "set_point": set_point,
            "_set_point_unit": set_point_unit,
            "ramp_rate": ramp_rate,
        }
