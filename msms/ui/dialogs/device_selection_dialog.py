"""Dialog for selecting devices to poll."""

from __future__ import annotations

import logging
import typing

from PyQt6 import QtCore, QtWidgets

if typing.TYPE_CHECKING:
    from msms.connectivity.device_repository import DiscoveredDevice

logger = logging.getLogger(__name__)


class DeviceSelectionDialog(QtWidgets.QDialog):
    """Dialog for discovering and selecting devices to poll."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        discover_devices: typing.Callable[[], list[DiscoveredDevice]] | None = None,
    ) -> None:
        """Initialize the device selection dialog.

        Args:
            parent: Parent widget.
            discover_devices: Callable returning the latest discovery snapshot.
        """
        super().__init__(parent)
        self.setWindowTitle("Select Devices")
        self.setMinimumWidth(800)
        self.setMinimumHeight(400)

        self.discovered_devices: list[DiscoveredDevice] = []
        self._discover_devices = discover_devices or list
        self._selected_addresses: set[str] = set()
        self._updating_selection = False

        self._setup_ui()

        self._polling_timer = QtCore.QTimer()
        self._polling_timer.timeout.connect(self._poll_devices)
        self._polling_timer.start(2000)

        self._poll_devices()

    def _setup_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)

        self.status_label = QtWidgets.QLabel("Scanning for devices...")
        layout.addWidget(self.status_label)

        self.device_table = QtWidgets.QTableWidget()
        self.device_table.setColumnCount(3)
        self.device_table.setHorizontalHeaderLabels(["Address", "Device", "IDN"])
        self.device_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.device_table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.MultiSelection)
        self.device_table.itemSelectionChanged.connect(self._capture_selection)
        self.header = self.device_table.horizontalHeader()
        if self.header is not None:
            self.header.setStretchLastSection(True)
        layout.addWidget(self.device_table)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _poll_devices(self) -> None:
        try:
            self.discovered_devices = self._discover_devices()
        except Exception:
            logger.exception("Error during device polling")
            self.status_label.setText("Error scanning for devices")
            return

        self._update_device_table()
        self.status_label.setText(f"Found {len(self.discovered_devices)} device(s)")

    def _update_device_table(self) -> None:
        self.device_table.setRowCount(len(self.discovered_devices))

        for row, device_info in enumerate(self.discovered_devices):
            address_item = QtWidgets.QTableWidgetItem(device_info.address or "N/A")
            self.device_table.setItem(row, 0, address_item)

            device_name = device_info.device_name or "Unknown"
            device_item = QtWidgets.QTableWidgetItem(device_name)
            self.device_table.setItem(row, 1, device_item)

            idn = device_info.idn or "N/A"
            idn_item = QtWidgets.QTableWidgetItem(idn)
            self.device_table.setItem(row, 2, idn_item)

        available_addresses = {device_info.address for device_info in self.discovered_devices if device_info.address}
        if self._selected_addresses:
            self._selected_addresses &= available_addresses
        else:
            self._selected_addresses = available_addresses

        self._updating_selection = True
        self.device_table.clearSelection()
        for row, device_info in enumerate(self.discovered_devices):
            if device_info.address in self._selected_addresses:
                self.device_table.selectRow(row)
        self._updating_selection = False

        self.device_table.resizeColumnsToContents()

    def get_selected_addresses(self) -> list[str]:
        self._capture_selection()
        return sorted(self._selected_addresses)

    def _capture_selection(self) -> None:
        if self._updating_selection:
            return

        selected_rows = {index.row() for index in self.device_table.selectedIndexes()}
        selected_addresses = set()
        for row in selected_rows:
            item = self.device_table.item(row, 0)
            if item is not None:
                selected_addresses.add(item.text())
        self._selected_addresses = selected_addresses

    def closeEvent(self, event: QtCore.QEvent | None) -> None:  # noqa: N802
        self._polling_timer.stop()
        if event:
            event.accept()
