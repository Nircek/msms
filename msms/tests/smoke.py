import logging
import os
import tempfile
import time
import typing
from pathlib import Path

from PySide6 import QtCore, QtWidgets

from msms.logging_config import setup_logging
from msms.ui.main_window import MainWindow

_NO_DEVICES_REASON = "no simulated devices discovered"
_EXPORT_MISSING_REASON = "expected export file missing"
_EXPORT_EMPTY_REASON = "export file is empty"


class TestSignals(QtCore.QObject):
    """Test-specific signals for smoke test operations.

    These signals are connected to managers during test setup
    to enable programmatic control of the application.
    """

    # Device signals
    device_discovery_start_requested = QtCore.Signal(object)
    device_discovery_stop_requested = QtCore.Signal()
    device_selection_requested = QtCore.Signal(object)
    device_acquisition_start_requested = QtCore.Signal()
    device_acquisition_stop_requested = QtCore.Signal()

    # Storage signals
    storage_export_requested = QtCore.Signal(object)


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

    # Create test signals and connect them to managers
    test_signals = TestSignals()
    test_signals.device_discovery_start_requested.connect(
        window.app_controller.managers.device.on_discovery_start_request
    )
    test_signals.device_discovery_stop_requested.connect(
        window.app_controller.managers.device.on_discovery_stop_request
    )
    test_signals.device_selection_requested.connect(window.app_controller.managers.device.on_device_select_request)
    test_signals.device_acquisition_start_requested.connect(
        window.app_controller.managers.device.on_acquisition_start_request
    )
    test_signals.device_acquisition_stop_requested.connect(
        window.app_controller.managers.device.on_acquisition_stop_request
    )
    test_signals.storage_export_requested.connect(window.app_controller.managers.storage.on_export_request)

    try:
        window.show()
        app.processEvents()

        discovered_devices: list = []

        def capture_devices(devices: list) -> None:
            discovered_devices.clear()
            discovered_devices.extend(devices)

        window.app_controller.managers.device.devices_discovered.connect(capture_devices)

        # Start device discovery and wait for devices to be discovered
        test_signals.device_discovery_start_requested.emit(500)
        _process_events(app, 2.0)  # Allow time for device discovery to complete

        # Stop discovery once we have devices
        test_signals.device_discovery_stop_requested.emit()

        if not discovered_devices:
            raise SmokeTestError(_NO_DEVICES_REASON)

        addresses = [device.address for device in discovered_devices]
        test_signals.device_selection_requested.emit(addresses)
        test_signals.device_acquisition_start_requested.emit()

        _process_events(app, 5.0)

        test_signals.device_acquisition_stop_requested.emit()
        app.processEvents()

        export_dir = Path(tempfile.mkdtemp(prefix="msms_smoke_"))
        export_path = export_dir / "acquisition.csv"
        test_signals.storage_export_requested.emit((export_path, None, True, True, False))
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
