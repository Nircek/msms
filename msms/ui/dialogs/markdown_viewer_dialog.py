import logging
from pathlib import Path

from PyQt6 import QtGui, QtWidgets

logger = logging.getLogger(__name__)


class MarkdownViewerDialog(QtWidgets.QDialog):
    """Dialog for displaying Markdown-formatted text with rich rendering."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        markdown_text: str = "",
        title: str = "Documentation",
    ) -> None:
        """Initialize the markdown viewer dialog.

        Args:
            parent: Parent widget.
            markdown_text: Markdown text to render.
            title: Dialog window title.
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        self._setup_ui()
        self.set_markdown(markdown_text)

    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        layout = QtWidgets.QVBoxLayout(self)

        # Text browser for rendering
        self.text_browser = QtWidgets.QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        self.text_browser.setOpenLinks(True)

        # Set a nice font
        font = QtGui.QFont("Monospace", 10)
        self.text_browser.setFont(font)

        layout.addWidget(self.text_browser)

        # Close button
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.close)
        layout.addWidget(button_box)

    def set_markdown(self, markdown_text: str) -> None:
        """Set and render the markdown content.

        Args:
            markdown_text: Markdown text to display.
        """
        self.text_browser.setMarkdown(markdown_text)

    @classmethod
    def from_file(
        cls,
        parent: QtWidgets.QWidget | None,
        file_path: Path | str,
        title: str | None = None,
    ) -> MarkdownViewerDialog:
        """Create dialog from a markdown file.

        Args:
            parent: Parent widget.
            file_path: Path to markdown file.
            title: Dialog title (defaults to filename).

        Returns:
            Configured MarkdownViewerDialog instance.
        """
        file_path = Path(file_path)

        if not file_path.exists():
            logger.error("Markdown file not found: %s", file_path)
            markdown_text = f"# Error\n\nFile not found: {file_path}"
        else:
            try:
                markdown_text = file_path.read_text(encoding="utf-8")
            except Exception as e:
                logger.exception("Error reading markdown file: %s", file_path)
                markdown_text = f"# Error\n\nCould not read file: {e}"

        dialog_title = title or file_path.name
        return cls(parent, markdown_text, dialog_title)
