"""Student-safe tool restrictions for classroom use."""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Tools allowed when student_mode is on (education-focused).
ALLOWED_TOOLS = frozenset({
    "web_search",
    "file_processor",
    "youtube_video",
    "screen_process",
    "reminder",
    "weather_report",
    "browser_control",
    "file_controller",
    "code_helper",
    "open_app",
    "save_memory",
    "shutdown_rina",
})

# Blocked in student mode — games, messaging, OS control, code execution chains.
BLOCKED_TOOLS = frozenset({
    "send_message",
    "game_updater",
    "flight_finder",
    "desktop_control",
    "computer_control",
    "computer_settings",
    "dev_agent",
    "agent_task",
    "cmd_control",
    "generated_code",
})


def _profile_path() -> Path:
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).resolve().parent.parent
    return base / "config" / "student_profile.json"


def is_student_mode() -> bool:
    try:
        if _profile_path().exists():
            data = json.loads(_profile_path().read_text(encoding="utf-8"))
            if "student_mode" in data:
                return bool(data["student_mode"])
            role = data.get("role", "student")
            return role == "student"
    except Exception:
        pass
    return True


def tool_allowed(name: str) -> bool:
    if not is_student_mode():
        return True
    if name in BLOCKED_TOOLS:
        return False
    return name in ALLOWED_TOOLS


def blocked_message(name: str) -> str:
    return (
        f"The tool '{name}' is disabled in student mode for safety. "
        "Ask your teacher if you need help with that task."
    )


def filter_tool_declarations(declarations: list[dict]) -> list[dict]:
    if not is_student_mode():
        return declarations
    return [d for d in declarations if d.get("name") in ALLOWED_TOOLS]
