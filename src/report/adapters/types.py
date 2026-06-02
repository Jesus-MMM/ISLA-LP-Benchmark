from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ReportData:
    variables: dict[str, Any] = field(default_factory=dict)
    tables: dict[str, tuple[list[str], list[list[str]]]] = field(default_factory=dict)
    images: dict[str, str] = field(default_factory=dict)
