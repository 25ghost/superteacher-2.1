"""
gen_reb_content.py V7
Extracts all content from REB S1/S2/S3 SB PDFs — no limits, lesson-specific, no TG.
"""

import json, re, os, sys
from pathlib import Path

try:
    import fitz
except ImportError:
    os.system("pip install PyMuPDF")
    import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import get_reb_book, _BASE

OUT = _BASE / "data" / "curriculum" / "math"
OUT.mkdir(parents=True, exist_ok=True)

PDFS = {
    "s1": get_reb_book("s1"),
    "s2": get_reb_book("s2"),
    "s3": get_reb_book("s3"),
}

P5_SIMPLE = {
    "set": "A set is a collection of things. Like your school bag contains {books, pens, ruler}. We use curly brackets { } to write sets.",
    "indices": "An index (plural: indices) is a shortcut for repeated multiplication. Instead of 2x2x2x2x2, write 2^5. The big number is the base, the small number is the power.",
    "surd": "A surd is a square root you can't simplify to a whole number. v2 is a surd because 2 is not 1, 4, 9, 16...",
    "zero negative": "Any number to power 0 equals 1. A negative power means 1 divided by the positive power: 2^-3 = 1/8.",
    "fractional": "A fractional index means a root: x^(1/2) = vx, x^(1/3) = cube root of x. The denominator is the root, the numerator is the power.",
    "polynomial": "A polynomial is a math expression with letters and numbers joined by + or -. Like 3x + 2y - 5.",
    "simultaneous": "Two equations solved together. x + y = 10 and x - y = 2 only x=6, y=4 works.",
    "inequalit": "Inequalities use <, >, <=, >= instead of =. They show a RANGE of answers.",
    "proportion": "Two equal ratios. 2 eggs for 1 cake 4 eggs for 2 cakes. The ratio 2:1 stays the same.",
    "thales": "If a triangle sits in a circle with one side as the diameter, the opposite angle is always 90 degrees.",
    "pythagoras": "In a right triangle: a^2 + b^2 = c^2. c is the longest side (hypotenuse).",
    "vector": "A vector shows direction AND distance. Like '3 steps north'. It's an arrow with length and direction.",
    "projection": "Projection is like casting a shadow. Parallel projection uses parallel light rays, orthogonal uses perpendicular rays.",
    "isometr": "Moving a shape without changing its size: slide (translation), flip (reflection), or spin (rotation).",
    "statistics grouped": "Grouping numbers into ranges. Ages: 10-14, 15-19, 20-24. Then count each group.",
    "tree venn": "Tree diagrams branch out all possible outcomes. Venn diagrams show how sets overlap.",
    "number base": "We usually count in base 10 (digits 0-9). Computers use base 2 (0 and 1). Different bases = different digits.",
    "algebraic fraction": "A fraction with letters: x/2 or 3/(x+1). Simplify the same way as regular fractions.",
    "quadratic": "An equation with x^2: x^2 - 5x + 6 = 0. The graph is a U-shape (parabola). Like throwing a ball!",
    "function": "A machine: put in a number, it does something, a new number comes out. f(x) = x + 2 means add 2.",
    "compound interest": "Interest on interest. Your money grows faster because you earn on both the original and the earned interest.",
    "trigonometry": "SOH CAH TOA: Sin = Opposite/Hypotenuse, Cos = Adjacent/Hypotenuse, Tan = Opposite/Adjacent.",
    "circle theorem": "Rules about angles in circles. The angle at the center is twice the angle at the edge.",
    "similar": "Same shape, different size. Like a photo and its enlargement. Angles stay the same, sides scale by the same factor.",
    "enlargement": "Make a shape bigger or smaller using a scale factor and a center point.",
    "transform": "Change a shape's position: slide (translation), flip (reflection), turn (rotation), or resize (enlargement).",
    "bivariate": "Two pieces of data per person: height AND weight. Plot them on a scatter graph to see patterns.",
    "probability": "How likely something is. Impossible = 0, certain = 1, coin flip heads = 1/2.",
    "percentage": "Out of 100. 80% = 80 out of 100. A 20,000 Frw shirt at 20% off saves 4,000 Frw.",
    "ratio proportion": "3:2 means 3 of one for every 2 of the other. Cross-multiply to solve.",
    "angle": "The space between two meeting lines. Measured in degrees. A right angle = 90 degrees.",
    "solid": "3D shapes: box (cuboid), can (cylinder), ball (sphere). Volume = space inside. Surface area = total outside area.",
    "equation": "A balanced scale. Do the same to both sides. If x + 3 = 7, subtract 3: x = 4.",
    "gradient": "How steep a line is. Rise/run: how much up divided by across.",
    "midpoint": "The line joining the midpoints of two triangle sides is parallel to the third side and half its length.",
    "median altitude leg": "Special relationships in right triangles. The altitude creates two smaller similar triangles.",
    "collinear": "Collinear points lie on the same straight line. Like three dots on a ruler.",
    "orthogonal": "Orthogonal means perpendicular. Orthogonal vectors meet at a right angle (90 degrees).",
}

def hwrap(title, body):
    return f"<html><body style=\"font-family:Consolas;font-size:10pt\">\n<h3>{title}</h3>\n{body}\n</body></html>"

def get_p5(topic):
    for key, val in P5_SIMPLE.items():
        if key in topic.lower():
            return val
    return ""

def simple_tag(text):
    if not text:
        return ""
    return f"\n\n<div style='background:#FFF3E6;padding:14px;border-radius:8px;border-left:4px solid #EF6C4D;margin:12px 0'><b>Simple Explanation:</b> {text}</div>"

def clean_text(text):
    text = re.sub(r'[?\u0000-\u0008\u000b\u000c\u000e-\u001f]+', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_pdf_text(pdf_path):
    doc = fitz.open(str(pdf_path))
    pages = []
    for pg in range(doc.page_count):
        pages.append(doc[pg].get_text("text"))
    doc.close()
    return '\n'.join(pages)

def find_unit_boundaries(level, text):
    lines = text.split('\n')
    boundaries = {}

    info = {}
    if level == "s1":
        info = {
            1: ("Unit 1: Sets", ["SETS"]),
            2: ("Unit 2: Sets of Numbers", ["SETS OF NUMBERS"]),
            3: ("Unit 3: Linear Functions, Equations and Inequalities", ["LINEAR FUNCTIONS"]),
            4: ("Unit 4: Percentage, Discount, Profit and Loss", ["PERCENTAGE", "DISCOUNT"]),
            5: ("Unit 5: Ratio and Proportion", ["RATIO AND PROPORTION"]),
            6: ("Unit 6: Points, Lines and Angles", ["POINTS", "LINES", "ANGLES"]),
            7: ("Unit 7: Solids", ["SOLIDS"]),
            8: ("Unit 8: Statistics", ["STATISTICS"]),
            9: ("Unit 9: Probability", ["PROBABILITY"]),
        }
    elif level == "s2":
        info = {
            1: ("Unit 1: Indices and Surds", ["INDICES AND SURDS"]),
            2: ("Unit 2: Polynomials", ["POLYNOMIALS"]),
            3: ("Unit 3: Simultaneous Linear Equations and Inequalities", ["SIMULTANEOUS LINEAR"]),
            4: ("Unit 4: Multiplier for Proportional Change", ["MULTIPLIER FOR"]),
            5: ("Unit 5: Thales' Theorem", ["THALES"]),
            6: ("Unit 6: Pythagoras' Theorem", ["PYTHAGORAS"]),
            7: ("Unit 7: Vectors", ["VECTORS"]),
            8: ("Unit 8: Parallel and Orthogonal Projection", ["PARALLEL AND ORTHOGONAL"]),
            9: ("Unit 9: Isometries", ["ISOMETRIES"]),
            10: ("Unit 10: Statistics", ["STATISTICS"]),
            11: ("Unit 11: Tree and Venn Diagrams", ["TREE AND VENN"]),
        }
    elif level == "s3":
        info = {
            1: ("Unit 1: Problem Sets Using Venn Diagrams", ["PROBLEMS ON SETS"]),
            2: ("Unit 2: Number Bases", ["NUMBER BASES"]),
            3: ("Unit 3: Algebraic Fractions", ["ALGEBRAIC FRACTIONS"]),
            4: ("Unit 4: Simultaneous Linear Equations and Inequalities", ["SIMULTANEOUS LINEAR"]),
            5: ("Unit 5: Quadratic Equations", ["QUADRATIC EQUATIONS"]),
            6: ("Unit 6: Linear and Quadratic Functions", ["LINEAR AND QUADRATIC"]),
            7: ("Unit 7: Compound Interest and Proportional Change", ["COMPOUND INTEREST"]),
            8: ("Unit 8: Right-Angled Triangles", ["RIGHT-ANGLED TRIANGLES"]),
            9: ("Unit 9: Circle Theorems", ["CIRCLE THEOREM"]),
            10: ("Unit 10: Collinear Points and Orthogonal Vectors", ["COLLINEAR POINTS"]),
            11: ("Unit 11: Enlargement and Similarity in 2D", ["ENLARGEMENT AND SIMILARITY"]),
            12: ("Unit 12: Inverse and Composite Transformations", ["INVERSE AND COMPOSITE"]),
            13: ("Unit 13: Bivariate Statistics", ["BIVARIATE"]),
        }

    # Find "Key unit competence" lines NOT in TOC (no dots)
    unit_markers = []
    for i, line in enumerate(lines):
        s = line.strip()
        if "key unit competence" in s.lower():
            if '...' not in s and '....' not in s:
                unit_markers.append(i)

    # For each marker, walk back to find ALL CAPS unit title
    seen_nums = set()
    prev_line = 0
    for cl in unit_markers:
        title_line = None
        title_text = ""
        # Search backwards up to 15 lines, checking each against keywords
        for j in range(cl - 1, max(0, cl - 15), -1):
            s = lines[j].strip()
            if not s or len(s) <= 3 or len(s) >= 60:
                continue
            s_upper = s.upper()
            # Check against all unmatched units
            for num, (t, keywords) in sorted(info.items()):
                if num in seen_nums:
                    continue
                if any(kw in s_upper for kw in keywords):
                    title_line = j
                    title_text = s_upper
                    break
            if title_line is not None:
                break
        if title_line is None:
            continue
        # Match to a unit
        for num, (t, keywords) in sorted(info.items()):
            if num in seen_nums:
                continue
            if any(kw in title_text for kw in keywords):
                if title_line >= prev_line:
                    boundaries[num] = {"start": title_line, "title": t}
                    seen_nums.add(num)
                    prev_line = title_line
                    break

    # Fill in any missing units
    for num in sorted(info.keys()):
        if num not in boundaries:
            # Place after previous unit's start
            prev = boundaries.get(num - 1, {})
            boundaries[num] = {"start": prev.get("end", prev.get("start", 0)) + 1 if prev else 0, "title": info[num][0]}
            seen_nums.add(num)

    nums = sorted(boundaries.keys())
    for idx, num in enumerate(nums):
        boundaries[num]["end"] = boundaries[nums[idx + 1]]["start"] if idx + 1 < len(nums) else len(lines) - 1

    return boundaries

def is_heading_like(s):
    """Check if a line looks like a section heading (short, not math expression, not bullet)."""
    if not s or len(s) < 4 or len(s) > 70:
        return False
    if s.startswith(('(', ')', '-', '*', '•', '�', '.')):
        return False
    if re.match(r'^[\d\s+\-÷×=<>()]+$', s):
        return False
    if '×' in s or '÷' in s or '=' in s or '+' in s or '−' in s:
        return False
    return True

LESSON_ALT_KEYS = {
    "Zero and negative indices": ["Negative indices", "Zero index"],
    "Introduction to surds": ["Definition of a surd", "Surds"],
    "Operations on surds": ["Operation on surds"],
    "Rationalising the denominator": ["rationalising the denominator"],
    "Laws of indices": ["Properties of indices", "Laws of indices"],
    "Fractional indices": ["Fractional indices"],
}

def find_lesson_start(unit_text, lesson_name, unit_num, lesson_idx):
    lines = unit_text.split('\n')

    # Build keyword list: exact name + alt keys + progressive subsets
    keywords = [lesson_name]
    if lesson_name in LESSON_ALT_KEYS:
        keywords.extend(LESSON_ALT_KEYS[lesson_name])
    # Progressive subsets (e.g., "Zero and negative indices" -> "negative indices")
    words = lesson_name.lower().split()
    for wlen in range(len(words) - 1, 1, -1):
        for start in range(len(words) - wlen + 1):
            subset = ' '.join(words[start:start + wlen])
            if subset not in {k.lower() for k in keywords}:
                keywords.append(subset)

    # Search for each keyword
    for kw in keywords:
        for i, line in enumerate(lines):
            s = line.strip()
            if kw.lower() in s.lower():
                if is_heading_like(s):
                    return i
                # If it's long but contains the keyword at the start (e.g., section heading with extra text)
                if len(s) < 80 and s.lower().startswith(kw.lower()):
                    return i

    # Fallback: section number inference
    section_num = f"{unit_num}.{lesson_idx + 1}"
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith(section_num + " ") or s.startswith(section_num + "\t"):
            if len(s) > 4:
                return i

    # Last resort: find ALL section headings, pick closest by idx
    heading_lines = []
    for i, line in enumerate(lines):
        s = line.strip()
        m = re.match(rf'^{unit_num}\.(\d+)(\.\d+)?\s+', s)
        if m:
            heading_lines.append((i, s))
    if heading_lines:
        idx = min(lesson_idx, len(heading_lines) - 1)
        return heading_lines[idx][0]

    return 0

def find_lesson_end(unit_text, lesson_name, lessons, lesson_idx):
    if lesson_idx + 1 >= len(lessons):
        return len(unit_text.split('\n'))

    lines = unit_text.split('\n')
    # Use the same strategy as find_lesson_start to find the next lesson
    next_start = find_lesson_start(unit_text, lessons[lesson_idx + 1], 
                                     re.search(r'(\d+)', unit_text.split('\n')[0] if unit_text.strip() else '').group(1) if re.search(r'(\d+)', unit_text.split('\n')[0] if unit_text.strip() else '') else '0',
                                     lesson_idx + 1)
    if next_start > find_lesson_start(unit_text, lesson_name, 0, lesson_idx):
        return next_start
    return len(lines)

def extract_lesson_text(unit_text, lesson_name, all_lessons, lesson_idx, unit_num):
    """Extract the text section belonging to this specific lesson."""
    lines = unit_text.split('\n')
    start = find_lesson_start(unit_text, lesson_name, unit_num, lesson_idx)

    # Find end: next lesson or end of text
    end = len(lines)
    for next_idx in range(lesson_idx + 1, len(all_lessons)):
        next_start = find_lesson_start(unit_text, all_lessons[next_idx], unit_num, next_idx)
        if next_start > start:
            end = next_start
            break

    if end <= start:
        end = len(lines)

    return '\n'.join(lines[start:end])

def parse_lesson_content(text):
    """
    Extract all paragraphs, examples, exercises, activities from lesson text.
    Returns (paragraphs, examples, exercises, activities).
    """
    lines = text.split('\n')
    paragraphs = []
    examples = []
    exercises = []
    activities = []
    solution_blocks = []

    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if not s:
            i += 1
            continue

        # Detect Solution
        if re.match(r'^Solution\s*', s, re.IGNORECASE):
            sol_lines = []
            i += 1
            while i < len(lines):
                ns = lines[i].strip()
                if re.match(r'^(Activity|Example|Exercise|Solution|Unit\s+summary|\d+\.\d+)', ns, re.IGNORECASE):
                    break
                if ns:
                    sol_lines.append(ns)
                i += 1
            if sol_lines:
                solution_blocks.append('\n'.join(sol_lines))
            continue

        # Detect Activity
        if re.match(r'^Activity\s+\d+\.?\d*', s, re.IGNORECASE):
            act_lines = [s]
            i += 1
            while i < len(lines):
                ns = lines[i].strip()
                if re.match(r'^(Activity|Example|Exercise|Solution|Unit\s+summary|\d+\.\d+)', ns, re.IGNORECASE):
                    break
                if ns:
                    act_lines.append(ns)
                i += 1
            activities.append('\n'.join(act_lines))
            continue

        # Detect Example
        if re.match(r'^Example\s+\d+\.?\d*', s, re.IGNORECASE):
            ex_lines = [s]
            i += 1
            while i < len(lines):
                ns = lines[i].strip()
                if re.match(r'^(Activity|Example|Exercise|Solution|Unit\s+summary|\d+\.\d+)', ns, re.IGNORECASE):
                    break
                if ns:
                    ex_lines.append(ns)
                i += 1
            examples.append('\n'.join(ex_lines))
            continue

        # Detect Exercise
        if re.match(r'^Exercise\s+\d+\.?\d*', s, re.IGNORECASE):
            ex_lines = [s]
            i += 1
            while i < len(lines):
                ns = lines[i].strip()
                if re.match(r'^(Activity|Example|Exercise|Solution|Unit\s+summary|\d+\.\d+)', ns, re.IGNORECASE):
                    break
                if ns:
                    ex_lines.append(ns)
                i += 1
            exercises.append('\n'.join(ex_lines))
            continue

        # Section heading (like "1.1.2 Properties of indices")
        if re.match(r'^\d+\.\d+(\.\d+)?\s', s):
            paragraphs.append(f"<h4>{s}</h4>")
            i += 1
            continue

        # Regular reading paragraph
        if len(s) > 5:
            paragraphs.append(s)

        i += 1

    return paragraphs, examples, exercises, activities

def gen_lesson(unit_name, lesson_name, unit_text, all_lessons, lesson_idx, unit_num):
    topic = lesson_name.lower()

    # Extract lesson-specific text
    lesson_text = extract_lesson_text(unit_text, lesson_name, all_lessons, lesson_idx, unit_num)
    paras, examples, exercises, activities = parse_lesson_content(lesson_text)

    # --- Build reading (paragraphs + activities) ---
    reading_parts = []

    # Add paragraphs
    for p in paras:
        reading_parts.append(f"<p>{p}</p>")

    # Add activities
    for act in activities:
        reading_parts.append(
            f"<div style='background:#E8F5E9;padding:12px;border-radius:6px;border-left:4px solid #4CAF50;margin:10px 0'>"
            f"<b>Activity:</b><br>{act.replace(chr(10), '<br>')}</div>"
        )

    # P5 simple explanation
    simple = get_p5(topic)
    if simple:
        reading_parts.append(simple_tag(simple))

    reading_body = '\n'.join(reading_parts) if reading_parts else f"<p><b>{lesson_name}</b> — refer to your textbook for this section.</p>"
    if not paras and not activities:
        # If we found nothing in lesson-specific text, fall back to the first portion of unit text
        fallback_lines = unit_text.split('\n')[:40]
        fallback_text = '\n'.join(fallback_lines)
        fb_paras, fb_examples, fb_exercises, fb_activities = parse_lesson_content(fallback_text)
        if fb_paras:
            reading_body = '\n'.join(f"<p>{p}</p>" for p in fb_paras)
        if fb_activities:
            for act in fb_activities:
                reading_body += f"<div style='background:#E8F5E9;padding:12px;border-radius:6px;border-left:4px solid #4CAF50;margin:10px 0'><b>Activity:</b><br>{act.replace(chr(10), '<br>')}</div>"
        if not examples and fb_examples:
            examples = fb_examples
        if not exercises and fb_exercises:
            exercises = fb_exercises

    reading_html = hwrap(lesson_name, reading_body)

    # --- Build examples ---
    ex_items = []
    for ex in examples:
        ex_items.append(f"<li style='margin-bottom:10px'><b>{ex.split(chr(10))[0]}:</b><br>{'<br>'.join(ex.split(chr(10))[1:])}</li>")
    if not ex_items:
        ex_items.append('<li><i>See worked examples in your textbook.</i></li>')
    example_html = hwrap("Worked Examples", '<ol>' + '\n'.join(ex_items) + '</ol>')

    # --- Build practice (exercises) ---
    pr_items = []
    for ex in exercises:
        lines = ex.split(chr(10))
        pr_items.append(f"<p><b>{lines[0]}:</b><br>{'<br>'.join(lines[1:])}</p>")
    if not pr_items:
        pr_items.append(f"<p>Practice problems on <b>{lesson_name}</b> from your textbook.</p>")
    practice_html = hwrap("Practice Questions", '\n'.join(pr_items))

    # --- Summary ---
    summary_html = hwrap("Summary",
        f"<p>* <b>{lesson_name}</b> is part of <b>{unit_name}</b>.</p>"
        f"<p>* Review the key rules and formulas before attempting problems.</p>"
        f"<p>* Show your working clearly step by step.</p>"
        f"<p>* Check your answers using the Classroom page.</p>")

    # --- Quiz ---
    quiz = {
        "question": f"Which statement best describes {lesson_name}?",
        "options": {"A": "The fundamental rules and definitions of this concept",
                    "B": "An unrelated mathematical idea from another topic",
                    "C": "A topic that only applies in advanced mathematics",
                    "D": "None of the above"},
        "answer": "A"
    }

    # --- Checkbox answers (just exercise prompts, no answer keys) ---
    checkbox_items = ["<h3>Exercises — Check Off When Done</h3>"]
    for ex in exercises:
        title = ex.split(chr(10))[0]
        checkbox_items.append(f"<p><input type='checkbox'> <b>{title}</b></p>")
    if not exercises:
        checkbox_items.append("<p>Complete the exercise problems from your textbook. Check them off here when finished.</p>")
    checkbox_html = '\n'.join(checkbox_items)

    # --- Deep explanation ---
    deep_html = hwrap("Deep Explanation",
        f"<p><b>Why This Matters:</b> {lesson_name} is used in many real-world situations.</p>"
        f"<p><b>Common Pitfalls:</b> Make sure you understand each rule before applying it.</p>"
        f"<p><b>Study Tip:</b> Practice a little every day rather than cramming.</p>")

    return {
        "objectives": f"By the end of this lesson on {lesson_name}, you should be able to understand and apply the key concepts.",
        "reading": reading_html,
        "examples": example_html,
        "practice": practice_html,
        "summary": summary_html,
        "quiz": quiz,
        "practice_answers": "Check your answers in the Classroom page.",
        "checkbox_answers": checkbox_html,
        "deep_explanation": deep_html,
        "diagrams": []
    }

UNITS = {
    "s1": [
        ("s1_unit1", "Unit 1: Sets", ["Introduction to set concept", "Describing sets techniques", "Set notation", "Membership of a set", "Number of members in a set", "Subset of a set", "The number of subsets", "Subsets of numbers", "Venn diagrams", "Set operations", "Other special sets", "Comparison of sets", "General problems on sets", "Relations and functions", "Papygram", "Mapping", "Graphs of relation", "Functions", "Inverse of a function", "Composite functions"]),
        ("s1_unit2", "Unit 2: Sets of Numbers", ["Sets of numbers and subsets", "Natural numbers", "The set of integers", "Rational numbers", "Irrational numbers", "Decimals"]),
        ("s1_unit3", "Unit 3: Linear Functions, Equations and Inequalities", ["Algebraic expressions", "Linear equations in one variable", "Linear inequalities", "Graphs of linear functions", "Word problems on equations and inequalities"]),
        ("s1_unit4", "Unit 4: Percentage, Discount, Profit and Loss", ["Percentage increase and decrease", "Discount and commission", "Profit and loss calculations", "Simple interest", "Real-life financial applications"]),
        ("s1_unit5", "Unit 5: Ratio and Proportion", ["Direct proportion", "Inverse proportion", "Dividing quantities in a given ratio", "Scale drawing and maps", "Applications of ratio and proportion"]),
        ("s1_unit6", "Unit 6: Points, Lines and Angles", ["Points and lines", "Types of angles", "Angle relationships", "Parallel lines and transversals", "Triangles and angle properties"]),
        ("s1_unit7", "Unit 7: Solids", ["Properties of solids", "Surface area of cuboids and cubes", "Volume of cuboids and cubes", "Surface area of cylinders", "Volume of cylinders"]),
        ("s1_unit8", "Unit 8: Statistics (Ungrouped Data)", ["Collecting and organizing data", "Frequency distribution tables", "Bar graphs and pictograms", "Mean, median and mode", "Range and interpretation"]),
        ("s1_unit9", "Unit 9: Probability", ["Introduction to probability", "Sample space and events", "Probability of simple events", "Complementary events", "Applications of probability"]),
    ],
    "s2": [
        ("s2_unit1", "Unit 1: Indices and Surds", ["Laws of indices", "Zero and negative indices", "Fractional indices", "Introduction to surds", "Operations on surds", "Rationalising the denominator"]),
        ("s2_unit2", "Unit 2: Polynomials", ["Introduction to polynomials", "Operations on polynomials", "Algebraic expressions", "Factorization of polynomials", "Special products"]),
        ("s2_unit3", "Unit 3: Simultaneous Linear Equations and Inequalities", ["Equations in two variables", "Solving simultaneous equations", "Inequalities", "Graphical solutions"]),
        ("s2_unit4", "Unit 4: Multiplier for Proportional Change", ["Properties of proportions", "Percentage change", "Applications of proportional change"]),
        ("s2_unit5", "Unit 5: Thales' Theorem", ["Midpoint theorem", "Thales' theorem", "Applications of Thales' theorem"]),
        ("s2_unit6", "Unit 6: Pythagoras' Theorem", ["Pythagoras' theorem", "Applying Pythagoras' theorem", "Real-world applications"]),
        ("s2_unit7", "Unit 7: Vectors", ["Concept of a vector", "Vectors on Cartesian plane", "Operations on vectors", "Magnitude of a vector"]),
        ("s2_unit8", "Unit 8: Parallel and Orthogonal Projection", ["Parallel projection", "Orthogonal projection", "Applications of projection"]),
        ("s2_unit9", "Unit 9: Isometries", ["Introduction to isometries", "Reflection", "Rotation", "Translation"]),
        ("s2_unit10", "Unit 10: Statistics (Grouped Data)", ["Grouped data", "Frequency distribution tables", "Histograms and frequency polygons", "Measures of central tendency", "Reading statistical graphs"]),
        ("s2_unit11", "Unit 11: Tree and Venn Diagrams and Sample Space", ["Introduction to tree diagrams", "Tree diagrams and outcomes", "Probability with tree and Venn diagrams", "Mutually exclusive events", "Independent events"]),
    ],
    "s3": [
        ("s3_unit1", "Unit 1: Problem Sets Using Venn Diagrams", ["Review of union intersection and complement of sets", "Two-set problems", "Three-set problems", "Word problems with Venn diagrams", "Applications of set theory in real life"]),
        ("s3_unit2", "Unit 2: Number Bases", ["Numbers and numerals", "Number bases", "Operations using bases", "Special bases", "Solving equations involving bases"]),
        ("s3_unit3", "Unit 3: Algebraic Fractions", ["Definition of algebraic fractions", "Simplification of fractions", "Addition and subtraction", "Multiplication of algebraic fractions", "Division of algebraic fractions", "Solving rational equations"]),
        ("s3_unit4", "Unit 4: Simultaneous Linear Equations and Inequalities", ["Simultaneous linear equations", "Inequalities", "Graphical representation", "Word problems"]),
        ("s3_unit5", "Unit 5: Quadratic Equations", ["Definition of quadratic equations", "Solving by factorization", "Solving by completing square", "Solving by quadratic formula", "Word problems involving quadratics"]),
        ("s3_unit6", "Unit 6: Linear and Quadratic Functions", ["Linear functions review", "Slope and gradient", "Quadratic functions", "Graphing quadratic functions"]),
        ("s3_unit7", "Unit 7: Compound Interest and Proportional Change", ["Reverse percentage", "Compound interest", "Compound proportional change"]),
        ("s3_unit8", "Unit 8: Right-Angled Triangles", ["Review of Pythagoras theorem", "Median theorem", "Altitude theorem", "Leg theorem", "Introduction to trigonometry", "Trigonometric ratios"]),
        ("s3_unit9", "Unit 9: Circle Theorems", ["Elements of a circle and disk", "Circle theorems", "Angle properties of circles"]),
        ("s3_unit10", "Unit 10: Collinear Points and Orthogonal Vectors", ["Collinear points", "Orthogonal vectors"]),
        ("s3_unit11", "Unit 11: Enlargement and Similarity in 2D", ["Similarity", "Enlargement"]),
        ("s3_unit12", "Unit 12: Inverse and Composite Transformations", ["Composite translations", "Composite reflections", "Composite rotations", "Mixed composite transformations", "Inverse transformations"]),
        ("s3_unit13", "Unit 13: Bivariate Statistics", ["Definition of bivariate data", "Frequency distribution", "Data presentation using graphs", "Scatter diagrams", "Correlation"]),
    ],
}


def generate_all():
    PRESERVE = {"s1_unit1", "s1_unit2"}
    total = 0

    # Extract all PDFs first
    print("Extracting PDFs...")
    sb_texts = {}
    for level, path in PDFS.items():
        if path.exists():
            sb_texts[level] = extract_pdf_text(path)
            print(f"  {level}: {len(sb_texts[level])} chars from {path.name}")
        else:
            print(f"  WARNING: {path} not found, skipping {level}")

    for level in ["s1", "s2", "s3"]:
        sb_text = sb_texts.get(level, "")
        if not sb_text:
            print(f"\nNo text for {level}, skipping")
            continue

        unit_list = UNITS.get(level, [])
        boundaries = find_unit_boundaries(level, sb_text)

        print(f"\n{'='*60}")
        print(f"Processing {level.upper()} ({len(unit_list)} units)")
        print(f"Boundaries found: {sorted(boundaries.keys())}")
        print(f"{'='*60}")

        for filename, unit_name, lessons in unit_list:
            out_path = OUT / f"{filename}.json"
            if filename in PRESERVE and out_path.exists():
                print(f"  {filename}: PRESERVED (existing)")
                continue

            num = int(filename.split('unit')[1].split('_')[0])
            unit_text = ""
            if num in boundaries:
                b = boundaries[num]
                lines = sb_text.split('\n')
                unit_lines = lines[b["start"]:b.get("end", len(lines))]
                unit_text = '\n'.join(unit_lines)
                print(f"  {filename}: {len(unit_text)} chars (lines {b['start']}-{b.get('end', len(lines))})")
            else:
                print(f"  {filename}: boundary NOT found, using full text")
                unit_text = sb_text

            lessons_content = [
                gen_lesson(unit_name, ln, unit_text, lessons, idx, num)
                for idx, ln in enumerate(lessons)
            ]

            with open(out_path, "w", encoding="utf-8") as f:
                json.dump({
                    "name": unit_name,
                    "lessons": lessons,
                    "lessons_content": lessons_content
                }, f, indent=2, ensure_ascii=False)

            # Check content quality
            total_chars = sum(len(c.get("reading", "")) + len(c.get("examples", "")) + len(c.get("practice", "")) for c in lessons_content)
            print(f"    -> {len(lessons)} lessons, {total_chars} total chars")
            total += 1

    print(f"\nDone! Generated {total} unit files")


if __name__ == "__main__":
    generate_all()
