from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_DIR))

from core.lesson_visuals import infer_lesson_diagrams  # noqa: E402


LESSON_ROOT = REPO_DIR / "data" / "curriculum" / "books" / "full"


def main() -> int:
    changed = 0
    diagram_counts: dict[str, int] = {}
    for path in sorted(LESSON_ROOT.rglob("lessons/*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        content = document.get("content")
        if not isinstance(content, dict):
            continue
        title = str(content.get("title", path.stem))
        parts = path.relative_to(LESSON_ROOT).parts
        subject = parts[2] if len(parts) >= 3 else ""
        diagrams = infer_lesson_diagrams(title, subject)
        content["diagrams"] = diagrams
        for diagram in diagrams:
            diagram_type = str(diagram.get("type", "unknown"))
            diagram_counts[diagram_type] = diagram_counts.get(diagram_type, 0) + 1
        path.write_text(
            json.dumps(document, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        changed += 1

    print(json.dumps(
        {
            "status": "ok",
            "lessons_updated": changed,
            "diagram_counts": dict(sorted(diagram_counts.items())),
        },
        indent=2,
        sort_keys=True,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
