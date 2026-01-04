import logging
import signal
import sys
import time
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui, QtWidgets

if TYPE_CHECKING:
    from types import FrameType

from msms.connectivity.device_repository import DeviceRepository
from msms.connectivity.visa import get_visa_library
from msms.logging_config import setup_logging
from msms.ui.main_window import MainWindow


def main() -> None:
    """Run CLI mode with device polling loop."""
    setup_logging()

    logger = logging.getLogger(__name__)
    logger.info("Starting MSMS application")

    try:
        visa_library = get_visa_library()
        logger.info("Using VISA library: %s", visa_library)

        repository = DeviceRepository(visa_library)

        repository.initialize_visa()
        try:
            devices = repository.discover_devices()
            repository.set_selected_addresses([device.address for device in devices])
            repository.prepare_devices()
            repository.initialize_devices()
            while True:
                time.sleep(2)
                print(repository.collect_data())
        finally:
            repository.close()
        logger.info("MSMS application completed successfully")
    except Exception:
        logger.exception("MSMS application failed")
        raise


def ui() -> None:
    """Run PyQt6 GUI application."""
    setup_logging()

    logger = logging.getLogger(__name__)
    logger.info("Starting MSMS application")

    app = QtWidgets.QApplication(sys.argv)

    app.setWindowIcon(QtGui.QIcon("icon.svg"))

    win = MainWindow()

    def handle_sigint(_signum: int, _frame: FrameType | None) -> None:
        logger.info("SIGINT received, shutting down UI")
        app.quit()

    signal.signal(signal.SIGINT, handle_sigint)
    timer = QtCore.QTimer()  # timer trick to make Python handle signals
    timer.timeout.connect(lambda: None)
    timer.start(2000)

    win.show()
    exit_code = app.exec()
    if win.isVisible():
        win.close()
    timer.stop()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
