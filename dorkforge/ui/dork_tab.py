"""Dork input tab — add dorks, load categories, manage queue."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QFileDialog,
)
from PyQt6.QtCore import Qt
from cloakbrowser import launch

from dorkforge.data.categories import RECON_CATEGORIES, RECON_ALL_DORKS
from dorkforge.engine.dorker import DorkEngine
from dorkforge.engine.enrich import Enricher

if TYPE_CHECKING:
    from dorkforge.ui.main_window import DorkForgeGUI


class DorkTab(QWidget):
    """Tab for entering and managing dork queries."""

    def __init__(self, main_window: DorkForgeGUI):
        super().__init__()
        self.main = main_window
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        top_row = QHBoxLayout()
        self.dork_input = QLineEdit()
        self.dork_input.setPlaceholderText("site:target.com inurl:admin")
        top_row.addWidget(self.dork_input, 1)
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_dork)
        top_row.addWidget(add_btn)
        load_btn = QPushButton("Load File")
        load_btn.clicked.connect(self._load_dork_file)
        top_row.addWidget(load_btn)
        layout.addLayout(top_row)

        self.dork_list = QListWidget()
        self.dork_list.setAlternatingRowColors(True)
        layout.addWidget(QLabel("Queued dorks (checked = active):"))
        layout.addWidget(self.dork_list, 1)

        cat_layout = QHBoxLayout()
        for name in RECON_CATEGORIES:
            btn = QPushButton(name)
            btn.clicked.connect(lambda _, n=name: self._add_category(n))
            cat_layout.addWidget(btn)
        cat_all = QPushButton("All Categories")
        cat_all.clicked.connect(self._add_all_categories)
        cat_layout.addWidget(cat_all)
        rem_btn = QPushButton("Remove Selected")
        rem_btn.clicked.connect(self._remove_selected)
        cat_layout.addWidget(rem_btn)
        run_btn = QPushButton("Run All")
        run_btn.setStyleSheet("background-color: #2ea043; color: white; font-weight: bold; padding: 6px 16px;")
        run_btn.clicked.connect(self._run_all)
        cat_layout.addWidget(run_btn)
        layout.addLayout(cat_layout)

    def _add_dork(self):
        text = self.dork_input.text().strip()
        if text:
            item = QListWidgetItem(text)
            item.setCheckState(Qt.CheckState.Checked)
            self.dork_list.addItem(item)
            self.dork_input.clear()
            self.main.log_message(f"Added dork: {text}")

    def _load_dork_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Dork File")
        if path:
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        item = QListWidgetItem(line)
                        item.setCheckState(Qt.CheckState.Checked)
                        self.dork_list.addItem(item)
            self.main.log_message(f"Loaded {self.dork_list.count()} dorks from {path}")

    def _add_category(self, name):
        dorks = RECON_CATEGORIES[name]
        for dork in dorks:
            item = QListWidgetItem(dork)
            item.setCheckState(Qt.CheckState.Checked)
            self.dork_list.addItem(item)
        self.main.log_message(f"Added category: {name} ({len(dorks)} dorks)")

    def _add_all_categories(self):
        for dork in RECON_ALL_DORKS:
            item = QListWidgetItem(dork)
            item.setCheckState(Qt.CheckState.Checked)
            self.dork_list.addItem(item)
        self.main.log_message(f"Added all categories ({len(RECON_ALL_DORKS)} dorks)")

    def _remove_selected(self):
        for item in self.dork_list.selectedItems():
            self.dork_list.takeItem(self.dork_list.row(item))

    def _run_all(self):
        active_dorks = []
        for i in range(self.dork_list.count()):
            item = self.dork_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                active_dorks.append(item.text())

        if not active_dorks:
            self.main.log_message("No active dorks to run")
            return

        settings = self.main.settings_tab
        engine = DorkEngine(
            headless=settings.headless_cb.isChecked(),
            pages=settings.pages_spin.value(),
            delay=settings.delay_spin.value(),
        )

        self.main.results_tab.clear_results()
        self.main.status(f"Running {len(active_dorks)} dorks...")

        def _run():
            all_results = []
            for i, dork in enumerate(active_dorks):
                self.main.log_message(f"Dork {i+1}/{len(active_dorks)}: {dork[:80]}")
                try:
                    results = engine.search(dork)
                    all_results.extend(results)
                    self.main.log_message(f"  → {len(results)} results")
                except Exception as e:
                    self.main.log_message(f"  ✗ Error: {e}")

            if all_results and settings.enrich_cb.isChecked():
                self.main.log_message(f"Enriching {len(all_results)} results...")
                enricher = Enricher()
                all_results = enricher.enrich(all_results)

            self.main.results_tab.display_results(all_results)
            self.main.status(f"Done — {len(all_results)} results")

        threading.Thread(target=_run, daemon=True).start()
