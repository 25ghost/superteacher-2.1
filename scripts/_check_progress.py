import json
from pathlib import Path
data = json.loads((Path(__file__).resolve().parent.parent / "data" / "curriculum" / "high_school.json").read_text())
for sl in data['sub_levels']:
    if 'S1' in sl['name']:
        for subj in sl.get('subjects', []):
            if subj['name'] == 'Mathematics':
                for unit in subj['units']:
                    cl = unit.get('lessons_content', [])
                    n = sum(1 for c in cl if c)
                    t = len(unit['lessons'])
                    print(f'{unit["name"]}: {n}/{t}')
