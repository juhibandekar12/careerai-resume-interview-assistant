"""
scripts/check_setup.py
-----------------------
Verifies that all required dependencies and services are available.
Run before starting the application:
    python scripts/check_setup.py
"""

import sys
import os
import importlib

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = "✅"
FAIL = "❌"
WARN = "⚠️ "

results = []

def check(label: str, fn):
    try:
        fn()
        results.append((PASS, label, "OK"))
    except Exception as e:
        results.append((FAIL, label, str(e)))


# ── Python version ─────────────────────────────────────────
def _py_version():
    assert sys.version_info >= (3, 10), f"Python 3.10+ required, got {sys.version}"

check("Python 3.10+", _py_version)


# ── Core packages ──────────────────────────────────────────
for pkg in [
    "fastapi", "uvicorn", "streamlit", "requests",
    "pdfplumber", "PyPDF2", "sklearn", "numpy", "pandas",
    "plotly", "pydantic",
]:
    def _import(p=pkg):
        importlib.import_module(p)
    check(f"Package: {pkg}", _import)


# ── spaCy + model ──────────────────────────────────────────
def _spacy():
    import spacy
    nlp = spacy.load("en_core_web_sm")

check("spaCy + en_core_web_sm", _spacy)


# ── Database ───────────────────────────────────────────────
def _db():
    from database.db import init_db, fetchone
    init_db()
    row = fetchone("SELECT COUNT(*) as cnt FROM users")
    assert row is not None

check("SQLite database", _db)


# ── job_roles.json ─────────────────────────────────────────
def _jobs():
    import json
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "job_roles.json")
    with open(path) as f:
        data = json.load(f)
    assert len(data) > 0

check("Job roles dataset", _jobs)


# ── Groq API (required for LLM features) ──────────────────
try:
    from utils.llm_service import is_groq_available
    if is_groq_available():
        results.append((PASS, "Groq API Connection", "Available ✓"))
    else:
        results.append((WARN, "Groq API Connection", "Key not configured – heuristic fallback active"))
except Exception as e:
    results.append((WARN, "Groq API Connection", str(e)))


# ── Print report ───────────────────────────────────────────
print("\n" + "="*60)
print("  CareerAI – Setup Check Report")
print("="*60)
all_pass = True
for icon, label, msg in results:
    status = f"{icon}  {label:<35} {msg}"
    print(status)
    if icon == FAIL:
        all_pass = False

print("="*60)
if all_pass:
    print("  All checks passed! Ready to start. 🚀")
else:
    print("  Some checks failed. Fix the issues above, then retry.")
print("="*60 + "\n")
sys.exit(0 if all_pass else 1)
