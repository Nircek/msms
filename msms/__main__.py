import logging

from msms.connectivity.data_collection import DataCollector
from msms.connectivity.visa import get_visa_library
from msms.logging_config import setup_logging


def main() -> None:
    setup_logging()

    logger = logging.getLogger(__name__)
    logger.info("Starting MSMS application")

    try:
        visa_library = get_visa_library()
        logger.info("Using VISA library: %s", visa_library)

        collector = DataCollector(visa_library)

        collector.initialize_visa()
        try:
            collector.discover_devices()
            collector.initialize_devices()
            collector.collect_data()
        finally:
            collector.cleanup()
        logger.info("MSMS application completed successfully")
    except Exception:
        logger.exception("MSMS application failed")
        raise


if __name__ == "__main__":
    main()
