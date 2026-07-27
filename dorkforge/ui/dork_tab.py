"""Dork input tab — add dorks, load categories, manage queue."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QFileDialog, QScrollArea, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal

from dorkforge.data.categories import RECON_CATEGORIES, RECON_ALL_DORKS
from dorkforge.engine.dorker import DorkEngine
from dorkforge.engine.enrich import Enricher
from dorkforge.engine.prober import ProbeEngine

if TYPE_CHECKING:
    from dorkforge.ui.main_window import DorkForgeGUI


class DorkTab(QWidget):
    """Tab for entering and managing dork queries."""

    results_ready = pyqtSignal(object)

    def __init__(self, main_window: DorkForgeGUI):
        super().__init__()
        self.main = main_window
        self._setup_ui()
        self.results_ready.connect(self.main.results_tab.display_results)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 18)
        layout.setSpacing(14)

        intro = QVBoxLayout()
        title = QLabel("Collection plan")
        title.setStyleSheet("font-size: 19px; font-weight: 750; color: #f0f5fc;")
        intro.addWidget(title)
        intro.addWidget(QLabel("Stage approved queries, select an intelligence playbook, and initiate collection."))
        layout.addLayout(intro)

        top_row = QHBoxLayout()
        self.dork_input = QLineEdit()
        self.dork_input.setPlaceholderText("site:target.com inurl:admin")
        top_row.addWidget(self.dork_input, 1)
        add_btn = QPushButton("Add to plan")
        add_btn.setObjectName("primaryButton")
        add_btn.clicked.connect(self._add_dork)
        top_row.addWidget(add_btn)
        load_btn = QPushButton("Import queries")
        load_btn.clicked.connect(self._load_dork_file)
        top_row.addWidget(load_btn)
        layout.addLayout(top_row)

        queue_header = QHBoxLayout()
        queue_label = QLabel("ACTIVE COLLECTION QUEUE")
        queue_label.setObjectName("sectionLabel")
        queue_header.addWidget(queue_label)
        queue_header.addStretch()
        self.queue_count = QLabel("0 queries")
        self.queue_count.setStyleSheet("color: #8ea2bf;")
        queue_header.addWidget(self.queue_count)
        layout.addLayout(queue_header)

        self.dork_list = QListWidget()
        self.dork_list.setAlternatingRowColors(True)
        self.dork_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.dork_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.dork_list.itemChanged.connect(self._update_queue_count)
        layout.addWidget(self.dork_list, 1)

        preset_label = QLabel("INTELLIGENCE PLAYBOOKS")
        preset_label.setObjectName("sectionLabel")
        layout.addWidget(preset_label)
        preset_scroll = QScrollArea()
        preset_scroll.setWidgetResizable(False)
        preset_scroll.setFrameShape(QFrame.Shape.NoFrame)
        preset_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        preset_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        preset_scroll.setFixedHeight(56)
        preset_content = QWidget()
        cat_layout = QHBoxLayout(preset_content)
        cat_layout.setContentsMargins(0, 0, 0, 6)
        cat_layout.setSpacing(8)
        for name in RECON_CATEGORIES:
            btn = QPushButton(name)
            btn.clicked.connect(lambda _, n=name: self._add_category(n))
            cat_layout.addWidget(btn)
        cat_all = QPushButton("Load all playbooks")
        cat_all.clicked.connect(self._add_all_categories)
        cat_layout.addWidget(cat_all)
        cat_layout.addStretch()
        preset_content.adjustSize()
        preset_scroll.setWidget(preset_content)
        layout.addWidget(preset_scroll)

        action_layout = QHBoxLayout()
        action_layout.addStretch()
        rem_btn = QPushButton("Remove selected")
        rem_btn.clicked.connect(self._remove_selected)
        action_layout.addWidget(rem_btn)
        run_btn = QPushButton("Start collection")
        run_btn.setObjectName("primaryButton")
        run_btn.clicked.connect(self._run_all)
        action_layout.addWidget(run_btn)
        probe_btn = QPushButton("PROBE RESULTS")
        probe_btn.setStyleSheet("background-color: #a371f7; color: white; font-weight: bold; padding: 6px 16px;")
        probe_btn.clicked.connect(self._probe_results)
        action_layout.addWidget(probe_btn)
        layout.addLayout(action_layout)

    def _add_dork(self):
        text = self.dork_input.text().strip()
        if text:
            self.add_queries([text])
            self.dork_input.clear()
            self.main.log_message(f"Added dork: {text}")

    def add_queries(self, queries: list[str]):
        """Add unique, enabled queries to the workspace queue."""
        existing = {self.dork_list.item(i).text() for i in range(self.dork_list.count())}
        for query in queries:
            query = query.strip()
            if query and query not in existing:
                item = QListWidgetItem(query)
                item.setCheckState(Qt.CheckState.Checked)
                self.dork_list.addItem(item)
                existing.add(query)
        self._update_queue_count()

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
            self._update_queue_count()

    def _add_category(self, name):
        dorks = RECON_CATEGORIES[name]
        for dork in dorks:
            item = QListWidgetItem(dork)
            item.setCheckState(Qt.CheckState.Checked)
            self.dork_list.addItem(item)
        self.main.log_message(f"Added category: {name} ({len(dorks)} dorks)")
        self._update_queue_count()

    def _add_all_categories(self):
        for dork in RECON_ALL_DORKS:
            item = QListWidgetItem(dork)
            item.setCheckState(Qt.CheckState.Checked)
            self.dork_list.addItem(item)
        self.main.log_message(f"Added all categories ({len(RECON_ALL_DORKS)} dorks)")
        self._update_queue_count()

    def _remove_selected(self):
        for item in self.dork_list.selectedItems():
            self.dork_list.takeItem(self.dork_list.row(item))
        self._update_queue_count()

    def _update_queue_count(self, *_):
        total = self.dork_list.count()
        active = sum(self.dork_list.item(i).checkState() == Qt.CheckState.Checked for i in range(total))
        self.queue_count.setText(f"{active} active · {total} total")

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
            proxy=settings.proxy_input.text().strip() or None,
            scope_domains=self._scope_domains(),
        )

        self.main.results_tab.clear_results()
        self.main.status(f"Running {len(active_dorks)} dorks...")

        def _run():
            all_results = []
            results_by_url = {}
            for i, dork in enumerate(active_dorks):
                self.main.log_message(f"Dork {i+1}/{len(active_dorks)}: {dork[:80]}")
                try:
                    results = engine.search(dork)
                    for result in results:
                        existing = results_by_url.get(result.url)
                        if existing:
                            if result.dork not in existing.dork.split(" | "):
                                existing.dork = f"{existing.dork} | {result.dork}"
                        else:
                            results_by_url[result.url] = result
                            all_results.append(result)
                    self.main.log_message(f"  → {len(results)} verified results")
                except Exception as e:
                    self.main.log_message(f"  ✗ Error: {e}")

            if all_results and settings.enrich_cb.isChecked():
                self.main.log_message(f"Enriching {len(all_results)} results...")
                enricher = Enricher()
                all_results = enricher.enrich(all_results)

            self.results_ready.emit(all_results)
            self.main.status(f"Done — {len(all_results)} results")

        threading.Thread(target=_run, daemon=True).start()

    def _probe_results(self):
        results = self.main.results_tab.results
        if not results:
            self.main.log_message("No results to probe. Run dorks first.")
            return

        settings = self.main.settings_tab
        self.main.status(f"Probing {len(results)} targets with CloakBrowser...")

        def _probe():
            prober = ProbeEngine(
                headless=settings.headless_cb.isChecked(),
                proxy=settings.proxy_input.text().strip() or None,
            )
            all_probes = prober.probe(results)
            interesting = [p for p in all_probes if p.is_interesting]
            self.main.log_message(
                f"Probe complete — {len(all_probes)} checks, "
                f"{len(interesting)} interesting"
            )
            for p in interesting[:20]:
                self.main.log_message(f"  [{p.verdict}] {p.cve} — {p.url}")
            if len(interesting) > 20:
                self.main.log_message(f"  ... and {len(interesting) - 20} more")
            self.main.results_tab.show_probe_results(all_probes)
            self.main.status(f"Probe done — {len(interesting)} interesting")

        threading.Thread(target=_probe, daemon=True).start()

    def _scope_domains(self) -> list[str]:
        """Read the operator's scope once, before the run begins."""
        raw_scope = self.main.results_tab.scope_input.text()
        return [domain.strip().lower() for domain in raw_scope.split(",") if domain.strip()]
