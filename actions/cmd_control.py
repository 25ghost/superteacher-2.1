"""Safe file-open helper for multi-step agent plans (no shell execution)."""
from __future__ import annotations

import re
import sys
from pathlib import Path


def _home_paths() -> dict[str, Path]:
    home = Path.home()
    desktop = home / "Desktop"
    if not desktop.exists() and sys.platform == "win32":
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
            )
            desktop = Path(winreg.QueryValueEx(key, "Desktop")[0])
        except Exception:
            pass
    return {
        "home": home,
        "desktop": desktop,
        "downloads": home / "Downloads",
        "documents": home / "Documents",
    }


def _resolve_file(task: str, paths: dict[str, Path]) -> Path | None:
    task_lower = task.lower()
    folder = paths["desktop"]
    if "download" in task_lower:
        folder = paths["downloads"]
    elif "document" in task_lower:
        folder = paths["documents"]

    match = re.search(r"([\w\-. ]+\.(txt|pdf|docx?|csv|json|py|md))", task, re.I)
    if match:
        name = match.group(1).strip()
        candidate = folder / name
        if candidate.exists():
            return candidate
    return None


def cmd_control(parameters: dict | None = None, player=None, speak=None) -> str:
    params = parameters or {}
    task = (params.get("task") or "").strip()
    if not task:
        return "Please describe what file to open."

    paths = _home_paths()
    target = _resolve_file(task, paths)

    if target and target.exists():
        if sys.platform == "win32":
            import os
            os.startfile(str(target))  # noqa: S606
            return f"Opened {target.name}."
        from actions.open_app import open_app
        return open_app({"app_name": str(target)}, player=player) or f"Opened {target.name}."

    if "notepad" in task.lower():
        from actions.open_app import open_app
        return open_app({"app_name": "notepad"}, player=player) or "Opened Notepad."

    return (
        "I can only open known files safely (no shell commands). "
        "Try file_controller or open_app instead."
    )
