import json
from pathlib import Path

# Fix Windows console encoding
import sys
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

CURRICULUM_DIR = Path("data/curriculum")
HS_PATH = CURRICULUM_DIR / "high_school.json"

# Load original high_school.json
with open(HS_PATH, "r", encoding="utf-8") as f:
    hs_data = json.load(f)

# Old S1 Mathematics units containing quizzes
old_s1_units = hs_data["sub_levels"][0]["subjects"][0]["units"]

# Define the new Unit 1 Sets Quiz
sets_quiz = [
  {
    "difficulty": "Easy",
    "question": "What is a set in mathematics?",
    "options": {
      "A": "A collection of distinct objects with a common feature",
      "B": "A single mathematical number",
      "C": "An equation with variables",
      "D": "A drawing of a circle"
    },
    "answer": "A"
  },
  {
    "difficulty": "Easy",
    "question": "Which symbol is used to denote that an element is a member of a set?",
    "options": {
      "A": "⊂",
      "B": "∈",
      "C": "∉",
      "D": "∅"
    },
    "answer": "B"
  },
  {
    "difficulty": "Easy",
    "question": "If set A = {2, 4, 6, 8}, what is the cardinality n(A)?",
    "options": {
      "A": "2",
      "B": "4",
      "C": "6",
      "D": "8"
    },
    "answer": "B"
  },
  {
    "difficulty": "Medium",
    "question": "If set B has 3 elements, how many subsets does B have?",
    "options": {
      "A": "3",
      "B": "6",
      "C": "8",
      "D": "9"
    },
    "answer": "C"
  },
  {
    "difficulty": "Medium",
    "question": "Given sets P = {a, b, c} and Q = {c, d, e}, what is P ∩ Q?",
    "options": {
      "A": "{a, b, c, d, e}",
      "B": "{c}",
      "C": "{a, b}",
      "D": "∅"
    },
    "answer": "B"
  },
  {
    "difficulty": "Medium",
    "question": "Given sets M = {1, 2} and N = {2, 3}, what is the union M ∪ N?",
    "options": {
      "A": "{2}",
      "B": "{1, 2, 3}",
      "C": "{1, 3}",
      "D": "{1, 2, 2, 3}"
    },
    "answer": "B"
  },
  {
    "difficulty": "Medium",
    "question": "What is the complement of set A, denoted by A', in relation to the universal set ε?",
    "options": {
      "A": "The set of elements in A that are not in ε",
      "B": "The set of elements in ε that are not in A",
      "C": "The union of A and ε",
      "D": "An empty set"
    },
    "answer": "B"
  },
  {
    "difficulty": "Hard",
    "question": "If n(A) = 15, n(B) = 20, and n(A ∩ B) = 5, what is n(A ∪ B)?",
    "options": {
      "A": "35",
      "B": "30",
      "C": "25",
      "D": "15"
    },
    "answer": "B"
  },
  {
    "difficulty": "Hard",
    "question": "Which of the following is always a subset of any set?",
    "options": {
      "A": "The universal set ε",
      "B": "The empty set ∅",
      "C": "The set itself only",
      "D": "A set with one element"
    },
    "answer": "B"
  },
  {
    "difficulty": "Hard",
    "question": "In a Venn diagram, if sets A and B are disjoint, it means:",
    "options": {
      "A": "They share all elements",
      "B": "Their intersection A ∩ B is empty",
      "C": "Their union A ∪ B is empty",
      "D": "One is a subset of the other"
    },
    "answer": "B"
  }
]

# Helper to format answers list to answers string
def format_answers(quiz):
    return ", ".join(f"{i+1}-{q['answer']}" for i, q in enumerate(quiz))

sets_quiz_answers = format_answers(sets_quiz)

# 1. Update S1 Mathematics
new_s1_units = []
for u_num in range(1, 10):
    unit_file = CURRICULUM_DIR / "math" / f"s1_unit{u_num}.json"
    with open(unit_file, "r", encoding="utf-8") as f:
        ud = json.load(f)
    
    # Map quiz and previous_answers
    if u_num == 1:
        quiz = sets_quiz
        prev_ans = ""
    else:
        # u_num >= 2 maps to old_s1_units[u_num - 2]
        old_unit = old_s1_units[u_num - 2]
        quiz = old_unit.get("unit_quiz", [])
        if u_num == 2:
            prev_ans = f"Unit 1 Quiz Answers: {sets_quiz_answers}"
        else:
            # previous unit is u_num - 1
            prev_unit_quiz = old_s1_units[u_num - 3].get("unit_quiz", [])
            prev_unit_ans_str = format_answers(prev_unit_quiz)
            prev_ans = f"Unit {u_num - 1} Quiz Answers: {prev_unit_ans_str}"

    new_s1_units.append({
        "name": ud["name"],
        "previous_answers": prev_ans,
        "lessons": ud["lessons"],
        "lessons_content": [],
        "unit_quiz": quiz
    })

# 2. Update S2 Mathematics
new_s2_units = []
for u_num in range(1, 12):
    unit_file = CURRICULUM_DIR / "math" / f"s2_unit{u_num}.json"
    with open(unit_file, "r", encoding="utf-8") as f:
        ud = json.load(f)
    
    new_s2_units.append({
        "name": ud["name"],
        "previous_answers": "",
        "lessons": ud["lessons"],
        "lessons_content": [],
        "unit_quiz": []
    })

# 3. Update S3 Mathematics
new_s3_units = []
for u_num in range(1, 14):
    unit_file = CURRICULUM_DIR / "math" / f"s3_unit{u_num}.json"
    with open(unit_file, "r", encoding="utf-8") as f:
        ud = json.load(f)
    
    new_s3_units.append({
        "name": ud["name"],
        "previous_answers": "",
        "lessons": ud["lessons"],
        "lessons_content": [],
        "unit_quiz": []
    })

# Replace in hs_data
hs_data["sub_levels"][0]["subjects"][0]["units"] = new_s1_units
hs_data["sub_levels"][1]["subjects"][0]["units"] = new_s2_units
hs_data["sub_levels"][2]["subjects"][0]["units"] = new_s3_units

# Save back high_school.json
with open(HS_PATH, "w", encoding="utf-8") as f:
    json.dump(hs_data, f, indent=2, ensure_ascii=False)

print("Successfully updated high_school.json Mathematics curriculum!")
