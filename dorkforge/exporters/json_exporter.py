from __future__ import annotations

import json
from typing import Any

from dorkforge.exporters.base import Exporter
from dorkforge.models.result import DorkResult


class JSONExporter(Exporter):
    extension = "json"

    def export(self, results: list[DorkResult], path: str) -> str:
        data = [r.to_dict() for r in results]
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        return path
