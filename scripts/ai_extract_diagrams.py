"""Step 2: Use AI to extract MathDiagramWidget params from figure context text."""
import json, re, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from or_client import OpenRouterClient, TEXT_MODELS

BASE = Path(__file__).resolve().parent.parent
MATH_DIR = BASE / "data" / "curriculum" / "math"

FIG_PATTERN = re.compile(r'Fig(?:ure)?\.?\s*(\d+)\.(\d+)', re.IGNORECASE)

TYPES_INFO = """
Valid diagram types and their params:
- triangle: right triangle, params={"a": leg, "b": leg, "c": hypotenuse, "angle_A": degrees}
- unit_circle: params={"angle": degrees, "show_sin": bool, "show_cos": bool, "show_tan": bool}
- cartesian: params={"x_min": num, "x_max": num, "y_min": num, "y_max": num, "function": "linear"|"quadratic", "m": num, "c": num, "a": num, "b": num, "c": num, "points": [[x,y],...]}
- geometry: params={"shape": "circle"|"inscribed_triangle"|"chords", "diameter_angle": num}
- venn: params={"sets": 2|3, "values": {"A": val, "B": val, "C": val, "AB": val, "outside": val}}
- number_line: params={"min": num, "max": num, "marks": [num,...], "highlight": [num,...]}
- transformation: params={"type": "translation"|"rotation"|"reflection", "dx": num, "dy": num, "angle": num, "line": "x"|"y"|"y=x", "shape": [[x,y],...]}
- angles: params={"type": "parallel_lines"|"vertical_angles", "angle": num}
"""

SYSTEM_PROMPT = f"""You are a math diagram analyzer. Given text describing a figure from a math textbook, determine the diagram type and extract exact parameters for rendering.

{TYPES_INFO}

Rules:
1. Output ONLY valid JSON object with "type" and "params" keys
2. Use exact measurements from the text (side lengths, angles, coordinates)
3. If the text mentions function equations, extract coefficients
4. For missing information, use reasonable defaults
5. If the figure type is unclear, output {{"type": "unknown"}}
6. NEVER include explanations or markdown — only JSON"""


def strip_html(text):
    return re.sub(r'<[^>]+>', '', text)


def extract_context(text, fig_num, window=300):
    """Get text surrounding a figure reference."""
    for m in FIG_PATTERN.finditer(text):
        if f"{m.group(1)}.{m.group(2)}" == fig_num:
            start = max(0, m.start() - window)
            end = min(len(text), m.end() + window)
            snippet = text[start:end]
            snippet = strip_html(snippet)
            snippet = re.sub(r'\s+', ' ', snippet).strip()
            return snippet
    return ""


def collect_figure_contexts():
    """Collect all figure references with their context from lesson JSONs."""
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

        unit_name = d.get("name", "")
        lessons = d.get("lessons", [])
        lessons_content = d.get("lessons_content", [])

        for idx, lc in enumerate(lessons_content):
            lesson_name = lessons[idx] if idx < len(lessons) else f"Lesson {idx+1}"

            # Collect text from all fields
            all_text = ""
            for field in ["reading", "examples", "practice", "summary",
                          "deep_explanation", "practice_answers", "objectives"]:
                val = lc.get(field, "")
                if isinstance(val, str):
                    all_text += val + "\n"

            # Find unique figure numbers in this lesson
            seen_figs = set()
            for m in FIG_PATTERN.finditer(all_text):
                fig_num = f"{m.group(1)}.{m.group(2)}"
                if fig_num in seen_figs:
                    continue
                seen_figs.add(fig_num)

                context = extract_context(all_text, fig_num)
                if context:
                    figures.append({
                        "level": level,
                        "unit_file": uf.name,
                        "unit_name": unit_name,
                        "lesson_idx": idx,
                        "lesson_name": lesson_name,
                        "fig_num": fig_num,
                        "context": context[:500],
                    })

    return figures


def process_with_ai(client, figure):
    """Send figure context to AI and get diagram params back."""
    prompt = f"""Analyze this math textbook figure description and output diagram parameters.

Figure number: {figure['fig_num']}
Unit: {figure['unit_name']}
Lesson: {figure['lesson_name']}

Description: {figure['context']}

Output ONLY valid JSON with "type" and "params" keys matching the valid types list."""

    try:
        result = client._call_with_fallback(
            pool=TEXT_MODELS,
            messages=[{"role": "system", "content": SYSTEM_PROMPT},
                      {"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        if result:
            # Clean markdown code fences if present
            result = re.sub(r'^```(?:json)?\s*', '', result.strip())
            result = re.sub(r'\s*```$', '', result.strip())
            return json.loads(result)
    except Exception as e:
        print(f"      AI error: {e}")
    return {"type": "unknown"}


def main():
    print("=" * 60)
    print("Step 2: AI Figure Parameter Extraction")
    print("=" * 60)

    client = OpenRouterClient()

    # Collect all figure contexts
    print("\nCollecting figure contexts from lesson JSONs...")
    figures = collect_figure_contexts()
    print(f"  Found {len(figures)} figure references with context")

    # Process each with AI
    print("\nProcessing with AI...")
    results = []
    success = 0
    unknown = 0
    start_time = time.time()

    for i, fig in enumerate(figures):
        diag = process_with_ai(client, fig)
        fig["diagram"] = diag
        results.append(fig)

        if diag.get("type") != "unknown":
            success += 1
        else:
            unknown += 1

        if (i + 1) % 5 == 0 or i == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            print(f"  [{i+1}/{len(figures)}] {success} ok, {unknown} unknown ({rate:.1f}/s)")

        if diag.get("type") != "unknown":
            print(f"    {fig['fig_num']} -> {diag['type']}")

    # Save results
    output_path = MATH_DIR / "_ai_diagram_params.json"
    summary = {
        "total": len(results),
        "success": success,
        "unknown": unknown,
        "results": results,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    elapsed = time.time() - start_time
    print(f"\n{'=' * 60}")
    print(f"Done! {success} diagrams extracted, {unknown} unknown")
    print(f"Time: {elapsed:.1f}s")
    print(f"Results saved to {output_path}")


if __name__ == "__main__":
    main()
