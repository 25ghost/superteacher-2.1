from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import urlparse


REPO_DIR = Path(__file__).resolve().parent.parent
CURRICULUM_DIR = REPO_DIR / "data" / "curriculum"
ALLOWED_SOURCE_HOSTS = {"elearning.reb.rw", "www.elearning.rtb.gov.rw"}
REQUIRED_LESSON_FIELDS = {
    "objectives",
    "reading",
    "deep_explanation",
    "practice",
    "practice_answers",
    "experiment",
    "assignment",
    "checkbox_answers",
}
SUPPORTED_DIAGRAMS = {
    "angles",
    "api_flow",
    "bar_chart",
    "cartesian",
    "circuit",
    "concept_map",
    "cycle",
    "force_diagram",
    "geometry",
    "number_line",
    "process_flow",
    "timeline",
    "transformation",
    "tree",
    "triangle",
    "unit_circle",
    "venn",
    "wave",
}


def fail(message: str) -> None:
    raise AssertionError(message)


def resolve_reference(reference: str) -> Path:
    candidate = (CURRICULUM_DIR / reference).resolve()
    try:
        candidate.relative_to(CURRICULUM_DIR.resolve())
    except ValueError:
        fail(f"Reference escapes curriculum directory: {reference}")
    if candidate.suffix.lower() != ".json" or not candidate.is_file():
        fail(f"Missing JSON reference: {reference}")
    return candidate


def validate_record(record: dict, origin: Path) -> int:
    for key in ("id", "name", "node_type"):
        if not str(record.get(key, "")).strip():
            fail(f"{origin}: node is missing {key}")

    for key in ("children_ref", "content_ref"):
        reference = record.get(key)
        if reference:
            resolve_reference(str(reference))

    metadata = record.get("metadata", {})
    if metadata and not isinstance(metadata, dict):
        fail(f"{origin}: metadata must be an object")
    for key in ("source_url", "syllabus_url"):
        source_url = metadata.get(key) if isinstance(metadata, dict) else None
        if not source_url:
            continue
        parsed = urlparse(str(source_url))
        if parsed.scheme != "https" or parsed.hostname not in ALLOWED_SOURCE_HOSTS:
            fail(f"{origin}: source URL is not on an approved official host: {source_url}")
    return 1


def validate_all_json() -> tuple[int, int]:
    json_files = sorted(CURRICULUM_DIR.rglob("*.json"))
    node_count = 0
    for path in json_files:
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            fail(f"{path}: invalid JSON: {exc}")
        if not isinstance(document, dict):
            fail(f"{path}: root must be an object")
        nodes = document.get("nodes", [])
        if nodes and not isinstance(nodes, list):
            fail(f"{path}: nodes must be an array")
        for record in nodes:
            if not isinstance(record, dict):
                fail(f"{path}: every node must be an object")
            node_count += validate_record(record, path)
    return len(json_files), node_count


def validate_reachable_lessons() -> tuple[int, dict[str, int]]:
    sys.path.insert(0, str(REPO_DIR))
    from core.curriculum_loader import (  # noqa: PLC0415
        cache_stats,
        clear_content_cache,
        get_children,
        get_levels,
        get_lesson_content,
    )

    clear_content_cache()
    stack = list(get_levels())
    counts: dict[str, int] = {}
    lesson_count = 0
    while stack:
        node = stack.pop()
        counts[node.node_type] = counts.get(node.node_type, 0) + 1
        if node.node_type != "lesson":
            stack.extend(get_children(node))
            continue

        content = get_lesson_content(node)
        if not content:
            fail(f"Lesson content could not be loaded: {'/'.join(node.path)}")
        missing = REQUIRED_LESSON_FIELDS - content.keys()
        if missing:
            fail(f"{'/'.join(node.path)} is missing fields: {sorted(missing)}")
        diagrams = content.get("diagrams", [])
        if not isinstance(diagrams, list):
            fail(f"{'/'.join(node.path)}: diagrams must be an array")
        unsupported = {
            item.get("type")
            for item in diagrams
            if isinstance(item, dict) and item.get("type") not in SUPPORTED_DIAGRAMS
        }
        if unsupported:
            fail(f"{'/'.join(node.path)} uses unsupported diagrams: {sorted(unsupported)}")
        lesson_count += 1

    stats = cache_stats()
    if stats["lesson_entries"] > stats["lesson_limit"]:
        fail(f"Lesson cache exceeded its entry limit: {stats}")
    if stats["lesson_bytes"] > stats["lesson_byte_limit"]:
        fail(f"Lesson cache exceeded its byte limit: {stats}")
    return lesson_count, counts


def main() -> int:
    json_count, manifest_nodes = validate_all_json()
    lesson_count, reachable_counts = validate_reachable_lessons()
    print(
        json.dumps(
            {
                "json_files": json_count,
                "manifest_nodes": manifest_nodes,
                "reachable_nodes": reachable_counts,
                "validated_lessons": lesson_count,
                "status": "ok",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
