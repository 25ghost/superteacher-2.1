"""Real progress stats derived from student_profile.json."""
from __future__ import annotations

from datetime import date, timedelta


def lessons_count(profile: dict) -> int:
    return len(profile.get("completed_lessons", []))


def quiz_average(profile: dict) -> str:
    scores = profile.get("quiz_scores", [])
    if not scores:
        return "—"
    return f"{int(sum(scores) / len(scores))}%"


def record_quiz_score(profile: dict, score: int) -> None:
    scores = profile.setdefault("quiz_scores", [])
    scores.append(max(0, min(100, int(score))))
    if len(scores) > 50:
        profile["quiz_scores"] = scores[-50:]
    profile["xp"] = int(profile.get("xp", 0)) + max(10, score // 5)


def touch_study_day(profile: dict) -> None:
    """Update streak when the student completes a lesson or quiz."""
    today = date.today().isoformat()
    last = profile.get("last_study_date", "")
    streak = int(profile.get("streak", 0))
    if last == today:
        profile["last_study_date"] = today
        return
    if last:
        try:
            prev = date.fromisoformat(last)
            if prev == date.today() - timedelta(days=1):
                streak += 1
            elif prev != date.today():
                streak = 1
        except ValueError:
            streak = 1
    else:
        streak = 1
    profile["streak"] = streak
    profile["last_study_date"] = today
