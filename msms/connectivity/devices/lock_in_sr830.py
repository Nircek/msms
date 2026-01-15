import logging
import time
from typing import ClassVar

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

    _SENS_MAP: ClassVar[dict[int, float]] = {  # source: SENS command parameters
        0: 2e-9,
        1: 5e-9,
        2: 10e-9,
        3: 20e-9,
        4: 50e-9,
        5: 100e-9,
        6: 200e-9,
        7: 500e-9,
        8: 1e-6,
        9: 2e-6,
        10: 5e-6,
        11: 10e-6,
        12: 20e-6,
        13: 50e-6,
        14: 100e-6,
        15: 200e-6,
        16: 500e-6,
        17: 1e-3,
        18: 2e-3,
        19: 5e-3,
        20: 10e-3,
        21: 20e-3,
        22: 50e-3,
        23: 100e-3,
        24: 200e-3,
        25: 500e-3,
        26: 1.0,
    }

    @classmethod
    def can_handle(cls, idn_parts: GpibIdnParts) -> bool:
        vendor, model, _serial, _version = idn_parts
        return vendor == "Stanford_Research_Systems" and model == "SR830"

    def initialize(self) -> None:
        # self.command_resource("*RST") # we should not reset the user settings

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
        while self._check_and_fix_overload():
            pass  # keep checking until no overload

        phase, frequence, amplitude = (self.query_resource(cmd) for cmd in ("PHAS?", "FREQ?", "SLVL?"))

        snap1 = self.query_resource("SNAP?3,4")
        snap2 = self.query_resource("SNAP?1,2,5,6,7,8")

        theta, r, x, y, *aux = [
            *snap1.split(","),
            *snap2.split(","),
        ]

        return {
            "X": x,
            "Y": y,
            "R": r,
            "theta": theta,
            "AUX1": aux[0],
            "AUX2": aux[1],
            "AUX3": aux[2],
            "AUX4": aux[3],
            "phase": phase,
            "frequency": frequence,
            "amplitude": amplitude,
        }

    def _get_voltage_range(self, sens_idx: int) -> float:
        return self._SENS_MAP.get(sens_idx, 1.0)

    def _check_and_fix_overload(self) -> bool:
        """Check for overload and increase sensitivity range if needed. It will
        also keep the voltage offsets the same.

        Returns True if adjustment was made.
        """
        try:
            lias_status_str = self.query_resource("LIAS?")
            lias_status = int(lias_status_str)
        except ValueError:
            logger.exception("Failed to parse LIAS status: %s", lias_status_str)
            return False

        if not (
            lias_status & 1  # Input/Reserve Overload
            or lias_status & 4  # Output Overload
        ):
            return False

        logger.warning("Detected overload condition (LIAS=%d). Adjusting settings.", lias_status)

        try:
            current_sens_str = self.query_resource("SENS?")
            current_sens_idx = int(float(current_sens_str))
        except ValueError:
            logger.exception("Failed to parse SENS index: %s", current_sens_str)
            return False

        if current_sens_idx >= max(self._SENS_MAP.keys()):
            logger.warning("Maximum sensitivity reached (1V). Cannot increase range.")
            return False

        offsets_info = {}
        current_range_v = self._get_voltage_range(current_sens_idx)

        for channel in (1, 2, 3):  # X, Y, R
            resp = self.query_resource(f"OEXP? {channel}")
            try:
                pct_str, expand_str = resp.split(",")
                old_pct, expand = float(pct_str), int(expand_str)

                abs_voltage_offset = current_range_v * (old_pct / 100.0)
                offsets_info[channel] = (abs_voltage_offset, expand)
            except ValueError:
                logger.exception("Failed to parse OEXP response for channel %d: %s", channel, resp)
                return False

        new_sens_idx = current_sens_idx + 1
        self.command_resource(f"SENS {new_sens_idx}")
        new_range_v = self._get_voltage_range(new_sens_idx)
        logger.info("Increased sensitivity from %e V to %e V", current_range_v, new_range_v)

        for channel, (abs_v, expand) in offsets_info.items():
            new_pct = (abs_v / new_range_v) * 100.0
            self.command_resource(f"OEXP {channel}, {new_pct:.2f}, {expand}")

        time.sleep(0.1)
        return True
