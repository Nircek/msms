import logging
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6 import QtGui, QtWidgets

if TYPE_CHECKING:
    from msms.ui.controllers.app_controller import ApplicationController

logger = logging.getLogger(__name__)


class ExperimentController:
    """Experiment action menu and related dialogs."""

    def __init__(
        self,
        parent: QtWidgets.QWidget,
        button: QtWidgets.QPushButton,
        app_controller: ApplicationController,
    ) -> None:
        self.parent = parent
        self.button = button
        self.app_controller = app_controller
        self._selected_device_addresses: list[str] = []

    def set_selected_devices(self, addresses: list[str]) -> None:
        self._selected_device_addresses = addresses

    def show_action_menu(self) -> None:
        """Show action menu for acquisition and exports."""
        menu = QtWidgets.QMenu(self.parent)

        if self.app_controller.is_acquiring:
            stop_action = QtGui.QAction("Stop", self.parent)
            stop_action.triggered.connect(self._stop_acquisition)
            menu.addAction(stop_action)
        else:
            start_action = QtGui.QAction("Start", self.parent)
            start_action.triggered.connect(self._start_acquisition)
            menu.addAction(start_action)

        menu.addSeparator()
        export_action = QtGui.QAction("Export Data to CSV...", self.parent)
        export_action.triggered.connect(self.export_data_to_csv)
        menu.addAction(export_action)

        menu.addSeparator()
        device_command_action = QtGui.QAction("Send Device Command...", self.parent)
        device_command_action.triggered.connect(self._open_device_command_dialog)
        menu.addAction(device_command_action)

        menu.addSeparator()
        interval_menu = QtWidgets.QMenu("Set Interval", self.parent)
        menu.addMenu(interval_menu)
        for interval_sec in [0.1, 0.5, 1.0, 2.0, 5.0]:
            interval_ms = int(interval_sec * 1000)
            action = QtGui.QAction(f"{interval_sec} s", self.parent)
            action.setCheckable(True)
            action.setChecked(interval_ms == self.app_controller.current_interval_ms)
            action.triggered.connect(lambda _, val=interval_ms: self._set_interval(val))
            interval_menu.addAction(action)

        menu.exec(QtGui.QCursor.pos())

    def _start_acquisition(self) -> None:
        """Start device acquisition."""
        if not self._selected_device_addresses:
            QtWidgets.QMessageBox.warning(
                self.parent,
                "Select Devices",
                "Select at least one device before starting acquisition.",
            )
            return

        logger.info("Starting device manager with interval %d ms", self.app_controller.current_interval_ms)
        self.app_controller.start_acquisition()

    def _stop_acquisition(self) -> None:
        """Stop acquisition."""
        logger.info("Stopping device manager")
        self.app_controller.stop_acquisition()

    def export_data_to_csv(self) -> None:
        """Export data to CSV via save dialog."""
        dialog = QtWidgets.QFileDialog(self.parent)
        dialog.setWindowTitle("Export Data to CSV")
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptMode.AcceptSave)
        dialog.setNameFilter("CSV Files (*.csv)")
        dialog.setDefaultSuffix("csv")
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            export_path = Path(dialog.selectedFiles()[0])
            logger.info("Exporting data to CSV file: %s", export_path)
            self.app_controller.request_export_to_csv(export_path)

    def _set_interval(self, value_ms: int) -> None:
        logger.info("Changing device manager interval to %d ms", value_ms)
        self.app_controller.set_interval(value_ms)

    def _open_device_command_dialog(self) -> None:
        # Import here to avoid circular dependency
        from msms.ui.dialogs.device_command_dialog import DeviceCommandDialog  # noqa: PLC0415

        dialog = DeviceCommandDialog(self.parent, self.app_controller)
        dialog.exec()
