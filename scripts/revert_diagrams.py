"""Step 1: Revert image-type diagrams from lesson JSONs — set diagrams to []."""
import json, shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
MATH_DIR = BASE / "data" / "curriculum" / "math"

def main():
    print("Reverting image-type diagrams...")
    reverted = 0
    for uf in sorted(MATH_DIR.glob("*_unit*.json")):
        if uf.name.endswith(".bak"):
            continue
        d = json.loads(uf.read_text(encoding="utf-8"))
        changed = False
        for lc in d.get("lessons_content", []):
            diags = lc.get("diagrams", [])
            if any(di.get("type") == "image" for di in diags):
                lc["diagrams"] = []
                changed = True
                reverted += 1
        if changed:
            bak = uf.with_suffix(uf.suffix + ".bak2")
            if not bak.exists():
                shutil.copy2(uf, bak)
            with open(uf, "w", encoding="utf-8") as f:
                json.dump(d, f, indent=2, ensure_ascii=False)
            print(f"  {uf.name}")
    print(f"Done. {reverted} lessons reverted.")

if __name__ == "__main__":
    main()
