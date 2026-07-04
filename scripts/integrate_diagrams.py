"""Phase 3: Update lesson JSONs — replace template diagrams with actual image refs."""
import json, re, shutil
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).resolve().parent.parent
MATH_DIR = BASE / "data" / "curriculum" / "math"
DIAGRAMS_DIR = BASE / "assets" / "diagrams"

FIG_PATTERN = re.compile(r'Fig(?:ure)?\.?\s*(\d+)\.(\d+)', re.IGNORECASE)


def get_caption(text, fig_num, max_len=80):
    """Extract a short caption for a figure reference from surrounding text."""
    for m in FIG_PATTERN.finditer(text):
        if m.group(0) and f"{m.group(1)}.{m.group(2)}" == fig_num:
            # Get text after the figure reference (up to ~60 chars or until newline/punctuation)
            after = text[m.end():m.end() + 80]
            after = after.split('\n')[0].strip()
            after = re.sub(r'<[^>]+>', '', after)  # strip HTML tags
            # Truncate at sentence end or comma
            after = re.split(r'[.,;]', after)[0].strip()
            caption = f"Fig. {fig_num}"
            if after:
                caption += f": {after}"
            return caption[:max_len]
    return f"Fig. {fig_num}"


def extract_context(text, fig_num):
    """Get the snippet of text surrounding a figure reference for dedup."""
    for m in FIG_PATTERN.finditer(text):
        if f"{m.group(1)}.{m.group(2)}" == fig_num:
            start = max(0, m.start() - 40)
            end = min(len(text), m.end() + 60)
            return text[start:end]
    return ""


def main():
    print("=" * 60)
    print("Phase 3: Integrate Diagrams into Lesson JSONs")
    print("=" * 60)

    # Load figure map
    map_path = MATH_DIR / "_figure_map.json"
    if not map_path.exists():
        print(f"ERROR: {map_path} not found")
        return

    with open(map_path, "r", encoding="utf-8") as f:
        figure_map = json.load(f)

    figure_refs = figure_map["figure_refs"]
    print(f"Loaded {len(figure_refs)} figure references")

    # Group refs by (unit_file, lesson_idx)
    refs_by_lesson = defaultdict(list)
    for ref in figure_refs:
        key = (ref["unit_file"], ref["lesson_idx"])
        refs_by_lesson[key].append(ref)

    print(f"Grouped into {len(refs_by_lesson)} lesson groups")

    # Process each unit file
    unit_files = sorted(set(r["unit_file"] for r in figure_refs))
    total_lessons_updated = 0
    total_diagrams_added = 0

    for uf_name in unit_files:
        uf_path = MATH_DIR / uf_name
        if not uf_path.exists():
            print(f"  WARNING: {uf_path} not found, skipping")
            continue

        # Backup original
        bak_path = uf_path.with_suffix(uf_path.suffix + ".bak")
        if not bak_path.exists():
            shutil.copy2(uf_path, bak_path)

        # Load unit data
        with open(uf_path, "r", encoding="utf-8") as f:
            unit_data = json.load(f)

        lessons = unit_data.get("lessons", [])
        lessons_content = unit_data.get("lessons_content", [])

        if not lessons_content:
            print(f"  {uf_name}: no lessons_content, skipping")
            continue

        lessons_updated = 0
        for idx in range(len(lessons)):
            if idx >= len(lessons_content):
                continue

            content = lessons_content[idx]
            lesson_name = lessons[idx] if idx < len(lessons) else f"Lesson {idx+1}"

            # Get all figure refs for this lesson
            lesson_refs = refs_by_lesson.get((uf_name, idx), [])

            if not lesson_refs:
                # No figure references in this lesson
                if "diagrams" in content:
                    content["diagrams"] = []
                continue

            # Deduplicate by (fig_num, page) combo
            seen = set()
            diagrams = []
            for ref in lesson_refs:
                key = (ref["fig_num"], tuple(ref.get("pages", [])))
                if key in seen:
                    continue
                seen.add(key)

                # Use the first page if multiple pages match
                pages = ref.get("pages", [])
                if not pages:
                    continue

                page = pages[0]
                level = ref["level"]
                img_file = f"{level}_p{page:03d}.png"
                img_path = DIAGRAMS_DIR / level / img_file

                if not img_path.exists():
                    print(f"    WARNING: {img_path} not found, skipping fig {ref['fig_num']}")
                    continue

                # Get caption from the content field where this fig was found
                field = ref.get("field", "reading")
                field_text = content.get(field, "")
                if isinstance(field_text, dict):
                    # For quiz, join all string values
                    field_text = " ".join(v for v in field_text.values() if isinstance(v, str))

                caption = get_caption(field_text, ref["fig_num"])

                img_rel = f"assets/diagrams/{level}/{img_file}"
                diagrams.append({
                    "type": "image",
                    "src": img_rel,
                    "caption": caption,
                })

            if diagrams:
                content["diagrams"] = diagrams
                lessons_updated += 1
                total_diagrams_added += len(diagrams)
            else:
                if "diagrams" in content:
                    content["diagrams"] = []

        if lessons_updated > 0:
            unit_data["lessons_content"] = lessons_content
            with open(uf_path, "w", encoding="utf-8") as f:
                json.dump(unit_data, f, indent=2, ensure_ascii=False)
            print(f"  {uf_name}: updated {lessons_updated}/{len(lessons)} lessons ({sum(len(c.get('diagrams',[])) for c in lessons_content)} total diagrams)")
            total_lessons_updated += lessons_updated
        else:
            print(f"  {uf_name}: no changes")

    print(f"\n{'=' * 60}")
    print(f"Done! {total_lessons_updated} lessons updated, {total_diagrams_added} total diagrams added")


if __name__ == "__main__":
    main()
