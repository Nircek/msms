# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QFrame, QHBoxLayout,
    QLabel, QMainWindow, QMenu, QMenuBar,
    QPushButton, QSizePolicy, QTextEdit, QVBoxLayout,
    QWidget)

from msms.ui.controllers.comment_controller import DoubleClickPlainTextEdit
from pyqtgraph import PlotWidget

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1200, 800)
        self.actionSelectDevices = QAction(MainWindow)
        self.actionSelectDevices.setObjectName(u"actionSelectDevices")
        self.actionManageAutomation = QAction(MainWindow)
        self.actionManageAutomation.setObjectName(u"actionManageAutomation")
        self.actionExport = QAction(MainWindow)
        self.actionExport.setObjectName(u"actionExport")
        self.actionRestoreLastFile = QAction(MainWindow)
        self.actionRestoreLastFile.setObjectName(u"actionRestoreLastFile")
        self.actionStartAcquisition = QAction(MainWindow)
        self.actionStartAcquisition.setObjectName(u"actionStartAcquisition")
        self.actionStopAcquisition = QAction(MainWindow)
        self.actionStopAcquisition.setObjectName(u"actionStopAcquisition")
        self.actionSendDeviceCommand = QAction(MainWindow)
        self.actionSendDeviceCommand.setObjectName(u"actionSendDeviceCommand")
        self.actionInterval_0_1s = QAction(MainWindow)
        self.actionInterval_0_1s.setObjectName(u"actionInterval_0_1s")
        self.actionInterval_0_1s.setCheckable(True)
        self.actionInterval_0_5s = QAction(MainWindow)
        self.actionInterval_0_5s.setObjectName(u"actionInterval_0_5s")
        self.actionInterval_0_5s.setCheckable(True)
        self.actionInterval_0_5s.setChecked(True)
        self.actionInterval_1_0s = QAction(MainWindow)
        self.actionInterval_1_0s.setObjectName(u"actionInterval_1_0s")
        self.actionInterval_1_0s.setCheckable(True)
        self.actionInterval_2_0s = QAction(MainWindow)
        self.actionInterval_2_0s.setObjectName(u"actionInterval_2_0s")
        self.actionInterval_2_0s.setCheckable(True)
        self.actionInterval_5_0s = QAction(MainWindow)
        self.actionInterval_5_0s.setObjectName(u"actionInterval_5_0s")
        self.actionInterval_5_0s.setCheckable(True)
        self.actionStartAutomation = QAction(MainWindow)
        self.actionStartAutomation.setObjectName(u"actionStartAutomation")
        self.actionStopAutomation = QAction(MainWindow)
        self.actionStopAutomation.setObjectName(u"actionStopAutomation")
        self.actionSkipToNext = QAction(MainWindow)
        self.actionSkipToNext.setObjectName(u"actionSkipToNext")
        self.actionQuit = QAction(MainWindow)
        self.actionQuit.setObjectName(u"actionQuit")
        self.actionAbout = QAction(MainWindow)
        self.actionAbout.setObjectName(u"actionAbout")
        self.actionAbout.setMenuRole(QAction.MenuRole.NoRole)
        self.actionHelp = QAction(MainWindow)
        self.actionHelp.setObjectName(u"actionHelp")
        self.actionHelp.setMenuRole(QAction.MenuRole.NoRole)
        self.centralWidget = QWidget(MainWindow)
        self.centralWidget.setObjectName(u"centralWidget")
        self._2 = QVBoxLayout(self.centralWidget)
        self._2.setSpacing(2)
        self._2.setObjectName(u"_2")
        self._2.setContentsMargins(0, 4, 0, 4)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(8)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.leftPane = QVBoxLayout()
        self.leftPane.setSpacing(4)
        self.leftPane.setObjectName(u"leftPane")
        self.automationStatusLayoutWidget = QWidget(self.centralWidget)
        self.automationStatusLayoutWidget.setObjectName(u"automationStatusLayoutWidget")
        self.automationStatusLayoutWidget.setMinimumSize(QSize(300, 0))
        self.automationStatusLayout = QVBoxLayout(self.automationStatusLayoutWidget)
        self.automationStatusLayout.setSpacing(0)
        self.automationStatusLayout.setObjectName(u"automationStatusLayout")
        self.automationStatusLayout.setContentsMargins(4, 0, 4, 0)
        self.row1 = QHBoxLayout()
        self.row1.setObjectName(u"row1")
        self.timeValue = QLabel(self.automationStatusLayoutWidget)
        self.timeValue.setObjectName(u"timeValue")
        self.timeValue.setStyleSheet(u"font-size: 32pt; font-weight: 700;")
        self.timeValue.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.row1.addWidget(self.timeValue)

        self.numberValue = QLabel(self.automationStatusLayoutWidget)
        self.numberValue.setObjectName(u"numberValue")
        self.numberValue.setStyleSheet(u"font-size: 32pt; font-weight: 700;")
        self.numberValue.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.row1.addWidget(self.numberValue)


        self.automationStatusLayout.addLayout(self.row1)

        self.row2 = QHBoxLayout()
        self.row2.setObjectName(u"row2")
        self.sampleLabel = QLabel(self.automationStatusLayoutWidget)
        self.sampleLabel.setObjectName(u"sampleLabel")
        self.sampleLabel.setStyleSheet(u"font-size: 9pt;")
        self.sampleLabel.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.row2.addWidget(self.sampleLabel)

        self.controlLabel = QLabel(self.automationStatusLayoutWidget)
        self.controlLabel.setObjectName(u"controlLabel")
        self.controlLabel.setStyleSheet(u"font-size: 9pt;")
        self.controlLabel.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.row2.addWidget(self.controlLabel)


        self.automationStatusLayout.addLayout(self.row2)

        self.row3 = QHBoxLayout()
        self.row3.setObjectName(u"row3")
        self.sampleValue = QLabel(self.automationStatusLayoutWidget)
        self.sampleValue.setObjectName(u"sampleValue")
        self.sampleValue.setStyleSheet(u"font-size: 32pt; font-weight: 700;")
        self.sampleValue.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.row3.addWidget(self.sampleValue)

        self.controlValue = QLabel(self.automationStatusLayoutWidget)
        self.controlValue.setObjectName(u"controlValue")
        self.controlValue.setStyleSheet(u"font-size: 32pt; font-weight: 700;")
        self.controlValue.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.row3.addWidget(self.controlValue)


        self.automationStatusLayout.addLayout(self.row3)

        self.row4 = QHBoxLayout()
        self.row4.setObjectName(u"row4")
        self.setPointLabel = QLabel(self.automationStatusLayoutWidget)
        self.setPointLabel.setObjectName(u"setPointLabel")
        self.setPointLabel.setStyleSheet(u"font-size: 9pt;")
        self.setPointLabel.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.row4.addWidget(self.setPointLabel)

        self.rampLabel = QLabel(self.automationStatusLayoutWidget)
        self.rampLabel.setObjectName(u"rampLabel")
        self.rampLabel.setStyleSheet(u"font-size: 9pt;")
        self.rampLabel.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.row4.addWidget(self.rampLabel)


        self.automationStatusLayout.addLayout(self.row4)

        self.row5 = QHBoxLayout()
        self.row5.setObjectName(u"row5")
        self.setPointValue = QLabel(self.automationStatusLayoutWidget)
        self.setPointValue.setObjectName(u"setPointValue")
        self.setPointValue.setStyleSheet(u"font-size: 32pt; font-weight: 700;")
        self.setPointValue.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.row5.addWidget(self.setPointValue)

        self.rampValue = QLabel(self.automationStatusLayoutWidget)
        self.rampValue.setObjectName(u"rampValue")
        self.rampValue.setStyleSheet(u"font-size: 32pt; font-weight: 700;")
        self.rampValue.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.row5.addWidget(self.rampValue)


        self.automationStatusLayout.addLayout(self.row5)


        self.leftPane.addWidget(self.automationStatusLayoutWidget)

        self.automationPlanTextEdit = QTextEdit(self.centralWidget)
        self.automationPlanTextEdit.setObjectName(u"automationPlanTextEdit")
        self.automationPlanTextEdit.setMaximumSize(QSize(16777215, 60))
        self.automationPlanTextEdit.viewport().setProperty(u"cursor", QCursor(Qt.CursorShape.ArrowCursor))
        self.automationPlanTextEdit.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        self.leftPane.addWidget(self.automationPlanTextEdit)

        self.line = QFrame(self.centralWidget)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.leftPane.addWidget(self.line)

        self.commentPlainTextEdit = DoubleClickPlainTextEdit(self.centralWidget)
        self.commentPlainTextEdit.setObjectName(u"commentPlainTextEdit")

        self.leftPane.addWidget(self.commentPlainTextEdit)


        self.horizontalLayout.addLayout(self.leftPane)

        self.centerPane = QVBoxLayout()
        self.centerPane.setObjectName(u"centerPane")
        self.plotWidget = PlotWidget(self.centralWidget)
        self.plotWidget.setObjectName(u"plotWidget")

        self.centerPane.addWidget(self.plotWidget)

        self.chartConfig = QHBoxLayout()
        self.chartConfig.setSpacing(16)
        self.chartConfig.setObjectName(u"chartConfig")
        self.autoFollowCheckBox = QCheckBox(self.centralWidget)
        self.autoFollowCheckBox.setObjectName(u"autoFollowCheckBox")
        self.autoFollowCheckBox.setChecked(True)

        self.chartConfig.addWidget(self.autoFollowCheckBox)

        self.xAxisPushButton = QPushButton(self.centralWidget)
        self.xAxisPushButton.setObjectName(u"xAxisPushButton")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.xAxisPushButton.sizePolicy().hasHeightForWidth())
        self.xAxisPushButton.setSizePolicy(sizePolicy)

        self.chartConfig.addWidget(self.xAxisPushButton)

        self.yAxisPushButton = QPushButton(self.centralWidget)
        self.yAxisPushButton.setObjectName(u"yAxisPushButton")
        sizePolicy.setHeightForWidth(self.yAxisPushButton.sizePolicy().hasHeightForWidth())
        self.yAxisPushButton.setSizePolicy(sizePolicy)

        self.chartConfig.addWidget(self.yAxisPushButton)

        self.chartConfig.setStretch(1, 1)
        self.chartConfig.setStretch(2, 1)

        self.centerPane.addLayout(self.chartConfig)

        self.centerPane.setStretch(0, 1)

        self.horizontalLayout.addLayout(self.centerPane)

        self.rightPane = QVBoxLayout()
        self.rightPane.setObjectName(u"rightPane")
        self.variablesTextEdit = QTextEdit(self.centralWidget)
        self.variablesTextEdit.setObjectName(u"variablesTextEdit")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.variablesTextEdit.sizePolicy().hasHeightForWidth())
        self.variablesTextEdit.setSizePolicy(sizePolicy1)
        self.variablesTextEdit.setMinimumSize(QSize(200, 0))
        self.variablesTextEdit.setMaximumSize(QSize(120, 16777215))
        self.variablesTextEdit.viewport().setProperty(u"cursor", QCursor(Qt.CursorShape.ArrowCursor))
        self.variablesTextEdit.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        self.rightPane.addWidget(self.variablesTextEdit)


        self.horizontalLayout.addLayout(self.rightPane)

        self.horizontalLayout.setStretch(1, 1)

        self._2.addLayout(self.horizontalLayout)

        MainWindow.setCentralWidget(self.centralWidget)
        self.menuBar = QMenuBar(MainWindow)
        self.menuBar.setObjectName(u"menuBar")
        self.menuBar.setGeometry(QRect(0, 0, 1200, 33))
        self.menuFile = QMenu(self.menuBar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuDevices = QMenu(self.menuBar)
        self.menuDevices.setObjectName(u"menuDevices")
        self.menuAcquisition = QMenu(self.menuBar)
        self.menuAcquisition.setObjectName(u"menuAcquisition")
        self.menuAutomation = QMenu(self.menuBar)
        self.menuAutomation.setObjectName(u"menuAutomation")
        self.menuHelp = QMenu(self.menuBar)
        self.menuHelp.setObjectName(u"menuHelp")
        MainWindow.setMenuBar(self.menuBar)

        self.menuBar.addAction(self.menuFile.menuAction())
        self.menuBar.addAction(self.menuDevices.menuAction())
        self.menuBar.addAction(self.menuAcquisition.menuAction())
        self.menuBar.addAction(self.menuAutomation.menuAction())
        self.menuBar.addAction(self.menuHelp.menuAction())
        self.menuFile.addAction(self.actionRestoreLastFile)
        self.menuFile.addAction(self.actionExport)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionQuit)
        self.menuDevices.addAction(self.actionSelectDevices)
        self.menuDevices.addAction(self.actionSendDeviceCommand)
        self.menuAcquisition.addAction(self.actionStartAcquisition)
        self.menuAcquisition.addAction(self.actionStopAcquisition)
        self.menuAcquisition.addSeparator()
        self.menuAutomation.addAction(self.actionManageAutomation)
        self.menuAutomation.addSeparator()
        self.menuAutomation.addAction(self.actionStartAutomation)
        self.menuAutomation.addAction(self.actionStopAutomation)
        self.menuAutomation.addAction(self.actionSkipToNext)
        self.menuHelp.addAction(self.actionAbout)
        self.menuHelp.addAction(self.actionHelp)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MSMS", None))
        self.actionSelectDevices.setText(QCoreApplication.translate("MainWindow", u"select devices", None))
        self.actionManageAutomation.setText(QCoreApplication.translate("MainWindow", u"manage automation", None))
        self.actionExport.setText(QCoreApplication.translate("MainWindow", u"export", None))
        self.actionRestoreLastFile.setText(QCoreApplication.translate("MainWindow", u"restore last file", None))
        self.actionStartAcquisition.setText(QCoreApplication.translate("MainWindow", u"start acquisition", None))
        self.actionStopAcquisition.setText(QCoreApplication.translate("MainWindow", u"stop acquisition", None))
        self.actionSendDeviceCommand.setText(QCoreApplication.translate("MainWindow", u"send device command", None))
        self.actionInterval_0_1s.setText(QCoreApplication.translate("MainWindow", u"0.1 s", None))
        self.actionInterval_0_5s.setText(QCoreApplication.translate("MainWindow", u"0.5 s", None))
        self.actionInterval_1_0s.setText(QCoreApplication.translate("MainWindow", u"1.0 s", None))
        self.actionInterval_2_0s.setText(QCoreApplication.translate("MainWindow", u"2.0 s", None))
        self.actionInterval_5_0s.setText(QCoreApplication.translate("MainWindow", u"5.0 s", None))
        self.actionStartAutomation.setText(QCoreApplication.translate("MainWindow", u"start automation", None))
        self.actionStopAutomation.setText(QCoreApplication.translate("MainWindow", u"stop automation", None))
        self.actionSkipToNext.setText(QCoreApplication.translate("MainWindow", u"skip to next step", None))
        self.actionQuit.setText(QCoreApplication.translate("MainWindow", u"quit", None))
        self.actionAbout.setText(QCoreApplication.translate("MainWindow", u"about", None))
        self.actionHelp.setText(QCoreApplication.translate("MainWindow", u"help", None))
        self.timeValue.setText(QCoreApplication.translate("MainWindow", u"21:37:15", None))
        self.numberValue.setText(QCoreApplication.translate("MainWindow", u"#12345", None))
        self.sampleLabel.setText(QCoreApplication.translate("MainWindow", u"Sample", None))
        self.controlLabel.setText(QCoreApplication.translate("MainWindow", u"Control", None))
        self.sampleValue.setText(QCoreApplication.translate("MainWindow", u"297.12K", None))
        self.controlValue.setText(QCoreApplication.translate("MainWindow", u"300.03K", None))
        self.setPointLabel.setText(QCoreApplication.translate("MainWindow", u"Set point", None))
        self.rampLabel.setText(QCoreApplication.translate("MainWindow", u" Ramp rate", None))
        self.setPointValue.setText(QCoreApplication.translate("MainWindow", u"350.0K", None))
        self.rampValue.setText(QCoreApplication.translate("MainWindow", u"0.1K/s", None))
        self.automationPlanTextEdit.setHtml(QCoreApplication.translate("MainWindow", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'.AppleSystemUIFont'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>", None))
        self.automationPlanTextEdit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Automation status.", None))
        self.commentPlainTextEdit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"You can write CSV header here at any time before the export. Also, you can double click to use a template.", None))
        self.autoFollowCheckBox.setText(QCoreApplication.translate("MainWindow", u"Follow", None))
        self.xAxisPushButton.setText(QCoreApplication.translate("MainWindow", u"X: time", None))
        self.yAxisPushButton.setText(QCoreApplication.translate("MainWindow", u"Y: value", None))
        self.variablesTextEdit.setHtml(QCoreApplication.translate("MainWindow", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'.AppleSystemUIFont'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Interval [s]:</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">3 s</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">AUX0 [V]:</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:"
                        "0; text-indent:0px;\">1.3333e-7</p></body></html>", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menuDevices.setTitle(QCoreApplication.translate("MainWindow", u"Devices", None))
        self.menuAcquisition.setTitle(QCoreApplication.translate("MainWindow", u"Acquisition", None))
        self.menuAutomation.setTitle(QCoreApplication.translate("MainWindow", u"Automation", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindow", u"Help", None))
    # retranslateUi

