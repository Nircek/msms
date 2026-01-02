import logging
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtWidgets

if TYPE_CHECKING:
    from msms.ui.automation.step_base import Step
    from msms.ui.controllers import ApplicationController

logger = logging.getLogger(__name__)


class AutomationController(QtCore.QObject):
    """Manage automation plan display and execution status."""

    def __init__(
        self,
        automation_plan_text: QtWidgets.QTextEdit,
        app_controller: ApplicationController,
    ) -> None:
        super().__init__()
        self.automation_plan_text = automation_plan_text
        self.app_controller = app_controller

        # Connect to automation manager signals
        self.app_controller.managers.automation.current_step_changed.connect(self._on_automation_step_changed)
        self.app_controller.managers.automation.automation_completed.connect(self._on_automation_completed)

    @QtCore.Slot(object)
    def _on_automation_step_changed(self, current_step: Step | None) -> None:
        """Update automation plan display when current step changes."""
        next_step = self.app_controller.managers.automation.next_step

        current_text = current_step.label if current_step else "No active step"
        next_text = next_step.label if next_step else "End of plan"

        html = (
            '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">'
            '<html><head><meta name="qrichtext" content="1" /><meta charset="utf-8" />'
            '<style type="text/css">p, li { white-space: pre-wrap; }'
            "hr { height: 1px; border-width: 0; }"
            'li.unchecked::marker { content: "\\2610"; }'
            'li.checked::marker { content: "\\2612"; }'
            "</style></head><body style=\" font-family:'.AppleSystemUIFont'; font-size:13pt; "
            'font-weight:400; font-style:normal;">'
            '<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; '
            f'-qt-block-indent:0; text-indent:0px;"><span style=" font-weight:700;">CURRENT: </span>{current_text}</p>'
            '<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; '
            f'-qt-block-indent:0; text-indent:0px;"><span style=" font-weight:700;">NEXT: '
            f"</span>{next_text}</p>"
            "</body></html>"
        )

        self.automation_plan_text.setHtml(html)
        logger.debug("Automation plan display updated: current=%s, next=%s", current_text, next_text)

    @QtCore.Slot()
    def _on_automation_completed(self) -> None:
        """Handle automation completion."""
        logger.info("Automation completed")
        self.automation_plan_text.setHtml(
            '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">'
            '<html><head><meta name="qrichtext" content="1" /><meta charset="utf-8" />'
            '<style type="text/css">p, li { white-space: pre-wrap; }hr { height: 1px; border-width: 0; }'
            'li.unchecked::marker { content: "\\2610"; }li.checked::marker { content: "\\2612"; }'
            "</style></head><body style=\" font-family:'.AppleSystemUIFont'; font-size:13pt; "
            'font-weight:400; font-style:normal;"><p style=" margin-top:0px; margin-bottom:0px; '
            'margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">'
            '<span style=" font-weight:700;">EXPERIMENT COMPLETED</span></p></body></html>'
        )
