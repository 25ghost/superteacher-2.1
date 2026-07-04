from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
from .curriculum_nodes import CurriculumNode


BASE_DIR = Path(__file__).resolve().parent.parent
CURRICULUM_DIR = BASE_DIR / "data" / "curriculum"
REB_RESOURCES_PATH = BASE_DIR / "data" / "reb_resources.json"

_cache: dict[str, dict] = {}
_reb_resources_cache: dict | None = None


def _load_json(file_key: str) -> dict:
    if file_key in _cache:
        return _cache[file_key]

    path = CURRICULUM_DIR / f"{file_key}.json"
    if not path.exists():
        return {"sub_levels": []}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    _cache[file_key] = data
    return data


def get_levels() -> list[CurriculumNode]:
    index_path = CURRICULUM_DIR / "index.json"
    if not index_path.exists():
        return []
    with open(index_path, "r", encoding="utf-8") as f:
        items = json.load(f)
    return [
        CurriculumNode(
            id=item["key"],
            name=item["name"],
            node_type="level",
            description=item.get("description", ""),
            icon=item.get("icon", ""),
            accent=item.get("accent", ""),
            path=[item["key"]],
        )
        for item in items
    ]


def get_children(node: CurriculumNode) -> list[CurriculumNode]:
    if node.node_type == "level":
        return _get_sublevels(node.id, node.path)
    elif node.node_type == "sublevel":
        return _get_subjects_for_sublevel(node.id, node.path)
    elif node.node_type == "alevel_category":
        return _get_combinations_for_category(node.id, node.path)
    elif node.node_type == "tvet_category":
        return _get_trade_groups_for_category(node.id, node.path)
    elif node.node_type == "combination":
        return _get_combination_subjects(node.id, node.path)
    elif node.node_type == "trade_group":
        return _get_trades_in_group(node.id, node.path)
    elif node.node_type == "trade":
        return _get_units_for_trade(node.id, node.path)
    elif node.node_type == "subject":
        return _get_units_for_subject(node.id, node.path)
    return []


def _get_sublevels(level_key: str, parent_path: list[str]) -> list[CurriculumNode]:
    data = _load_json(level_key)
    sub_levels = data.get("sub_levels", [])
    result = []
    for i, sl in enumerate(sub_levels):
        key = f"{level_key}_{i}"
        if "combinations" in sl:
            node_type = "alevel_category"
        elif "trade_groups" in sl:
            node_type = "tvet_category"
        else:
            node_type = "sublevel"
        result.append(CurriculumNode(
            id=key,
            name=sl.get("name", ""),
            node_type=node_type,
            description=sl.get("description", ""),
            path=parent_path + [key],
        ))
    return result


def _get_combinations_for_category(cat_id: str, parent_path: list[str]) -> list[CurriculumNode]:
    for key in ["primary", "high_school", "college"]:
        data = _load_json(key)
        for sl in data.get("sub_levels", []):
            sl_idx = data["sub_levels"].index(sl)
            sl_key = f"{key}_{sl_idx}"
            if sl_key != cat_id:
                continue
            result = []
            for ci, combo in enumerate(sl.get("combinations", [])):
                cid = f"{key}_{sl_idx}_combo_{ci}"
                result.append(CurriculumNode(
                    id=cid,
                    name=combo.get("name", ""),
                    node_type="combination",
                    description=combo.get("description", ""),
                    path=parent_path + [cid],
                ))
            return result
    return []


def _get_trade_groups_for_category(cat_id: str, parent_path: list[str]) -> list[CurriculumNode]:
    for key in ["primary", "high_school", "college"]:
        data = _load_json(key)
        for sl in data.get("sub_levels", []):
            sl_idx = data["sub_levels"].index(sl)
            sl_key = f"{key}_{sl_idx}"
            if sl_key != cat_id:
                continue
            result = []
            for ti, tg in enumerate(sl.get("trade_groups", [])):
                tid = f"{key}_{sl_idx}_tg_{ti}"
                result.append(CurriculumNode(
                    id=tid,
                    name=tg.get("name", ""),
                    node_type="trade_group",
                    description=tg.get("description", ""),
                    path=parent_path + [tid],
                ))
            return result
    return []


def _get_subjects_for_sublevel(id: str, parent_path: list[str]) -> list[CurriculumNode]:
    subjects_data = _find_subjects(id)
    result = []
    for s in subjects_data:
        result.append(CurriculumNode(
            id=s.get("name", "").lower().replace(" ", "_").replace("&", "and").replace("(", "").replace(")", ""),
            name=s.get("name", ""),
            node_type="subject",
            description=s.get("description", ""),
            path=parent_path + [s.get("name", "")],
        ))
    return result


def _get_combination_subjects(id: str, parent_path: list[str]) -> list[CurriculumNode]:
    combo = _find_combination(id)
    if not combo:
        return []
    result = []
    for s in combo.get("subjects", []):
        result.append(CurriculumNode(
            id=s.get("name", "").lower().replace(" ", "_"),
            name=s.get("name", ""),
            node_type="subject",
            description=s.get("description", ""),
            path=parent_path + [s.get("name", "")],
        ))
    return result


def _get_trades_in_group(id: str, parent_path: list[str]) -> list[CurriculumNode]:
    group = _find_trade_group(id)
    if not group:
        return []
    result = []
    for t in group.get("trades", []):
        result.append(CurriculumNode(
            id=t.get("name", "").lower().replace(" ", "_"),
            name=t.get("name", ""),
            node_type="trade",
            description=t.get("description", ""),
            path=parent_path + [t.get("name", "")],
        ))
    return result


def _get_units_for_trade(id: str, parent_path: list[str]) -> list[CurriculumNode]:
    trade = _find_trade_by_id(id)
    if not trade:
        return []
    result = []
    for u in trade.get("units", []):
        result.append(CurriculumNode(
            id=u.get("name", "").lower().replace(" ", "_"),
            name=u.get("name", ""),
            node_type="unit",
            lessons=u.get("lessons", []),
            path=parent_path + [u.get("name", "")],
        ))
    return result


def _get_units_for_subject(id: str, parent_path: list[str]) -> list[CurriculumNode]:
    subject = _find_subject_by_id(id, parent_path)
    if not subject:
        return []
    result = []
    for u in subject.get("units", []):
        result.append(CurriculumNode(
            id=u.get("name", "").lower().replace(" ", "_"),
            name=u.get("name", ""),
            node_type="unit",
            lessons=u.get("lessons", []),
            icon="",
            path=parent_path + [u.get("name", "")],
        ))
    return result


def get_node_by_path(path: list[str]) -> Optional[CurriculumNode]:
    if not path:
        return None
    levels = get_levels()
    for l in levels:
        if l.id == path[0]:
            if len(path) == 1:
                return l
            node = _descend(l, path[1:])
            if node:
                return node
    return None


def _match_node(node: CurriculumNode, name_or_id: str) -> bool:
    return node.id == name_or_id or node.name == name_or_id


def _descend(node: CurriculumNode, remaining: list[str]) -> Optional[CurriculumNode]:
    children = get_children(node)
    for c in children:
        if _match_node(c, remaining[0]):
            if len(remaining) == 1:
                return c
            result = _descend(c, remaining[1:])
            if result:
                return result
    return None


def load_reb_resources() -> dict:
    global _reb_resources_cache
    if _reb_resources_cache is not None:
        return _reb_resources_cache
    if not REB_RESOURCES_PATH.exists():
        _reb_resources_cache = {"levels": []}
        return _reb_resources_cache
    try:
        with open(REB_RESOURCES_PATH, "r", encoding="utf-8") as f:
            _reb_resources_cache = json.load(f)
    except Exception:
        _reb_resources_cache = {"levels": []}
    return _reb_resources_cache


def get_reb_study_order(level_name: str = "") -> list[str]:
    """Return REB daily subject order for a level (e.g. 'Primary 5', 'Senior 2')."""
    data = load_reb_resources()
    levels = data.get("levels", [])
    if not level_name:
        return levels[0].get("order", []) if levels else []
    key = level_name.strip().lower()
    for entry in levels:
        if entry.get("level", "").lower() == key:
            return entry.get("order", [])
    for entry in levels:
        if key in entry.get("level", "").lower():
            return entry.get("order", [])
    return []


def get_reb_level_summaries() -> list[tuple[str, str, list[str]]]:
    """(level, focus, subject_order) for UI study-plan panels."""
    data = load_reb_resources()
    out = []
    for entry in data.get("levels", []):
        out.append((
            entry.get("level", ""),
            entry.get("focus", ""),
            entry.get("order", []),
        ))
    return out


def get_lesson_context(full_path: list[str]) -> str:
    if not full_path:
        return ""

    LABEL_MAP = {
        "level": "Level",
        "sublevel": "Program",
        "alevel_category": "Category",
        "tvet_category": "Category",
        "combination": "Combination",
        "trade_group": "Trade Group",
        "trade": "Trade",
        "subject": "Subject",
        "unit": "Unit",
    }

    labels: list[tuple[str, str]] = []
    leaf_subject_name = ""
    last_unit_node = None

    for i in range(len(full_path)):
        node = get_node_by_path(full_path[: i + 1])
        if node:
            label = LABEL_MAP.get(node.node_type, node.node_type.replace("_", " ").title())
            labels.append((label, node.name))
            if node.node_type in ("subject", "trade"):
                leaf_subject_name = node.name
            if node.node_type == "unit":
                last_unit_node = node
        elif last_unit_node and last_unit_node.lessons and full_path[i] in last_unit_node.lessons:
            labels.append(("Lesson", full_path[i]))
            break
        else:
            labels.append(("Path", full_path[i]))

    lines = ["[CURRENT LESSON FOCUS]"]
    for label, value in labels:
        lines.append(f"{label}: {value}")

    lines.append("")
    study_order = get_reb_study_order()
    if study_order:
        lines.append("--- REB RECOMMENDED DAILY SUBJECT ORDER (P4–S6) ---")
        lines.append(" → ".join(study_order[:8]))

    lines.append("")
    lines.append("The student is following the Rwanda Education Board (REB) curriculum.")
    lines.append("Teach this exact topic. Focus ONLY on this. Do not deviate to unrelated subjects.")
    lines.append("If asked about anything outside this topic, gently redirect back.")

    lines.append("")
    lines.append("--- REB CROSS-CUTTING THEMES ---")
    lines.append("Integrate these naturally when relevant:")
    lines.append("* Peace and Values Education \u2014 promote harmony, respect and empathy")
    lines.append("* Environment and Sustainability \u2014 encourage environmental awareness and action")
    lines.append("* Gender \u2014 promote equality and equal opportunities for all")
    lines.append("* Financial Education \u2014 teach money management and financial literacy where relevant")
    lines.append("* Inclusive Education \u2014 adapt explanations for all learning needs")
    lines.append("* ICT Integration \u2014 use technology to enhance learning")
    lines.append("* Standardization Culture \u2014 emphasize quality, accuracy and standards")
    lines.append("* Genocide Studies \u2014 teach with sensitivity when historically relevant")

    lines.append("")
    lines.append("--- REB CROSS-CUTTING COMPETENCIES ---")
    lines.append("Foster these in every lesson:")
    lines.append("* Critical thinking and problem solving")
    lines.append("* Creativity and innovation")
    lines.append("* Research and inquiry skills")
    lines.append("* Communication and collaboration")
    lines.append("* Cooperation and teamwork")
    lines.append("* Lifelong learning")
    lines.append("* Digital literacy")

    lines.append("")
    if leaf_subject_name:
        style = get_subject_teaching_style(leaf_subject_name)
        if style:
            lines.append(f"--- {leaf_subject_name.upper()} TEACHING STYLE ---")
            lines.append(style)

    return "\n".join(lines)


def get_subject_teaching_style(subject_name: str) -> str:
    path = BASE_DIR / "core" / "subject_focus.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            styles = json.load(f)
        for key in styles:
            if subject_name and subject_name.lower() == key.lower():
                return styles[key]
    except Exception:
        pass
    return ""


def _find_subjects(parent_id: str) -> list:
    for key in ["primary", "high_school", "college"]:
        data = _load_json(key)
        for sl in data.get("sub_levels", []):
            sl_id = f"{key}_{data.get('sub_levels', []).index(sl)}"
            if sl_id == parent_id:
                return sl.get("subjects", [])
            for combo in sl.get("combinations", []):
                combo_id = f"{key}_{data.get('sub_levels', []).index(sl)}_combo_{sl.get('combinations', []).index(combo)}"
                if combo_id == parent_id:
                    return combo.get("subjects", [])
            for tg in sl.get("trade_groups", []):
                tg_id = f"{key}_{data.get('sub_levels', []).index(sl)}_tg_{sl.get('trade_groups', []).index(tg)}"
                if tg_id == parent_id:
                    return tg.get("trades", [])
    return []


def _find_combination(combo_id: str) -> Optional[dict]:
    for key in ["primary", "high_school", "college"]:
        data = _load_json(key)
        for sl in data.get("sub_levels", []):
            sl_idx = data["sub_levels"].index(sl)
            for ci, combo in enumerate(sl.get("combinations", [])):
                cid = f"{key}_{sl_idx}_combo_{ci}"
                if cid == combo_id:
                    return combo
    return None


def _find_trade_group(tg_id: str) -> Optional[dict]:
    for key in ["primary", "high_school", "college"]:
        data = _load_json(key)
        for sl in data.get("sub_levels", []):
            sl_idx = data["sub_levels"].index(sl)
            for ti, tg in enumerate(sl.get("trade_groups", [])):
                tid = f"{key}_{sl_idx}_tg_{ti}"
                if tid == tg_id:
                    return tg
    return None


def _find_subject_by_id(subject_id: str, parent_path: Optional[list[str]] = None) -> Optional[dict]:
    search_keys = ["primary", "high_school", "college"]
    target_sl_idx: Optional[int] = None
    is_combo = False

    if parent_path:
        search_keys = [parent_path[0]]
        for p in parent_path:
            if "_combo_" in p:
                is_combo = True
            # Extract sublevel index from IDs like "primary_1" or "high_school_0"
            parts = p.rsplit("_", 1)
            if len(parts) == 2 and parts[1].isdigit() and not any(x in p for x in ["_combo_", "_tg_"]):
                target_sl_idx = int(parts[1])

    for key in search_keys:
        data = _load_json(key)
        for sl_idx, sl in enumerate(data.get("sub_levels", [])):
            if target_sl_idx is not None and sl_idx != target_sl_idx:
                continue

            if is_combo:
                for combo in sl.get("combinations", []):
                    for s in combo.get("subjects", []):
                        sid = s.get("name", "").lower().replace(" ", "_")
                        if sid == subject_id:
                            return s
                continue

            for s in sl.get("subjects", []):
                sid = s.get("name", "").lower().replace(" ", "_").replace("&", "and").replace("(", "").replace(")", "")
                if sid == subject_id:
                    return s

    return None


def _find_trade_by_id(trade_id: str) -> Optional[dict]:
    for key in ["primary", "high_school", "college"]:
        data = _load_json(key)
        for sl in data.get("sub_levels", []):
            for tg in sl.get("trade_groups", []):
                for t in tg.get("trades", []):
                    tid = t.get("name", "").lower().replace(" ", "_")
                    if tid == trade_id:
                        return t
    return None
