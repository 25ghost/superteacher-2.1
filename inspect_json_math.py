import json
from pathlib import Path

math_dir = Path("data/curriculum/math")
for level in ["s1", "s2", "s3"]:
    print(f"=== {level.upper()} ===")
    for fpath in sorted(math_dir.glob(f"{level}_unit*.json"), key=lambda x: int(x.stem.split("unit")[1])):
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"  File: {fpath.name}")
        print(f"    Name: {data.get('name')}")
        print(f"    Lessons: {data.get('lessons')}")
