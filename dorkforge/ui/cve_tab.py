"""CVE Intel tab — view active CVEs, copy dorks, refresh feed."""

from __future__ import annotations

import json
import urllib.request
import ssl
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem,
    QHeaderView, QPushButton, QMessageBox,
)

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import QApplication

from dorkforge.data.categories import CVE_INTEL

if TYPE_CHECKING:
    from dorkforge.ui.main_window import DorkForgeGUI


class CVEThread(QThread):
    """Background thread for fetching live CVE data."""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def run(self):
        try:
            now = datetime.now(timezone.utc)
            start = now - timedelta(days=30)
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(
                "https://services.nvd.nist.gov/rest/json/cves/2.0"
                f"?pubStartDate={start.strftime('%Y-%m-%dT%H:%M:%S.000')}"
                f"&pubEndDate={now.strftime('%Y-%m-%dT%H:%M:%S.000')}"
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
        layout.setContentsMargins(20, 20, 20, 18)
        layout.setSpacing(14)

        header = QLabel(
            '<span style="font-size:19px; font-weight:750; color:#f0f5fc">Active CVE hunting</span><br>'
            '<span style="color:gray">Double-click a CVE or its dorks to copy</span>'
        )
        header.setWordWrap(True)
        layout.addWidget(header)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["CVE / Detail", "Value"])
        self.tree.setAlternatingRowColors(True)
        self.tree.header().setStretchLastSection(True)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
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
            root = QTreeWidgetItem([cve_name, "Built-in hunt playbook"])
            root.setForeground(0, QColor("#ff8b8b"))
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
        self.tree.clear()
        for entry in cves:
            cve = entry.get("cve", {})
            cve_id = cve.get("id", "Unknown CVE")
            descriptions = cve.get("descriptions", [])
            description = next((d.get("value", "") for d in descriptions if d.get("lang") == "en"), "")
            metrics = cve.get("metrics", {})
            cvss = metrics.get("cvssMetricV31", metrics.get("cvssMetricV30", []))
            score = cvss[0].get("cvssData", {}).get("baseScore", "—") if cvss else "—"
            root = QTreeWidgetItem([cve_id, f"CVSS {score}"])
            root.setForeground(0, QColor("#ff8b8b"))
            font = QFont(); font.setBold(True); root.setFont(0, font)
            root.addChild(QTreeWidgetItem(["Description", description]))
            root.addChild(QTreeWidgetItem(["Source", "NIST National Vulnerability Database"] ))
            self.tree.addTopLevelItem(root)
        self.tree.expandToDepth(0)

    def _on_nvd_error(self, err: str):
        self.main.log_message(f"NVD fetch failed: {err}")
        QMessageBox.warning(self, "NVD Error", f"Could not fetch CVE data:\n{err}")
