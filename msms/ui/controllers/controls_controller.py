import logging

from PySide6 import QtCore, QtGui, QtWidgets

from msms.ui.controllers import ApplicationController, AutomationController

logger = logging.getLogger(__name__)


class QHLine(QtWidgets.QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)


class SymbolButton(QtWidgets.QPushButton):
    """Button with large symbol and tooltip description."""

    def __init__(self, symbol: str, description: str, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(symbol, parent)
        self.setMinimumHeight(40)
        self.setStyleSheet("font-size: 20pt;")
        self.setToolTip(description)


class ControlsController(QtCore.QObject):
    """Manage dynamic control panel with device selection and acquisition/automation controls."""

    # Device signals
    device_selection_requested = QtCore.Signal()
    acquisition_start_requested = QtCore.Signal()
    acquisition_stop_requested = QtCore.Signal()
    manual_measurement_requested = QtCore.Signal()
    interval_change_requested = QtCore.Signal(int)

    # Automation signals
    automation_edit_requested = QtCore.Signal()
    automation_start_requested = QtCore.Signal()
    automation_stop_requested = QtCore.Signal()
    automation_skip_requested = QtCore.Signal()

    def __init__(self, placeholder: QtWidgets.QWidget, app_controller: ApplicationController) -> None:
        super().__init__()
        self.placeholder = placeholder
        self.app_controller = app_controller

        # State tracking
        self._acquisition_running = True  # it will be changed during initialization
        self._automation_running = True  # it will be changed during initialization
        self._devices_selected = False

        # Widget references
        self._layout = QtWidgets.QVBoxLayout(placeholder)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)
        self._select_devices_button: QtWidgets.QPushButton | None = None
        self._acq_button: SymbolButton | None = None
        self._interval_button: SymbolButton | None = None
        self._manual_button: SymbolButton | None = None
        self._automation_button: SymbolButton | None = None
        self._skip_button: SymbolButton | None = None
        self._edit_button: SymbolButton | None = None
        self._automation_status_display: QtWidgets.QTextEdit | None = None

        # Initialize with selection screen
        self._show_device_selection_screen()

    def _clear_layout(self) -> None:
        """Remove all widgets from the placeholder."""
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()

    def _show_device_selection_screen(self) -> None:
        """Show initial screen with SELECT DEVICES button."""
        self._clear_layout()

        self._select_devices_button = QtWidgets.QPushButton("SELECT DEVICES")
        self._select_devices_button.setMinimumHeight(185)
        self._select_devices_button.setStyleSheet("font-size: 18pt; font-weight: bold;")
        self._select_devices_button.clicked.connect(self._on_select_devices_clicked)

        self._layout.addWidget(self._select_devices_button)

    def _show_full_controls(self) -> None:
        """Show full control panel after device selection."""
        self._clear_layout()

        acq_label = QtWidgets.QLabel("DATA ACQUISITION")
        acq_label.setStyleSheet("font-weight: bold; font-size: 10pt;")
        self._layout.addWidget(acq_label)

        acq_layout = QtWidgets.QHBoxLayout()

        self._acq_button = SymbolButton("", "")
        self._on_acq_clicked()  # Initialize button state
        self._acq_button.clicked.connect(self._on_acq_clicked)
        acq_layout.addWidget(self._acq_button)

        self._interval_button = SymbolButton("🕐", "Change acquisition interval")
        self._interval_button.clicked.connect(self._on_interval_clicked)
        self._update_interval_button()
        acq_layout.addWidget(self._interval_button)

        self._manual_button = SymbolButton("➀", "One-time manual measurement")
        self._manual_button.clicked.connect(self._on_manual_clicked)
        acq_layout.addWidget(self._manual_button)
        self._layout.addLayout(acq_layout)

        self._layout.addWidget(QHLine())

        auto_label = QtWidgets.QLabel("AUTOMATION")
        auto_label.setStyleSheet("font-weight: bold; font-size: 10pt;")
        self._layout.addWidget(auto_label)

        self._automation_status_display = QtWidgets.QTextEdit(self.placeholder)
        self._automation_status_display.setReadOnly(True)
        self._automation_status_display.setPlaceholderText("Automation status.")
        self._automation_status_display.setMaximumSize(16777215, 60)
        self._automation_status_display.viewport().setProperty(
            "cursor", QtGui.QCursor(QtCore.Qt.CursorShape.ArrowCursor)
        )
        self._automation_status_display.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.NoTextInteraction)
        self._automation_status_display.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed
        )
        self._layout.addWidget(self._automation_status_display)

        self.automation_controller = AutomationController(
            automation_plan_text=self._automation_status_display, app_controller=self.app_controller
        )

        auto_layout = QtWidgets.QHBoxLayout()

        self._automation_button = SymbolButton("", "")
        self._on_automation_clicked()  # Initialize button state
        self._automation_button.clicked.connect(self._on_automation_clicked)
        auto_layout.addWidget(self._automation_button)

        self._skip_button = SymbolButton("⏭", "Skip to next step")
        self._skip_button.clicked.connect(self._on_skip_clicked)
        auto_layout.addWidget(self._skip_button)

        self._edit_button = SymbolButton("✎", "Edit automation plan")
        self._edit_button.clicked.connect(self._on_edit_clicked)
        auto_layout.addWidget(self._edit_button)
        self._layout.addLayout(auto_layout)

    @QtCore.Slot()
    def _on_select_devices_clicked(self) -> None:
        """Handle SELECT DEVICES button click."""
        logger.info("Select devices clicked")
        self.device_selection_requested.emit()

    @QtCore.Slot()
    def on_devices_selected(self) -> None:
        """Called when devices have been selected."""
        logger.info("Devices selected, showing full controls")
        self._devices_selected = True
        self._show_full_controls()

    @QtCore.Slot()
    def _on_acq_clicked(self) -> None:
        """Toggle between REC and STOP for acquisition."""
        if self._acq_button is None:
            return

        if self._acquisition_running:
            logger.info("Stop acquisition clicked")
            self.acquisition_stop_requested.emit()
            self._acquisition_running = False
            self._acq_button.setText("●")
            self._acq_button.setToolTip("Start data acquisition")
            self._acq_button.setStyleSheet("QToolTip, QPushButton { font-size: 20pt; } QPushButton { color: red; }")
        else:
            logger.info("Start acquisition clicked")
            self.acquisition_start_requested.emit()
            self._acquisition_running = True
            self._acq_button.setText("■")
            self._acq_button.setToolTip("Stop data acquisition")
            self._acq_button.setStyleSheet("QToolTip, QPushButton { font-size: 20pt; } QPushButton { color: black; }")

    @QtCore.Slot()
    def _on_interval_clicked(self) -> None:
        """Display interval selection menu with predefined and custom options."""
        menu = QtWidgets.QMenu()

        # Predefined intervals
        for seconds in [3, 5, 10]:
            action = menu.addAction(f"{seconds} seconds")
            assert action is not None
            action.triggered.connect(lambda _checked=None, s=seconds: self._set_interval(s * 1000))

        # Custom interval option
        menu.addSeparator()
        custom_action = menu.addAction("Custom...")
        assert custom_action is not None
        custom_action.triggered.connect(self._show_custom_interval_dialog)

        menu.exec(QtGui.QCursor.pos())

    def _set_interval(self, interval_ms: int) -> None:
        """Update acquisition interval and button display."""
        logger.info("Setting interval to %d ms", interval_ms)
        self.app_controller.current_interval_ms = interval_ms
        self.interval_change_requested.emit(interval_ms)
        self._update_interval_button()

    def _show_custom_interval_dialog(self) -> None:
        """Show dialog for custom interval input."""
        value, ok = QtWidgets.QInputDialog.getDouble(
            self.placeholder, "Custom Interval", "Enter interval in seconds:", 5.0, 0.5, 3600.0, 1
        )
        if ok:
            self._set_interval(int(value * 1000))

    def _update_interval_button(self) -> None:
        """Update interval button tooltip with current value."""
        if self._interval_button is not None:
            seconds = self.app_controller.current_interval_ms / 1000
            self._interval_button.setToolTip(f"Change acquisition interval (current: {seconds:.1f}s)")

    @QtCore.Slot()
    def _on_manual_clicked(self) -> None:
        """Trigger manual single measurement."""
        logger.info("Manual measurement clicked")
        self.manual_measurement_requested.emit()

    @QtCore.Slot()
    def _on_edit_clicked(self) -> None:
        """Handle edit automation button click."""
        logger.info("Edit automation clicked")
        self.automation_edit_requested.emit()

    @QtCore.Slot()
    def _on_automation_clicked(self) -> None:
        """Toggle between START and STOP for automation."""
        if self._automation_button is None:
            return

        if self._automation_running:
            logger.info("Stop automation clicked")
            self.automation_stop_requested.emit()
            self._automation_running = False
            self._automation_button.setText("▶")
            self._automation_button.setToolTip("Start automation")
            self._automation_button.setStyleSheet(
                "QToolTip, QPushButton { font-size: 20pt; } QPushButton { color: green; }"
            )
        else:
            logger.info("Start automation clicked")
            self.automation_start_requested.emit()
            self._automation_running = True
            self._automation_button.setText("⏸")
            self._automation_button.setToolTip("Pause automation")
            self._automation_button.setStyleSheet(
                "QToolTip, QPushButton { font-size: 20pt; } QPushButton { color: blue; }"
            )

    @QtCore.Slot()
    def _on_skip_clicked(self) -> None:
        """Handle skip to next step button click."""
        logger.info("Skip to next step clicked")
        self.automation_skip_requested.emit()
