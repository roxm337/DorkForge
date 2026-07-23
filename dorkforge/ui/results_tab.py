"""Results tab — table view, filtering, export, context menu."""

from __future__ import annotations

import csv
import json
import urllib.parse
import webbrowser
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QFileDialog, QMessageBox, QMenu, QAbstractItemView, QApplication,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush, QClipboard, QAction

from dorkforge.models.result import DorkResult
from dorkforge.exporters import EXPORTER_MAP

if TYPE_CHECKING:
    from dorkforge.ui.main_window import DorkForgeGUI


class ResultsTab(QWidget):
    """Tab displaying dork results with filtering and export."""

    def __init__(self, main_window: DorkForgeGUI):
        super().__init__()
        self.main = main_window
        self.results: list[DorkResult] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 18)
        layout.setSpacing(14)

        heading = QHBoxLayout()
        title_block = QVBoxLayout()
        title = QLabel("Findings")
        title.setStyleSheet("font-size: 19px; font-weight: 750; color: #f0f5fc;")
        title_block.addWidget(title)
        title_block.addWidget(QLabel("Review, scope, and export the evidence collected by your active queue."))
        heading.addLayout(title_block)
        heading.addStretch()
        layout.addLayout(heading)

        filter_row = QHBoxLayout()
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Search URL, title, technology, or dork…")
        self.filter_input.textChanged.connect(self._apply_filter)
        filter_row.addWidget(self.filter_input, 1)
        self.scope_input = QLineEdit()
        self.scope_input.setPlaceholderText("Scope domains (comma-separated)")
        self.scope_input.setMaximumWidth(250)
        self.scope_input.textChanged.connect(self._apply_filter)
        filter_row.addWidget(self.scope_input)

        clear_btn = QPushButton("Clear findings")
        clear_btn.clicked.connect(self.clear_results)
        filter_row.addWidget(clear_btn)
        layout.addLayout(filter_row)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["URL", "Title", "Dork", "Status", "Tech", "Endpoints", "Forms"])
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._table_context_menu)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(self.table, 1)

        export_row = QHBoxLayout()
        self.count_label = QLabel("0 findings")
        self.count_label.setStyleSheet("font-weight: 700; color: #7de0ba;")
        export_row.addWidget(self.count_label)
        export_row.addStretch()
        for fmt, label in [("json", "JSON"), ("csv", "CSV"), ("urls", "URLs"), ("html", "HTML Report")]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, f=fmt: self._export(f))
            export_row.addWidget(btn)
        layout.addLayout(export_row)

    def display_results(self, results: list[DorkResult]):
        self.results = results
        self.table.setRowCount(len(results))
        for row, r in enumerate(results):
            self.table.setItem(row, 0, QTableWidgetItem(r.url))
            self.table.setItem(row, 1, QTableWidgetItem(r.title[:100] if r.title else ""))
            self.table.setItem(row, 2, QTableWidgetItem(r.dork))
            status_item = QTableWidgetItem(str(r.status))
            if r.status:
                color = {2: QColor("#3fb950"), 3: QColor("#d29922"), 4: QColor("#f85149"), 5: QColor("#f85149")}.get(
                    r.status // 100, QColor("#8b949e")
                )
                status_item.setForeground(color)
            self.table.setItem(row, 3, status_item)
            tech_str = ", ".join(r.tech[:5]) if r.tech else ""
            self.table.setItem(row, 4, QTableWidgetItem(tech_str))
            self.table.setItem(row, 5, QTableWidgetItem(str(len(r.endpoints))))
            self.table.setItem(row, 6, QTableWidgetItem(str(r.forms)))

        self.count_label.setText(f"{len(results)} findings")

    def clear_results(self):
        self.results.clear()
        self.table.setRowCount(0)
        self.count_label.setText("0 findings")
        self.main.log_message("Results cleared")

    def _apply_filter(self):
        for row, result in enumerate(self.results):
            self.table.setRowHidden(row, not self._matches_active_filters(result))

    def _matches_active_filters(self, result: DorkResult) -> bool:
        text = self.filter_input.text().lower().strip()
        domains = [domain.strip().lower() for domain in self.scope_input.text().split(",") if domain.strip()]
        haystack = " ".join((result.url, result.title, result.dork, " ".join(result.tech))).lower()
        return (not text or text in haystack) and (
            not domains or any(self._domain_in_scope(urllib.parse.urlparse(result.url).hostname or "", domain) for domain in domains)
        )

    @staticmethod
    def _domain_in_scope(hostname: str, scope: str) -> bool:
        scope = scope.lower().strip().lstrip(".")
        hostname = hostname.lower().strip(".")
        return hostname == scope or hostname.endswith(f".{scope}")

    def _visible_results(self) -> list[DorkResult]:
        return [result for result in self.results if self._matches_active_filters(result)]

    def _table_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item:
            return
        row = item.row()
        url = self.table.item(row, 0).text()
        menu = QMenu()
        copy_url = menu.addAction("Copy URL")
        copy_all = menu.addAction("Copy All URLs")
        menu.addSeparator()
        open_browser = menu.addAction("Open in Browser")
        menu.addSeparator()
        set_scope = menu.addAction("Add Domain to Scope")
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if action == copy_url:
            QApplication.clipboard().setText(url)
        elif action == copy_all:
            urls = "\n".join(self.table.item(r, 0).text() for r in range(self.table.rowCount()))
            QApplication.clipboard().setText(urls)
        elif action == open_browser:
            webbrowser.open(url)
        elif action == set_scope:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc
            current = self.scope_input.text()
            if domain not in current:
                self.scope_input.setText((current + ", " + domain).strip(", "))

    def _export(self, fmt: str):
        results = self._visible_results()
        if not results:
            QMessageBox.warning(self, "No Data", "No results to export.")
            return
        exporter_cls = EXPORTER_MAP.get(fmt)
        if not exporter_cls:
            return
        default_name = f"dork_results.{exporter_cls.extension}"
        path, _ = QFileDialog.getSaveFileName(self, "Export", default_name)
        if path:
            exporter_cls().export(results, path)
            self.main.log_message(f"Exported {len(results)} filtered results to {path}")
