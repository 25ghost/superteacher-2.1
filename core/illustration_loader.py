from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import urlparse

import requests


BASE_DIR = Path(__file__).resolve().parent.parent
TEXTBOOK_CACHE_DIR = BASE_DIR / ".cache" / "textbooks"
ALLOWED_SOURCE_HOSTS = {
    "elearning.reb.rw",
    "www.elearning.rtb.gov.rw",
}
MAX_PDF_BYTES = 200 * 1024 * 1024


class IllustrationLoadError(RuntimeError):
    pass


def _validate_official_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_SOURCE_HOSTS:
        raise IllustrationLoadError("Only official REB and RTB HTTPS resources are allowed.")


def _pdf_cache_path(url: str) -> Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return TEXTBOOK_CACHE_DIR / f"{digest}.pdf"


def _looks_like_pdf(path: Path) -> bool:
    try:
        if path.stat().st_size < 8 or path.stat().st_size > MAX_PDF_BYTES:
            return False
        with path.open("rb") as handle:
            return handle.read(5) == b"%PDF-"
    except OSError:
        return False


def get_cached_official_pdf(url: str) -> Path:
    """Stream one approved official PDF into the on-demand local cache."""
    _validate_official_url(url)
    target = _pdf_cache_path(url)
    if target.is_file() and _looks_like_pdf(target):
        return target

    TEXTBOOK_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(".pdf.part")
    partial.unlink(missing_ok=True)

    try:
        with requests.get(
            url,
            stream=True,
            timeout=(12, 90),
            headers={"User-Agent": "SuperTeacher/2.1 textbook-viewer"},
        ) as response:
            response.raise_for_status()
            _validate_official_url(response.url)
            content_length = int(response.headers.get("Content-Length", "0") or 0)
            if content_length > MAX_PDF_BYTES:
                raise IllustrationLoadError("The official textbook is larger than the safe cache limit.")

            written = 0
            with partial.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    written += len(chunk)
                    if written > MAX_PDF_BYTES:
                        raise IllustrationLoadError("The official textbook exceeded the safe cache limit.")
                    handle.write(chunk)
    except (OSError, requests.RequestException, ValueError) as exc:
        partial.unlink(missing_ok=True)
        raise IllustrationLoadError(f"Could not load the official textbook: {exc}") from exc

    if not _looks_like_pdf(partial):
        partial.unlink(missing_ok=True)
        raise IllustrationLoadError("The downloaded resource is not a valid PDF file.")
    partial.replace(target)
    return target
