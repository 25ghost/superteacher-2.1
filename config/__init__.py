import json, os
from pathlib import Path

_BASE = Path(__file__).resolve().parent.parent
_CONFIG_PATH = _BASE / "config" / "api_keys.json"
_PATHS_CONFIG_PATH = _BASE / "config" / "paths.json"
_paths_cache = None

def get_config() -> dict:
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_os() -> str:
    return get_config().get("os_system", "windows").lower()

def is_windows() -> bool: return get_os() == "windows"
def is_mac()     -> bool: return get_os() == "mac"
def is_linux()   -> bool: return get_os() == "linux"

def get_paths_config() -> dict:
    global _paths_cache
    if _paths_cache is None:
        with open(_PATHS_CONFIG_PATH, "r", encoding="utf-8") as f:
            _paths_cache = json.load(f)
    return _paths_cache

def get_reb_book(level: str) -> Path:
    cfg = get_paths_config()
    rel = cfg["reb_books_dir"]
    fname = cfg["reb_levels"][level]
    return _BASE / rel / fname
