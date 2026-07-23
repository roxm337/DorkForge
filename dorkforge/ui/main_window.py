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
        self.setWindowTitle("DorkForge · Recon workspace")
        self.resize(1360, 860)
        self._setup_ui()
        self.log_requested.connect(self._append_log)
        self.status_requested.connect(self._display_status)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 20, 24, 18)
        layout.setSpacing(16)

        header = QFrame()
        header.setObjectName("appHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 14, 20, 14)
        brand = QVBoxLayout()
        title = QLabel("DORKFORGE")
        title.setObjectName("brandTitle")
        subtitle = QLabel("Reconnaissance workspace · search, enrich, triage")
        subtitle.setObjectName("brandSubtitle")
        brand.addWidget(title)
        brand.addWidget(subtitle)
        header_layout.addLayout(brand)
        header_layout.addStretch()
        self.activity_label = QLabel("●  READY")
        self.activity_label.setObjectName("activityPill")
        header_layout.addWidget(self.activity_label)
        layout.addWidget(header)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        layout.addWidget(self.tabs, 1)

        self.results_tab = ResultsTab(self)

        self.dork_tab = DorkTab(self)
        self.tabs.addTab(self.dork_tab, "  Workspace  ")
        self.tabs.addTab(self.results_tab, "  Findings  ")

        self.settings_tab = SettingsTab(self)
        self.tabs.addTab(self.settings_tab, "  Settings  ")

        self.cve_tab = CVETab(self)
        self.tabs.addTab(self.cve_tab, "  CVE Intel  ")

        self.log = QTextEdit()
        self.log.setObjectName("activityLog")
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(112)
        log_title = QLabel("ACTIVITY")
        log_title.setObjectName("sectionLabel")
        layout.addWidget(log_title)
        layout.addWidget(self.log)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready · Configure a search to begin")

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
        self.activity_label.setText("●  IN PROGRESS" if busy else "●  READY")
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
QMainWindow, QWidget { background: #0b1220; color: #d8e2f0; font-family: Inter, "Helvetica Neue", Arial; font-size: 13px; }
QFrame#appHeader { background: #101b2e; border: 1px solid #22324b; border-radius: 12px; }
QLabel#brandTitle { color: #f3f7fc; font-size: 21px; font-weight: 800; letter-spacing: 3px; }
QLabel#brandSubtitle { color: #8ea2bf; font-size: 12px; }
QLabel#activityPill { background: #112b27; color: #62d6ae; border-radius: 12px; font-size: 11px; font-weight: 700; padding: 6px 11px; letter-spacing: 1px; }
QLabel#activityPill[busy="true"] { background: #2c2412; color: #f5c451; }
QLabel#sectionLabel { color: #7990b1; font-size: 10px; font-weight: 800; letter-spacing: 1.5px; }
QTabWidget::pane { border: 1px solid #22324b; border-radius: 10px; top: -1px; background: #0f192a; }
QTabBar::tab { background: transparent; color: #8295b2; border: 0; border-bottom: 2px solid transparent; padding: 11px 8px; margin-right: 12px; font-weight: 700; }
QTabBar::tab:selected { color: #7de0ba; border-bottom-color: #42c995; }
QTabBar::tab:hover { color: #d8e2f0; }
QLineEdit, QSpinBox { background: #0b1423; border: 1px solid #2a3b57; border-radius: 7px; padding: 9px 10px; color: #edf4ff; selection-background-color: #1c705b; }
QLineEdit:focus, QSpinBox:focus { border: 1px solid #4bcb9b; }
QPushButton { background: #17243a; border: 1px solid #2b405e; border-radius: 7px; color: #d9e4f3; padding: 9px 13px; font-weight: 650; }
QPushButton:hover { background: #213452; border-color: #41658e; }
QPushButton:pressed { background: #101a2b; }
QPushButton#primaryButton { background: #30ae80; border-color: #42cb9a; color: #071610; font-weight: 800; }
QPushButton#primaryButton:hover { background: #45c997; }
QGroupBox { background: #111d30; border: 1px solid #253851; border-radius: 10px; margin-top: 13px; padding: 16px 14px 12px; font-weight: 750; color: #b9c8dc; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; color: #79dcb7; }
QListWidget, QTreeWidget, QTableWidget, QTextEdit { background: #0b1423; border: 1px solid #263951; border-radius: 8px; color: #dce7f5; alternate-background-color: #0f1b2d; }
QListWidget::item, QTreeWidget::item { padding: 7px; border-bottom: 1px solid #16243a; }
QListWidget::item:selected, QTreeWidget::item:selected, QTableWidget::item:selected { background: #1a4c45; color: #ffffff; }
QHeaderView::section { background: #15233a; color: #93a9c6; border: 0; border-bottom: 1px solid #2a3c57; padding: 9px; font-weight: 800; }
QStatusBar { background: #0b1220; color: #7d91ad; border-top: 1px solid #1c2b43; }
QTextEdit#activityLog { font-family: "SF Mono", Menlo, monospace; color: #9fb3cc; font-size: 11px; padding: 7px; }
QCheckBox { spacing: 8px; padding: 4px; } QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #3a506f; border-radius: 4px; background: #0b1423; } QCheckBox::indicator:checked { background: #37bd8d; border-color: #37bd8d; }
QScrollBar:vertical { background: #0b1423; width: 10px; margin: 4px 1px; } QScrollBar::handle:vertical { background: #314766; min-height: 28px; border-radius: 5px; } QScrollBar::handle:vertical:hover { background: #4b6b94; }
QScrollBar:horizontal { background: #0b1423; height: 10px; margin: 1px 4px; } QScrollBar::handle:horizontal { background: #314766; min-width: 28px; border-radius: 5px; } QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
"""


if __name__ == "__main__":
    main()
