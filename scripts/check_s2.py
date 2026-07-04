import json
with open('data/curriculum/high_school.json', encoding='utf-8') as f:
    d = json.load(f)

for sl in d['sub_levels']:
    if 'Senior 2' in sl['name']:
        for subj in sl['subjects']:
            if subj['name'] == 'Mathematics':
                for u in subj['units']:
                    print(f"{u['name']}:")
                    print(f"  Lessons: {u.get('lessons', [])}")
                    print(f"  Has lessons_content: {'lessons_content' in u}")
                    if 'lessons_content' in u:
                        print(f"  Content entries: {len(u['lessons_content'])}")
                    print()
