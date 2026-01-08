import logging
from pathlib import Path

from PySide6 import QtCore, QtWidgets

logger = logging.getLogger(__name__)


def custom_sort_available_columns(columns: list[str]) -> list[str]:
    """Sort alphabetically but first should be 'Time', 'sample', 'X', 'Y' and last 'dt', 'timestamp'."""
    first = ["time", "row_number", "sample", "control", "X", "Y"]
    last = ["dt", "timestamp"]
    priority = {name: -1 - index for index, name in enumerate(reversed(first))} | {
        name: 1 + index for index, name in enumerate(last)
    }
    return sorted(columns, key=lambda col: priority.get(col, 0))


class ExportDialog(QtWidgets.QDialog):
    """Dialog for configuring CSV export options."""

    def __init__(
        self,
        parent: QtWidgets.QWidget,
        available_columns: list[str],
        default_path: Path | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Export Data to CSV")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        self._available_columns = available_columns
        self._default_path = default_path
        self._selected_path: Path | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:  # noqa: PLR0915
        """Create dialog UI with export options."""
        layout = QtWidgets.QVBoxLayout(self)

        # File selection
        file_group = QtWidgets.QGroupBox("Export File")
        file_layout = QtWidgets.QHBoxLayout(file_group)
        self.path_edit = QtWidgets.QLineEdit()
        if self._default_path:
            self.path_edit.setText(str(self._default_path))
        self.path_edit.setReadOnly(True)
        file_layout.addWidget(self.path_edit)

        browse_button = QtWidgets.QPushButton("Browse...")
        browse_button.clicked.connect(self._browse_file)
        file_layout.addWidget(browse_button)
        layout.addWidget(file_group)

        # Column selection
        column_group = QtWidgets.QGroupBox("Columns to Export")
        column_layout = QtWidgets.QVBoxLayout(column_group)

        select_buttons_layout = QtWidgets.QHBoxLayout()
        select_all_button = QtWidgets.QPushButton("Select All")
        select_all_button.clicked.connect(self._select_all_columns)
        select_buttons_layout.addWidget(select_all_button)

        deselect_all_button = QtWidgets.QPushButton("Deselect All")
        deselect_all_button.clicked.connect(self._deselect_all_columns)
        select_buttons_layout.addWidget(deselect_all_button)
        column_layout.addLayout(select_buttons_layout)

        selection_hint = QtWidgets.QLabel("Hint: Use Shift or Ctrl to select multiple columns")
        selection_hint.setStyleSheet("QLabel { color: gray; font-size: 9pt; }")
        column_layout.addWidget(selection_hint)

        self.column_list = QtWidgets.QListWidget()
        self.column_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        for column in custom_sort_available_columns(self._available_columns):
            item = QtWidgets.QListWidgetItem(column)
            item.setSelected(True)  # Default: all columns selected
            self.column_list.addItem(item)
        self.column_list.itemSelectionChanged.connect(self._update_column_order_hint)
        column_layout.addWidget(self.column_list)

        # Column order hint
        self.column_order_hint = QtWidgets.QLabel()
        self.column_order_hint.setWordWrap(True)
        self.column_order_hint.setStyleSheet("QLabel { color: gray; font-size: 8pt; }")
        column_layout.addWidget(self.column_order_hint)
        self._update_column_order_hint()  # Initialize hint

        layout.addWidget(column_group)

        # Format options
        format_group = QtWidgets.QGroupBox("Format Options")
        format_layout = QtWidgets.QVBoxLayout(format_group)

        self.include_comments_checkbox = QtWidgets.QCheckBox("Include comments and metadata")
        self.include_comments_checkbox.setChecked(True)
        format_layout.addWidget(self.include_comments_checkbox)

        self.include_automation_log_checkbox = QtWidgets.QCheckBox("Include automation execution log")
        self.include_automation_log_checkbox.setChecked(True)
        format_layout.addWidget(self.include_automation_log_checkbox)

        layout.addWidget(format_group)

        # Dialog buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    @QtCore.Slot()
    def _browse_file(self) -> None:
        """Show file browser for selecting export path."""
        dialog = QtWidgets.QFileDialog(self)
        dialog.setWindowTitle("Export Data to CSV")
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptMode.AcceptSave)
        dialog.setNameFilter("CSV Files (*.csv)")
        dialog.setDefaultSuffix("csv")
        if self._default_path:
            dialog.selectFile(str(self._default_path))
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self._selected_path = Path(dialog.selectedFiles()[0])
            self.path_edit.setText(str(self._selected_path))

    @QtCore.Slot()
    def _select_all_columns(self) -> None:
        """Select all columns in the list."""
        for i in range(self.column_list.count()):
            item = self.column_list.item(i)
            if item:
                item.setSelected(True)

    @QtCore.Slot()
    def _deselect_all_columns(self) -> None:
        """Deselect all columns in the list."""
        self.column_list.clearSelection()

    @QtCore.Slot()
    def _update_column_order_hint(self) -> None:
        """Update the hint showing column export order."""
        selected = self.get_selected_columns()
        if selected:
            self.column_order_hint.setText(f"Export order: {', '.join(selected)}")
        else:
            self.column_order_hint.setText("No columns selected")

    @QtCore.Slot()
    def _validate_and_accept(self) -> None:
        """Validate selections and accept dialog."""
        if not self._selected_path:
            QtWidgets.QMessageBox.warning(self, "No File Selected", "Please select a file to export to.")
            return

        selected_columns = self.get_selected_columns()
        if not selected_columns:
            QtWidgets.QMessageBox.warning(self, "No Columns Selected", "Please select at least one column to export.")
            return

        self.accept()

    def get_selected_path(self) -> Path | None:
        """Return the selected export file path."""
        return self._selected_path

    def get_selected_columns(self) -> list[str]:
        """Return list of selected column names."""
        return [item.text() for item in self.column_list.selectedItems()]

    def get_include_comments(self) -> bool:
        """Return whether to include comments in export."""
        return self.include_comments_checkbox.isChecked()

    def get_include_automation_log(self) -> bool:
        """Return whether to include automation log in export."""
        return self.include_automation_log_checkbox.isChecked()
