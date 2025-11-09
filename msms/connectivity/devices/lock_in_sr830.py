import logging

from msms.connectivity.devices.common.device_base import DeviceBase
from msms.connectivity.devices.common.register_device import GpibIdnParts, register_device

logger = logging.getLogger(__name__)

INPUT_BUFFER_LIMIT = 256 - 2  # 256 is max command length, -2 for \n and \r


@register_device(
    initials="LI",
    short_display_name="Lock-In SR-830",
    full_display_name="Stanford Research Lock-In Amplifier SR-830",
)
class LockInSr830(DeviceBase):
    """Stanford Research SR-830 lock-in amplifier driver."""

    @classmethod
    def can_handle(cls, idn_parts: GpibIdnParts) -> bool:
        vendor, model, _serial, _version = idn_parts
        return vendor == "Stanford_Research_Systems" and model == "SR830"

    def initialize(self) -> None:
        self.command_resource("*RST")

        cmds = [
            "PHAS?",  # query phase shift -180.0..180.0
            "FREQ?",  # query frequency 0.001..102k; 5 digits or 0.0001
            "SLVL?",  # query amplitude; 0.004..5.000; 0.002
            "FAST?",  # should be '0' to get ASCII responses
            "*ESR?",  # query Event Status Byte
            "*SRE?",  # query Serial Poll Enable Register
            "*STB?",  # query Serial Poll Status Byte
            "*PSC?",  # query Power On Status Clear
            "ERRE?",  # query Error Status Enable Register
            "ERRS?",  # query Error Status Byte
            "LIAE?",  # query Lock-In Amplifier Status Enable Register
            "LIAS?",  # query Lock-In Status Byte
            "SNAP?1,2,3,4",  # the X,Y (1,2) and theta,R (3,4) are not in sync
            # theta is 0 if r is 0
            "SNAP?1,2,5,6,7,8",  # XY and all AUX
        ]

        for cmd in cmds:
            self.query_resource(cmd)

        long_cmd = ";".join(cmds)
        assert len(long_cmd) <= INPUT_BUFFER_LIMIT
        self.command_resource(long_cmd)
        print([self.read_resource().strip() for _ in cmds])

    def update(self) -> dict[str, str]:
        phase, frequence, amplitude = (self.query_resource(cmd) for cmd in ("PHAS?", "FREQ?", "SLVL?"))
        data = self.query_resource("SNAP?1,2,5,6,7,8").split(",")
        return {
            "X": data[0],
            "Y": data[1],
            "AUX1": data[2],
            "AUX2": data[3],
            "AUX3": data[4],
            "AUX4": data[5],
            "phase": phase,
            "frequency": frequence,
            "amplitude": amplitude,
        }
