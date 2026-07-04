import json
from pathlib import Path

curriculum_dir = Path("data/curriculum")
for fpath in curriculum_dir.glob("*.json"):
    if fpath.name == "index.json":
        continue
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        continue
    
    if isinstance(data, dict):
        sub_levels = data.get("sub_levels", [])
        for sl_idx, sl in enumerate(sub_levels):
            for subj in sl.get("subjects", []):
                if subj.get("name", "").lower() == "mathematics":
                    print(f"File: {fpath.name}, Level: {sl.get('name')}, Subject: {subj.get('name')}, Units count: {len(subj.get('units', []))}")
