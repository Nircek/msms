import logging
import logging.handlers
from datetime import UTC, datetime
from pathlib import Path


def setup_logging() -> None:
    log_level = logging.INFO
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    log_file_path = logs_dir / f"msms_{timestamp}.log"

    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file_path,
        maxBytes=100 * 1024 * 1024,  # 100 MB
        backupCount=10,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Log the configuration
    logger = logging.getLogger(__name__)
    logger.info("Logging initialized")
