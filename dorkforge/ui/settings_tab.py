"""Settings tab — search config, enrichment toggle, proxy, webhooks."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QFormLayout, QCheckBox, QSpinBox, QLabel, QLineEdit
from PyQt6.QtCore import Qt

if TYPE_CHECKING:
    from dorkforge.ui.main_window import DorkForgeGUI


class SettingsTab(QWidget):
    """Settings for search behavior, enrichment, proxy, and webhooks."""

    def __init__(self, main_window: DorkForgeGUI):
        super().__init__()
        self.main = main_window
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        grp = QGroupBox("Search")
        gf = QFormLayout(grp)
        self.pages_spin = QSpinBox()
        self.pages_spin.setRange(1, 50)
        self.pages_spin.setValue(2)
        gf.addRow("Pages per dork:", self.pages_spin)
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(1, 30)
        self.delay_spin.setValue(4)
        gf.addRow("Delay (seconds):", self.delay_spin)
        self.headless_cb = QCheckBox("Headless (no browser window)")
        self.headless_cb.setChecked(True)
        gf.addRow(self.headless_cb)
        layout.addWidget(grp)

        grp2 = QGroupBox("Enrichment")
        gf2 = QFormLayout(grp2)
        self.enrich_cb = QCheckBox("Deep scan results (status, tech, forms, endpoints)")
        gf2.addRow(self.enrich_cb)
        layout.addWidget(grp2)

        grp3 = QGroupBox("Proxy & Webhooks")
        gf3 = QFormLayout(grp3)
        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("http://127.0.0.1:8080")
        gf3.addRow("Proxy URL:", self.proxy_input)
        self.discord_input = QLineEdit()
        self.discord_input.setPlaceholderText("Discord webhook URL")
        gf3.addRow("Discord:", self.discord_input)
        self.slack_input = QLineEdit()
        self.slack_input.setPlaceholderText("Slack webhook URL")
        gf3.addRow("Slack:", self.slack_input)
        layout.addWidget(grp3)

        layout.addStretch()
