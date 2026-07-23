from __future__ import annotations

import csv
from typing import Any

from dorkforge.exporters.base import Exporter
from dorkforge.models.result import DorkResult


class CSVExporter(Exporter):
    extension = "csv"

    def export(self, results: list[DorkResult], path: str) -> str:
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["url", "title", "dork", "status", "tech", "endpoints", "forms", "timestamp"])
            for r in results:
                w.writerow([
                    r.url,
                    r.title,
                    r.dork,
                    r.status,
                    "; ".join(r.tech) if r.tech else "",
                    len(r.endpoints),
                    r.forms,
                    r.timestamp,
                ])
        return path
