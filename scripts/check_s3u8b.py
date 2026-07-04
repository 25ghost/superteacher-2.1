import json
from pathlib import Path

fpath = Path("data/curriculum/math/s3_unit8.json")
with open(fpath, encoding="utf-8") as f:
    d = json.load(f)

print(f"Unit: {d['name']}")
print(f"File size: {fpath.stat().st_size} bytes")
print()
total_reb = 0
for i, (ln, lc) in enumerate(zip(d['lessons'], d['lessons_content'])):
    reading = lc['reading']
    examples = lc.get('examples', '') or ''
    practice = lc.get('practice', '') or ''
    summary = lc.get('summary', '') or ''
    deep = lc.get('deep_explanation', '') or ''
    total = len(reading) + len(examples) + len(practice) + len(summary) + len(deep)
    
    # Check if reading has reb content (not placeholder)
    has_reb = 'Student Book carefully' not in reading and len(reading) > 200
    
    print(f"Lesson {i}: {ln}")
    print(f"  reading={len(reading)}, examples={len(examples)}, practice={len(practice)}, total_content={total}")
    if has_reb:
        total_reb += 1
        print(f"  Reading preview: {reading[100:300]}")
    else:
        print(f"  READING IS PLACEHOLDER: {reading[100:200]}")
    print()

print(f"Total lessons with REB reading: {total_reb}/{len(d['lessons'])}")
