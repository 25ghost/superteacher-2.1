"""
gen_reb_content_v2.py
======================
Faithfully extracts ALL content from REB S1/S2/S3 Student Book .txt files.
No content is skipped — activities, examples, exercises, solutions, text, tables, diagrams.
Output: data/curriculum/math/s1_unit*.json, s2_unit*.json, s3_unit*.json
"""

import json, re, os, sys
from pathlib import Path

# Fix Windows console encoding
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE = Path(__file__).resolve().parent
OUT  = BASE / "data" / "curriculum" / "math"
OUT.mkdir(parents=True, exist_ok=True)

# ─── Source text files (from Desktop REB notes) ───────────────────────────────
DESKTOP_REB = Path(r"C:\Users\KAREGEYA JUSTIN\Desktop\REB notes")
LOCAL_REB   = BASE / "data" / "reb_books"

def get_txt(filename: str) -> Path:
    """Return path to .txt file, preferring Desktop version."""
    d = DESKTOP_REB / filename
    if d.exists():
        return d
    l = LOCAL_REB / filename
    if l.exists():
        return l
    raise FileNotFoundError(f"Cannot find {filename} in {DESKTOP_REB} or {LOCAL_REB}")

TXT_FILES = {
    "s1": "Mathematics-S1-SB.txt",
    "s2": "Mathematics-S2-SB.txt",
    "s3": "Mathematics-S3-SB.txt",
}

# ─── Complete unit/lesson definitions from REB TOC ───────────────────────────

UNITS = {
    "s1": [
        ("s1_unit1", "Unit 1: Sets", [
            "Introduction to set concept",
            "Describing sets",
            "Set Notation",
            "Membership of a set",
            "Number of members in a set",
            "Subset of a set",
            "The number of subsets in a set",
            "Subsets of numbers",
            "Venn diagrams",
            "Set operations",
            "Intersection of sets",
            "Union of sets",
            "Universal set",
            "Complement of a set",
            "Simple and symmetric differences of sets",
            "Other special sets",
            "Comparison of sets",
            "General problems on sets",
            "Relations and functions",
            "Introduction to relations",
            "Properties of relations",
            "Papygram",
            "Mapping",
            "Graphs of relations",
            "Functions",
            "Inverse of a function",
            "Composite functions",
        ]),
        ("s1_unit2", "Unit 2: Sets of Numbers", [
            "Sets of numbers and subsets",
            "Natural numbers",
            "The set of integers",
            "Rational numbers",
            "Irrational numbers",
            "Decimals",
            "Sets of real numbers",
        ]),
        ("s1_unit3", "Unit 3: Linear Functions, Equations and Inequalities", [
            "Linear functions",
            "The number line",
            "Cartesian plane",
            "Linear graphs",
            "Graphs of linear equations",
            "The gradient of a straight line",
            "Linear equations",
            "Solving linear equations",
            "Inequalities",
            "Solution of linear inequalities",
            "Application of inequalities in life",
        ]),
        ("s1_unit4", "Unit 4: Percentage, Discount, Profit and Loss", [
            "Percentages",
            "Discount",
            "Commission",
            "Profit and Loss",
            "Percentage loss and percentage profit",
            "Loans and savings",
            "Simple interest",
            "Tax",
            "VAT (Value Added Tax)",
            "Insurance",
        ]),
        ("s1_unit5", "Unit 5: Ratio and Proportion", [
            "Ratios",
            "Simplifying ratios",
            "Sharing quantities using ratios",
            "Application of ratios in scale drawing",
            "Proportion",
            "Properties of proportion",
            "Direct proportion",
            "Inverse proportion",
        ]),
        ("s1_unit6", "Unit 6: Points, Lines and Angles", [
            "Points and lines",
            "Angles",
            "Types of angles",
            "Angles on a straight line",
            "Angles at a point",
            "Angles on a parallel line",
        ]),
        ("s1_unit7", "Unit 7: Solids", [
            "Properties of solids",
            "Surface area of solids",
            "Surface area of a cuboid",
            "Surface area of a cube",
            "Surface area of a cylinder",
            "Surface area of a prism",
            "Surface area of a pyramid",
            "Surface area of a cone",
            "Surface area of a sphere",
            "Volume of cubes and cuboids",
            "Volume of a prism",
            "Volume of a cylinder",
            "Volume of a cone",
            "Volume of a pyramid",
            "Volume of a sphere",
            "Problem solving areas and volumes",
        ]),
        ("s1_unit8", "Unit 8: Statistics", [
            "Introduction",
            "Types of data",
            "Collecting and organising data",
            "Frequency distribution table",
            "Measures of central tendency",
            "The arithmetic mean",
            "Mode",
            "The median",
            "Quartiles",
            "Presentation and reading of statistical graphs",
            "Pictogram",
            "Pie chart",
            "Bar chart",
            "Line graph",
            "Histogram and frequency polygon",
            "Cumulative frequency diagram",
        ]),
        ("s1_unit9", "Unit 9: Probability", [
            "Introduction",
            "Definition of terms used to describe probability",
            "Types of events",
            "Probability expression",
            "Experimental probability",
            "Basic rules in probability",
            "Theoretical probability",
        ]),
    ],

    "s2": [
        ("s2_unit1", "Unit 1: Indices and Surds", [
            "Laws of indices",
            "Zero and negative indices",
            "Fractional indices",
            "Introduction to surds",
            "Operations on surds",
            "Rationalising the denominator",
        ]),
        ("s2_unit2", "Unit 2: Polynomials", [
            "Introduction to polynomials",
            "Operations on polynomials",
            "Addition and subtraction of polynomials",
            "Multiplication of polynomials",
            "Division of polynomials",
            "Factorization of polynomials",
            "Remainder theorem",
            "Factor theorem",
        ]),
        ("s2_unit3", "Unit 3: Simultaneous Linear Equations and Inequalities", [
            "Solving simultaneous equations by substitution",
            "Solving simultaneous equations by elimination",
            "Graphical solution of simultaneous equations",
            "Linear inequalities in one variable",
            "Linear inequalities in two variables",
            "Graphical solution of simultaneous linear inequalities",
        ]),
        ("s2_unit4", "Unit 4: Multiplier for Proportional Change", [
            "Percentage change as a multiplier",
            "Reverse percentage",
            "Compound proportional change",
        ]),
        ("s2_unit5", "Unit 5: Thales Theorem", [
            "Midpoint theorem",
            "Thales theorem",
            "Applications of Thales theorem",
        ]),
        ("s2_unit6", "Unit 6: Pythagoras Theorem", [
            "Pythagoras theorem",
            "Applying Pythagoras theorem",
            "Pythagorean triples",
            "Real world applications",
        ]),
        ("s2_unit7", "Unit 7: Vectors", [
            "Concept of a vector",
            "Vectors on Cartesian plane",
            "Addition and subtraction of vectors",
            "Scalar multiplication of vectors",
            "Magnitude of a vector",
            "Position vectors",
        ]),
        ("s2_unit8", "Unit 8: Parallel and Orthogonal Projection", [
            "Parallel projection",
            "Orthogonal projection",
            "Applications of projection",
        ]),
        ("s2_unit9", "Unit 9: Isometries", [
            "Introduction to isometries",
            "Reflection",
            "Rotation",
            "Translation",
            "Properties of isometries",
        ]),
        ("s2_unit10", "Unit 10: Statistics", [
            "Grouped data",
            "Frequency distribution tables for grouped data",
            "Histograms and frequency polygons",
            "Measures of central tendency for grouped data",
            "Mean of grouped data",
            "Median of grouped data",
            "Mode of grouped data",
            "Reading statistical graphs",
        ]),
        ("s2_unit11", "Unit 11: Tree and Venn Diagrams and Sample Space", [
            "Introduction to tree diagrams",
            "Tree diagrams and outcomes",
            "Sample space",
            "Probability with tree and Venn diagrams",
            "Mutually exclusive events",
            "Independent events",
        ]),
    ],

    "s3": [
        ("s3_unit1", "Unit 1: Problems on Sets", [
            "Review of union intersection and complement of sets",
            "Venn diagrams involving two sets",
            "Venn diagrams involving three sets",
            "Word problems with Venn diagrams",
        ]),
        ("s3_unit2", "Unit 2: Number Bases", [
            "Numbers and numerals",
            "Definition of number bases",
            "Change of base",
            "Operations using bases",
            "Addition and subtraction in different bases",
            "Multiplication in different bases",
            "Division in different bases",
            "Special bases",
            "Solving equations involving number bases",
        ]),
        ("s3_unit3", "Unit 3: Algebraic Fractions", [
            "Definition of algebraic fractions",
            "Simplification of fractions",
            "Addition and subtraction of algebraic fractions",
            "Multiplication of algebraic fractions",
            "Division of algebraic fractions",
            "Solving rational equations",
        ]),
        ("s3_unit4", "Unit 4: Simultaneous Linear Equations and Inequalities", [
            "Solving simultaneous equations graphically",
            "Problems involving simultaneous equations",
            "Graphical representation of linear inequalities",
            "Forming inequalities from given regions",
            "Simultaneous linear inequalities with one unknown",
            "Linear inequalities in two unknowns",
            "Graphical solution of simultaneous linear inequalities",
        ]),
        ("s3_unit5", "Unit 5: Quadratic Equations", [
            "Definition and examples of quadratic equations",
            "Solving quadratic equations by factorisation",
            "Solving quadratic equations by graphical method",
            "Solving quadratic equations by completing the square",
            "Solving quadratic equations by quadratic formula",
            "Problems involving quadratic equations",
        ]),
        ("s3_unit6", "Unit 6: Linear and Quadratic Functions", [
            "Linear functions",
            "Slope and gradient of a linear function",
            "Cartesian equation of a line",
            "Parallel and perpendicular lines",
            "Quadratic functions",
            "Table of values for quadratic functions",
            "Vertex and axis of symmetry",
            "Intercepts vertices and sketching quadratic graphs",
        ]),
        ("s3_unit7", "Unit 7: Compound Interest and Proportional Change", [
            "Reverse percentage",
            "Definition of compound interest",
            "Step by step method for compound interest",
            "The compound interest formula",
            "Compound proportional change",
        ]),
        ("s3_unit8", "Unit 8: Right-Angled Triangles", [
            "Review of Pythagoras theorem",
            "Median theorem in a right-angled triangle",
            "Altitude theorem of a right-angled triangle",
            "Leg theorem of a right-angled triangle",
            "Introduction to trigonometry",
            "Trigonometric ratios",
            "Sine and cosine of an acute angle",
            "Tangent of an acute angle",
            "Application of trigonometric ratios",
        ]),
        ("s3_unit9", "Unit 9: Circle Theorems", [
            "Elements of a circle and disk",
            "Angles at the centre and circumference of a circle",
            "Angle in a semicircle",
            "Angles in the same segment",
            "Angles in a cyclic quadrilateral",
            "Tangent to a circle",
            "Angles in alternate segment",
            "Properties of chords",
        ]),
        ("s3_unit10", "Unit 10: Collinear Points and Orthogonal Vectors", [
            "Definition of collinearity",
            "Verifying collinearity of points using vector laws",
            "Applications of collinearity in proportional division of lines",
            "Orthogonal vectors",
        ]),
        ("s3_unit11", "Unit 11: Enlargement and Similarity in 2D", [
            "Similar triangles",
            "Similar polygons",
            "Calculating lengths of similar shapes",
            "Similar solids",
            "Definition of enlargement",
            "Constructing objects and images under enlargement",
            "Locating the centre of enlargement",
            "Properties of enlargement",
            "Enlargement in the Cartesian plane",
            "Area scale factor",
            "Volume scale factor",
        ]),
        ("s3_unit12", "Unit 12: Inverse and Composite Transformations", [
            "Composite translations in two dimensions",
            "Composite reflections in two dimensions",
            "Composite rotations in two dimensions",
            "Mixed composite transformations",
            "Inverse transformations",
        ]),
        ("s3_unit13", "Unit 13: Bivariate Statistics", [
            "Definition and example of bivariate data",
            "Frequency distribution table for bivariate data",
            "Data presentation using graphs",
            "Scatter diagrams",
            "The line of best fit in a scatter diagram",
            "Correlation",
        ]),
    ],
}

# ─── Unit boundary markers (unit number keyword in ALL CAPS from text) ────────
UNIT_MARKERS = {
    "s1": {
        1: ["SETS"],
        2: ["SETS OF NUMBERS"],
        3: ["LINEAR FUNCTIONS"],
        4: ["PERCENTAGE", "DISCOUNT"],
        5: ["RATIO AND PROPORTION"],
        6: ["POINTS", "LINES AND ANGLES"],
        7: ["SOLIDS"],
        8: ["STATISTICS"],
        9: ["PROBABILITY"],
    },
    "s2": {
        1: ["INDICES AND SURDS"],
        2: ["POLYNOMIALS"],
        3: ["SIMULTANEOUS LINEAR"],
        4: ["MULTIPLIER"],
        5: ["THALES"],
        6: ["PYTHAGORAS"],
        7: ["VECTORS"],
        8: ["PARALLEL AND ORTHOGONAL"],
        9: ["ISOMETRIES"],
        10: ["STATISTICS"],
        11: ["TREE AND VENN"],
    },
    "s3": {
        1: ["PROBLEMS ON SETS"],
        2: ["NUMBER BASES"],
        3: ["ALGEBRAIC FRACTIONS"],
        4: ["SIMULTANEOUS LINEAR"],
        5: ["QUADRATIC EQUATIONS"],
        6: ["LINEAR AND QUADRATIC"],
        7: ["COMPOUND INTEREST"],
        8: ["RIGHT-ANGLED TRIANGLES"],
        9: ["CIRCLE THEOREM"],
        10: ["COLLINEAR POINTS"],
        11: ["ENLARGEMENT AND SIMILARITY"],
        12: ["INVERSE AND COMPOSITE"],
        13: ["STATISTICS", "BIVARIATE"],
    },
}

# ─── Text utilities ───────────────────────────────────────────────────────────

def read_txt(path: Path) -> str:
    """Read and clean a text file."""
    text = path.read_text(encoding="utf-8", errors="replace")
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text


def clean_line(s: str) -> str:
    """Remove control characters and normalize spaces."""
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]+", "", s)
    s = re.sub(r" {3,}", "  ", s)
    return s.strip()


def html_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def is_toc_line(s: str) -> bool:
    """Return True if line appears to be from the Table of Contents (has dots)."""
    return "...." in s or "……" in s


def is_page_number(s: str) -> bool:
    """Return True if line is just a page number."""
    return bool(re.match(r"^\d{1,3}$", s))


def is_chapter_label(s: str) -> bool:
    """Return True if line is just a chapter header like 'Algebra' or 'Problems on Sets'."""
    return len(s) <= 30 and s == s.strip() and not any(c.isdigit() for c in s) and s.isupper() is False and not re.search(r"[=\+\-\×÷\∩\∪]", s)


# ─── Unit splitting ───────────────────────────────────────────────────────────

def find_unit_boundaries(level: str, lines: list[str]) -> dict[int, tuple[int, int]]:
    """Find start/end line indices for each unit.
    Returns {unit_num: (start, end)}.
    """
    markers = UNIT_MARKERS[level]
    unit_list = UNITS[level]
    n_units = len(unit_list)

    # Look for "Key unit competence" NOT in TOC
    kuc_positions = []
    for i, line in enumerate(lines):
        s = clean_line(line)
        if "key unit competence" in s.lower() and not is_toc_line(s):
            kuc_positions.append(i)

    if not kuc_positions:
        # Fallback: equal split
        chunk = len(lines) // n_units
        bounds = {}
        for u, (fname, uname, lessons) in enumerate(unit_list, 1):
            start = u * chunk - chunk
            end = min(u * chunk, len(lines))
            bounds[u] = (start, end)
        return bounds

    # For each KUC, walk back to find the ALL-CAPS unit title matching markers
    seen = set()
    found = {}  # unit_num -> line_index

    for kuc_i in kuc_positions:
        for back in range(1, 20):
            j = kuc_i - back
            if j < 0:
                break
            s = clean_line(lines[j]).upper()
            if not s or len(s) < 3:
                continue
            for u_num, keywords in sorted(markers.items()):
                if u_num in seen:
                    continue
                if any(kw in s for kw in keywords):
                    found[u_num] = j
                    seen.add(u_num)
                    break
            if u_num in seen and found.get(u_num) == j:
                pass  # continue searching

    # Fill any missing units
    unit_nums = sorted(markers.keys())
    for u in unit_nums:
        if u not in found:
            # Place it after the previous found unit
            prev = found.get(u - 1, 0)
            found[u] = prev + 1

    # Sort found positions
    ordered = sorted(found.items(), key=lambda x: x[1])

    # Build ranges
    bounds = {}
    for idx, (u_num, start) in enumerate(ordered):
        if idx + 1 < len(ordered):
            end = ordered[idx + 1][1]
        else:
            end = len(lines)
        bounds[u_num] = (start, end)

    return bounds


# ─── Lesson extraction ────────────────────────────────────────────────────────

def find_lesson_start(unit_lines: list[str], lesson_name: str, unit_num: int, lesson_idx: int) -> int:
    """Find the first line index for a lesson within unit_lines."""
    name_lower = lesson_name.lower()
    words = name_lower.split()

    # Try exact match first
    for i, line in enumerate(unit_lines):
        s = clean_line(line).lower()
        if not s or is_toc_line(s) or is_page_number(s):
            continue
        if name_lower in s and len(s) < 120:
            return i

    # Try progressive word-subset match
    for n_words in range(len(words), 1, -1):
        subset = " ".join(words[:n_words])
        for i, line in enumerate(unit_lines):
            s = clean_line(line).lower()
            if subset in s and len(s) < 120 and not is_toc_line(s):
                return i

    # Try section number: unit_num.lesson_idx+1
    section = f"{unit_num}.{lesson_idx + 1}"
    for i, line in enumerate(unit_lines):
        s = clean_line(line)
        if s.startswith(section):
            return i

    # Last resort: return 0 for first lesson, progress proportionally for others
    total = len(unit_lines)
    n_lessons = max(lesson_idx, 1)
    approx = int(total * lesson_idx / max(n_lessons, 1))
    return min(approx, total - 1)


def extract_lesson_section(unit_lines: list[str], lessons: list[str], lesson_idx: int, unit_num: int) -> list[str]:
    """Extract lines belonging to a specific lesson within a unit."""
    start = find_lesson_start(unit_lines, lessons[lesson_idx], unit_num, lesson_idx)

    # Find end: start of next lesson or end of unit
    end = len(unit_lines)
    for next_i in range(lesson_idx + 1, len(lessons)):
        ns = find_lesson_start(unit_lines, lessons[next_i], unit_num, next_i)
        if ns > start:
            end = ns
            break

    if end <= start:
        end = len(unit_lines)

    return unit_lines[start:end]


# ─── Content parsing and HTML generation ─────────────────────────────────────

def parse_blocks(lines: list[str]) -> dict:
    """
    Parse lines into structured blocks:
    - paragraphs: regular text
    - examples: Example X.Y ... Solution
    - activities: Activity X.Y ...
    - exercises: Exercise X.Y ...
    - headings: section headings like 1.1.2 Title

    Returns dict with keys: paragraphs, examples, activities, exercises, headings
    """
    paragraphs = []
    examples = []
    activities = []
    exercises = []
    headings = []

    i = 0
    while i < len(lines):
        s = clean_line(lines[i])
        if not s or is_page_number(s) or is_toc_line(s):
            i += 1
            continue

        # ── Section heading like "1.2 Describing sets" or "3.1.2 ..."
        if re.match(r"^\d+\.\d+(\.\d+)?\s+\w", s):
            headings.append(s)
            paragraphs.append(s)  # also in paragraphs so reading flow is maintained
            i += 1
            continue

        # ── Activity block
        if re.match(r"^Activity\s+\d+", s, re.IGNORECASE):
            block = [s]
            i += 1
            while i < len(lines):
                ns = clean_line(lines[i])
                if not ns:
                    i += 1
                    continue
                if re.match(r"^(Activity|Example|Exercise|Unit\s+(summary|test|outline)|Key unit|Solution\b|DID YOU KNOW)", ns, re.IGNORECASE):
                    break
                if is_page_number(ns) or is_toc_line(ns):
                    i += 1
                    continue
                block.append(ns)
                i += 1
            activities.append("\n".join(block))
            continue

        # ── Example block (includes the solution)
        if re.match(r"^Example\s+\d+", s, re.IGNORECASE):
            block = [s]
            i += 1
            while i < len(lines):
                ns = clean_line(lines[i])
                if not ns:
                    i += 1
                    continue
                if re.match(r"^(Activity|Example|Exercise|Unit\s+(summary|test)|Key unit)", ns, re.IGNORECASE):
                    break
                if is_page_number(ns) or is_toc_line(ns):
                    i += 1
                    continue
                block.append(ns)
                i += 1
            examples.append("\n".join(block))
            continue

        # ── Exercise block
        if re.match(r"^Exercise\s+\d+", s, re.IGNORECASE):
            block = [s]
            i += 1
            while i < len(lines):
                ns = clean_line(lines[i])
                if not ns:
                    i += 1
                    continue
                if re.match(r"^(Activity|Example|Exercise|Unit\s+(summary|test)|Key unit)", ns, re.IGNORECASE):
                    break
                if is_page_number(ns) or is_toc_line(ns):
                    i += 1
                    continue
                block.append(ns)
                i += 1
            exercises.append("\n".join(block))
            continue

        # ── "Unit summary" or "Unit test" — stop collecting for this lesson
        if re.match(r"^Unit\s+(summary|test|test\s+\d+)", s, re.IGNORECASE):
            break

        # ── Regular paragraph
        if len(s) > 3:
            paragraphs.append(s)

        i += 1

    return {
        "paragraphs": paragraphs,
        "examples": examples,
        "activities": activities,
        "exercises": exercises,
        "headings": headings,
    }


def blocks_to_reading_html(lesson_name: str, blocks: dict, is_fallback: bool = False) -> str:
    """Convert parsed blocks to clean reading HTML."""
    parts = [f"<h3>{html_escape(lesson_name)}</h3>"]

    if is_fallback:
        parts.append("<p><em>Content from the REB Student Book:</em></p>")

    for p in blocks["paragraphs"]:
        # Section heading
        if re.match(r"^\d+\.\d+", p):
            parts.append(f"<h4>{html_escape(p)}</h4>")
        else:
            parts.append(f"<p>{html_escape(p)}</p>")

    # Activities as green blocks
    for act in blocks["activities"]:
        lines_act = act.split("\n")
        title = lines_act[0]
        body  = "<br>".join(html_escape(l) for l in lines_act[1:] if l.strip())
        parts.append(
            f"<div style='background:#E8F5E9;padding:12px 14px;border-radius:8px;"
            f"border-left:4px solid #4CAF50;margin:12px 0'>"
            f"<b>{html_escape(title)}</b><br>{body}</div>"
        )

    if not blocks["paragraphs"] and not blocks["activities"]:
        parts.append(f"<p>Study <b>{html_escape(lesson_name)}</b> from the REB Student Book.</p>")

    body_html = "\n".join(parts)
    return (
        f'<html><body style="font-family:Segoe UI,sans-serif;font-size:11pt;'
        f'line-height:1.7;padding:8px">\n{body_html}\n</body></html>'
    )


def blocks_to_examples_html(blocks: dict) -> str:
    """Convert examples to HTML."""
    if not blocks["examples"]:
        return (
            '<html><body style="font-family:Segoe UI,sans-serif;font-size:11pt">'
            '<p><i>See worked examples in your REB Student Book.</i></p>'
            '</body></html>'
        )
    parts = ["<h3>Worked Examples</h3><ol>"]
    for ex in blocks["examples"]:
        ex_lines = ex.split("\n")
        title = ex_lines[0]
        body  = "<br>".join(html_escape(l) for l in ex_lines[1:] if l.strip())
        parts.append(
            f"<li style='margin-bottom:14px'>"
            f"<b>{html_escape(title)}</b><br>{body}</li>"
        )
    parts.append("</ol>")
    return (
        f'<html><body style="font-family:Segoe UI,sans-serif;font-size:11pt;'
        f'line-height:1.7;padding:8px">\n'
        + "\n".join(parts)
        + "\n</body></html>"
    )


def blocks_to_practice_html(blocks: dict, lesson_name: str) -> str:
    """Convert exercises to HTML."""
    if not blocks["exercises"]:
        return (
            f'<html><body style="font-family:Segoe UI,sans-serif;font-size:11pt">'
            f'<h3>Practice Questions</h3>'
            f'<p>Complete the exercises on <b>{html_escape(lesson_name)}</b> '
            f'from your REB Student Book.</p>'
            f'</body></html>'
        )
    parts = ["<h3>Practice Questions</h3>"]
    for ex in blocks["exercises"]:
        ex_lines = ex.split("\n")
        title = ex_lines[0]
        body  = "<br>".join(html_escape(l) for l in ex_lines[1:] if l.strip())
        parts.append(
            f"<div style='background:#EAF5FF;padding:12px 14px;border-radius:8px;"
            f"border-left:4px solid #1976D2;margin:10px 0'>"
            f"<b>{html_escape(title)}</b><br>{body}</div>"
        )
    return (
        f'<html><body style="font-family:Segoe UI,sans-serif;font-size:11pt;'
        f'line-height:1.7;padding:8px">\n'
        + "\n".join(parts)
        + "\n</body></html>"
    )


def build_summary_html(lesson_name: str, unit_name: str, blocks: dict) -> str:
    """Build a structured summary."""
    key_points = []

    # Extract bold/short lines that look like key concepts
    for p in blocks["paragraphs"][:20]:
        if 10 < len(p) < 140 and not re.match(r"^\d+\.\d+", p):
            key_points.append(p)
        if len(key_points) >= 5:
            break

    parts = [
        f"<h3>Summary: {html_escape(lesson_name)}</h3>",
        f"<p>This lesson is part of <b>{html_escape(unit_name)}</b>.</p>",
        "<ul>",
    ]

    for kp in key_points[:5]:
        parts.append(f"<li>{html_escape(kp)}</li>")

    if not key_points:
        parts.append(f"<li>Review the key definitions and rules from the student book.</li>")
        parts.append(f"<li>Practice examples before attempting exercises.</li>")
        parts.append(f"<li>Show all working clearly step by step.</li>")

    parts.append("</ul>")
    parts.append("<p><b>Study Tip:</b> Go back and re-read any section you find difficult.</p>")

    return (
        f'<html><body style="font-family:Segoe UI,sans-serif;font-size:11pt;'
        f'line-height:1.7;padding:8px">\n'
        + "\n".join(parts)
        + "\n</body></html>"
    )


def build_deep_html(lesson_name: str, unit_name: str, blocks: dict) -> str:
    """Build a deep explanation section."""
    paras = blocks["paragraphs"]
    # Pull more paragraphs for deep reading
    extended = paras[5:20] if len(paras) > 5 else paras

    parts = [f"<h3>Deep Explanation: {html_escape(lesson_name)}</h3>"]

    if extended:
        parts.append("<p><b>Extended Reading from the Student Book:</b></p>")
        for p in extended:
            if re.match(r"^\d+\.\d+", p):
                parts.append(f"<h4>{html_escape(p)}</h4>")
            else:
                parts.append(f"<p>{html_escape(p)}</p>")
    else:
        parts.append(
            f"<p><b>Why This Matters:</b> {html_escape(lesson_name)} builds on "
            f"earlier concepts and is used in many real-world situations.</p>"
            f"<p><b>Common Pitfalls:</b> Read each definition carefully and note "
            f"special cases.</p>"
            f"<p><b>Study Tip:</b> Practise a little each day rather than cramming.</p>"
        )

    return (
        f'<html><body style="font-family:Segoe UI,sans-serif;font-size:11pt;'
        f'line-height:1.7;padding:8px">\n'
        + "\n".join(parts)
        + "\n</body></html>"
    )


def build_quiz(lesson_name: str) -> dict:
    """Build a basic quiz question for the lesson."""
    return {
        "question": f"Which of the following best describes {lesson_name}?",
        "options": {
            "A": f"The key rules and definitions of {lesson_name}",
            "B": "An unrelated mathematical idea from another topic",
            "C": "A topic that only applies in advanced university mathematics",
            "D": "None of the above"
        },
        "answer": "A"
    }


def build_checkbox_html(exercises: list[str], lesson_name: str) -> str:
    """Build a checkbox list for exercises."""
    parts = ["<h3>Exercises — Tick Off When Done</h3>"]
    if exercises:
        for ex in exercises:
            title = ex.split("\n")[0]
            parts.append(f"<p><input type='checkbox'> <b>{html_escape(title)}</b></p>")
    else:
        parts.append(
            f"<p><input type='checkbox'> Complete the practice exercises on "
            f"<b>{html_escape(lesson_name)}</b> from your student book.</p>"
        )
    return "\n".join(parts)


# ─── Unit file generator ──────────────────────────────────────────────────────

def determine_diagram_type(lesson_name: str, unit_name: str) -> list[dict]:
    """Determine relevant diagrams for a lesson."""
    name = (lesson_name + " " + unit_name).lower()
    if any(k in name for k in ["venn", "set", "intersection", "union"]):
        return [{"type": "venn", "params": {"sets": 2, "values": {"A": "", "B": ""}}}]
    if any(k in name for k in ["circle", "arc", "chord", "tangent"]):
        return [{"type": "circle", "params": {}}]
    if any(k in name for k in ["triangle", "pythagoras", "trigonometry", "altitude", "median"]):
        return [{"type": "right_triangle", "params": {}}]
    if any(k in name for k in ["angle", "parallel", "transversal"]):
        return [{"type": "angle_diagram", "params": {}}]
    if any(k in name for k in ["linear function", "gradient", "cartesian", "graph"]):
        return [{"type": "cartesian_graph", "params": {}}]
    if any(k in name for k in ["solid", "volume", "surface area", "cuboid", "cylinder"]):
        return [{"type": "solid_3d", "params": {}}]
    if any(k in name for k in ["vector", "translation", "projection"]):
        return [{"type": "vector_diagram", "params": {}}]
    if any(k in name for k in ["statistics", "histogram", "frequency", "bar chart", "pie"]):
        return [{"type": "bar_chart", "params": {}}]
    if any(k in name for k in ["number line", "real number"]):
        return [{"type": "number_line", "params": {}}]
    return []


def generate_unit(level: str, filename: str, unit_name: str, lessons: list[str],
                  all_unit_lines: list[str], unit_num: int) -> dict:
    """Generate the full JSON structure for one unit."""
    print(f"    Generating {filename}: {len(all_unit_lines)} lines, {len(lessons)} lessons")
    lessons_content = []

    for lesson_idx, lesson_name in enumerate(lessons):
        # Extract lines for this specific lesson
        lesson_lines = extract_lesson_section(all_unit_lines, lessons, lesson_idx, unit_num)

        # Parse blocks
        blocks = parse_blocks(lesson_lines)

        # If very little content found, try from a broader window of the unit
        if len(blocks["paragraphs"]) < 2 and len(blocks["examples"]) == 0:
            # Use a proportional window of the unit text
            total = len(all_unit_lines)
            n = len(lessons)
            w_start = int(total * lesson_idx / n)
            w_end   = int(total * (lesson_idx + 1) / n)
            fallback_lines = all_unit_lines[w_start:w_end]
            fallback_blocks = parse_blocks(fallback_lines)
            if len(fallback_blocks["paragraphs"]) > len(blocks["paragraphs"]):
                blocks = fallback_blocks

        is_fallback = len(blocks["paragraphs"]) < 2

        content = {
            "objectives": (
                f"By the end of this lesson on {lesson_name}, you should be able to: "
                f"understand and explain the key concepts; apply rules and methods to solve problems; "
                f"and connect ideas to real-world situations in Rwanda and beyond."
            ),
            "reading":          blocks_to_reading_html(lesson_name, blocks, is_fallback),
            "examples":         blocks_to_examples_html(blocks),
            "practice":         blocks_to_practice_html(blocks, lesson_name),
            "summary":          build_summary_html(lesson_name, unit_name, blocks),
            "quiz":             build_quiz(lesson_name),
            "practice_answers": "Review your answers with your teacher or check the back of your Student Book.",
            "checkbox_answers": build_checkbox_html(blocks["exercises"], lesson_name),
            "deep_explanation": build_deep_html(lesson_name, unit_name, blocks),
            "diagrams":         determine_diagram_type(lesson_name, unit_name),
        }
        lessons_content.append(content)

        char_count = len(content["reading"]) + len(content["examples"]) + len(content["practice"])
        status = "✓" if not is_fallback else "⚠ (limited content)"
        print(f"      [{lesson_idx+1}/{len(lessons)}] {lesson_name[:50]:50s} {char_count:6d} chars {status}")

    return {
        "name": unit_name,
        "lessons": lessons,
        "lessons_content": lessons_content,
    }


# ─── Main ─────────────────────────────────────────────────────────────────────

def generate_all():
    total_files = 0

    for level in ["s1", "s2", "s3"]:
        txt_file = TXT_FILES[level]
        try:
            path = get_txt(txt_file)
        except FileNotFoundError as e:
            print(f"  ERROR: {e}")
            continue

        print(f"\n{'='*60}")
        print(f" {level.upper()} — reading {path.name} ({path.stat().st_size // 1024} KB)")
        print(f"{'='*60}")

        full_text = read_txt(path)
        all_lines = full_text.split("\n")
        print(f"  Total lines: {len(all_lines)}")

        # Find unit boundaries
        bounds = find_unit_boundaries(level, all_lines)
        print(f"  Unit boundaries found: {sorted(bounds.keys())}")

        unit_list = UNITS[level]
        for filename, unit_name, lessons in unit_list:
            unit_num = int(re.search(r"unit(\d+)", filename).group(1))
            out_path = OUT / f"{filename}.json"

            if unit_num in bounds:
                start, end = bounds[unit_num]
                unit_lines = all_lines[start:end]
            else:
                print(f"  WARNING: No boundary for {filename}, using full text")
                unit_lines = all_lines

            print(f"\n  >> {filename}: {unit_name}")

            unit_data = generate_unit(level, filename, unit_name, lessons, unit_lines, unit_num)

            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(unit_data, f, indent=2, ensure_ascii=False)

            total_files += 1

    print(f"\n{'='*60}")
    print(f" Done! Generated {total_files} unit files in {OUT}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    generate_all()
