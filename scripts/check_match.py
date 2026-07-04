import json
from pathlib import Path

# Load high_school.json S3 lessons
with open('data/curriculum/high_school.json', encoding='utf-8') as f:
    hs = json.load(f)

hs_units = {}
for sl in hs['sub_levels']:
    if 'Senior 3' in sl['name']:
        for subj in sl['subjects']:
            if subj['name'] == 'Mathematics':
                for u in subj['units']:
                    name = u['name']
                    lessons = u.get('lessons', [])
                    hs_units[name] = lessons

# Load per-unit files
math_dir = Path('data/curriculum/math')
for i in range(1, 14):
    fpath = math_dir / f's3_unit{i}.json'
    if fpath.exists():
        with open(fpath, encoding='utf-8') as f:
            pu = json.load(f)
        
        unit_name = pu['name']
        pu_lessons = pu['lessons']
        
        # Find matching hs unit
        hs_key = None
        for hk in hs_units:
            if hk.replace(' ', '') == unit_name.replace(' ', '') or \
               hk.split(':')[0].strip() == unit_name.split(':')[0].strip():
                hs_key = hk
                break
        
        if hs_key:
            hs_lessons = hs_units[hs_key]
            match = all(pl == hl for pl, hl in zip(pu_lessons, hs_lessons))
            print(f"Unit {i}: {unit_name}")
            print(f"  HS: {hs_key}")
            print(f"  PER-UNIT ({len(pu_lessons)}): {pu_lessons}")
            print(f"  HIGH_SCHOOL ({len(hs_lessons)}): {hs_lessons}")
            print(f"  MATCH: {match}")
            if not match:
                missing = [l for l in pu_lessons if l not in hs_lessons]
                extra = [l for l in hs_lessons if l not in pu_lessons]
                if missing: print(f"  Missing from HS: {missing}")
                if extra: print(f"  Extra in HS: {extra}")
        else:
            print(f"Unit {i}: NO MATCH in high_school.json for '{unit_name}'")
        print()
