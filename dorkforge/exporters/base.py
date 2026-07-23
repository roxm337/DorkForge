from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from dorkforge.models.result import DorkResult


class Exporter(ABC):
    """Base class for all exporters."""

    extension: str = ""

    @abstractmethod
    def export(self, results: list[DorkResult], path: str) -> str:
        """Export results to file. Returns the path written."""
        ...
