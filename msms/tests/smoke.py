import logging
import os
import tempfile
import time
import typing
from pathlib import Path

from PyQt6 import QtCore, QtWidgets

from msms.logging_config import setup_logging
from msms.ui.main_window import MainWindow

_NO_DEVICES_REASON = "no simulated devices discovered"
_EXPORT_MISSING_REASON = "expected export file missing"
_EXPORT_EMPTY_REASON = "export file is empty"


class SmokeTestError(RuntimeError):
    """Raised when the smoke test expectations are not met."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"Smoke test failed: {reason}")


def _ensure_application() -> tuple[QtWidgets.QApplication, bool]:
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
        return app, True
    return typing.cast("QtWidgets.QApplication", app), False


def _process_events(app: QtWidgets.QApplication, duration_seconds: float) -> None:
    end_time = time.monotonic() + duration_seconds
    while time.monotonic() < end_time:
        app.processEvents(QtCore.QEventLoop.ProcessEventsFlag.AllEvents, 100)
        time.sleep(0.05)


def main() -> int:
    """Run an automated smoke test of the UI acquisition flow.

    Returns:
        Zero on success.

    Raises:
        SmokeTestError: If smoke test expectations are not met.
    """
    os.environ.setdefault("MSMS_SIM", "y")
    setup_logging(logging.INFO)
    logger = logging.getLogger(__name__)

    app, owns_app = _ensure_application()
    window = MainWindow()

    try:
        window.show()
        app.processEvents()

        discovered_devices: list = []

        def capture_devices(devices: list) -> None:
            discovered_devices.clear()
            discovered_devices.extend(devices)

        window.app_controller.devices_discovered.connect(capture_devices)

        # Start device discovery and wait for devices to be discovered
        window.app_controller.start_discovery(interval_ms=500)
        _process_events(app, 2.0)  # Allow time for device discovery to complete

        # Stop discovery once we have devices
        window.app_controller.stop_discovery()

        if not discovered_devices:
            raise SmokeTestError(_NO_DEVICES_REASON)

        addresses = [device.address for device in discovered_devices]
        window.app_controller.update_selected_devices(addresses)
        window.app_controller.start_acquisition()

        _process_events(app, 5.0)

        window.app_controller.stop_acquisition()
        app.processEvents()

        export_dir = Path(tempfile.mkdtemp(prefix="msms_smoke_"))
        export_path = export_dir / "acquisition.csv"
        window.app_controller.request_export_to_csv(export_path)
        _process_events(app, 0.5)  # Allow time for export signal to complete

        if not export_path.exists():
            raise SmokeTestError(_EXPORT_MISSING_REASON)
        if export_path.stat().st_size == 0:
            raise SmokeTestError(_EXPORT_EMPTY_REASON)

        logger.info("Smoke test succeeded; data exported to %s", export_path)
        return 0
    finally:
        try:
            window.close()
        finally:
            if owns_app:
                app.quit()
            app.processEvents(QtCore.QEventLoop.ProcessEventsFlag.AllEvents, 100)
