import inspect
import logging
import logging.handlers
import os
from datetime import UTC, datetime
from pathlib import Path

import msms

init_timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")


def setup_correct_cwd() -> None:
    """Set current working directory to the parent of the module."""
    module_path = Path(inspect.getfile(msms)).resolve()
    assert module_path.parts[-2:] == ("msms", "__init__.py"), module_path
    parent_of_module = module_path.parent.parent
    os.chdir(parent_of_module)


def get_logs_file_path(suffix: str, prefix: str | None = None) -> Path:
    """Generate timestamped log file path."""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    if prefix is None:
        prefix = f"msms_{init_timestamp}"
    file_name = f"{prefix}{suffix}"
    return logs_dir / file_name


def setup_logging(log_level: int = logging.INFO) -> None:
    """Configure root logger with console and rotating file handlers."""
    setup_correct_cwd()
    log_file_path = get_logs_file_path(".log")

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
