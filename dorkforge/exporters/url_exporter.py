from __future__ import annotations

from dorkforge.exporters.base import Exporter
from dorkforge.models.result import DorkResult


class URLExporter(Exporter):
    extension = "txt"

    def export(self, results: list[DorkResult], path: str) -> str:
        with open(path, "w") as f:
            for r in results:
                f.write(r.url + "\n")
        return path
