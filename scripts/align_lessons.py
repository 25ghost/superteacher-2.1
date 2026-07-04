"""Align per-unit lesson names with high_school.json lesson names."""
import json
from pathlib import Path

MATH_DIR = Path("data/curriculum/math")
HS_FILE = Path("data/curriculum/high_school.json")

with open(HS_FILE, encoding="utf-8") as f:
    hs = json.load(f)

# Build map of (level_index, unit_index) -> high_school lesson names
# Level order: Senior 1 = 0, Senior 2 = 1, Senior 3 = 2
levels_map = {}

for sl_idx, sl in enumerate(hs["sub_levels"]):
    level_key = {"Senior 1 (S1)": "s1", "Senior 2 (S2)": "s2", "Senior 3 (S3)": "s3"}.get(sl["name"])
    if not level_key:
        continue
    for subj in sl.get("subjects", []):
        if subj["name"] == "Mathematics":
            for u_idx, u in enumerate(subj["units"]):
                hs_lessons = u.get("lessons", [])
                levels_map[(level_key, u_idx + 1)] = hs_lessons
            break

print(f"Found {len(levels_map)} unit mappings")
for (lk, un), lessons in sorted(levels_map.items()):
    print(f"  {lk}_unit{un}: {len(lessons)} lessons: {lessons}")

# Update per-unit files
for (lk, un), hs_lessons in levels_map.items():
    fpath = MATH_DIR / f"{lk}_unit{un}.json"
    if not fpath.exists():
        print(f"\nMISSING: {fpath}")
        continue
    
    with open(fpath, encoding="utf-8") as f:
        pu = json.load(f)
    
    pu_lessons = pu.get("lessons", [])
    pu_content = pu.get("lessons_content", [])
    
    # Rename lessons but keep content aligned
    new_lessons = list(hs_lessons)
    new_content = []
    
    for i, hl in enumerate(hs_lessons):
        # Find matching content: try exact name first, then position
        content = None
        for j, pl in enumerate(pu_lessons):
            if pl == hl and j < len(pu_content):
                content = pu_content[j]
                break
        
        # If no exact match, try by position
        if content is None and i < len(pu_content):
            content = pu_content[i]
        
        # Pad if needed
        if content is None:
            content = pu_content[-1] if pu_content else {}
        
        new_content.append(content)
    
    pu["lessons"] = new_lessons
    pu["lessons_content"] = new_content[:len(hs_lessons)]
    
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(pu, f, indent=2, ensure_ascii=False)
    
    print(f"\nUpdated {lk}_unit{un}.json: {len(pu_lessons)} -> {len(new_lessons)} lessons")

print("\nDone! All per-unit files now aligned with high_school.json.")
