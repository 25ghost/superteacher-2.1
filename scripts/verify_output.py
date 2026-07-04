import json, os
from pathlib import Path

math_dir = Path("data/curriculum/math")

for level in ["s1", "s2", "s3"]:
    print(f"\n{'='*40}")
    print(f"  {level.upper()}")
    print(f"{'='*40}")
    for fpath in sorted(math_dir.glob(f"{level}_unit*.json")):
        with open(fpath, encoding="utf-8") as f:
            d = json.load(f)
        n_lessons = len(d["lessons"])
        n_content = len(d["lessons_content"])
        total_size = len(str(d))
        
        # Count which lessons have real content vs placeholder
        real = 0
        for lc in d["lessons_content"]:
            reading = lc.get("reading", "")
            if "This lesson covers" not in reading or len(reading) > 500:
                real += 1
        
        fsize = os.path.getsize(fpath)
        print(f"  {fpath.name}: {n_lessons} lessons, {real}/{n_lessons} with REB content, {fsize/1024:.0f}KB")

print("\nAll JSON files are valid!")
