import logging
import os

logger = logging.getLogger(__name__)


def get_visa_library() -> str:
    """Return VISA library path based on MSMS_SIM environment variable."""
    visa_library = ""
    if os.getenv("MSMS_SIM", ""):
        visa_library = "msms/connectivity/sim_instruments.yml@sim"
        logger.info("Using simulation mode")
    else:
        logger.info("Using real hardware mode")
    return visa_library
