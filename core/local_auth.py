"""Local account storage for single-machine Rahura deployments."""
from __future__ import annotations

import hashlib
import json
import secrets
import sys
from pathlib import Path


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


ACCOUNTS_PATH = _base_dir() / "config" / "accounts.json"
_SALT_PREFIX = "rahura-rina-v1:"


def _hash_password(password: str, salt: str) -> str:
    digest = hashlib.sha256(f"{_SALT_PREFIX}{salt}:{password}".encode()).hexdigest()
    return f"sha256:{salt}:{digest}"


def _verify_hash(password: str, stored: str) -> bool:
    try:
        scheme, salt, expected = stored.split(":", 2)
    except ValueError:
        return False
    if scheme != "sha256":
        return False
    return _hash_password(password, salt).split(":", 2)[2] == expected


def _load_accounts() -> list[dict]:
    if not ACCOUNTS_PATH.exists():
        return []
    try:
        data = json.loads(ACCOUNTS_PATH.read_text(encoding="utf-8"))
        return data.get("accounts", []) if isinstance(data, dict) else []
    except Exception:
        return []


def _save_accounts(accounts: list[dict]) -> None:
    ACCOUNTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    ACCOUNTS_PATH.write_text(
        json.dumps({"accounts": accounts}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def has_accounts() -> bool:
    return bool(_load_accounts())


def register(username: str, password: str, role: str = "student") -> tuple[bool, str]:
    username = username.strip()
    password = password.strip()
    if len(username) < 2:
        return False, "Username must be at least 2 characters."
    if len(password) < 4:
        return False, "Password must be at least 4 characters."
    accounts = _load_accounts()
    key = username.lower()
    if any(a.get("username", "").lower() == key for a in accounts):
        return False, "That username is already taken on this device."
    salt = secrets.token_hex(8)
    accounts.append({
        "username": username,
        "password_hash": _hash_password(password, salt),
        "role": role if role in ("student", "teacher") else "student",
    })
    _save_accounts(accounts)
    return True, "Account created."


def authenticate(username: str, password: str) -> tuple[bool, str, str]:
    """Returns (ok, message, role)."""
    username = username.strip()
    password = password.strip()
    if not username or not password:
        return False, "Enter username and password.", "student"
    accounts = _load_accounts()
    if not accounts:
        ok, msg = register(username, password, role="student")
        if ok:
            return True, "Welcome! Your local account was created.", "student"
        return False, msg, "student"
    for acct in accounts:
        if acct.get("username", "").lower() == username.lower():
            if _verify_hash(password, acct.get("password_hash", "")):
                return True, "Signed in.", acct.get("role", "student")
            return False, "Incorrect password.", "student"
    return False, "No account found with that username.", "student"
