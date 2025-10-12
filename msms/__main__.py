import logging

from msms.connectivity import controller
from msms.logging_config import setup_logging


def main() -> None:
    setup_logging()

    logger = logging.getLogger(__name__)
    logger.info("Starting MSMS application")

    try:
        controller.main()
        logger.info("MSMS application completed successfully")
    except Exception:
        logger.exception("MSMS application failed")
        raise


if __name__ == "__main__":
    main()
