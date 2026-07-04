import json
from pathlib import Path

fpath = Path("data/curriculum/math/s2_unit1.json")
with open(fpath, encoding="utf-8") as f:
    d = json.load(f)

# Check first lesson's reading
lc0 = d["lessons_content"][0]
print(f"Lesson 0: {d['lessons'][0]}")
print(f"Reading length: {len(lc0['reading'])}")
print(f"Reading starts with: {lc0['reading'][:200]}")
print(f"Contains REB text: {'Activity 1.1' in lc0['reading'] or 'Index notation' in lc0['reading']}")
print()

# Check last lesson
lc_last = d["lessons_content"][-1]
print(f"Last lesson: {d['lessons'][-1]}")
print(f"Reading length: {len(lc_last['reading'])}")
print(f"Reading starts with: {lc_last['reading'][:200]}")
