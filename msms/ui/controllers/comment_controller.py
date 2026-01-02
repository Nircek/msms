import logging

from PySide6 import QtCore, QtGui, QtWidgets

from msms.ui.dialogs import DescriptionDialog

logger = logging.getLogger(__name__)


class DoubleClickPlainTextEdit(QtWidgets.QPlainTextEdit):
    """Plain text edit that emits a signal on double-click."""

    double_clicked = QtCore.Signal()

    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent | None) -> None:  # noqa: N802
        """Emit signal on double-click."""
        self.double_clicked.emit()
        if event:
            super().mouseDoubleClickEvent(event)


class CommentController(QtCore.QObject):
    """Manage experiment description/comment editing."""

    description_changed = QtCore.Signal(object)

    def __init__(self, comment_text_edit: DoubleClickPlainTextEdit, parent_window: QtWidgets.QWidget) -> None:
        super().__init__()
        self.comment_text_edit = comment_text_edit
        self.parent_window = parent_window

        # Connect signals
        self.comment_text_edit.double_clicked.connect(self._on_double_click)
        self.comment_text_edit.textChanged.connect(self._on_text_changed)

    @QtCore.Slot()
    def _on_text_changed(self) -> None:
        """Emit description change when text changes."""
        comment = self.comment_text_edit.toPlainText()
        self.description_changed.emit(comment)

    @QtCore.Slot()
    def _on_double_click(self) -> None:
        """Show description editor dialog on double-click."""
        current_description = self.comment_text_edit.toPlainText()
        dialog = DescriptionDialog(self.parent_window, current_description)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            description = dialog.get_description()
            self.set_description(description)
            self.description_changed.emit(description)

    @QtCore.Slot(object)
    def on_description_changed(self, description: str) -> None:
        """Update comment text from external source (e.g., storage manager)."""
        previously_blocked = self.comment_text_edit.blockSignals(True)
        self.comment_text_edit.setPlainText(description)
        self.comment_text_edit.blockSignals(previously_blocked)

    def set_description(self, description: str) -> None:
        """Set description text programmatically."""
        self.comment_text_edit.setPlainText(description)
