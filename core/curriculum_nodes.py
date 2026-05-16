from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CurriculumNode:
    """A small navigation record. Heavy lesson content lives in referenced files."""

    id: str
    name: str
    node_type: str
    description: str = ""
    icon: str = ""
    accent: str = ""
    path: list[str] = field(default_factory=list)
    children_ref: str = ""
    content_ref: str = ""
    status: str = "ready"
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def lessons(self) -> list[str]:
        """Compatibility view used by older UI code."""
        return list(self.metadata.get("lesson_titles", []))
