import json
with open('data/curriculum/high_school.json', encoding='utf-8') as f:
    d = json.load(f)

for sl in d['sub_levels']:
    if 'Senior 3' in sl['name']:
        for subj in sl['subjects']:
            if subj['name'] == 'Mathematics':
                for u in subj['units']:
                    ls = u.get('lessons', [])
                    lc = u.get('lessons_content', [])
                    print(f"{u['name']}:")
                    print(f"  Lessons ({len(ls)}): {ls}")
                    print(f"  Has lessons_content: {'lessons_content' in u}")
                    if 'lessons_content' in u:
                        print(f"  Content entries: {len(lc)}")
                    print()
