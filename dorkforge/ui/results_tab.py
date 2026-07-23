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
    QFileDialog, QMessageBox, QMenu, QAbstractItemView,
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

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Filter:"))
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter results...")
        self.filter_input.textChanged.connect(self._apply_filter)
        filter_row.addWidget(self.filter_input, 1)
        self.scope_input = QLineEdit()
        self.scope_input.setPlaceholderText("Scope domains (comma-sep)")
        self.scope_input.setMaximumWidth(250)
        filter_row.addWidget(self.scope_input)

        clear_btn = QPushButton("Clear")
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
        layout.addWidget(self.table, 1)

        export_row = QHBoxLayout()
        self.count_label = QLabel("0 results")
        export_row.addWidget(self.count_label)
        export_row.addStretch()
        for fmt, label in [("json", "JSON"), ("csv", "CSV"), ("urls", "URLs"), ("html", "HTML Report")]:
            btn = QPushButton(f"Export {label}")
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

        self.count_label.setText(f"{len(results)} results")

    def clear_results(self):
        self.results.clear()
        self.table.setRowCount(0)
        self.count_label.setText("0 results")
        self.main.log_message("Results cleared")

    def _apply_filter(self):
        text = self.filter_input.text().lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

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
        if not self.results:
            QMessageBox.warning(self, "No Data", "No results to export.")
            return
        exporter_cls = EXPORTER_MAP.get(fmt)
        if not exporter_cls:
            return
        default_name = f"dork_results.{exporter_cls.extension}"
        path, _ = QFileDialog.getSaveFileName(self, "Export", default_name)
        if path:
            exporter_cls().export(self.results, path)
            self.main.log_message(f"Exported {len(self.results)} results to {path}")
