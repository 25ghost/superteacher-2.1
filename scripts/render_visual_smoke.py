from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_DIR))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt  # noqa: E402
from PyQt6.QtGui import QFont, QPixmap  # noqa: E402
from PyQt6.QtWidgets import QApplication, QGridLayout, QLabel, QVBoxLayout, QWidget  # noqa: E402

from ui import LIGHT, MathDiagramWidget  # noqa: E402


VISUALS = [
    ("Cartesian", "cartesian", {"function": "linear", "m": 1, "c": 1}),
    ("Venn", "venn", {"sets": 2, "values": {"A": "A", "AB": "A∩B", "B": "B"}}),
    ("Circuit", "circuit", {}),
    ("Wave", "wave", {"cycles": 2.5}),
    ("Forces", "force_diagram", {}),
    ("Timeline", "timeline", {"labels": ["Cause", "Event", "Change", "Impact"]}),
    ("Process", "process_flow", {"labels": ["Prepare", "Perform", "Check", "Improve"]}),
    ("Bar chart", "bar_chart", {"labels": ["A", "B", "C", "D"], "values": [4, 8, 6, 10]}),
    ("Concept map", "concept_map", {"center": "Main idea", "nodes": ["Terms", "Method", "Example", "Check"]}),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    app = QApplication.instance() or QApplication([])
    root = QWidget()
    root.setStyleSheet("background: #F6F8FB;")
    grid = QGridLayout(root)
    grid.setContentsMargins(14, 14, 14, 14)
    grid.setHorizontalSpacing(12)
    grid.setVerticalSpacing(12)

    for index, (label_text, visual_type, params) in enumerate(VISUALS):
        cell = QWidget()
        cell.setStyleSheet("background: white; border: 1px solid #D9E2EC; border-radius: 8px;")
        layout = QVBoxLayout(cell)
        layout.setContentsMargins(8, 8, 8, 8)
        title = QLabel(label_text)
        title.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        title.setStyleSheet("color: #14213D; background: transparent; border: none;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        diagram = MathDiagramWidget(LIGHT, visual_type, params)
        diagram.setFixedSize(300, 200)
        layout.addWidget(title)
        layout.addWidget(diagram)
        grid.addWidget(cell, index // 3, index % 3)

    root.setFixedSize(980, 730)
    root.show()
    app.processEvents()
    pixmap = QPixmap(root.size())
    root.render(pixmap)
    if not pixmap.save(str(args.output), "PNG"):
        raise RuntimeError(f"Could not save {args.output}")
    root.close()
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
