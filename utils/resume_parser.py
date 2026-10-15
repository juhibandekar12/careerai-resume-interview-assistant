"""
utils/resume_parser.py
----------------------
Extracts structured information (skills, education, experience, etc.)
from raw resume text using spaCy NLP and regex patterns.
"""

import re
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ── Try to load spaCy model (graceful fallback) ────────────────────────────────
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
except Exception:
    SPACY_AVAILABLE = False
    logger.warning("spaCy model not available – falling back to regex-only extraction.")

# ── Try pdfplumber then PyPDF2 ─────────────────────────────────────────────────
try:
    import pdfplumber
    PDF_BACKEND = "pdfplumber"
except ImportError:
    try:
        import PyPDF2
        PDF_BACKEND = "pypdf2"
    except ImportError:
        PDF_BACKEND = None
        logger.warning("No PDF library found. Install pdfplumber or PyPDF2.")

# ──────────────────────────────────────────────────────────────────────────────
# Master skill taxonomy (technology-focused)
# ──────────────────────────────────────────────────────────────────────────────
SKILL_KEYWORDS = [
    # Programming languages
    "python","java","javascript","typescript","c++","c#","c","ruby","go","golang",
    "rust","swift","kotlin","php","r","scala","matlab","bash","shell","perl",
    # Web
    "html","css","react","angular","vue","nextjs","nodejs","express","django",
    "flask","fastapi","spring","laravel","rails","jquery","bootstrap","tailwind",
    # Data / ML
    "machine learning","deep learning","neural network","nlp","computer vision",
    "tensorflow","pytorch","keras","scikit-learn","pandas","numpy","scipy",
    "matplotlib","seaborn","plotly","hugging face","transformers","llm","gpt",
    "bert","langchain","openai","llama","stable diffusion",
    # Data engineering
    "sql","mysql","postgresql","sqlite","mongodb","redis","cassandra","oracle",
    "elasticsearch","hadoop","spark","kafka","airflow","dbt","snowflake",
    "bigquery","databricks",
    # DevOps / Cloud
    "aws","azure","gcp","docker","kubernetes","terraform","ansible","jenkins",
    "ci/cd","github actions","linux","nginx","apache","microservices","rest api",
    "graphql","grpc",
    # Tools
    "git","github","gitlab","jira","confluence","figma","postman","swagger",
    "excel","tableau","power bi","looker",
    # Soft skills
    "leadership","communication","teamwork","problem solving","agile","scrum",
    "project management","critical thinking","time management",
]

EDUCATION_KEYWORDS = [
    "bachelor", "master", "phd", "b.tech", "m.tech", "b.e.", "m.e.", "mba",
    "bsc", "msc", "b.sc", "m.sc", "associate", "diploma", "certification",
    "university", "college", "institute", "school", "degree",
]

SECTION_HEADERS = {
    "experience": ["experience", "work experience", "employment history",
                   "professional experience", "work history", "internship"],
    "education": ["education", "academic background", "qualifications",
                  "educational background"],
    "skills": ["skills", "technical skills", "core competencies", "technologies",
               "tools", "expertise", "proficiencies"],
    "projects": ["projects", "personal projects", "key projects",
                 "academic projects", "side projects"],
    "certifications": ["certifications", "certificates", "licenses",
                       "achievements", "awards", "accomplishments"],
    "contact": ["contact", "personal information", "about"],
}


# ──────────────────────────────────────────────────────────────────────────────
# PDF text extraction
# ──────────────────────────────────────────────────────────────────────────────

def extract_text_from_pdf(file_path: str) -> str:
    """Extract raw text from a PDF file using the best available library."""
    text = ""
    if PDF_BACKEND == "pdfplumber":
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    elif PDF_BACKEND == "pypdf2":
        import PyPDF2
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"
    else:
        raise RuntimeError("No PDF library available. Install pdfplumber.")
    return text.strip()


# ──────────────────────────────────────────────────────────────────────────────
# Contact information extraction
# ──────────────────────────────────────────────────────────────────────────────

def extract_contact_info(text: str) -> dict:
    """Extract email, phone, LinkedIn, GitHub from resume text."""
    contact = {}
    # Email
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", text)
    if email_match:
        contact["email"] = email_match.group()
    # Phone
    phone_match = re.search(
        r"(\+?\d{1,3}[\s.-]?)?(\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})", text
    )
    if phone_match:
        contact["phone"] = phone_match.group().strip()
    # LinkedIn
    linkedin_match = re.search(r"linkedin\.com/in/[\w-]+", text, re.I)
    if linkedin_match:
        contact["linkedin"] = linkedin_match.group()
    # GitHub
    github_match = re.search(r"github\.com/[\w-]+", text, re.I)
    if github_match:
        contact["github"] = github_match.group()
    # Name (first non-empty line heuristic)
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if lines:
        contact["name"] = lines[0]
    return contact


# ──────────────────────────────────────────────────────────────────────────────
# Skills extraction
# ──────────────────────────────────────────────────────────────────────────────

def extract_skills(text: str) -> list[str]:
    """Return a deduplicated list of skills found in the resume text."""
    text_lower = text.lower()
    found = set()
    for skill in SKILL_KEYWORDS:
        # Use word-boundary matching
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found.add(skill.title() if " " not in skill else skill.title())

    # spaCy NER for additional named entities
    if SPACY_AVAILABLE:
        doc = nlp(text[:100000])  # cap at 100 k chars
        for ent in doc.ents:
            if ent.label_ in ("ORG", "PRODUCT", "WORK_OF_ART"):
                candidate = ent.text.strip().lower()
                if any(k in candidate for k in ["js", "api", "net", "sql"]):
                    found.add(ent.text.strip())

    return sorted(found)


# ──────────────────────────────────────────────────────────────────────────────
# Section segmentation helper
# ──────────────────────────────────────────────────────────────────────────────

def _split_into_sections(text: str) -> dict[str, str]:
    """
    Split resume text into named sections based on common section headers.
    Returns a dict: {section_name: section_content}.
    """
    lines = text.split("\n")
    sections: dict[str, list[str]] = {"preamble": []}
    current = "preamble"

    for line in lines:
        line_lower = line.strip().lower()
        matched = False
        for section, keywords in SECTION_HEADERS.items():
            if any(line_lower == kw or line_lower.startswith(kw + ":") for kw in keywords):
                current = section
                sections.setdefault(current, [])
                matched = True
                break
        if not matched:
            sections.setdefault(current, []).append(line)

    return {k: "\n".join(v).strip() for k, v in sections.items()}


# ──────────────────────────────────────────────────────────────────────────────
# Education extraction
# ──────────────────────────────────────────────────────────────────────────────

def extract_education(text: str) -> list[dict]:
    """Extract education entries from the resume."""
    sections = _split_into_sections(text)
    edu_text = sections.get("education", text)
    entries = []
    lines = [l.strip() for l in edu_text.split("\n") if l.strip()]
    year_pattern = re.compile(r"\b(19|20)\d{2}\b")
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(kw in line_lower for kw in EDUCATION_KEYWORDS):
            entry = {"institution": "", "degree": line, "year": ""}
            if i + 1 < len(lines):
                entry["institution"] = lines[i + 1]
            year_match = year_pattern.search(line)
            if year_match:
                entry["year"] = year_match.group()
            entries.append(entry)
    return entries[:10]  # cap


# ──────────────────────────────────────────────────────────────────────────────
# Experience extraction
# ──────────────────────────────────────────────────────────────────────────────

def extract_experience(text: str) -> list[dict]:
    """Extract work-experience entries from the resume."""
    sections = _split_into_sections(text)
    exp_text = sections.get("experience", "")
    entries = []
    # Split on lines that look like job titles (contain years)
    year_pattern = re.compile(r"\b(19|20)\d{2}\b")
    lines = [l.strip() for l in exp_text.split("\n") if l.strip()]
    current: dict[str, Any] = {}
    for line in lines:
        if year_pattern.search(line) and len(line) < 120:
            if current:
                entries.append(current)
            current = {"title": line, "description": ""}
        elif current:
            current["description"] += " " + line
    if current:
        entries.append(current)
    return entries[:15]


# ──────────────────────────────────────────────────────────────────────────────
# Projects extraction
# ──────────────────────────────────────────────────────────────────────────────

def extract_projects(text: str) -> list[dict]:
    """Extract project entries from the resume."""
    sections = _split_into_sections(text)
    proj_text = sections.get("projects", "")
    entries = []
    lines = [l.strip() for l in proj_text.split("\n") if l.strip()]
    current: dict[str, str] = {}
    for line in lines:
        # Heuristic: short lines (< 80 chars) that don't start with bullet are titles
        if len(line) < 80 and not line.startswith(("-", "•", "*", "·", "–")):
            if current:
                entries.append(current)
            current = {"name": line, "description": ""}
        elif current:
            current["description"] += " " + line
    if current:
        entries.append(current)
    return entries[:10]


# ──────────────────────────────────────────────────────────────────────────────
# Certifications extraction
# ──────────────────────────────────────────────────────────────────────────────

def extract_certifications(text: str) -> list[str]:
    """Extract certification names from the resume."""
    sections = _split_into_sections(text)
    cert_text = sections.get("certifications", "")
    cert_keywords = [
        "certified", "certification", "certificate", "aws", "azure", "gcp",
        "pmp", "scrum", "agile", "cisco", "oracle", "google", "microsoft",
        "comptia", "coursera", "udemy", "edx",
    ]
    lines = [l.strip() for l in cert_text.split("\n") if l.strip()]
    certs = []
    for line in lines:
        if any(kw in line.lower() for kw in cert_keywords) and len(line) < 200:
            certs.append(line.lstrip("-•*·– "))
    return certs[:20]


# ──────────────────────────────────────────────────────────────────────────────
# Master parse function
# ──────────────────────────────────────────────────────────────────────────────

def parse_resume(file_path: str) -> dict:
    """
    Full pipeline: PDF → text → structured data.
    Returns a dict with all extracted fields.
    """
    try:
        raw_text = extract_text_from_pdf(file_path)
    except Exception as exc:
        logger.error("PDF extraction failed: %s", exc)
        return {"error": str(exc)}

    parsed = {
        "raw_text": raw_text,
        "contact_info": extract_contact_info(raw_text),
        "skills": extract_skills(raw_text),
        "education": extract_education(raw_text),
        "experience": extract_experience(raw_text),
        "projects": extract_projects(raw_text),
        "certifications": extract_certifications(raw_text),
    }
    logger.info(
        "Resume parsed: %d skills, %d education entries, %d experience entries",
        len(parsed["skills"]),
        len(parsed["education"]),
        len(parsed["experience"]),
    )
    return parsed
