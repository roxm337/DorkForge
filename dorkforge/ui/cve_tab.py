"""CVE Intel tab — view active CVEs, copy dorks, refresh feed."""

from __future__ import annotations

import json
import urllib.request
import ssl
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem,
    QHeaderView, QPushButton, QMessageBox, QApplication, QDialog, QFormLayout,
    QLineEdit, QTextEdit, QDialogButtonBox,
)

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont
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


class CVEEditorDialog(QDialog):
    """Focused editor for a single CVE hunt playbook."""

    FIELDS = (
        ("cvss", "CVSS"), ("type", "Vulnerability type"), ("product", "Affected product"),
        ("status", "Status"), ("patch", "Patch guidance"), ("detection", "Detection notes"),
        ("poc", "PoC / reference"), ("nuclei", "Nuclei template"), ("notes", "Operator notes"),
    )

    def __init__(self, parent=None, name: str = "", info: dict[str, str] | None = None):
        super().__init__(parent)
        self.setWindowTitle("Add CVE playbook" if not name else "Edit CVE playbook")
        self.setMinimumWidth(620)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name_input = QLineEdit(name)
        self.name_input.setPlaceholderText("CVE-YYYY-NNNNN (Product)")
        form.addRow("Playbook name", self.name_input)
        self.inputs: dict[str, QLineEdit] = {}
        info = info or {}
        for key, label in self.FIELDS:
            field = QLineEdit(info.get(key, ""))
            self.inputs[key] = field
            form.addRow(label, field)
        layout.addLayout(form)
        layout.addWidget(QLabel("Dorks — one query per line"))
        self.dorks_input = QTextEdit(info.get("dorks", "").replace(" | ", "\n"))
        self.dorks_input.setPlaceholderText('inurl:/example\nintitle:"Product" "login"')
        self.dorks_input.setMinimumHeight(130)
        layout.addWidget(self.dorks_input)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def data(self) -> tuple[str, dict[str, str]]:
        name = self.name_input.text().strip()
        info = {key: field.text().strip() for key, field in self.inputs.items() if field.text().strip()}
        dorks = [line.strip() for line in self.dorks_input.toPlainText().splitlines() if line.strip()]
        info["dorks"] = " | ".join(dorks)
        return name, info


class CVETab(QWidget):
    """Tab showing CVE intel with copy-to-clipboard on double-click."""

    def __init__(self, main_window: DorkForgeGUI):
        super().__init__()
        self.main = main_window
        self.storage_path = Path.home() / ".dorkforge" / "cve_playbooks.json"
        self.cve_data, self.deleted_names = self._load_playbooks()
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
        add_btn = QPushButton("Add playbook")
        add_btn.setObjectName("primaryButton")
        add_btn.clicked.connect(self._add_playbook)
        btn_row.addWidget(add_btn)
        edit_btn = QPushButton("Edit selected")
        edit_btn.clicked.connect(self._edit_selected)
        btn_row.addWidget(edit_btn)
        delete_btn = QPushButton("Delete selected")
        delete_btn.clicked.connect(self._delete_selected)
        btn_row.addWidget(delete_btn)
        queue_btn = QPushButton("Add dorks to queue")
        queue_btn.clicked.connect(self._add_selected_dorks_to_queue)
        btn_row.addWidget(queue_btn)
        btn_row.addStretch()
        playbooks_btn = QPushButton("My playbooks")
        playbooks_btn.clicked.connect(self._populate)
        btn_row.addWidget(playbooks_btn)
        refresh_btn = QPushButton("Refresh from NVD")
        refresh_btn.clicked.connect(self._refresh_from_nvd)
        btn_row.addWidget(refresh_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _populate(self):
        self.tree.clear()
        for cve_name, info in self.cve_data.items():
            root = QTreeWidgetItem([cve_name, "Hunt playbook"])
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

    def _load_playbooks(self) -> tuple[dict[str, dict[str, str]], set[str]]:
        playbooks = {name: dict(info) for name, info in CVE_INTEL.items()}
        deleted: set[str] = set()
        try:
            saved = json.loads(self.storage_path.read_text(encoding="utf-8"))
            deleted = set(saved.get("deleted", []))
            playbooks.update(saved.get("playbooks", {}))
            for name in deleted:
                playbooks.pop(name, None)
        except FileNotFoundError:
            pass
        except (OSError, json.JSONDecodeError) as error:
            self.main.log_message(f"Could not load saved CVE playbooks: {error}")
        return playbooks, deleted

    def _save_playbooks(self):
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {"playbooks": self.cve_data, "deleted": sorted(self.deleted_names)}
            self.storage_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        except OSError as error:
            QMessageBox.warning(self, "Could not save playbooks", str(error))
            return False
        return True

    def _selected_playbook_name(self) -> str | None:
        item = self.tree.currentItem()
        if not item:
            return None
        return item.parent().text(0) if item.parent() else item.text(0)

    def _add_playbook(self):
        dialog = CVEEditorDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, info = dialog.data()
            if not name:
                QMessageBox.warning(self, "Playbook name required", "Give this CVE playbook a clear name.")
                return
            if name in self.cve_data:
                QMessageBox.warning(self, "Playbook exists", "Use Edit selected to change an existing playbook.")
                return
            self.cve_data[name] = info
            self.deleted_names.discard(name)
            if self._save_playbooks():
                self._populate()
                self.main.log_message(f"Added CVE playbook: {name}")

    def _edit_selected(self):
        name = self._selected_playbook_name()
        if not name or name not in self.cve_data:
            QMessageBox.information(self, "Select a playbook", "Select a CVE playbook to edit.")
            return
        dialog = CVEEditorDialog(self, name, self.cve_data[name])
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_name, info = dialog.data()
            if not new_name:
                QMessageBox.warning(self, "Playbook name required", "Give this CVE playbook a clear name.")
                return
            if new_name != name and new_name in self.cve_data:
                QMessageBox.warning(self, "Playbook exists", "Choose a different name or edit that playbook instead.")
                return
            self.cve_data.pop(name)
            self.cve_data[new_name] = info
            self.deleted_names.discard(new_name)
            if name in CVE_INTEL and name != new_name:
                self.deleted_names.add(name)
            if self._save_playbooks():
                self._populate()
                self.main.log_message(f"Updated CVE playbook: {new_name}")

    def _delete_selected(self):
        name = self._selected_playbook_name()
        if not name or name not in self.cve_data:
            QMessageBox.information(self, "Select a playbook", "Select a CVE playbook to delete.")
            return
        confirm = QMessageBox.question(self, "Delete playbook", f'Delete "{name}"?')
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.cve_data.pop(name)
        if name in CVE_INTEL:
            self.deleted_names.add(name)
        if self._save_playbooks():
            self._populate()
            self.main.log_message(f"Deleted CVE playbook: {name}")

    def _add_selected_dorks_to_queue(self):
        name = self._selected_playbook_name()
        info = self.cve_data.get(name or "", {})
        dorks = [dork.strip() for dork in info.get("dorks", "").split("|") if dork.strip()]
        if not dorks:
            QMessageBox.information(self, "No dorks", "The selected playbook has no dorks to add.")
            return
        self.main.dork_tab.add_queries(dorks)
        self.main.tabs.setCurrentWidget(self.main.dork_tab)
        self.main.log_message(f"Added {len(dorks)} dorks from {name} to the queue")

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
            cve_info = self.cve_data.get(item.text(0))
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
