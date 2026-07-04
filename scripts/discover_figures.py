"""Phase 1: Discover figure references in lesson JSONs & map them to PDF pages."""
import json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import get_reb_book, _BASE

MATH_DIR = _BASE / "data" / "curriculum" / "math"

PDFS = {
    "s1": get_reb_book("s1"),
    "s2": get_reb_book("s2"),
    "s3": get_reb_book("s3"),
}

FIG_PATTERN = re.compile(r'Fig(?:ure)?\.?\s*(\d+)\.(\d+)', re.IGNORECASE)


def extract_page_text(pdf_path):
    """Extract text per-page from PDF. Returns list of (page_num, text)."""
    import fitz
    doc = fitz.open(str(pdf_path))
    pages = []
    for pg in range(doc.page_count):
        text = doc[pg].get_text("text")
        pages.append((pg + 1, text))
    doc.close()
    return pages


def find_figures_in_text(text):
    """Find all Fig. N.N references in a text string."""
    matches = []
    for m in FIG_PATTERN.finditer(text):
        matches.append({
            "fig_num": f"{m.group(1)}.{m.group(2)}",
            "chapter": int(m.group(1)),
            "fig_index": int(m.group(2)),
            "context_start": max(0, m.start() - 40),
            "context_end": min(len(text), m.end() + 60),
        })
    return matches


def find_figures_in_content(content, path_hint=""):
    """Scan all string fields in a lesson content dict for figure references."""
    figures = []
    text_fields = ["reading", "examples", "practice", "summary",
                   "deep_explanation", "practice_answers", "checkbox_answers",
                   "objectives"]
    for field in text_fields:
        val = content.get(field, "")
        if isinstance(val, str):
            for fig in find_figures_in_text(val):
                fig["field"] = field
                fig["path"] = path_hint
                figures.append(fig)
        elif isinstance(val, dict):
            # quiz field
            for k, v in val.items():
                if isinstance(v, str):
                    for fig in find_figures_in_text(v):
                        fig["field"] = f"quiz.{k}"
                        fig["path"] = path_hint
                        figures.append(fig)
    return figures


def match_figure_to_page(fig_num, page_texts):
    """Find which PDF page(s) contain a given Fig. N.N reference."""
    matching_pages = []
    for page_num, text in page_texts:
        # Search for the exact figure reference in the page text
        # Try both "Fig. N.N" and "Fig N.N" and "Figure N.N"
        for pattern in [
            rf'Fig(?:ure)?\.?\s*{re.escape(fig_num)}',
            rf'[Ff]ig\.?\s*{re.escape(fig_num)}',
            rf'{re.escape(fig_num)}\s*[Ff]ig',
        ]:
            if re.search(pattern, text):
                matching_pages.append(page_num)
                break
    return sorted(set(matching_pages))


def main():
    print("=" * 60)
    print("Phase 1: Discover Figure References")
    print("=" * 60)

    # Step 1: Load per-page text from all PDFs
    print("\nLoading PDF page text...")
    page_texts_by_level = {}
    for level, pdf_path in PDFS.items():
        if pdf_path.exists():
            print(f"  {level}: {pdf_path.name}")
            page_texts_by_level[level] = extract_page_text(pdf_path)
            print(f"    -> {len(page_texts_by_level[level])} pages loaded")
        else:
            print(f"  WARNING: {pdf_path} not found, skipping {level}")

    # Step 2: Scan all unit JSON files for figure references
    print("\nScanning lesson JSON files for figure references...")
    unit_files = sorted(MATH_DIR.glob("*_unit*.json"))
    # Exclude .bak files and non-unit files
    unit_files = [f for f in unit_files if not f.name.endswith(".bak")
                  and f.name not in ("_validate.py", "pilot_enrich.py",
                                     "reb_restructure.py", "gen_s3_full.py")]

    figure_refs = []  # List of {level, unit_file, unit_name, lesson_idx, lesson_name, fig_num, chapter, fig_index, field, context}

    for uf in unit_files:
        try:
            data = json.loads(uf.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  ERROR loading {uf.name}: {e}")
            continue

        # Determine level from filename (s1_unit, s2_unit, s3_unit, p1p3_unit, p4p6_unit)
        fname = uf.stem
        level = None
        for lvl in ["s1", "s2", "s3"]:
            if fname.startswith(lvl):
                level = lvl
                break
        if not level:
            if fname.startswith("p1p3") or fname.startswith("p4p6"):
                continue  # Skip primary for now
            continue

        unit_name = data.get("name", "")
        lessons = data.get("lessons", [])
        lessons_content = data.get("lessons_content", [])

        for idx, lesson_name in enumerate(lessons):
            content = lessons_content[idx] if idx < len(lessons_content) else {}
            figures = find_figures_in_content(content, f"{uf.name} / {lesson_name}")
            for fig in figures:
                figure_refs.append({
                    "level": level,
                    "unit_file": uf.name,
                    "unit_name": unit_name,
                    "lesson_idx": idx,
                    "lesson_name": lesson_name,
                    "fig_num": fig["fig_num"],
                    "chapter": fig["chapter"],
                    "fig_index": fig["fig_index"],
                    "field": fig["field"],
                    "context": None,  # Will fill after page matching
                })

    print(f"  Found {len(figure_refs)} figure references across {len(unit_files)} unit files")

    # Step 3: Match each figure reference to PDF pages
    print("\nMatching figure references to PDF pages...")
    matched = 0
    unmatched = 0
    for ref in figure_refs:
        level = ref["level"]
        if level not in page_texts_by_level:
            ref["pages"] = []
            unmatched += 1
            continue
        pages = match_figure_to_page(ref["fig_num"], page_texts_by_level[level])
        ref["pages"] = pages
        if pages:
            matched += 1
        else:
            unmatched += 1

    print(f"  Matched: {matched}, Unmatched: {unmatched}")

    # Step 4: Deduplicate and organize by unique (level, page) pairs for rendering
    unique_pages = set()
    for ref in figure_refs:
        for p in ref.get("pages", []):
            unique_pages.add((ref["level"], p))

    print(f"\n  Unique (level, page) pairs to render: {len(unique_pages)}")

    # Step 5: Save the mapping
    output = {
        "figure_refs": figure_refs,
        "unique_pages": sorted([{"level": l, "page": p} for l, p in unique_pages],
                               key=lambda x: (x["level"], x["page"])),
    }
    output_path = MATH_DIR / "_figure_map.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nSaved figure mapping to {output_path}")
    print(f"  {len(figure_refs)} total figure references")
    print(f"  {len(unique_pages)} unique pages to render")

    # Print summary by level
    for level in ["s1", "s2", "s3"]:
        level_refs = [r for r in figure_refs if r["level"] == level]
        level_pages = set()
        for r in level_refs:
            for p in r.get("pages", []):
                level_pages.add(p)
        print(f"  {level}: {len(level_refs)} refs, {len(level_pages)} pages")


if __name__ == "__main__":
    main()
