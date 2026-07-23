"""DorkForge main GUI window."""

from __future__ import annotations

import logging
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QTextEdit, QStatusBar, QTabWidget
from PyQt6.QtCore import Qt

from dorkforge.ui.dork_tab import DorkTab
from dorkforge.ui.results_tab import ResultsTab
from dorkforge.ui.settings_tab import SettingsTab
from dorkforge.ui.cve_tab import CVETab

logger = logging.getLogger(__name__)


class DorkForgeGUI(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DorkForge — Google Dorking & CVE Hunting")
        self.resize(1280, 800)
        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        self.dork_tab = DorkTab(self)
        tabs.addTab(self.dork_tab, "Dorks")

        self.results_tab = ResultsTab(self)
        tabs.addTab(self.results_tab, "Results")

        self.settings_tab = SettingsTab(self)
        tabs.addTab(self.settings_tab, "Settings")

        self.cve_tab = CVETab(self)
        tabs.addTab(self.cve_tab, "CVE Intel")

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(100)
        layout.addWidget(QLabel("Log:"))
        layout.addWidget(self.log)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def log_message(self, msg: str):
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.append(f"[{ts}] {msg}")
        logger.info(msg)

    def status(self, msg: str):
        self.status_bar.showMessage(msg)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = DorkForgeGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
