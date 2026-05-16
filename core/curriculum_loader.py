from __future__ import annotations

import json
import threading
from collections import OrderedDict
from pathlib import Path
from typing import Any, Optional

from .curriculum_nodes import CurriculumNode


BASE_DIR = Path(__file__).resolve().parent.parent
CURRICULUM_DIR = BASE_DIR / "data" / "curriculum"
INDEX_PATH = CURRICULUM_DIR / "index.json"
REB_RESOURCES_PATH = BASE_DIR / "data" / "reb_resources.json"

# Navigation files are small and reused while browsing. Lesson files can be
# larger, so only the three most recently used lessons remain in memory.
_MANIFEST_CACHE_LIMIT = 16
_CONTENT_CACHE_LIMIT = 3
_CONTENT_CACHE_BYTES = 4 * 1024 * 1024

_manifest_cache: OrderedDict[str, tuple[int, int, dict[str, Any]]] = OrderedDict()
_content_cache: OrderedDict[str, tuple[int, int, dict[str, Any]]] = OrderedDict()
_content_cache_size = 0
_reb_resources_cache: dict[str, Any] | None = None
_cache_lock = threading.RLock()


class CurriculumDataError(RuntimeError):
    pass


def _safe_json_path(relative_ref: str) -> Path:
    if not relative_ref or not relative_ref.lower().endswith(".json"):
        raise CurriculumDataError(f"Invalid curriculum JSON reference: {relative_ref!r}")

    root = CURRICULUM_DIR.resolve()
    candidate = (CURRICULUM_DIR / relative_ref).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise CurriculumDataError("Curriculum reference escapes the curriculum directory") from exc
    return candidate


def _read_json(relative_ref: str, *, content: bool = False) -> dict[str, Any]:
    global _content_cache_size

    path = _safe_json_path(relative_ref)
    if not path.is_file():
        raise CurriculumDataError(f"Curriculum file is missing: {relative_ref}")

    stat = path.stat()
    cache = _content_cache if content else _manifest_cache
    limit = _CONTENT_CACHE_LIMIT if content else _MANIFEST_CACHE_LIMIT

    with _cache_lock:
        cached = cache.get(relative_ref)
        if cached and cached[0] == stat.st_mtime_ns and cached[1] == stat.st_size:
            cache.move_to_end(relative_ref)
            return cached[2]
        if cached and content:
            _content_cache_size -= cached[1]
        cache.pop(relative_ref, None)

    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise CurriculumDataError(f"Could not read {relative_ref}: {exc}") from exc

    if not isinstance(payload, dict):
        raise CurriculumDataError(f"Curriculum file must contain a JSON object: {relative_ref}")

    with _cache_lock:
        cache[relative_ref] = (stat.st_mtime_ns, stat.st_size, payload)
        cache.move_to_end(relative_ref)
        if content:
            _content_cache_size += stat.st_size

        while len(cache) > limit or (content and _content_cache_size > _CONTENT_CACHE_BYTES):
            _, evicted = cache.popitem(last=False)
            if content:
                _content_cache_size -= evicted[1]

    return payload


def _node_from_record(record: dict[str, Any], parent_path: list[str]) -> CurriculumNode:
    node_id = str(record.get("id", "")).strip()
    name = str(record.get("name", "")).strip()
    node_type = str(record.get("node_type", "")).strip()
    if not node_id or not name or not node_type:
        raise CurriculumDataError("Every manifest node needs id, name, and node_type")

    return CurriculumNode(
        id=node_id,
        name=name,
        node_type=node_type,
        description=str(record.get("description", "")),
        icon=str(record.get("icon", "")),
        accent=str(record.get("accent", "")),
        path=parent_path + [node_id],
        children_ref=str(record.get("children_ref", "")),
        content_ref=str(record.get("content_ref", "")),
        status=str(record.get("status", "ready")),
        metadata=dict(record.get("metadata", {})),
    )


def _nodes_from_document(document: dict[str, Any], parent_path: list[str]) -> list[CurriculumNode]:
    records = document.get("nodes", [])
    if not isinstance(records, list):
        raise CurriculumDataError("Manifest 'nodes' must be an array")
    return [_node_from_record(record, parent_path) for record in records if isinstance(record, dict)]


def get_levels() -> list[CurriculumNode]:
    try:
        document = _read_json("index.json")
        return _nodes_from_document(document, [])
    except CurriculumDataError:
        return []


def get_children(node: CurriculumNode | None) -> list[CurriculumNode]:
    if node is None:
        return get_levels()
    if not node.children_ref:
        return []
    try:
        document = _read_json(node.children_ref)
        metadata = document.get("metadata")
        if isinstance(metadata, dict):
            node.metadata.update(metadata)
        children = _nodes_from_document(document, node.path)
        node.metadata["lesson_titles"] = [
            child.name for child in children if child.node_type == "lesson"
        ]
        return children
    except CurriculumDataError:
        return []


def get_node_by_path(path: list[str]) -> Optional[CurriculumNode]:
    if not path:
        return None

    children = get_levels()
    current: CurriculumNode | None = None
    for expected_id in path:
        current = next((node for node in children if node.id == expected_id), None)
        if current is None:
            return None
        children = get_children(current)
    return current


def get_lesson_content(
    path_or_node: list[str] | CurriculumNode,
) -> dict[str, Any] | None:
    """Load one lesson payload on demand. No other lesson is read.

    Callers that already resolved a lesson node can pass it directly and avoid
    retraversing the manifest path. The UI may continue passing a path.
    """
    node = (
        path_or_node
        if isinstance(path_or_node, CurriculumNode)
        else get_node_by_path(path_or_node)
    )
    if not node or node.node_type != "lesson" or not node.content_ref:
        return None
    try:
        document = _read_json(node.content_ref, content=True)
    except CurriculumDataError:
        return None

    content = document.get("content", document)
    return dict(content) if isinstance(content, dict) else None


def get_unit_metadata(path: list[str]) -> dict[str, Any]:
    node = get_node_by_path(path)
    if not node or node.node_type != "unit" or not node.children_ref:
        return {}
    try:
        document = _read_json(node.children_ref)
    except CurriculumDataError:
        return {}
    metadata = document.get("metadata", {})
    return dict(metadata) if isinstance(metadata, dict) else {}


def get_source_links(path: list[str]) -> dict[str, str]:
    """Return official source links from the selected node or its ancestors.

    This traverses navigation manifests only. It never downloads the source or
    opens lesson content, which keeps remote books fully on-demand.
    """
    links: dict[str, str] = {}
    for index in range(1, len(path) + 1):
        node = get_node_by_path(path[:index])
        if not node:
            break
        for key in ("source_url", "syllabus_url"):
            value = node.metadata.get(key)
            if isinstance(value, str) and value.startswith("https://"):
                links[key] = value
    return links


def clear_content_cache() -> None:
    global _content_cache_size
    with _cache_lock:
        _content_cache.clear()
        _content_cache_size = 0


def cache_stats() -> dict[str, int]:
    with _cache_lock:
        return {
            "manifest_entries": len(_manifest_cache),
            "lesson_entries": len(_content_cache),
            "lesson_bytes": _content_cache_size,
            "manifest_limit": _MANIFEST_CACHE_LIMIT,
            "lesson_limit": _CONTENT_CACHE_LIMIT,
            "lesson_byte_limit": _CONTENT_CACHE_BYTES,
        }


def load_reb_resources() -> dict[str, Any]:
    global _reb_resources_cache
    if _reb_resources_cache is not None:
        return _reb_resources_cache
    if not REB_RESOURCES_PATH.exists():
        _reb_resources_cache = {"levels": []}
        return _reb_resources_cache
    try:
        with REB_RESOURCES_PATH.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        _reb_resources_cache = data if isinstance(data, dict) else {"levels": []}
    except (OSError, json.JSONDecodeError):
        _reb_resources_cache = {"levels": []}
    return _reb_resources_cache


def get_reb_study_order(level_name: str = "") -> list[str]:
    levels = load_reb_resources().get("levels", [])
    if not level_name:
        return levels[0].get("order", []) if levels else []
    key = level_name.strip().lower()
    for entry in levels:
        if str(entry.get("level", "")).lower() == key:
            return list(entry.get("order", []))
    return []


def get_reb_level_summaries() -> list[tuple[str, str, list[str]]]:
    return [
        (
            str(entry.get("level", "")),
            str(entry.get("focus", "")),
            list(entry.get("order", [])),
        )
        for entry in load_reb_resources().get("levels", [])
        if isinstance(entry, dict)
    ]


def get_lesson_context(full_path: list[str]) -> str:
    if not full_path:
        return ""

    labels: list[str] = []
    for index in range(1, len(full_path) + 1):
        node = get_node_by_path(full_path[:index])
        if node:
            label = node.node_type.replace("_", " ").title()
            labels.append(f"{label}: {node.name}")

    lines = [
        "[CURRENT LESSON FOCUS]",
        *labels,
        "",
        "The student is following an official Rwanda curriculum source.",
        "Teach this exact topic and distinguish official source material from added explanation.",
        "Foster critical thinking, problem solving, research, communication, teamwork, and digital literacy.",
    ]
    return "\n".join(lines)
