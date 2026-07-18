from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_DIR))

from core.lesson_visuals import infer_lesson_diagrams  # noqa: E402


CURRICULUM_DIR = REPO_DIR / "data" / "curriculum"
MANIFEST_DIR = CURRICULUM_DIR / "manifests"
OUTPUT_DIR = CURRICULUM_DIR / "books" / "full"


O_LEVEL_THEMES: dict[str, list[tuple[str, list[str]]]] = {
    "mathematics": [
        ("Number and algebra", ["Number systems", "Algebraic expressions", "Linear equations", "Sequences and patterns"]),
        ("Geometry and measurement", ["Angles and constructions", "Similarity and congruence", "Area and volume", "Coordinate geometry"]),
        ("Functions and data", ["Relations and functions", "Graphs", "Statistics", "Probability"]),
    ],
    "english": [
        ("Listening and speaking", ["Active listening", "Discussion skills", "Oral presentation", "Debate and persuasion"]),
        ("Language use", ["Sentence structure", "Verb forms and agreement", "Vocabulary in context", "Editing and punctuation"]),
        ("Reading", ["Reading for main ideas", "Inference and evidence", "Text structure", "Critical reading"]),
        ("Writing", ["Paragraph development", "Narrative writing", "Expository writing", "Formal letters and reports"]),
        ("Literature", ["Plot and setting", "Character and conflict", "Poetry techniques", "Theme and interpretation"]),
    ],
    "kinyarwanda": [
        ("Kumva no kuvuga", ["Gutega amatwi", "Kuganira neza", "Kuvugira mu ruhame", "Kungurana ibitekerezo"]),
        ("Ikibonezamvugo", ["Amoko y'amagambo", "Interuro n'imyandikire", "Ibihe by'inshinga", "Gukosora amakosa"]),
        ("Gusoma no gusesengura", ["Igitekerezo nyamukuru", "Ingingo n'ibimenyetso", "Gusesengura umwandiko", "Ubuvanganzo nyarwanda"]),
        ("Kwandika", ["Kubaka igika", "Inkuru ngufi", "Ibaruwa n'itangazo", "Inyandiko nsesengurabitekerezo"]),
    ],
    "physics": [
        ("Measurement and mechanics", ["Physical quantities and units", "Motion and graphs", "Forces and Newton's laws", "Work, energy and power"]),
        ("Matter and heat", ["Density and pressure", "Temperature measurement", "Heat transfer", "Thermal expansion"]),
        ("Waves and optics", ["Wave quantities", "Sound", "Reflection and refraction", "Lenses and optical systems"]),
        ("Electricity and magnetism", ["Charge and current", "Circuit calculations", "Magnetic fields", "Electromagnetic induction"]),
        ("Modern applications", ["Atomic structure", "Radioactivity and safety", "Energy technology", "Experimental investigation"]),
    ],
    "chemistry": [
        ("Working scientifically", ["Laboratory safety", "Measurement and observation", "Separation techniques", "Reporting an investigation"]),
        ("Matter and particles", ["States of matter", "Elements and compounds", "Atomic structure", "The periodic table"]),
        ("Bonding and reactions", ["Ionic and covalent bonding", "Writing formulae", "Chemical equations", "Energy changes"]),
        ("Acids and materials", ["Acids, bases and indicators", "Salts", "Metals and reactivity", "Corrosion and prevention"]),
        ("Carbon and environment", ["Carbon compounds", "Fuels", "Water and air chemistry", "Green chemistry"]),
    ],
    "biology": [
        ("Cells and organisation", ["Cell structure", "Microscopy", "Specialised cells", "Levels of organisation"]),
        ("Life processes", ["Nutrition", "Transport", "Respiration", "Excretion"]),
        ("Coordination and reproduction", ["Nervous and hormonal coordination", "Plant responses", "Human reproduction", "Plant reproduction"]),
        ("Inheritance and change", ["Genes and chromosomes", "Variation", "Natural selection", "Biotechnology"]),
        ("Ecology and health", ["Food chains and cycles", "Population studies", "Disease prevention", "Conservation"]),
    ],
    "geography": [
        ("Geographical skills", ["Map symbols and scale", "Direction and coordinates", "Contours and relief", "Fieldwork methods"]),
        ("Physical geography", ["Weather and climate", "Rocks and landforms", "Soils", "Rivers and drainage"]),
        ("Human geography", ["Population", "Settlement", "Migration", "Urbanisation"]),
        ("Economic geography", ["Agriculture", "Industry", "Transport and trade", "Tourism"]),
        ("Rwanda and sustainability", ["Regions of Rwanda", "Natural resources", "Environmental hazards", "Sustainable development"]),
    ],
    "history-citizenship": [
        ("Historical enquiry", ["Sources and evidence", "Chronology", "Cause and consequence", "Interpreting the past"]),
        ("Rwanda through time", ["Pre-colonial Rwanda", "Colonial rule", "Independence", "Reconstruction and development"]),
        ("Regional and world history", ["Great Lakes societies", "African nationalism", "World conflicts", "International cooperation"]),
        ("Citizenship", ["Identity and values", "Rights and responsibilities", "Democratic participation", "Peace and unity"]),
        ("Governance and society", ["Public institutions", "Rule of law", "Gender equality", "Community service"]),
    ],
    "ict": [
        ("Computer systems", ["Hardware components", "Software and operating systems", "Data representation", "Troubleshooting"]),
        ("Productivity tools", ["Word processing", "Spreadsheets", "Presentations", "Collaborative documents"]),
        ("Data and programming", ["Algorithms", "Programming fundamentals", "Databases", "Testing and debugging"]),
        ("Networks and internet", ["Network concepts", "Web research", "Digital communication", "Cloud services"]),
        ("Digital responsibility", ["Cybersecurity", "Privacy", "Digital citizenship", "Technology projects"]),
    ],
    "entrepreneurship": [
        ("Entrepreneurial mindset", ["Needs and opportunities", "Creativity", "Calculated risk", "Ethics and responsibility"]),
        ("From idea to market", ["Business ideas", "Market research", "Customer value", "Marketing"]),
        ("Business planning", ["Business models", "Operations", "People and teamwork", "Business plans"]),
        ("Money and records", ["Costs and pricing", "Cash flow", "Profit and loss", "Record keeping"]),
        ("Growth and impact", ["Quality and customer care", "Risk management", "Sustainable enterprise", "Pitching a venture"]),
    ],
}


A_LEVEL_THEMES: dict[str, list[tuple[str, list[str]]]] = {
    "core-mathematics": [
        ("Algebra", ["Indices and surds", "Polynomials", "Equations and inequalities", "Sequences and series"]),
        ("Functions", ["Domain and range", "Composite and inverse functions", "Transformations of graphs", "Mathematical models"]),
        ("Trigonometry", ["Radian measure", "Trigonometric identities", "Equations", "Applications"]),
        ("Coordinate geometry", ["Straight lines", "Circles", "Parametric representations", "Loci"]),
        ("Calculus", ["Limits and continuity", "Differentiation", "Applications of derivatives", "Integration"]),
        ("Vectors and matrices", ["Vectors", "Vector geometry", "Matrices", "Linear transformations"]),
        ("Probability and statistics", ["Counting techniques", "Probability distributions", "Statistical inference", "Correlation and regression"]),
    ],
    "physics": [
        ("Mechanics", ["Kinematics", "Dynamics", "Momentum", "Circular motion"]),
        ("Matter and energy", ["Properties of matter", "Thermal physics", "Oscillations", "Energy systems"]),
        ("Waves", ["Wave theory", "Superposition", "Optics", "Sound"]),
        ("Electricity", ["Electric fields", "DC circuits", "Capacitance", "Electromagnetic induction"]),
        ("Modern physics", ["Quantum ideas", "Atomic physics", "Nuclear physics", "Applications and safety"]),
        ("Practical physics", ["Measurement uncertainty", "Experimental design", "Data analysis", "Evaluation"]),
    ],
    "chemistry": [
        ("Physical chemistry", ["Atomic structure", "Bonding", "Energetics", "Equilibrium"]),
        ("Inorganic chemistry", ["Periodicity", "Main-group chemistry", "Transition elements", "Qualitative analysis"]),
        ("Organic chemistry", ["Hydrocarbons", "Functional groups", "Reaction mechanisms", "Polymers"]),
        ("Analytical chemistry", ["Moles and titration", "Spectroscopic ideas", "Chromatography", "Data interpretation"]),
        ("Applied chemistry", ["Industrial processes", "Environmental chemistry", "Materials", "Practical investigation"]),
    ],
    "biology": [
        ("Cell biology", ["Cell ultrastructure", "Biological molecules", "Enzymes", "Membrane transport"]),
        ("Physiology", ["Gas exchange", "Transport systems", "Homeostasis", "Coordination"]),
        ("Genetics", ["DNA and protein synthesis", "Inheritance", "Variation", "Biotechnology"]),
        ("Ecology", ["Energy flow", "Nutrient cycles", "Population ecology", "Conservation"]),
        ("Evolution and investigation", ["Natural selection", "Classification", "Experimental design", "Biological data"]),
    ],
    "geography": [
        ("Physical systems", ["Geomorphology", "Weather and climate", "Hydrology", "Ecosystems"]),
        ("Human systems", ["Population", "Settlement", "Development", "Globalisation"]),
        ("Resources", ["Agriculture", "Energy", "Industry", "Transport"]),
        ("Rwanda and the region", ["Regional geography", "Urban change", "Rural transformation", "Environmental management"]),
        ("Geographical investigation", ["GIS and maps", "Fieldwork design", "Data presentation", "Evaluation"]),
    ],
    "history": [
        ("Historical method", ["Source criticism", "Competing interpretations", "Causation", "Essay argument"]),
        ("Rwanda and the Great Lakes", ["State formation", "Colonial encounters", "Independence", "Post-conflict reconstruction"]),
        ("Africa", ["Pre-colonial states", "Colonialism", "Nationalism", "Contemporary integration"]),
        ("World history", ["Revolutions", "World wars", "Cold War", "International institutions"]),
        ("Citizenship and governance", ["Constitutionalism", "Human rights", "Peacebuilding", "Development policy"]),
    ],
    "economics": [
        ("Foundations", ["Scarcity and choice", "Production possibility curves", "Economic systems", "Specialisation"]),
        ("Markets", ["Demand and supply", "Elasticity", "Market structures", "Market failure"]),
        ("Macroeconomics", ["National income", "Inflation and unemployment", "Money and banking", "Fiscal and monetary policy"]),
        ("Development", ["Growth and development", "Poverty and inequality", "Population and labour", "Sustainable development"]),
        ("International economics", ["Trade", "Exchange rates", "Balance of payments", "Regional integration"]),
    ],
    "literature": [
        ("Reading literature", ["Close reading", "Context", "Interpretation", "Critical argument"]),
        ("Prose", ["Narrative voice", "Characterisation", "Structure", "Theme"]),
        ("Drama", ["Dramatic form", "Dialogue and stagecraft", "Conflict", "Performance interpretation"]),
        ("Poetry", ["Voice and tone", "Imagery", "Sound and rhythm", "Comparative analysis"]),
        ("Writing about texts", ["Thesis statements", "Using evidence", "Analytical paragraphs", "Editing literary essays"]),
    ],
    "computer-science": [
        ("Computational thinking", ["Algorithms", "Abstraction", "Decomposition", "Complexity"]),
        ("Programming", ["Data types and control flow", "Functions and modules", "Data structures", "Testing"]),
        ("Computer systems", ["Architecture", "Operating systems", "Data representation", "Logic"]),
        ("Data and networks", ["Databases", "Networking", "Web systems", "Cybersecurity"]),
        ("Software projects", ["Requirements", "Design", "Implementation", "Evaluation"]),
    ],
}


TVET_SPECIALISATIONS: dict[str, list[str]] = {
    "software-development": ["Programming foundations", "Web applications", "Databases", "APIs", "Testing and deployment"],
    "networking": ["Network devices", "Addressing and routing", "Cabling and wireless", "Network services", "Security and troubleshooting"],
    "multimedia": ["Visual design", "Photography and audio", "Video production", "Interactive media", "Publishing workflow"],
    "animal-health": ["Animal anatomy", "Disease prevention", "Clinical observation", "Farm biosecurity", "Animal welfare"],
    "crop-production": ["Soil preparation", "Crop establishment", "Plant nutrition", "Pest management", "Harvest and storage"],
    "food-processing": ["Food safety", "Processing methods", "Preservation", "Quality control", "Packaging"],
    "food-beverage": ["Food safety", "Kitchen operations", "Food service", "Beverage service", "Customer care"],
    "building-construction": ["Construction safety", "Materials", "Setting out", "Masonry and concrete", "Finishing"],
    "automobile-technology": ["Workshop safety", "Engine systems", "Electrical systems", "Braking and steering", "Diagnostics"],
    "tourism": ["Tourism products", "Guiding", "Reservations", "Customer service", "Sustainable tourism"],
    "welding": ["Workshop safety", "Materials", "Welding processes", "Fabrication", "Inspection"],
    "solar-energy": ["Electrical safety", "Solar resources", "PV components", "Installation", "Maintenance"],
    "industrial-electricity": ["Electrical safety", "Circuits", "Machines", "Control systems", "Maintenance"],
    "basic-science": ["Applied mathematics", "Applied science", "Technical communication", "Digital skills", "Workplace learning"],
    "soft-skills": ["Communication", "Teamwork", "Problem solving", "Work readiness", "Entrepreneurship"],
}


def slug(value: str) -> str:
    normalized = value.lower().replace("&", " and ")
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return normalized or "item"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def generated_lesson(level: str, subject: str, unit: str, lesson: str) -> dict[str, Any]:
    is_language = subject.lower() in {"english", "ikinyarwanda", "kinyarwanda", "literature in english"}
    is_science = subject.lower() in {"physics", "chemistry", "biology"}
    is_technical = subject.lower() in TVET_SPECIALISATIONS or "software" in subject.lower()

    method = (
        "Read the example or source text, identify the pattern, practise it in a new context, "
        "then explain why your choice is effective."
        if is_language
        else "Define the system, identify known and unknown quantities, select a justified method, "
        "show each step, and test whether the result is reasonable."
    )
    experiment = (
        f"Plan a small investigation for {lesson}. State the question, variables, equipment, safety controls, "
        "method, results table, conclusion and one improvement."
        if is_science
        else f"Create a practical demonstration of {lesson}. Record your starting assumptions, procedure, "
        "evidence, result and one improvement you would make."
    )
    if is_technical:
        experiment = (
            f"Complete a supervised workshop task demonstrating {lesson}. Use a risk check, tool/material list, "
            "step sequence, quality criteria, evidence record and post-task evaluation."
        )

    return {
        "content": {
            "title": lesson,
            "objectives": (
                f"By the end of this {level} lesson, you should be able to:\n"
                f"- Define and describe the central ideas in {lesson}.\n"
                f"- Connect {lesson} to the wider unit {unit}.\n"
                "- Apply a clear method to an unfamiliar problem or situation.\n"
                "- Explain and evaluate your reasoning using appropriate evidence."
            ),
            "reading": (
                f"STUDY GUIDE — {subject.upper()}\n\n"
                f"{lesson} is studied within {unit}. Begin by identifying the key vocabulary, rules, processes "
                "or relationships in the topic. Separate facts that must be remembered from ideas that must be "
                "understood and methods that must be practised.\n\n"
                f"A reliable learning method is: {method}\n\n"
                "Do not treat the title as an isolated fact. Ask what causes the result, what evidence supports "
                "it, when the method applies, and where it may fail. Compare your notes with the official student "
                "book or syllabus linked by the school whenever that source is available."
            ),
            "deep_explanation": (
                "1. LANGUAGE OF THE TOPIC\n"
                f"Write precise definitions for the important terms in {lesson}. Add an example and a non-example "
                "for each term.\n\n"
                "2. STRUCTURE\n"
                f"Break {lesson} into inputs, process or relationship, and outcome. Draw arrows between ideas that "
                "depend on one another.\n\n"
                "3. REASONING\n"
                "For every rule or claim, ask: what conditions are required, what evidence would confirm it, and "
                "what common mistake would produce a wrong conclusion?\n\n"
                "4. TRANSFER\n"
                f"Apply the idea once in a familiar classroom situation and once in a new Rwandan community, "
                "workplace, environmental or economic context."
            ),
            "examples": (
                f"Worked study example:\n1. Restate the task about {lesson} in your own words.\n"
                "2. List the facts or evidence given.\n3. Select a principle from the lesson and justify it.\n"
                "4. Apply the principle one step at a time.\n5. Check the result against the original task.\n\n"
                "Second example: change one condition in the task. Predict what changes, what remains the same, "
                "and why."
            ),
            "practice": (
                f"1. Define {lesson} in your own words and give one accurate example.\n"
                f"2. Explain how {lesson} connects to {unit}.\n"
                "3. Correct a likely misconception about this topic.\n"
                "4. Apply the lesson to a new real-life or workplace situation and show your reasoning.\n"
                "5. Design a challenging question on the topic, solve it, and explain why the distractors or "
                "alternative approaches are weaker."
            ),
            "practice_answers": (
                "1. A strong answer contains a precise definition, required conditions and a relevant example.\n"
                "2. The connection must name the larger process or relationship, not merely repeat both titles.\n"
                "3. State the mistaken claim, provide a counterexample or evidence, then give the corrected claim.\n"
                "4. Identify the context, choose a justified method, show evidence or working, and check the result.\n"
                "5. The proposed question and solution should test understanding, include plausible alternatives, "
                "and explain the reasoning."
            ),
            "summary": (
                f"- {lesson} belongs to the wider unit {unit}.\n"
                "- Master vocabulary, relationships, method and limitations.\n"
                "- Use evidence or shown working instead of unsupported conclusions.\n"
                "- Review the linked official source where available and ask a teacher about any mismatch."
            ),
            "quiz": {
                "question": f"Which approach best demonstrates mastery of {lesson}?",
                "options": {
                    "A": "Memorising the title only",
                    "B": "Applying the idea, showing evidence and checking the conclusion",
                    "C": "Copying an example without identifying its conditions",
                    "D": "Skipping unfamiliar cases",
                },
                "answer": "B",
            },
            "checkbox_answers": (
                "☐ I can define the key terms without copying.\n"
                "☐ I can explain how the ideas connect.\n"
                "☐ I can apply the method to an unfamiliar case.\n"
                "☐ I can identify and correct a common mistake.\n"
                "☐ I checked my conclusion using evidence, units, logic or source text."
            ),
            "experiment": experiment,
            "assignment": (
                f"Produce a one-page mastery sheet for {lesson}: a concept map, five key terms, one fully worked "
                "application, one misconception with correction, three challenge questions with answers, and a "
                "short reflection on where the topic appears outside class."
            ),
            "diagrams": infer_lesson_diagrams(lesson, subject, unit),
            "provenance": "SuperTeacher structured study guide generated from the catalogued curriculum topic.",
        }
    }


def enrich_legacy(
    raw: dict[str, Any] | None,
    level: str,
    subject: str,
    unit: str,
    lesson: str,
) -> dict[str, Any]:
    if not raw:
        return generated_lesson(level, subject, unit, lesson)

    content = dict(raw)
    fallback = generated_lesson(level, subject, unit, lesson)["content"]
    for key, value in fallback.items():
        if not content.get(key):
            content[key] = value
    content["title"] = lesson
    content["provenance"] = "Migrated from the repository's archived local curriculum notes and enriched by SuperTeacher."
    return {"content": content}


def legacy_lookup(source: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for level in source.get("sub_levels", []):
        match = re.search(r"\b(S[123])\b", str(level.get("name", "")), re.IGNORECASE)
        if not match:
            continue
        level_id = match.group(1).lower()
        for subject in level.get("subjects", []):
            result[(level_id, slug(str(subject.get("name", ""))))] = subject
    return result


def themes_for(pathway: str, subject_id: str, subject_name: str) -> list[tuple[str, list[str]]]:
    if pathway == "o-level":
        return O_LEVEL_THEMES.get(subject_id, O_LEVEL_THEMES["english"])
    if pathway == "a-level":
        return A_LEVEL_THEMES.get(subject_id, A_LEVEL_THEMES["literature"])

    modules = TVET_SPECIALISATIONS.get(subject_id)
    if not modules:
        modules = ["Safety and readiness", "Technical foundations", "Practical operations", "Quality control", "Workplace development"]
    return [
        (module, [
            f"{module}: concepts and terminology",
            f"{module}: tools, materials and preparation",
            f"{module}: practical procedure",
            f"{module}: quality, safety and troubleshooting",
        ])
        for module in modules
    ]


def build_book(
    pathway: str,
    level_id: str,
    subject_record: dict[str, Any],
    legacy_subject: dict[str, Any] | None,
) -> str:
    subject_id = str(subject_record["id"])
    subject_name = str(subject_record["name"])
    level_name = level_id.upper().replace("L", "RQF Level ") if pathway == "tvet" else level_id.upper()
    base_ref = f"books/full/{pathway}/{level_id}/{subject_id}"
    base_dir = CURRICULUM_DIR / base_ref

    units: list[dict[str, Any]] = []
    if legacy_subject and legacy_subject.get("units"):
        source_units = [
            (
                str(item.get("name", f"Unit {index + 1}")),
                list(item.get("lessons", [])),
                list(item.get("lessons_content", [])),
            )
            for index, item in enumerate(legacy_subject["units"])
        ]
    else:
        source_units = [(name, lessons, []) for name, lessons in themes_for(pathway, subject_id, subject_name)]

    for unit_index, (unit_name, lesson_titles, raw_contents) in enumerate(source_units, start=1):
        unit_id = f"unit-{unit_index:02d}-{slug(unit_name)[:48]}"
        unit_ref = f"{base_ref}/units/{unit_id}.json"
        units.append({
            "id": unit_id,
            "name": unit_name,
            "node_type": "unit",
            "description": f"{len(lesson_titles)} on-demand lesson notes",
            "children_ref": unit_ref,
            "status": "ready",
        })

        lesson_nodes: list[dict[str, Any]] = []
        for lesson_index, title_value in enumerate(lesson_titles, start=1):
            lesson_title = str(title_value)
            lesson_id = f"lesson-{lesson_index:02d}-{slug(lesson_title)[:52]}"
            content_ref = f"{base_ref}/lessons/{unit_index:02d}-{lesson_id}.json"
            lesson_nodes.append({
                "id": lesson_id,
                "name": lesson_title,
                "node_type": "lesson",
                "description": "Notes, deep explanation, practice, experiment, assignment and CheckBox answers",
                "content_ref": content_ref,
                "status": "ready",
            })
            raw = raw_contents[lesson_index - 1] if lesson_index <= len(raw_contents) else None
            write_json(
                CURRICULUM_DIR / content_ref,
                enrich_legacy(raw, level_name, subject_name, unit_name, lesson_title),
            )

        write_json(
            CURRICULUM_DIR / unit_ref,
            {
                "metadata": {
                    "competence": f"Build confident understanding and application of {unit_name}.",
                    "lesson_count": len(lesson_nodes),
                },
                "nodes": lesson_nodes,
            },
        )

    book_ref = f"{base_ref}/book.json"
    write_json(
        CURRICULUM_DIR / book_ref,
        {
            "metadata": {
                "book": subject_name,
                "level": level_name,
                "unit_count": len(units),
                "loading": "Each unit manifest and lesson content file is loaded only when selected.",
            },
            "nodes": units,
        },
    )
    return book_ref


def build(source: dict[str, Any]) -> dict[str, int]:
    legacy = legacy_lookup(source)
    statistics = {"books": 0, "units": 0, "lessons": 0}

    for pathway, level_prefix in (("o-level", "s"), ("a-level", "s"), ("tvet", "l")):
        pathway_dir = MANIFEST_DIR / pathway.replace("-", "_")
        if not pathway_dir.is_dir():
            continue
        for manifest_path in sorted(pathway_dir.glob(f"{level_prefix}[0-9].json")):
            level_id = manifest_path.stem
            document = json.loads(manifest_path.read_text(encoding="utf-8"))
            for record in document.get("nodes", []):
                subject_id = str(record["id"])
                aliases = [subject_id]
                if subject_id == "kinyarwanda":
                    aliases.append("ikinyarwanda")
                legacy_subject = next(
                    (legacy.get((level_id, alias)) for alias in aliases if legacy.get((level_id, alias))),
                    None,
                )
                book_ref = build_book(pathway, level_id, record, legacy_subject)
                record["children_ref"] = book_ref
                record["status"] = "ready"
                record["description"] = "Study notes available — opens one lesson at a time"
                statistics["books"] += 1

                book = json.loads((CURRICULUM_DIR / book_ref).read_text(encoding="utf-8"))
                statistics["units"] += len(book.get("nodes", []))
                for unit in book.get("nodes", []):
                    unit_doc = json.loads((CURRICULUM_DIR / unit["children_ref"]).read_text(encoding="utf-8"))
                    statistics["lessons"] += len(unit_doc.get("nodes", []))
            write_json(manifest_path, document)
    return statistics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--legacy-source", required=True, type=Path)
    args = parser.parse_args()
    source = json.loads(args.legacy_source.read_text(encoding="utf-8"))
    stats = build(source)
    print(json.dumps({"status": "ok", **stats}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
