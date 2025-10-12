import logging
import os

import pyvisa

logger = logging.getLogger(__name__)


def main() -> None:
    visa_library = ""
    if os.getenv("MSMS_SIM", ""):
        visa_library = "msms/connectivity/sim_instruments.yml@sim"
        logger.info("Using simulation mode")
    else:
        logger.info("Using real hardware mode")

    logger.info("Using VISA library", extra={"visa_library": visa_library})

    try:
        rm = pyvisa.ResourceManager(visa_library)
        resources = rm.list_resources()
        logger.info("Available VISA resources", extra={"resources": list(resources)})

        if not resources:
            logger.warning("No VISA resources found")
        else:
            logger.info("Found %d VISA resource(s)", len(resources))
            for i, resource in enumerate(resources, start=1):
                logger.info("Resource %d: %s", i, resource)

    except Exception:
        logger.exception("Failed to initialize VISA resource manager")
        raise


if __name__ == "__main__":
    main()
