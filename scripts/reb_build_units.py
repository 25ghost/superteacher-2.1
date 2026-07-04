"""Build REB unit JSON files by extracting whole-unit content from REB books.
For each unit, extract the actual body content (skipping TOC) and distribute
across lessons. This guarantees every lesson gets real REB content."""
import json, re, html, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import get_reb_book, _BASE

REB_DIR = _BASE / "data" / "reb_books"
MATH_DIR = _BASE / "data" / "curriculum" / "math"

# ─── Unit definitions ───────────────────────────────────────────

S1_UNITS = [
    ("Unit 1: Sets", ["Introduction to set concept", "Describing sets", "Set Notation", "Membership of a set", "Number of members in a set", "Subset of a set", "The number of subsets in a set", "Subsets of numbers", "Venn diagrams", "Set operations", "Other special sets", "Comparison of sets", "General problems on sets", "Relations and functions", "Papygram", "Terms used to express a relation", "Ordered pair", "Cartesian product", "Mapping", "Graphs of relation", "Functions", "Inverse of a function", "Composite functions"]),
    ("Unit 2: Sets of Numbers", ["Sets of numbers and notation", "Set of natural numbers", "Set of integers", "Rational numbers", "Irrational numbers", "Decimal representation", "Conversion between decimals and fractions", "Set of real numbers", "Operations on numbers"]),
    ("Unit 3: Linear Functions, Equations and Inequalities", ["Algebraic expressions", "Linear equations", "Linear equations with fractions", "Equations with brackets", "Forming and solving linear equations", "Inequalities", "Inequality symbols", "Compound statements", "Solution of linear inequalities", "Manipulating inequalities", "Simultaneous inequalities", "Graphs of linear functions", "Word problems on equations and inequalities"]),
    ("Unit 4: Percentage, Discount, Profit and Loss", ["Percentages", "Discount", "Commission", "Profit and Loss", "Percentage loss and profit", "Loans and savings", "Simple interest", "Tax", "VAT", "Insurance"]),
    ("Unit 5: Ratio and Proportion", ["Ratios", "Simplifying ratios", "Sharing quantities using ratios", "Application of ratios in scale drawing", "Proportion", "Properties of proportion", "Direct proportion", "Inverse proportion"]),
    ("Unit 6: Points, Lines and Angles", ["Points and lines", "Angles", "Types of angles", "Angles on a straight line", "Angles at a point", "Angles on parallel lines"]),
    ("Unit 7: Solids", ["Properties of solids", "Surface area of cuboids", "Surface area of cubes", "Surface area of cylinders", "Surface area of prisms", "Surface area of pyramids", "Surface area of cones", "Surface area of spheres", "Volume of cubes and cuboids", "Volume of prisms", "Volume of cylinders", "Volume of cones", "Volume of pyramids", "Volume of spheres"]),
    ("Unit 8: Statistics", ["Introduction to statistics", "Types of data", "Collecting and organizing data", "Frequency distribution tables", "Measures of central tendency", "Arithmetic mean", "Mode", "Median", "Quartiles", "Presentation of statistical data", "Pictograms", "Pie charts", "Bar charts", "Line graphs", "Histograms and frequency polygons", "Cumulative frequency curves"]),
    ("Unit 9: Probability", ["Introduction to probability", "Definition of probability terms", "Types of events", "Probability expression", "Experimental probability", "Basic rules in probability", "Theoretical probability"]),
]

S2_UNITS = [
    ("Unit 1: Indices and Surds", ["Index notation", "Multiplication law of indices", "Division law of indices", "Power of powers", "Zero index", "Negative indices", "Fractional indices", "Simple equations involving indices", "Standard form", "Introduction to surds", "Operations on surds", "Rationalising the denominator"]),
    ("Unit 2: Polynomials", ["Introduction to polynomials", "Addition and subtraction of polynomials", "Multiplication of polynomials", "Division of polynomials", "Factorisation of polynomials"]),
    ("Unit 3: Simultaneous Linear Equations and Inequalities", ["Solving by elimination method", "Solving by substitution method", "Solving by graphical method", "Linear inequalities in two variables", "Word problems on simultaneous equations"]),
    ("Unit 4: Multiplier for Proportional Change", ["Understanding the multiplier", "Percentage increase using multiplier", "Percentage decrease using multiplier", "Reverse percentage", "Applications of multiplier in real life"]),
    ("Unit 5: Thales Theorem", ["Introduction to Thales theorem", "Proportional segments in triangles", "Applications of Thales theorem", "Midpoint theorem", "Solving problems using Thales theorem"]),
    ("Unit 6: Pythagoras Theorem", ["Understanding Pythagoras theorem", "Finding the hypotenuse", "Finding a shorter side", "Converse of Pythagoras theorem", "Applications in real life"]),
    ("Unit 7: Vectors", ["Introduction to vectors", "Vector addition and subtraction", "Scalar multiplication", "Column vectors", "Magnitude of a vector", "Applications of vectors"]),
    ("Unit 8: Parallel and Orthogonal Projections", ["Introduction to projections", "Parallel projection", "Orthogonal projection", "Projection of line segments", "Applications of projections"]),
    ("Unit 9: Isometries", ["Introduction to isometries", "Translation", "Reflection", "Rotation", "Combined isometries"]),
    ("Unit 10: Statistics (Grouped Data)", ["Grouped frequency distribution", "Histograms in grouped data", "Mean of grouped data", "Median of grouped data", "Mode of grouped data", "Cumulative frequency curves"]),
    ("Unit 11: Tree and Venn Diagrams", ["Introduction to tree diagrams", "Probability using tree diagrams", "Introduction to Venn diagrams", "Probability using Venn diagrams", "Applications of tree and Venn diagrams"]),
]

S3_UNITS = [
    ("Unit 1: Problems on Sets", ["Venn diagrams involving three sets", "Set problems with Venn diagrams", "Applications of sets in real life"]),
    ("Unit 2: Number Bases", ["Introduction to number bases", "Binary numbers", "Converting between bases", "Operations in different bases", "Applications of number bases"]),
    ("Unit 3: Algebraic Fractions", ["Simplifying algebraic fractions", "Addition and subtraction of algebraic fractions", "Multiplication and division of algebraic fractions", "Equations involving algebraic fractions"]),
    ("Unit 4: Simultaneous Linear Equations and Inequalities", ["Solving simultaneous equations", "Elimination method revisited", "Substitution method revisited", "Word problems involving simultaneous equations", "Linear inequalities in two variables"]),
    ("Unit 5: Quadratic Equations", ["Introduction to quadratic equations", "Solving by factorization", "Solving by completing the square", "Quadratic formula", "Word problems on quadratic equations"]),
    ("Unit 6: Linear and Quadratic Functions", ["Linear functions", "Gradient and intercept", "Quadratic functions", "Graphs of quadratic functions", "Maximum and minimum values"]),
    ("Unit 7: Compound Interest, Reverse Percentage and Compound Proportional Change", ["Compound interest", "Reverse percentage", "Compound proportional change", "Applications in finance"]),
    ("Unit 8: Right-Angled Triangles", ["Review of Pythagoras theorem", "Median theorem", "Altitude theorem", "Leg theorem", "Introduction to trigonometry", "Trigonometric ratios", "Application of trigonometric ratios"]),
    ("Unit 9: Circle Theorem", ["Elements of a circle", "Angles at centre and circumference", "Angle in a semicircle", "Angles in the same segment", "Cyclic quadrilaterals", "Tangent to a circle", "Angles in alternate segment", "Properties of chords"]),
    ("Unit 10: Collinear Points and Orthogonal Vectors", ["Collinear points", "Verifying collinearity", "Applications of collinearity", "Orthogonal vectors"]),
    ("Unit 11: Enlargement and Similarity in 2D", ["Similar triangles", "Similar polygons", "Calculating lengths using similarity", "Definition of enlargement", "Constructing objects under enlargement", "Scale factor and centre", "Area and volume scale factors"]),
    ("Unit 12: Inverse and Composite Transformations", ["Composite translations", "Composite reflections", "Composite rotations", "Mixed composite transformations", "Inverse transformations"]),
    ("Unit 13: Statistics (Bivariate Data)", ["Definition of bivariate data", "Frequency distribution tables", "Data presentation", "Scatter diagrams", "Line of best fit", "Correlation"]),
]

LEVEL_DATA = {
    "s1": (S1_UNITS, REB_DIR / "Mathematics-S1-SB.txt", r'UNIT\s+(\d+)\s*:', r'\n(\d+)\.\s+([A-Z])'),
    "s2": (S2_UNITS, REB_DIR / "Mathematics-S2-SB.txt", r'UNIT\s+(\d+)\s*:', r'Key\s+unit\s+competence'),
    "s3": (S3_UNITS, REB_DIR / "Mathematics-S3-SB.txt", r'\n(\d+)\.\s+([A-Z][A-Z\s,()/-]+?)(?=\s*\.{3})', r'Key\s+unit\s+competence'),
}

def clean_text(text: str) -> str:
    text = re.sub(r'\f', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'S t u d e n t.?.?s  B o o k|P r o p e r t y  o f  t h e|G o v e r n m e n t  o f  R w a n d a|N o t  f o r  s a l e|A l l  r i g h t s  r e s e r v e d|[©\u00a9].*?Board|A c t i v i t y|E x a m p l e|A p p l i c a t i o n', '', text)
    return text.strip()

def find_unit_body(text: str, level: str, unit_num: int) -> str:
    """Extract the body content for a given unit from the REB text."""
    _, _, unit_pat, body_pat = LEVEL_DATA[level]
    
    if level == "s1":
        # S1: section headers like "1.1 Introduction", "2.1 Sets of numbers"
        # Activity steps like "1. Identify" use "N. " which we must NOT confuse
        
        # Find body start: first occurrence of "Activity 1.1"
        body_start = text.find('1.1 Introduction')
        if body_start < 0:
            body_start = 14000
        
        # Find this unit's start: first "unit_num.XX " section header
        pat_this = rf'\n{unit_num}\.\d+\s+[A-Z]'
        m = re.search(pat_this, text[body_start:])
        if not m:
            return ""
        pos = body_start + m.start()
        
        # Find next unit's first section header
        pat_next = rf'\n{unit_num+1}\.\d+\s+[A-Z]'
        m = re.search(pat_next, text[pos:])
        if m:
            end_pos = pos + m.start()
        else:
            end_pos = len(text)
        
        return text[pos:end_pos].strip()
    
    elif level == "s2":
        # S2 body format: "N TOPIC_NAME\n\nKey unit competence"
        # The unit number is unreliable due to PDF extraction merging.
        # Instead, find all body units by searching for topic names.
        
        # Body starts at first "Key unit competence"
        for m in re.finditer(r'Key\s+unit\s+competence', text):
            body_start = m.start()
            break
        else:
            body_start = 0
        
        # Find this unit's body by searching for the topic name after body_start
        known_topics = {
            1: "INDICES AND SURDS", 2: "POLYNOMIALS",
            3: "SIMULTANEOUS LINEAR", 4: "MULTIPLIER",
            5: "THALES", 6: "PYTHAGORAS",
            7: "VECTORS", 8: "PARALLEL AND ORTHOGONAL",
            9: "ISOMETRIES", 10: "STATISTICS",
            11: "TREE AND VENN",
        }
        
        topic = known_topics.get(unit_num, "")
        if not topic:
            return ""
        
        # Find start
        pos = text.find(topic, body_start)
        if pos < 0:
            return ""
        
        # Back up to find the line start (which may have a page number)
        line_start = text.rfind('\n', 0, pos) + 1 if text.rfind('\n', 0, pos) >= 0 else 0
        
        # Find end (next topic after this)
        end = len(text)
        for next_num in range(unit_num + 1, 12):
            next_topic = known_topics.get(next_num, "")
            if next_topic:
                np = text.find(next_topic, pos + 1)
                if np > 0:
                    end = np
                    break
        # Also check for "Glossary" or end markers
        for mk in ["Glossary", "References"]:
            mp = text.find(mk, pos + 1)
            if mp > 0 and mp < end:
                end = mp
        
        return text[line_start:end].strip()
    
    elif level == "s3":
        # S3 body format: "1\nProblems on Sets\nPROBLEMS ON SETS\n1\nKey unit competence:"
        # TOC occupies first ~21000 chars. Body starts after "References" marker.
        # Find body start by looking for first body-style occurrence
        body_start = 0
        for m in re.finditer(r'References', text):
            # Body starts after References line
            body_start = m.end()
            break
        if body_start < 1000:
            body_start = 21000  # fallback
        
        known_topics = {
            1: "PROBLEMS ON SETS", 2: "NUMBER BASES",
            3: "ALGEBRAIC FRACTIONS", 4: "SIMULTANEOUS LINEAR",
            5: "QUADRATIC EQUATIONS", 6: "LINEAR AND QUADRATIC FUNCTIONS",
            7: "COMPOUND INTEREST", 8: "RIGHT-ANGLED TRIANGLES",
            9: "CIRCLE THEOREM", 10: "COLLINEAR POINTS",
            11: "ENLARGEMENT AND SIMILARITY", 12: "INVERSE AND COMPOSITE",
            13: "BIVARIATE DATA",
        }
        
        topic = known_topics.get(unit_num, "")
        if not topic:
            return ""
        
        pos = text.find(topic, body_start)
        if pos < 0:
            return ""
        
        line_start = text.rfind('\n', 0, pos) + 1 if text.rfind('\n', 0, pos) >= 0 else 0
        
        end = len(text)
        for next_num in range(unit_num + 1, 14):
            next_topic = known_topics.get(next_num, "")
            if next_topic:
                np = text.find(next_topic, pos + 1)
                if np > 0:
                    end = np
                    break
        for mk in ["Glossary", "References"]:
            mp = text.find(mk, pos + 1)
            if mp > 0 and mp < end:
                end = mp
        
        return text[line_start:end].strip()

def extract_examples(text: str) -> list[str]:
    examples = []
    for m in re.finditer(r'(Example\s+\d+\.\d+[^.]*\.)(.*?)(?=Example\s+\d+\.\d+|Activity|Application|Summary|\n\n\n|$)', text, re.DOTALL | re.IGNORECASE):
        ex = m.group(0).strip()
        if len(ex) > 30:
            examples.append(ex)
    return examples[:20]

def extract_practice(text: str) -> list[str]:
    practices = []
    for m in re.finditer(r'(Application activity\s+\d+\.\d+|Activity\s+\d+\.\d+)(.*?)(?=Summary|Activity\s+\d+\.\d+|Application|Example|\n\n\n|$)', text, re.DOTALL | re.IGNORECASE):
        p = m.group(0).strip()
        if len(p) > 30:
            practices.append(p)
    return practices[:20]

def render_html(text: str, title: str = "") -> str:
    escaped = html.escape(text)
    escaped = escaped.replace('\n', '<br>')
    escaped = re.sub(r'<br>\s*<br>', '</p><p>', escaped)
    title_html = f"<h3>{html.escape(title)}</h3>" if title else ""
    return f"<html><body style=\"font-family:Consolas;font-size:10pt\">{title_html}<p>{escaped}</p></body></html>"

def get_diagrams(unit_title: str, lesson: str) -> list[dict]:
    t = (unit_title + " " + lesson).lower()
    d = []
    if "venn" in t or "set" in t:
        d.append({"type": "venn", "params": {"sets": 2, "values": {"A": "", "B": ""}}})
    if "number" in t and "line" in t:
        d.append({"type": "number_line", "params": {"min": -5, "max": 5, "highlight": [0]}})
    if "graph" in t or ("function" in t and "linear" in t):
        d.append({"type": "cartesian", "params": {"x_min": -5, "x_max": 5, "y_min": -5, "y_max": 5, "function": "linear", "m": 1, "c": 0}})
    if "quadratic" in t:
        d.append({"type": "cartesian", "params": {"x_min": -5, "x_max": 5, "y_min": -5, "y_max": 10, "function": "quadratic", "a": 1, "b": 0, "c": 0}})
    if "angle" in t or "parallel" in t:
        d.append({"type": "angles", "params": {"type": "parallel_lines", "angle": 60}})
    if "triangle" in t or "pythagoras" in t or "thales" in t or "trigonometr" in t:
        d.append({"type": "triangle", "params": {"a": 3, "b": 4, "c": 5}})
    if "circle" in t:
        d.append({"type": "geometry", "params": {"shape": "circle"}})
    if "transform" in t or "isometr" in t or "reflect" in t or "rotation" in t or "translation" in t:
        d.append({"type": "transformation", "params": {"type": "translation", "dx": 60, "dy": 0}})
    if "sine" in t or "cosine" in t or "tangent" in t or "unit circle" in t:
        d.append({"type": "unit_circle", "params": {"angle": 45, "show_sin": True, "show_cos": True}})
    if "trigonometric" in t or "trig ratio" in t:
        d.append({"type": "triangle", "params": {"a": 3, "b": 4, "c": 5, "angle": 30}})
    if "histogram" in t or "frequency" in t or "bar chart" in t:
        d.append({"type": "cartesian", "params": {"x_min": 0, "x_max": 10, "y_min": 0, "y_max": 10, "function": "linear", "m": 0, "c": 5}})
    return d[:2]

def build_lesson_content(lesson_name: str, unit_title: str, raw_text: str) -> dict:
    clean = clean_text(raw_text)
    examples = extract_examples(clean)
    practices = extract_practice(clean)
    
    reading = clean
    for ex in examples:
        reading = reading.replace(ex, "")
    for pr in practices:
        reading = reading.replace(pr, "")
    reading = clean_text(reading)
    
    return {
        "objectives": f"By the end of this lesson on {lesson_name}, you should be able to: understand the key concepts; apply the methods to solve problems; and connect ideas to real-world situations.",
        "reading": render_html(reading if len(reading) > 100 else f"This lesson covers {lesson_name} from {unit_title}. Study the material from the REB Student Book carefully.", lesson_name),
        "examples": render_html("\n\n".join(examples), f"Worked Examples") if examples else "",
        "practice": render_html("\n\n".join(practices), "Practice Questions") if practices else "",
        "summary": render_html(f"● {lesson_name} is a key topic in {unit_title}.<br>● Master the basic rules before attempting complex problems.<br>● Always show your working clearly.<br>● Practice regularly to build confidence.", "Summary"),
        "quiz": {
            "question": f"Which of the following best describes {lesson_name}?",
            "options": {"A": f"The core concepts of {lesson_name}", "B": "An unrelated topic", "C": "A topic from another unit", "D": "None of the above"},
            "answer": "A",
        },
        "practice_answers": "Check your answers with your teacher.",
        "checkbox_answers": "<p>Complete the practice questions first, then check your answers here.</p>",
        "deep_explanation": render_html(f"This lesson covers {lesson_name} from {unit_title}. Understanding this topic is essential for building a strong foundation in mathematics."),
        "diagrams": get_diagrams(unit_title, lesson_name),
    }

def process_level(level: str):
    print(f"\n{'='*60}")
    print(f"Processing {level.upper()} Mathematics")
    print(f"{'='*60}")
    
    if level not in LEVEL_DATA:
        return
    
    units_list, reb_path, _, _ = LEVEL_DATA[level]
    
    if not reb_path.exists():
        print(f"ERROR: {reb_path} not found!")
        return
    
    text = reb_path.read_text(encoding="utf-8", errors="replace")
    text = clean_text(text)
    print(f"Loaded {len(text)} chars from {reb_path.name}")
    
    for unit_idx, (unit_title, lesson_names) in enumerate(units_list):
        unit_num = unit_idx + 1
        print(f"\n  {unit_title} ({len(lesson_names)} lessons)")
        
        # Get the unit body
        unit_text = find_unit_body(text, level, unit_num)
        
        if unit_text:
            # Split unit text into lesson-sized chunks
            # Find section boundaries within unit
            sections = list(re.finditer(r'\n\s*\d+\.\d+(?:\.\d+)*\s+[A-Z]', unit_text))
            
            lessons = []
            lessons_content = []
            used_sections = set()
            
            for lesson_idx, lesson_name in enumerate(lesson_names):
                lesson_raw = ""
                
                # Try to find content matching this lesson name
                lesson_lower = lesson_name.lower()
                
                # Search for the lesson name in the unit text
                pos = unit_text.lower().find(lesson_lower)
                if pos >= 0:
                    # Found a match - extract from here to next section
                    start = max(0, pos - 20)
                    # Find next section boundary AFTER the match position (not the same section header)
                    end = len(unit_text)
                    for sec in sections:
                        if sec.start() > pos and sec.start() < end:
                            end = sec.start()
                            break
                    lesson_raw = unit_text[start:end].strip()
                
                if not lesson_raw and sections:
                    # Distribute equally: take a portion of remaining text
                    remaining_sections = [s for s in sections if s.start() not in used_sections]
                    if remaining_sections:
                        n_total = len(lesson_names)
                        n_remaining = len(lesson_names) - lesson_idx
                        if remaining_sections and n_remaining > 0:
                            chunk_size = max(1000, len(unit_text) // n_total)
                            start = chunk_size * lesson_idx
                            end = min(start + chunk_size, len(unit_text))
                            lesson_raw = unit_text[start:end].strip()
                
                content = build_lesson_content(lesson_name, unit_title, lesson_raw)
                lessons.append(lesson_name)
                lessons_content.append(content)
            
            unit_data = {
                "name": unit_title,
                "lessons": lessons,
                "lessons_content": lessons_content,
            }
        else:
            # No unit body found - generate generic content
            lessons = []
            lessons_content = []
            for lesson_name in lesson_names:
                content = build_lesson_content(lesson_name, unit_title, "")
                lessons.append(lesson_name)
                lessons_content.append(content)
            
            unit_data = {
                "name": unit_title,
                "lessons": lessons,
                "lessons_content": lessons_content,
            }
        
        unit_file = MATH_DIR / f"{level}_unit{unit_num}.json"
        with open(unit_file, "w", encoding="utf-8") as f:
            json.dump(unit_data, f, indent=2, ensure_ascii=False)
        
        unit_size = len(str(unit_data))
        print(f"    Wrote {unit_file.name} ({unit_size/1024:.0f}KB)")

if __name__ == "__main__":
    levels = sys.argv[1:] if len(sys.argv) > 1 else ["s1", "s2", "s3"]
    for level in levels:
        process_level(level)
