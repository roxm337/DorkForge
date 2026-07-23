"""CVE Intel tab — view active CVEs, copy dorks, refresh feed."""

from __future__ import annotations

import json
import urllib.request
import ssl
from typing import TYPE_CHECKING, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem,
    QHeaderView, QPushButton, QMessageBox,
)

from PyQt6.QtGui import QClipboard
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QClipboard

from dorkforge.data.categories import CVE_INTEL

if TYPE_CHECKING:
    from dorkforge.ui.main_window import DorkForgeGUI


class CVEThread(QThread):
    """Background thread for fetching live CVE data."""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def run(self):
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(
                "https://services.nvd.nist.gov/rest/json/cves/2.0"
                "?pubStartDate=2026-07-01T00:00:00.000"
                "&pubEndDate=2026-07-23T00:00:00.000"
                "&cvssV3Severity=CRITICAL",
                headers={"User-Agent": "DorkForge/1.0"},
            )
            with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
                data = json.loads(resp.read().decode())
            cves = data.get("vulnerabilities", [])
            self.finished.emit(cves)
        except Exception as e:
            self.error.emit(str(e))


class CVETab(QWidget):
    """Tab showing CVE intel with copy-to-clipboard on double-click."""

    def __init__(self, main_window: DorkForgeGUI):
        super().__init__()
        self.main = main_window
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        header = QLabel(
            '<b>Active CVE Hunting — July 2026</b><br>'
            '<span style="color:gray">Double-click a CVE or its dorks to copy</span>'
        )
        header.setWordWrap(True)
        layout.addWidget(header)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["CVE / Detail", "Value"])
        self.tree.setAlternatingRowColors(True)
        self.tree.header().setStretchLastSection(True)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.itemDoubleClicked.connect(self._on_double_click)

        self._populate()
        layout.addWidget(self.tree, 1)

        btn_row = QHBoxLayout()
        refresh_btn = QPushButton("Refresh from NVD")
        refresh_btn.clicked.connect(self._refresh_from_nvd)
        btn_row.addWidget(refresh_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _populate(self):
        self.tree.clear()
        for cve_name, info in CVE_INTEL.items():
            root = QTreeWidgetItem([cve_name, ""])
            root.setForeground(0, QColor("#FF4444"))
            font = QFont()
            font.setBold(True)
            root.setFont(0, font)

            severity_colors = {
                "cvss": QColor("#FF6B6B"),
                "type": QColor("#FFA94D"),
                "product": QColor("#69DB7C"),
                "status": QColor("#FFD43B"),
                "patch": QColor("#69DB7C"),
                "detection": QColor("#74C0FC"),
                "poc": QColor("#FFA500"),
                "nuclei": QColor("#FFA500"),
                "dorks": QColor("#88CCFF"),
            }

            for key, val in info.items():
                child = QTreeWidgetItem([key.replace("_", " ").title(), str(val)])
                color = severity_colors.get(key, QColor("#C9D1D9"))
                child.setForeground(0, color)
                child.setForeground(1, color)
                if key in ("poc", "nuclei"):
                    child.setForeground(1, QColor("#88FF88"))
                root.addChild(child)

            self.tree.addTopLevelItem(root)

    def _on_double_click(self, item: QTreeWidgetItem, col: int):
        parent = item.parent()
        if parent:
            key = item.text(0).lower()
            val = item.text(1)
            if "dork" in key and val:
                QApplication.clipboard().setText(val)
                self.main.log_message(f"Copied dorks to clipboard: {val}")
            elif val.startswith(("http://", "https://")):
                QApplication.clipboard().setText(val)
                self.main.log_message(f"Copied URL to clipboard: {val}")
        else:
            cve_info = CVE_INTEL.get(item.text(0))
            if cve_info and "dorks" in cve_info:
                QApplication.clipboard().setText(cve_info["dorks"])
                self.main.log_message(f"Copied dorks for {item.text(0)} to clipboard")

    def _refresh_from_nvd(self):
        self.main.log_message("Fetching live CVEs from NIST NVD API...")
        self.thread = CVEThread()
        self.thread.finished.connect(self._on_nvd_results)
        self.thread.error.connect(self._on_nvd_error)
        self.thread.start()

    def _on_nvd_results(self, cves: list):
        self.main.log_message(f"Fetched {len(cves)} critical CVEs from NVD")
        self._populate()

    def _on_nvd_error(self, err: str):
        self.main.log_message(f"NVD fetch failed: {err}")
        QMessageBox.warning(self, "NVD Error", f"Could not fetch CVE data:\n{err}")



