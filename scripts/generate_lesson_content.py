import json, time, sys, pathlib
from google import genai

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"
CURRICULUM_PATH = BASE_DIR / "data" / "curriculum" / "high_school.json"

GEMINI_MODEL = "models/gemini-2.5-flash-lite"

PROMPT_TEMPLATE = """You are a REB (Rwanda Education Board) Mathematics curriculum expert for Senior 1.

Generate lesson content for the following topic:

Subject: {subject}
Unit: {unit}
Lesson: {lesson}

The student is in Senior 1 (S1) in Rwanda. Write in clear English appropriate for 13-14 year old students.

Use Rwanda-specific examples where possible (Rwandan francs, local places, cultural contexts).

Return ONLY valid JSON with this exact structure (no markdown, no code fences):
{{
  "content": {{
    "objectives": "2-3 learning objectives starting with 'By the end of this lesson, you should be able to:'",
    "reading": "Clear explanation of the topic with definitions, step-by-step breakdown, and one Rwanda-focused example. Around 150-200 words.",
    "examples": "Two worked examples with step-by-step solutions. Label them Example 1 and Example 2.",
    "practice": "5 practice questions of increasing difficulty (easy, medium, hard). Number them 1-5.",
    "summary": "A brief summary of the key points in 3-4 bullet points.",
    "quiz": "One multiple choice question with 4 options (A, B, C, D) and the correct answer labeled as 'answer'. Format: {{'question': '...', 'options': {{'A': '...', 'B': '...', 'C': '...', 'D': '...'}}, 'answer': 'A'}}"
  }}
}}
"""

def get_gemini_key():
    with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("gemini_api_key", "")

def load_curriculum():
    with open(CURRICULUM_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_curriculum(data):
    with open(CURRICULUM_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("  [Save] Saved")

def load_progress():
    p = BASE_DIR / "scripts" / ".gen_progress.json"
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_progress(progress):
    p = BASE_DIR / "scripts" / ".gen_progress.json"
    with open(p, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2)

def call_gemini(client, prompt):
    for attempt in range(5):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            msg = str(e)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                wait = 30 * (attempt + 1)
                print(f"  [Quota] retry in {wait}s ({attempt+1}/5)")
                time.sleep(wait)
                continue
            if "503" in msg or "UNAVAILABLE" in msg:
                wait = 15 * (attempt + 1)
                print(f"  [Busy] retry in {wait}s ({attempt+1}/5)")
                time.sleep(wait)
                continue
            print(f"  [Error] {msg[:100]}")
            return None
    return None

def parse_content(text):
    if not text:
        return None
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    text = text.strip()
    try:
        result = json.loads(text)
        if "content" in result:
            return result["content"]
        return result
    except json.JSONDecodeError:
        print(f"  [JSON error] Could not parse response")
        return None

def generate_content(client, subject, unit, lesson):
    prompt = PROMPT_TEMPLATE.format(subject=subject, unit=unit, lesson=lesson)
    text = call_gemini(client, prompt)
    if text:
        return parse_content(text)
    return None

def main():
    api_key = get_gemini_key()
    if not api_key:
        print("[Error] No Gemini API key found")
        sys.exit(1)
    client = genai.Client(api_key=api_key, http_options={"api_version": "v1beta"})

    data = load_curriculum()
    progress = load_progress()
    total = 0
    done = 0
    skipped = 0

    for sub_level in data["sub_levels"]:
        level_name = sub_level["name"]
        if "S1" not in level_name:
            continue
        for subject in sub_level.get("subjects", []):
            subject_name = subject["name"]
            if subject_name != "Mathematics":
                continue
            for unit in subject["units"]:
                unit_name = unit["name"]
                lessons = unit.get("lessons", [])
                contents = unit.get("lessons_content", [])
                for i, lesson_name in enumerate(lessons):
                    total += 1
                    lesson_key = f"S1_Math_{unit_name}_{lesson_name}"
                    if lesson_key in progress and progress[lesson_key] == True:
                        skipped += 1
                        continue
                    if i < len(contents) and contents[i]:
                        skipped += 1
                        continue

                    print(f"\n[{done+1}/{total}] Generating: {lesson_name}")
                    content = generate_content(client, subject_name, unit_name, lesson_name)
                    if content:
                        if "lessons_content" not in unit:
                            unit["lessons_content"] = [None] * len(lessons)
                        while len(unit["lessons_content"]) <= i:
                            unit["lessons_content"].append(None)
                        unit["lessons_content"][i] = content
                        save_curriculum(data)
                        progress[lesson_key] = True
                        save_progress(progress)
                        print("  [OK] Done")
                        done += 1
                    else:
                        print("  [Skip] Failed - will retry next run")
                        progress[lesson_key] = "failed"
                        save_progress(progress)

                    time.sleep(5)

    print(f"\n{'='*40}")
    print(f"Total: {total} | Generated: {done} | Skipped: {skipped}")
    print(f"{'='*40}")

if __name__ == "__main__":
    main()
