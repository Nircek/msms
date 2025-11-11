import logging
import typing

from PyQt6 import QtCore, QtWidgets

if typing.TYPE_CHECKING:
    from msms.connectivity.device_repository import DiscoveredDevice
    from msms.ui.controllers.app_controller import ApplicationController

logger = logging.getLogger(__name__)


class DeviceSelectionDialog(QtWidgets.QDialog):
    """Dialog for discovering and selecting devices to poll."""

    def __init__(self, parent: QtWidgets.QWidget, app_controller: ApplicationController) -> None:
        super().__init__(parent)
        self.setWindowTitle("Select Devices")
        self.setMinimumWidth(800)
        self.setMinimumHeight(400)

        self.discovered_devices: list[DiscoveredDevice] = []
        self._app_controller = app_controller
        self._selected_addresses: set[str] = set()
        self._updating_selection = False

        self._setup_ui()

        self._app_controller.devices_discovered.connect(self._on_devices_discovered)
        self._app_controller.start_discovery(interval_ms=2000)
        self.finished.connect(lambda *_: self._app_controller.stop_discovery())

    def _setup_ui(self) -> None:
        """Create dialog UI with device table and buttons."""
        layout = QtWidgets.QVBoxLayout(self)

        self.status_label = QtWidgets.QLabel("Scanning for devices...")
        layout.addWidget(self.status_label)

        self.device_table = QtWidgets.QTableWidget()
        self.device_table.setStyleSheet(
            "QTableWidget::item:selected { background-color: cyan; selection-color: #000000; }"
        )

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

    @QtCore.pyqtSlot(object)
    def _on_devices_discovered(self, devices: list[DiscoveredDevice]) -> None:
        self.discovered_devices = devices
        self._update_device_table()
        self.status_label.setText(f"Found {len(self.discovered_devices)} device(s)")

    def _update_device_table(self) -> None:
        """Populate table with discovered devices and restore selection."""
        self.device_table.setRowCount(len(self.discovered_devices))

        for row, device_info in enumerate(self.discovered_devices):
            address_item = QtWidgets.QTableWidgetItem(device_info.address or "N/A")
            address_item.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable)
            self.device_table.setItem(row, 0, address_item)

            device_name = device_info.device_name or "Unknown"
            device_item = QtWidgets.QTableWidgetItem(device_name)
            device_item.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable)
            self.device_table.setItem(row, 1, device_item)

            idn = device_info.idn or "N/A"
            idn_item = QtWidgets.QTableWidgetItem(idn)
            idn_item.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable)
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
        """Return sorted list of selected device addresses."""
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
        self.finished.emit(0)
        if event:
            event.accept()
