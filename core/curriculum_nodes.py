from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class CurriculumNode:
    id: str
    name: str
    node_type: str
    description: str = ""
    icon: str = ""
    accent: str = ""
    children: list[CurriculumNode] = field(default_factory=list)
    lessons: list[str] = field(default_factory=list)
    path: list[str] = field(default_factory=list)
