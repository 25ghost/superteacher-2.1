"""Extract accurate diagram params from figure context text using regex + smart defaults."""
import json, re
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).resolve().parent.parent
MATH_DIR = BASE / "data" / "curriculum" / "math"

FIG_PATTERN = re.compile(r'Fig(?:ure)?\.?\s*(\d+)\.(\d+)', re.IGNORECASE)


def strip_html(text):
    return re.sub(r'<[^>]+>', '', text)


def extract_context(all_text, fig_num, window=300):
    for m in FIG_PATTERN.finditer(all_text):
        if f"{m.group(1)}.{m.group(2)}" == fig_num:
            start = max(0, m.start() - window)
            end = min(len(all_text), m.end() + window)
            snippet = all_text[start:end]
            snippet = strip_html(snippet)
            snippet = re.sub(r'\s+', ' ', snippet).strip()
            return snippet
    return ""


def extract_angle(text):
    m = re.search(r'∠\s*([A-Z]+)\s*=\s*(\d+)°?', text)
    if m:
        return float(m.group(2))
    m = re.search(r'angle\s+(\w+)\s*=\s*(\d+)°?', text, re.I)
    if m:
        return float(m.group(2))
    m = re.search(r'(\d+)°', text)
    if m:
        return float(m.group(1))
    return None


def extract_lengths(text):
    lengths = [float(x) for x in re.findall(r'(\d+\.?\d*)\s*(?:cm|m|mm)', text)]
    return lengths


def extract_function(text):
    m = re.search(r'y\s*=\s*([+-]?\d*\.?\d*)\s*x\s*([+-]\s*\d+\.?\d*)?', text)
    if m:
        m_val = m.group(1).strip()
        c_val = m.group(2).strip() if m.group(2) else "0"
        m_val = float(m_val) if m_val and m_val not in ("", "+", "-") else (1 if m_val in ("", "+") else -1)
        c_val = float(c_val.replace(" ", "")) if c_val else 0
        return {"function": "linear", "m": m_val, "c": c_val}
    m = re.search(r'y\s*=\s*([+-]?\d*\.?\d*)\s*x\s*[²^]2\s*([+-]\s*\d+\.?\d*)?\s*x\s*([+-]\s*\d+\.?\d*)?', text)
    if m:
        return {"function": "quadratic", "a": 1, "b": 0, "c": 0}
    return None


DIAGRAM_RULES = [
    ("venn", r'\b(venn|set)\b', lambda ctx: {
        "type": "venn",
        "params": {"sets": 3 if "three" in ctx.lower() or "3" in ctx.split()[1:3] else 2,
                   "values": {"A": "", "B": "", "outside": ""}}
    }),
    ("triangle", r'\b(triangle|right.angled|pythagoras|thales|hypotenuse|leg|altitude)\b', lambda ctx: {
        "type": "triangle",
        "params": extract_triangle_params(ctx)
    }),
    ("unit_circle", r'\b(unit circle|sin|cos|tan|sine|cosine|tangent|trigonometr|SOH|CAH|TOA)\b', lambda ctx: {
        "type": "unit_circle",
        "params": {"angle": extract_angle(ctx) or 45, "show_sin": True, "show_cos": True, "show_tan": False}
    }),
    ("cartesian", r'\b(graph|function|coordinate|axis|plot|linear|quadratic|parabola|y\s*=)\b', lambda ctx: {
        "type": "cartesian",
        "params": {"x_min": -5, "x_max": 5, "y_min": -5, "y_max": 5, **extract_cartesian_params(ctx)}
    }),
    ("angles", r'\b(angle|parallel|transversal|vertical|alternate|corresponding)\b', lambda ctx: {
        "type": "angles",
        "params": {"type": "parallel_lines" if "parallel" in ctx.lower() else "vertical_angles",
                   "angle": extract_angle(ctx) or 60}
    }),
    ("number_line", r'\b(number line|inequalit|number line|range|-\d+.*\d+)\b', lambda ctx: {
        "type": "number_line",
        "params": {"min": -5, "max": 5, "highlight": [0]}
    }),
    ("geometry", r'\b(circle theorem|inscribed|diameter|radius|chord|arc|circumference)\b', lambda ctx: {
        "type": "geometry",
        "params": {"shape": "circle"}
    }),
    ("transformation", r'\b(transform|reflect|rotation|translat|isometr|enlargement|similar|scale factor)\b', lambda ctx: {
        "type": "transformation",
        "params": {"type": "translation", "dx": 60, "dy": 0}
    }),
]


def extract_triangle_params(ctx):
    lens = extract_lengths(ctx)
    angle = extract_angle(ctx)
    params = {"a": 3, "b": 4, "c": 5}
    if len(lens) >= 3:
        params["a"], params["b"], params["c"] = lens[0], lens[1], lens[2]
    elif len(lens) == 2:
        params["a"], params["b"] = lens[0], lens[1]
        params["c"] = round((lens[0]**2 + lens[1]**2)**0.5, 1)
    elif len(lens) == 1:
        params["a"] = lens[0]
        params["b"] = round(lens[0] * 0.75, 1)
        params["c"] = round((params["a"]**2 + params["b"]**2)**0.5, 1)
    if angle:
        params["angle_A"] = angle
    return params


def extract_cartesian_params(ctx):
    func = extract_function(ctx)
    if func:
        return func
    if "linear" in ctx.lower():
        return {"function": "linear", "m": 1, "c": 0}
    if "quadratic" in ctx.lower() or "parabola" in ctx.lower():
        return {"function": "quadratic", "a": 1, "b": 0, "c": 0}
    return {}


def classify_figure(ctx):
    if not ctx:
        return None
    for name, pattern, builder in DIAGRAM_RULES:
        if re.search(pattern, ctx, re.I):
            return builder(ctx)
    return None


def collect_all_figures():
    """Collect all (unit_file, lesson_idx, fig_num, context) tuples."""
    figures = []
    for uf in sorted(MATH_DIR.glob("*_unit*.json")):
        if uf.name.endswith(".bak") or uf.name.endswith(".bak2"):
            continue
        try:
            d = json.loads(uf.read_text(encoding="utf-8"))
        except:
            continue
        level = uf.stem.split("_")[0]
        if level not in ("s1", "s2", "s3"):
            continue
        for idx, lc in enumerate(d.get("lessons_content", [])):
            all_text = ""
            for field in ["reading", "examples", "practice"]:
                val = lc.get(field, "")
                if isinstance(val, str):
                    all_text += val + "\n"
            seen = set()
            for m in FIG_PATTERN.finditer(all_text):
                fig_num = f"{m.group(1)}.{m.group(2)}"
                if fig_num in seen:
                    continue
                seen.add(fig_num)
                ctx = extract_context(all_text, fig_num)
                if ctx:
                    figures.append({
                        "unit_file": uf.name,
                        "lesson_idx": idx,
                        "fig_num": fig_num,
                        "context": ctx,
                    })
    return figures


def main():
    print("=" * 60)
    print("Extracting diagram params from figure context text")
    print("=" * 60)

    figures = collect_all_figures()
    print(f"Found {len(figures)} figure references")

    classified = 0
    unclassified = 0
    type_counts = defaultdict(int)

    results = []
    for fig in figures:
        diag = classify_figure(fig["context"])
        if diag:
            classified += 1
            type_counts[diag["type"]] += 1
        else:
            unclassified += 1
        results.append({**fig, "diagram": diag or {"type": "unknown"}})

    print(f"\nClassified: {classified}, Unclassified: {unclassified}")
    print(f"Types: {dict(type_counts)}")

    # Group by (unit_file, lesson_idx) for applying to JSONs
    by_lesson = defaultdict(list)
    for r in results:
        if r["diagram"]["type"] != "unknown":
            by_lesson[(r["unit_file"], r["lesson_idx"])].append(r)

    print(f"\nLessons with classified diagrams: {len(by_lesson)}")

    # Apply to lesson JSONs
    print("\nApplying to lesson JSONs...")
    applied = 0
    for (uf_name, lesson_idx), fig_list in by_lesson.items():
        uf_path = MATH_DIR / uf_name
        if not uf_path.exists():
            continue
        d = json.loads(uf_path.read_text(encoding="utf-8"))
        lessons_content = d.get("lessons_content", [])
        if lesson_idx >= len(lessons_content):
            continue
        # Build deduplicated diagrams per figure (one per ref)
        diags = []
        seen = set()
        for fig in fig_list:
            if fig["fig_num"] in seen:
                continue
            seen.add(fig["fig_num"])
            diags.append(fig["diagram"])
        if diags:
            lessons_content[lesson_idx]["diagrams"] = diags
            applied += 1

        with open(uf_path, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2, ensure_ascii=False)

    print(f"Applied diagrams to {applied} lessons")
    print(f"Lessons with no classification (empty diagrams): {len(figures) - classified} figures unclassified")


if __name__ == "__main__":
    main()
