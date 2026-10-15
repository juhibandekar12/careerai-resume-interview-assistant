"""
utils/helpers.py
-----------------
Shared utility functions used across the application.
"""

import os
import re
import json
import math
import hashlib
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


def save_uploaded_file(file_bytes: bytes, original_filename: str) -> str:
    """
    Save uploaded file bytes to the uploads/ directory.
    Returns the full path of the saved file.
    """
    safe_name = re.sub(r"[^\w\-_\. ]", "_", original_filename)
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename   = f"{timestamp}_{safe_name}"
    file_path  = UPLOAD_DIR / filename
    file_path.write_bytes(file_bytes)
    logger.info("Saved uploaded file: %s", file_path)
    return str(file_path)


def format_skills_list(skills: list[str]) -> str:
    """Return a comma-separated, title-cased skills string."""
    return ", ".join(s.title() for s in sorted(set(skills)))


def calculate_profile_completeness(resume_data: dict) -> int:
    """
    Return a completeness score (0-100) for a parsed resume.
    """
    score = 0
    checks = {
        "contact_info": 15,
        "skills":       25,
        "education":    20,
        "experience":   25,
        "projects":     10,
        "certifications": 5,
    }
    for field, weight in checks.items():
        val = resume_data.get(field)
        if val and (isinstance(val, dict) and val) or \
           (isinstance(val, list) and len(val) > 0):
            score += weight
    return min(score, 100)


def truncate_text(text: str, max_chars: int = 300) -> str:
    """Truncate text to max_chars, appending '…' if truncated."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "…"


def sanitize_input(text: str) -> str:
    """Strip dangerous characters from user input."""
    return re.sub(r"[<>\"';&]", "", text).strip()


def pretty_json(obj) -> str:
    """Return a pretty-printed JSON string."""
    return json.dumps(obj, indent=2, ensure_ascii=False, default=str)


def normalize_score(score: float, min_val: float = 0, max_val: float = 10) -> float:
    """Clamp and normalize a score to [0, 10]."""
    return max(min_val, min(max_val, float(score)))


def score_to_grade(score: float) -> str:
    """Convert a 0-10 score to a letter grade."""
    if score >= 9:   return "A+"
    if score >= 8:   return "A"
    if score >= 7:   return "B+"
    if score >= 6:   return "B"
    if score >= 5:   return "C"
    if score >= 4:   return "D"
    return "F"


def score_to_color(score: float) -> str:
    """Map a 0-10 score to a hex colour for visualisation."""
    if score >= 8:   return "#10b981"   # emerald
    if score >= 6:   return "#3b82f6"   # blue
    if score >= 4:   return "#f59e0b"   # amber
    return "#ef4444"                    # red


def current_year() -> int:
    return datetime.now().year


def file_hash(path: str) -> str:
    """Return MD5 hash of a file (used to detect duplicate uploads)."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def format_date(dt_str: str | None) -> str:
    """Format an ISO datetime string for display."""
    if not dt_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%d %b %Y, %I:%M %p")
    except (ValueError, TypeError):
        return str(dt_str)
