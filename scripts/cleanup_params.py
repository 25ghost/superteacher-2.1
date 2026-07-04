"""Clean up diagram params: fix bad values, add fallbacks for unclassified figures."""
import json, re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
MATH_DIR = BASE / "data" / "curriculum" / "math"


def validate_params(diag):
    """Fix or flag bad parameter values."""
    if not diag or diag.get("type") in (None, "unknown"):
        return False
    t = diag["type"]
    p = diag.get("params", {})

    if t == "triangle":
        a, b, c = p.get("a", 3), p.get("b", 4), p.get("c", 5)
        if any(v <= 0 or v > 200 for v in (a, b, c)):
            p["a"], p["b"], p["c"] = 3, 4, 5
        if p.get("angle_A") is not None and (p["angle_A"] <= 0 or p["angle_A"] >= 180):
            p.pop("angle_A", None)
        return True

    if t == "unit_circle":
        angle = p.get("angle", 45)
        if angle <= 0 or angle >= 360:
            p["angle"] = 45
        return True

    if t == "angles":
        angle = p.get("angle", 60)
        if angle <= 0 or angle >= 180:
            p["angle"] = 60
        return True

    if t == "cartesian":
        for k in ("x_min", "x_max", "y_min", "y_max"):
            if p.get(k, 0) == 0 and k not in ("x_min", "y_min"):
                p[k] = 5
            if p.get(k, -100) < -100 or p.get(k, 100) > 100:
                p[k] = 5
        return True

    return True


def main():
    print("Cleaning up diagram params...")
    cleaned = 0
    for uf in sorted(MATH_DIR.glob("*_unit*.json")):
        if uf.name.endswith(".bak"):
            continue
        try:
            d = json.loads(uf.read_text(encoding="utf-8"))
        except:
            continue
        level = uf.stem.split("_")[0]
        if level not in ("s1", "s2", "s3"):
            continue

        changed = False
        for lc in d.get("lessons_content", []):
            diags = lc.get("diagrams", [])
            if not diags:
                continue
            valid = [di for di in diags if validate_params(di)]
            if len(valid) != len(diags):
                lc["diagrams"] = valid
                changed = True
                cleaned += len(diags) - len(valid)

        if changed:
            with open(uf, "w", encoding="utf-8") as f:
                json.dump(d, f, indent=2, ensure_ascii=False)
            print(f"  {uf.name}")

    print(f"Cleaned up {cleaned} bad param entries")
    print("Done.")


if __name__ == "__main__":
    main()
