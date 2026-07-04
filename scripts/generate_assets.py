"""Generate placeholder PNG assets for Rahura UI when branded images are unavailable."""
from __future__ import annotations

import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Install Pillow first: pip install pillow")
    sys.exit(1)

BASE = Path(__file__).resolve().parent.parent / "assets" / "rahura"

ASSETS: list[tuple[str, tuple[int, int, int], str]] = [
    ("rahura-logo.png", (25, 55, 109), "Rahura"),
    ("rahura-emblem.png", (239, 108, 77), "Rina"),
    ("jean-michel-habineza.jpg", (33, 91, 154), "Learn"),
    ("rah-21.jpg", (47, 157, 104), "REB"),
    ("s-calculator-b.jpg", (123, 95, 214), "Math"),
    ("exercise-book-green.jpg", (33, 167, 168), "Science"),
    ("exercise-book-red.jpg", (239, 108, 77), "English"),
    ("g-box-a.jpg", (25, 55, 109), "Physics"),
    ("eb-blue-48-a.jpg", (47, 157, 104), "Biology"),
    ("colored-pencils.jpg", (246, 180, 67), "Arts"),
    ("1.jpg", (239, 108, 77), "TVET"),
]


def _make(path: Path, rgb: tuple[int, int, int], label: str) -> None:
    w, h = 640, 360
    img = Image.new("RGB", (w, h), rgb)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 48)
    except OSError:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), label, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((w - tw) // 2, (h - th) // 2), label, fill=(255, 255, 255), font=font)
    img.save(path, quality=85)
    print(f"  created {path.name}")


def main() -> None:
    BASE.mkdir(parents=True, exist_ok=True)
    print(f"Generating placeholders in {BASE}")
    for name, color, label in ASSETS:
        _make(BASE / name, color, label)
    print("Done.")


if __name__ == "__main__":
    main()
