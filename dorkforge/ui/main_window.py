"""DorkForge main GUI window."""

from __future__ import annotations

import logging
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel,
    QTextEdit, QStatusBar, QTabWidget, QFrame, QPushButton,
)
from PyQt6.QtCore import Qt, pyqtSignal

from dorkforge.ui.dork_tab import DorkTab
from dorkforge.ui.results_tab import ResultsTab
from dorkforge.ui.settings_tab import SettingsTab
from dorkforge.ui.cve_tab import CVETab

logger = logging.getLogger(__name__)


class DorkForgeGUI(QMainWindow):
    """Main application window."""

    log_requested = pyqtSignal(str)
    status_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DorkForge · Intelligence Workspace")
        self.resize(1360, 860)
        self._setup_ui()
        self.log_requested.connect(self._append_log)
        self.status_requested.connect(self._display_status)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(28, 22, 28, 18)
        layout.setSpacing(14)

        header = QFrame()
        header.setObjectName("appHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(22, 16, 22, 16)
        brand = QVBoxLayout()
        brand.setSpacing(2)
        classification = QLabel("AUTHORIZED ASSESSMENT  /  OPERATOR CONSOLE")
        classification.setObjectName("classificationLabel")
        title = QLabel("DORKFORGE")
        title.setObjectName("brandTitle")
        subtitle = QLabel("Search intelligence · asset triage · evidence export")
        subtitle.setObjectName("brandSubtitle")
        brand.addWidget(classification)
        brand.addWidget(title)
        brand.addWidget(subtitle)
        header_layout.addLayout(brand)
        header_layout.addStretch()
        self.activity_label = QLabel("●  COLLECTION STANDBY")
        self.activity_label.setObjectName("activityPill")
        header_layout.addWidget(self.activity_label)
        layout.addWidget(header)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        layout.addWidget(self.tabs, 1)

        self.results_tab = ResultsTab(self)

        self.dork_tab = DorkTab(self)
        self.tabs.addTab(self.dork_tab, "  Operations  ")
        self.tabs.addTab(self.results_tab, "  Findings  ")

        self.settings_tab = SettingsTab(self)
        self.tabs.addTab(self.settings_tab, "  Collection  ")

        self.cve_tab = CVETab(self)
        self.tabs.addTab(self.cve_tab, "  Intel Library  ")

        self.log = QTextEdit()
        self.log.setObjectName("activityLog")
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(112)
        log_title = QLabel("OPERATOR ACTIVITY")
        log_title.setObjectName("sectionLabel")
        layout.addWidget(log_title)
        layout.addWidget(self.log)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Collection standby · Configure scope and queue to begin")

    def log_message(self, msg: str):
        self.log_requested.emit(msg)
        logger.info(msg)

    def _append_log(self, msg: str):
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.append(f"[{ts}] {msg}")

    def status(self, msg: str):
        self.status_requested.emit(msg)

    def _display_status(self, msg: str):
        self.status_bar.showMessage(msg)
        busy = msg.lower().startswith(("running", "fetching", "enriching"))
        self.activity_label.setText("●  COLLECTION ACTIVE" if busy else "●  COLLECTION STANDBY")
        self.activity_label.setProperty("busy", busy)
        self.activity_label.style().unpolish(self.activity_label)
        self.activity_label.style().polish(self.activity_label)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLE)
    window = DorkForgeGUI()
    window.show()
    sys.exit(app.exec())


APP_STYLE = """
QMainWindow, QWidget { background: #101419; color: #d8dee7; font-family: "Avenir Next", Inter, "Helvetica Neue", Arial; font-size: 13px; }
QFrame#appHeader { background: #171d24; border: 1px solid #323d49; border-left: 3px solid #d5a44c; border-radius: 8px; }
QLabel#classificationLabel { color: #d5a44c; font-family: "SF Mono", Menlo, monospace; font-size: 9px; font-weight: 700; letter-spacing: 1.4px; }
QLabel#brandTitle { color: #f2f4f7; font-size: 23px; font-weight: 800; letter-spacing: 4px; }
QLabel#brandSubtitle { color: #92a0af; font-size: 12px; }
QLabel#activityPill { background: #1c2c32; color: #9fd2c0; border: 1px solid #365a58; border-radius: 4px; font-family: "SF Mono", Menlo, monospace; font-size: 10px; font-weight: 700; padding: 7px 10px; letter-spacing: .6px; }
QLabel#activityPill[busy="true"] { background: #362c1d; color: #f0c870; border-color: #756038; }
QLabel#sectionLabel { color: #8795a5; font-family: "SF Mono", Menlo, monospace; font-size: 10px; font-weight: 700; letter-spacing: 1.4px; }
QTabWidget::pane { border: 1px solid #323d49; border-radius: 7px; top: -1px; background: #151a21; }
QTabBar::tab { background: transparent; color: #8996a6; border: 0; border-bottom: 2px solid transparent; padding: 11px 9px; margin-right: 14px; font-weight: 650; }
QTabBar::tab:selected { color: #e5e9ef; border-bottom-color: #d5a44c; }
QTabBar::tab:hover { color: #d8dee7; }
QLineEdit, QSpinBox { background: #0f141a; border: 1px solid #374350; border-radius: 5px; padding: 9px 10px; color: #eef1f5; selection-background-color: #2c6673; }
QLineEdit:focus, QSpinBox:focus { border: 1px solid #72aebb; background: #121a21; }
QPushButton { background: #202831; border: 1px solid #3b4856; border-radius: 5px; color: #d7dee7; padding: 9px 13px; font-weight: 650; }
QPushButton:hover { background: #293541; border-color: #62778b; }
QPushButton:pressed { background: #182029; }
QPushButton#primaryButton { background: #c99743; border-color: #e0b35e; color: #18140d; font-weight: 800; }
QPushButton#primaryButton:hover { background: #e0b35e; border-color: #f1cc7c; }
QGroupBox { background: #181f27; border: 1px solid #35414d; border-radius: 7px; margin-top: 13px; padding: 17px 14px 12px; font-weight: 700; color: #d5dde6; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; color: #b9c5d1; }
QListWidget, QTreeWidget, QTableWidget, QTextEdit { background: #11171d; border: 1px solid #35414d; border-radius: 6px; color: #dce3eb; alternate-background-color: #161e26; }
QListWidget::item, QTreeWidget::item { padding: 7px; border-bottom: 1px solid #202a34; }
QListWidget::item:hover, QTreeWidget::item:hover, QTableWidget::item:hover { background: #1e2b35; }
QListWidget::item:selected, QTreeWidget::item:selected, QTableWidget::item:selected { background: #244a58; color: #ffffff; }
QHeaderView::section { background: #1c252e; color: #aebbc8; border: 0; border-bottom: 1px solid #3a4754; padding: 9px; font-family: "SF Mono", Menlo, monospace; font-size: 10px; font-weight: 700; }
QStatusBar { background: #101419; color: #8593a3; border-top: 1px solid #293440; }
QTextEdit#activityLog { font-family: "SF Mono", Menlo, monospace; color: #a9b7c5; font-size: 11px; padding: 7px; }
QCheckBox { spacing: 8px; padding: 4px; } QCheckBox::indicator { width: 15px; height: 15px; border: 1px solid #526170; border-radius: 3px; background: #11171d; } QCheckBox::indicator:checked { background: #d5a44c; border-color: #e5bd70; }
QScrollBar:vertical { background: #11171d; width: 10px; margin: 4px 1px; } QScrollBar::handle:vertical { background: #3c4b5a; min-height: 28px; border-radius: 4px; } QScrollBar::handle:vertical:hover { background: #586d80; }
QScrollBar:horizontal { background: #11171d; height: 10px; margin: 1px 4px; } QScrollBar::handle:horizontal { background: #3c4b5a; min-width: 28px; border-radius: 4px; } QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
"""


if __name__ == "__main__":
    main()
