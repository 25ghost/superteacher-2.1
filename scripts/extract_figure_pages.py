"""Phase 2: Render PDF pages containing figure references to high-res PNGs."""
import json, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import get_reb_book, _BASE

MATH_DIR = _BASE / "data" / "curriculum" / "math"
DIAGRAMS_DIR = _BASE / "assets" / "diagrams"

PDFS = {
    "s1": get_reb_book("s1"),
    "s2": get_reb_book("s2"),
    "s3": get_reb_book("s3"),
}

DPI = 250


def main():
    print("=" * 60)
    print(f"Phase 2: Extract Figure Pages at {DPI} DPI")
    print("=" * 60)

    # Load the figure map
    map_path = MATH_DIR / "_figure_map.json"
    if not map_path.exists():
        print(f"ERROR: {map_path} not found. Run Phase 1 first (discover_figures.py)")
        sys.exit(1)

    with open(map_path, "r", encoding="utf-8") as f:
        figure_map = json.load(f)

    unique_pages = figure_map["unique_pages"]
    print(f"\nPages to render: {len(unique_pages)}")

    # Group by level for progress tracking
    from collections import defaultdict
    pages_by_level = defaultdict(list)
    for entry in unique_pages:
        pages_by_level[entry["level"]].append(entry["page"])

    import fitz

    total_pages = len(unique_pages)
    rendered = 0
    skipped = 0
    errors = 0
    total_bytes = 0
    start_time = time.time()

    for level in ["s1", "s2", "s3"]:
        pdf_path = PDFS.get(level)
        if not pdf_path or not pdf_path.exists():
            print(f"\n  WARNING: {level} PDF not found, skipping")
            continue

        pages_to_render = sorted(set(pages_by_level.get(level, [])))
        if not pages_to_render:
            print(f"\n  {level}: no pages to render")
            continue

        out_dir = DIAGRAMS_DIR / level
        out_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n  {level}: opening {pdf_path.name}...")
        doc = fitz.open(str(pdf_path))
        print(f"  {level}: {len(pages_to_render)} pages to render")

        for page_num in pages_to_render:
            # Page numbers are 1-based in our mapping, PyMuPDF uses 0-based
            page_idx = page_num - 1
            if page_idx < 0 or page_idx >= doc.page_count:
                print(f"    WARNING: Page {page_num} out of range (max {doc.page_count})")
                continue

            # Output file name: s1_p046.png (zero-padded to 3 digits)
            out_name = f"{level}_p{page_num:03d}.png"
            out_path = out_dir / out_name

            if out_path.exists():
                skipped += 1
                continue

            try:
                page = doc[page_idx]
                pix = page.get_pixmap(dpi=DPI)
                pix.save(str(out_path))
                file_size = out_path.stat().st_size
                total_bytes += file_size
                rendered += 1
                if rendered % 20 == 0 or rendered == 1:
                    elapsed = time.time() - start_time
                    rate = rendered / elapsed if elapsed > 0 else 0
                    print(f"    [{rendered}/{total_pages}] Page {page_num} -> {out_name} ({file_size // 1024} KB, {rate:.1f} pg/s)")
            except Exception as e:
                print(f"    ERROR rendering page {page_num}: {e}")
                errors += 1

        doc.close()

        # Print level summary
        level_count = len(pages_to_render)
        level_bytes = sum(
            (out_dir / f"{level}_p{p:03d}.png").stat().st_size
            for p in pages_to_render
            if (out_dir / f"{level}_p{p:03d}.png").exists()
        )
        print(f"  {level}: {rendered} rendered, {skipped} skipped, {errors} errors, {level_bytes // (1024*1024)} MB")

    elapsed = time.time() - start_time
    print(f"\n{'=' * 60}")
    print(f"Done! {rendered} pages rendered, {skipped} skipped, {errors} errors")
    print(f"Total size: {total_bytes // (1024*1024)} MB")
    print(f"Time: {elapsed:.1f}s ({rendered/elapsed:.1f} pages/s)")


if __name__ == "__main__":
    main()
