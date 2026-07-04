import json
from pathlib import Path

fpath = Path("data/curriculum/math/s3_unit8.json")
with open(fpath, encoding="utf-8") as f:
    d = json.load(f)

print(f"Unit: {d['name']}")
for i, (ln, lc) in enumerate(zip(d['lessons'], d['lessons_content'])):
    reading = lc['reading']
    has_reb = len(reading) > 500 and 'Student Book' not in reading
    excerpt = reading[:150]
    print(f"\nLesson {i}: {ln}")
    print(f"  REB content: {has_reb}, length: {len(reading)}")
    print(f"  Excerpt: {excerpt}")
