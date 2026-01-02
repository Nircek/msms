import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtWidgets

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


class DescriptionDialog(QtWidgets.QDialog):
    """Dialog for creating structured automation descriptions with predefined sections."""

    def __init__(self, parent: QtWidgets.QWidget | None = None, initial_text: str = "") -> None:
        """Initialize the description dialog.

        Args:
            parent: Parent widget.
            initial_text: Initial description text to parse and populate fields.
        """
        super().__init__(parent)
        self.setWindowTitle("Automation Description")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        self._setup_ui()
        self._parse_initial_text(initial_text)

    def _setup_ui(self) -> None:
        """Set up the dialog UI with form fields."""
        layout = QtWidgets.QVBoxLayout(self)

        # Create form with input fields
        form_layout = self._create_form_fields()
        layout.addLayout(form_layout)

        # Add preview section
        self._create_preview_section(layout)

        # Add buttons
        self._create_buttons(layout)

        # Connect signals and initial update
        self._connect_signals()
        self._update_preview()

    def _create_form_fields(self) -> QtWidgets.QFormLayout:
        """Create the form layout with all input fields.

        Returns:
            Form layout with all fields configured.
        """
        form_layout = QtWidgets.QFormLayout()
        form_layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # Paper logbook ID
        self.logbook_id_edit = QtWidgets.QLineEdit()
        self.logbook_id_edit.setPlaceholderText("e.g., LB-2025-001")
        form_layout.addRow("Paper Logbook ID:", self.logbook_id_edit)

        # Experimenter's name
        self.experimenter_edit = QtWidgets.QLineEdit()
        self.experimenter_edit.setPlaceholderText("Full name")
        form_layout.addRow("Experimenter's Name:", self.experimenter_edit)

        # Date
        self.date_edit = QtWidgets.QDateEdit()
        self.date_edit.setCalendarPopup(True)
        date = datetime.now().astimezone()
        self.date_edit.setDate(QtCore.QDate(date.year, date.month, date.day))
        form_layout.addRow("Date:", self.date_edit)

        # Duration
        self.duration_edit = QtWidgets.QLineEdit()
        self.duration_edit.setPlaceholderText("e.g., 2 hours, 3 days")
        form_layout.addRow("Duration:", self.duration_edit)

        # Material / Sample number
        self.sample_edit = QtWidgets.QLineEdit()
        self.sample_edit.setPlaceholderText("e.g., Sample #42, CuO-123")
        form_layout.addRow("Material / Sample Number:", self.sample_edit)

        # Measured parameters
        self.parameters_edit = QtWidgets.QTextEdit()
        self.parameters_edit.setPlaceholderText("e.g., AC magnetic susceptibility vs temperature")
        self.parameters_edit.setMaximumHeight(80)
        form_layout.addRow("Measured Parameters:", self.parameters_edit)

        # Changes to procedures
        self.procedures_edit = QtWidgets.QTextEdit()
        self.procedures_edit.setPlaceholderText("Any modifications to standard procedures")
        self.procedures_edit.setMaximumHeight(80)
        form_layout.addRow("Changes to Procedures:", self.procedures_edit)

        # Additional notes
        self.notes_edit = QtWidgets.QTextEdit()
        self.notes_edit.setPlaceholderText("Any additional observations or notes")
        self.notes_edit.setMaximumHeight(100)
        form_layout.addRow("Additional Notes:", self.notes_edit)

        return form_layout

    def _create_preview_section(self, layout: QtWidgets.QVBoxLayout) -> None:
        """Create the preview section.

        Args:
            layout: Parent layout to add preview section to.
        """
        preview_label = QtWidgets.QLabel("<b>Preview:</b>")
        layout.addWidget(preview_label)

        self.preview_text = QtWidgets.QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(150)
        layout.addWidget(self.preview_text)

    def _create_buttons(self, layout: QtWidgets.QVBoxLayout) -> None:
        """Create dialog buttons.

        Args:
            layout: Parent layout to add buttons to.
        """
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _connect_signals(self) -> None:
        """Connect all widget signals for live preview updates."""
        self.logbook_id_edit.textChanged.connect(self._update_preview)
        self.experimenter_edit.textChanged.connect(self._update_preview)
        self.date_edit.dateChanged.connect(self._update_preview)
        self.duration_edit.textChanged.connect(self._update_preview)
        self.sample_edit.textChanged.connect(self._update_preview)
        self.parameters_edit.textChanged.connect(self._update_preview)
        self.procedures_edit.textChanged.connect(self._update_preview)
        self.notes_edit.textChanged.connect(self._update_preview)

    def _parse_initial_text(self, text: str) -> None:
        """Parse existing description text and populate form fields.

        Args:
            text: Existing description text to parse.
        """
        if not text:
            return

        section_content = self._extract_sections(text)
        self._populate_fields_from_sections(section_content)

    @staticmethod
    def _extract_sections(text: str) -> dict[str, list[str]]:
        """Extract sections from markdown-formatted text.

        Args:
            text: Markdown text to parse.

        Returns:
            Dictionary mapping section names to their content lines.
        """
        lines = text.strip().split("\n")
        current_section = None
        section_content: dict[str, list[str]] = {}

        for raw_line in lines:
            stripped_line = raw_line.strip()
            if stripped_line.startswith(("# ", "## ")):
                current_section = stripped_line.lstrip("#").strip().rstrip(":")
                section_content[current_section] = []
            elif current_section and stripped_line:
                section_content[current_section].append(stripped_line)

        return section_content

    def _populate_fields_from_sections(self, section_content: dict[str, list[str]]) -> None:
        """Populate form fields from parsed section content.

        Args:
            section_content: Dictionary of section names to content lines.
        """
        # Paper logbook ID
        self._set_text_if_exists(section_content, "Paper Logbook ID", self.logbook_id_edit.setText)

        # Experimenter
        experimenter_key = self._find_key(section_content, ["Experimenter's Name", "Experimenter"])
        if experimenter_key:
            self.experimenter_edit.setText("\n".join(section_content[experimenter_key]))

        # Date
        self._parse_and_set_date(section_content)

        # Duration
        self._set_text_if_exists(section_content, "Duration", self.duration_edit.setText)

        # Sample
        sample_key = self._find_key(section_content, ["Material / Sample Number", "Sample"])
        if sample_key:
            self.sample_edit.setText("\n".join(section_content[sample_key]))

        # Parameters
        params_key = self._find_key(section_content, ["Measured Parameters", "Parameters"])
        if params_key:
            self.parameters_edit.setPlainText("\n".join(section_content[params_key]))

        # Procedures
        proc_key = self._find_key(section_content, ["Changes to Procedures", "Procedures"])
        if proc_key:
            self.procedures_edit.setPlainText("\n".join(section_content[proc_key]))

        # Notes
        notes_key = self._find_key(section_content, ["Additional Notes", "Notes"])
        if notes_key:
            self.notes_edit.setPlainText("\n".join(section_content[notes_key]))

    @staticmethod
    def _find_key(sections: dict[str, list[str]], keys: list[str]) -> str | None:
        """Find the first matching key from a list of possible keys.

        Args:
            sections: Dictionary to search.
            keys: List of possible keys to find.

        Returns:
            First matching key or None.
        """
        for key in keys:
            if key in sections:
                return key
        return None

    @staticmethod
    def _set_text_if_exists(
        sections: dict[str, list[str]],
        key: str,
        setter: Callable[[str], None],
    ) -> None:
        """Set text field if section exists.

        Args:
            sections: Section content dictionary.
            key: Section key to look for.
            setter: Callable to set the text.
        """
        if key in sections and callable(setter):
            setter("\n".join(sections[key]))

    def _parse_and_set_date(self, section_content: dict[str, list[str]]) -> None:
        """Parse and set date from section content.

        Args:
            section_content: Dictionary of section content.
        """
        if "Date" not in section_content:
            return

        date_str = "\n".join(section_content["Date"])
        try:
            parsed_date = datetime.strptime(date_str.split(",")[0].strip(), "%Y-%m-%d").replace(tzinfo=UTC)
            date = parsed_date.date()
            self.date_edit.setDate(QtCore.QDate(date.year, date.month, date.day))
        except ValueError, IndexError:
            pass

    def _update_preview(self) -> None:
        """Update the preview text based on current form values."""
        description = self.get_description()
        self.preview_text.setPlainText(description)

    def get_description(self) -> str:
        """Generate the formatted description from form fields.

        Returns:
            Formatted description text with all sections.
        """
        sections = []

        logbook_id = self.logbook_id_edit.text().strip()
        if logbook_id:
            sections.append(f"## Paper Logbook ID\n{logbook_id}")

        experimenter = self.experimenter_edit.text().strip()
        if experimenter:
            sections.append(f"## Experimenter's Name\n{experimenter}")

        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        duration = self.duration_edit.text().strip()
        if date_str or duration:
            date_line = f"Date: {date_str}"
            if duration:
                date_line += f", Duration: {duration}"
            sections.append(f"## Date and Duration\n{date_line}")

        sample = self.sample_edit.text().strip()
        if sample:
            sections.append(f"## Material / Sample Number\n{sample}")

        parameters = self.parameters_edit.toPlainText().strip()
        if parameters:
            sections.append(f"## Measured Parameters\n{parameters}")

        procedures = self.procedures_edit.toPlainText().strip()
        if procedures:
            sections.append(f"## Changes to Procedures\n{procedures}")

        notes = self.notes_edit.toPlainText().strip()
        if notes:
            sections.append(f"## Additional Notes\n{notes}")

        if not sections:
            return "# Automation Description\n\n(No information provided)"

        return "# Automation Description\n\n" + "\n\n".join(sections)
