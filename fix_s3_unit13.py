"""
fix_s3_unit13.py
Fix the s3_unit13 (Bivariate Statistics) content by finding the correct section.
"""
import json, re, sys
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE = Path(__file__).resolve().parent
OUT  = BASE / "data" / "curriculum" / "math"
S3_FILE = Path(r"C:\Users\KAREGEYA JUSTIN\Desktop\REB notes\Mathematics-S3-SB.txt")

def html_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def read_txt(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    return text.replace("\r\n", "\n").replace("\r", "\n")

def clean_line(s):
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]+", "", s)
    return s.strip()

def is_toc_line(s):
    return "...." in s or "......" in s

def is_page_number(s):
    return bool(re.match(r"^\d{1,3}$", s))

text = read_txt(S3_FILE)
lines = text.split("\n")

# Find "STATISTICS (BIVARIATE" or "13." near "BIVARIATE"
start_idx = None
for i, line in enumerate(lines):
    s = clean_line(line).upper()
    if "BIVARIATE" in s and i > 20000:
        # Walk back to find "13" marker
        for j in range(i, max(0, i-30), -1):
            if "13." in clean_line(lines[j]) or "STATISTICS (BIVARIATE" in clean_line(lines[j]).upper():
                start_idx = j
                break
        if start_idx:
            break
    if "STATISTICS (BIVARIATE DATA)" in s:
        start_idx = i
        break

if not start_idx:
    # Look for line 233 page marker plus "Statistics (Bivariate Data)"
    for i, line in enumerate(lines):
        s = clean_line(line)
        if "Statistics (Bivariate" in s and i > 20000:
            start_idx = max(0, i - 5)
            break

if not start_idx:
    # Fallback: find "13." in TOC region and add ~20000 lines offset
    for i, line in enumerate(lines):
        s = clean_line(line)
        if re.match(r"^13\.", s) and i < 500:
            # Found TOC entry, search for actual content past line 20000
            for j in range(20000, len(lines)):
                ns = clean_line(lines[j])
                if "bivariate" in ns.lower() or ("statistics" in ns.lower() and j > 23000):
                    start_idx = max(0, j - 2)
                    break
            break

print(f"S3 unit13 content starts at line: {start_idx}")

# Extract content
if start_idx:
    unit13_lines = lines[start_idx:]
else:
    unit13_lines = lines[-3000:]  # Last 3000 lines as fallback

print(f"Unit13 lines: {len(unit13_lines)}")

# Parse blocks for each lesson
lessons = [
    "Definition and example of bivariate data",
    "Frequency distribution table for bivariate data",
    "Data presentation using graphs",
    "Scatter diagrams",
    "The line of best fit in a scatter diagram",
    "Correlation",
]

def find_lesson_start_in(lines_list, lesson_name):
    kw = lesson_name.lower()
    words = kw.split()
    # Try full name
    for i, line in enumerate(lines_list):
        s = clean_line(line).lower()
        if kw in s and not is_toc_line(s) and len(s) < 150:
            return i
    # Try 3+ word subset
    for n in range(len(words), 2, -1):
        subset = " ".join(words[:n])
        for i, line in enumerate(lines_list):
            s = clean_line(line).lower()
            if subset in s and not is_toc_line(s):
                return i
    # Try section numbers
    for i, line in enumerate(lines_list):
        s = clean_line(line)
        if re.match(r"^13\.\d", s):
            return i
    return 0

def parse_blocks(lines_list):
    paragraphs, examples, exercises, activities = [], [], [], []
    i = 0
    while i < len(lines_list):
        s = clean_line(lines_list[i])
        if not s or is_page_number(s) or is_toc_line(s):
            i += 1
            continue
        if re.match(r"^Activity\s+\d+", s, re.IGNORECASE):
            block = [s]; i += 1
            while i < len(lines_list):
                ns = clean_line(lines_list[i])
                if re.match(r"^(Activity|Example|Exercise|Unit\s+(summary|test))", ns, re.IGNORECASE): break
                if ns and not is_page_number(ns) and not is_toc_line(ns):
                    block.append(ns)
                i += 1
            activities.append("\n".join(block)); continue
        if re.match(r"^Example\s+\d+", s, re.IGNORECASE):
            block = [s]; i += 1
            while i < len(lines_list):
                ns = clean_line(lines_list[i])
                if re.match(r"^(Activity|Example|Exercise|Unit\s+(summary|test))", ns, re.IGNORECASE): break
                if ns and not is_page_number(ns) and not is_toc_line(ns):
                    block.append(ns)
                i += 1
            examples.append("\n".join(block)); continue
        if re.match(r"^Exercise\s+\d+", s, re.IGNORECASE):
            block = [s]; i += 1
            while i < len(lines_list):
                ns = clean_line(lines_list[i])
                if re.match(r"^(Activity|Example|Exercise|Unit\s+(summary|test))", ns, re.IGNORECASE): break
                if ns and not is_page_number(ns) and not is_toc_line(ns):
                    block.append(ns)
                i += 1
            exercises.append("\n".join(block)); continue
        if re.match(r"^Unit\s+(summary|test)", s, re.IGNORECASE): break
        if re.match(r"^References$", s, re.IGNORECASE): break
        if re.match(r"^Glossary$", s, re.IGNORECASE): break
        if len(s) > 3:
            paragraphs.append(s)
        i += 1
    return {"paragraphs": paragraphs, "examples": examples, "exercises": exercises, "activities": activities}

def make_reading_html(lesson_name, blocks):
    parts = [f"<h3>{html_escape(lesson_name)}</h3>"]
    for p in blocks["paragraphs"]:
        if re.match(r"^\d+\.\d+", p):
            parts.append(f"<h4>{html_escape(p)}</h4>")
        else:
            parts.append(f"<p>{html_escape(p)}</p>")
    for act in blocks["activities"]:
        ls = act.split("\n"); title = ls[0]; body = "<br>".join(html_escape(l) for l in ls[1:] if l)
        parts.append(f"<div style='background:#E8F5E9;padding:12px;border-radius:8px;border-left:4px solid #4CAF50;margin:10px 0'><b>{html_escape(title)}</b><br>{body}</div>")
    if not blocks["paragraphs"] and not blocks["activities"]:
        parts.append(f"<p>Study <b>{html_escape(lesson_name)}</b> from the REB Student Book on Bivariate Statistics.</p>")
    return f'<html><body style="font-family:Segoe UI,sans-serif;font-size:11pt;line-height:1.7;padding:8px">\n' + "\n".join(parts) + "\n</body></html>"

def make_examples_html(blocks):
    if not blocks["examples"]:
        return '<html><body style="font-family:Segoe UI,sans-serif;font-size:11pt"><p><i>See worked examples in your REB Student Book.</i></p></body></html>'
    parts = ["<h3>Worked Examples</h3><ol>"]
    for ex in blocks["examples"]:
        ls = ex.split("\n"); title = ls[0]; body = "<br>".join(html_escape(l) for l in ls[1:] if l)
        parts.append(f"<li style='margin-bottom:14px'><b>{html_escape(title)}</b><br>{body}</li>")
    parts.append("</ol>")
    return f'<html><body style="font-family:Segoe UI,sans-serif;font-size:11pt;line-height:1.7;padding:8px">\n' + "\n".join(parts) + "\n</body></html>"

def make_practice_html(blocks, lesson_name):
    if not blocks["exercises"]:
        return f'<html><body style="font-family:Segoe UI,sans-serif;font-size:11pt"><h3>Practice Questions</h3><p>Complete exercises on <b>{html_escape(lesson_name)}</b> from your REB Student Book.</p></body></html>'
    parts = ["<h3>Practice Questions</h3>"]
    for ex in blocks["exercises"]:
        ls = ex.split("\n"); title = ls[0]; body = "<br>".join(html_escape(l) for l in ls[1:] if l)
        parts.append(f"<div style='background:#EAF5FF;padding:12px;border-radius:8px;border-left:4px solid #1976D2;margin:10px 0'><b>{html_escape(title)}</b><br>{body}</div>")
    return f'<html><body style="font-family:Segoe UI,sans-serif;font-size:11pt;line-height:1.7;padding:8px">\n' + "\n".join(parts) + "\n</body></html>"

lessons_content = []
for idx, lesson in enumerate(lessons):
    start = find_lesson_start_in(unit13_lines, lesson)
    if idx + 1 < len(lessons):
        end = find_lesson_start_in(unit13_lines, lessons[idx + 1])
        if end <= start:
            # proportional fallback
            end = int(len(unit13_lines) * (idx + 1) / len(lessons))
    else:
        end = len(unit13_lines)

    lesson_lines = unit13_lines[start:end]
    blocks = parse_blocks(lesson_lines)

    # Fallback if too few
    if len(blocks["paragraphs"]) < 2:
        w_start = int(len(unit13_lines) * idx / len(lessons))
        w_end   = int(len(unit13_lines) * (idx + 1) / len(lessons))
        fb_blocks = parse_blocks(unit13_lines[w_start:w_end])
        if len(fb_blocks["paragraphs"]) > len(blocks["paragraphs"]):
            blocks = fb_blocks

    reading = make_reading_html(lesson, blocks)
    examples = make_examples_html(blocks)
    practice = make_practice_html(blocks, lesson)

    total = len(reading) + len(examples) + len(practice)
    status = "OK" if len(blocks["paragraphs"]) >= 2 else "limited"
    print(f"  [{idx+1}/{len(lessons)}] {lesson[:50]:50s} {total:6d} chars ({status})")

    lessons_content.append({
        "objectives": f"By the end of this lesson on {lesson}, you should be able to understand, analyze and interpret bivariate data effectively.",
        "reading": reading,
        "examples": examples,
        "practice": practice,
        "summary": f'<html><body style="font-family:Segoe UI,sans-serif;font-size:11pt;padding:8px"><h3>Summary: {html_escape(lesson)}</h3><p>This lesson covers <b>{html_escape(lesson)}</b> as part of <b>Unit 13: Bivariate Statistics</b>.</p><p>Review key definitions and practice interpreting scatter diagrams and correlation.</p></body></html>',
        "quiz": {
            "question": f"Which best describes {lesson}?",
            "options": {"A": f"The key rules and definitions of {lesson}", "B": "An unrelated topic", "C": "A primary school concept", "D": "None of the above"},
            "answer": "A"
        },
        "practice_answers": "Review your answers with your teacher.",
        "checkbox_answers": f"<h3>Exercises</h3><p><input type='checkbox'> Complete {html_escape(lesson)} exercises from your Student Book.</p>",
        "deep_explanation": f'<html><body style="font-family:Segoe UI,sans-serif;font-size:11pt;padding:8px"><h3>Deep Explanation: {html_escape(lesson)}</h3><p>Bivariate statistics examines the relationship between two variables. This section — {html_escape(lesson)} — is essential for understanding data analysis in real life.</p></body></html>',
        "diagrams": [{"type": "bar_chart", "params": {}}]
    })

unit_data = {
    "name": "Unit 13: Bivariate Statistics",
    "lessons": lessons,
    "lessons_content": lessons_content
}

out_path = OUT / "s3_unit13.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(unit_data, f, indent=2, ensure_ascii=False)

print(f"\nSaved: {out_path}")
