import logging
from typing import TYPE_CHECKING

from PyQt6 import QtCore, QtWidgets

if TYPE_CHECKING:
    from msms.connectivity.device_repository import DiscoveredDevice
    from msms.ui.controllers.app_controller import ApplicationController

logger = logging.getLogger(__name__)


class DeviceCommandDialog(QtWidgets.QDialog):
    """Dialog for selecting a device and sending commands to it."""

    # Device command signals
    device_info_requested = QtCore.pyqtSignal()
    device_command_requested = QtCore.pyqtSignal(object, object)

    def __init__(self, parent: QtWidgets.QWidget, app_controller: ApplicationController) -> None:
        """Initialize the device command dialog.

        Args:
            parent: Parent widget.
            app_controller: Application controller for device operations.
        """
        super().__init__(parent)
        self.app_controller = app_controller
        self._device_info: dict[str, DiscoveredDevice] = {}

        self.setWindowTitle("Send Device Command")
        self.setModal(True)
        self.resize(500, 300)

        layout = QtWidgets.QVBoxLayout(self)

        # Device selection
        device_label = QtWidgets.QLabel("Select Device:")
        layout.addWidget(device_label)

        self.device_combo = QtWidgets.QComboBox()
        layout.addWidget(self.device_combo)

        # Command input
        command_label = QtWidgets.QLabel("Command:")
        layout.addWidget(command_label)

        self.command_text = QtWidgets.QPlainTextEdit()
        self.command_text.setPlaceholderText("Enter SCPI command (e.g., *IDN?)")
        layout.addWidget(self.command_text)

        # Buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._send_command)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.device_info_requested.connect(self.app_controller.managers.device.on_device_info_request)
        self.device_command_requested.connect(self.app_controller.managers.device.on_device_command_request)
        self.app_controller.managers.device.device_info_collected.connect(self._on_device_info_received)
        self.device_info_requested.emit()

    @QtCore.pyqtSlot(object)
    def _on_device_info_received(self, device_info: dict[str, DiscoveredDevice]) -> None:
        """Handle device info response from the device manager."""
        self._device_info = device_info
        self.device_combo.clear()

        for address, info in device_info.items():
            display_text = f"{info.device_name or 'Unknown'} ({address})"
            if info.idn:
                display_text += f" - {info.idn}"
            self.device_combo.addItem(display_text, address)

        if not device_info:
            self.device_combo.addItem("No devices available", None)
            self.device_combo.setEnabled(False)

        # Disconnect signal to avoid multiple connections
        self.app_controller.managers.device.device_info_collected.disconnect(self._on_device_info_received)

    def _send_command(self) -> None:
        """Send the command to the selected device."""
        device_address = self.device_combo.currentData()
        command = self.command_text.toPlainText().strip()

        if not device_address:
            QtWidgets.QMessageBox.warning(self, "No Device Selected", "Please select a device first.")
            return

        if not command:
            QtWidgets.QMessageBox.warning(self, "No Command", "Please enter a command to send.")
            return

        self.device_command_requested.emit(device_address, command)

        QtWidgets.QMessageBox.information(
            self,
            "Command Sent",
            f"Command sent to device {device_address}:\n{command}",
        )
        self.accept()
