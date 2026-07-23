from __future__ import annotations

import dataclasses
import json
from datetime import datetime
from typing import Any


@dataclasses.dataclass
class DorkResult:
    url: str
    title: str = ""
    dork: str = ""
    status: int = 0
    tech: list[str] = dataclasses.field(default_factory=list)
    endpoints: list[str] = dataclasses.field(default_factory=list)
    forms: int = 0
    page: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> DorkResult:
        return cls(**{k: v for k, v in d.items() if k in {f.name for f in dataclasses.fields(cls)}})

    @property
    def domain(self) -> str:
        from urllib.parse import urlparse
        return urlparse(self.url).netloc
