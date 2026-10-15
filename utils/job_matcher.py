"""
utils/job_matcher.py
--------------------
TF-IDF + Cosine Similarity based job recommendation engine.
Matches a user's skill set against the job-role dataset.
"""

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# Path to the job dataset JSON
DATA_PATH = Path(__file__).parent.parent / "data" / "job_roles.json"


def _load_job_data() -> list[dict]:
    """Load the job-roles dataset. Returns an empty list on failure."""
    if not DATA_PATH.exists():
        logger.error("job_roles.json not found at %s", DATA_PATH)
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _skills_to_text(skills: list[str]) -> str:
    """Convert a list of skills into a single lowercase string for TF-IDF."""
    return " ".join(s.lower().replace(" ", "_") for s in skills)


def recommend_jobs(user_skills: list[str], top_n: int = 5) -> list[dict[str, Any]]:
    """
    Use TF-IDF + cosine similarity to match user skills against job roles.

    Parameters
    ----------
    user_skills : list[str]
        Skills extracted from the user's resume.
    top_n : int
        Number of top job recommendations to return.

    Returns
    -------
    list[dict]
        Each dict contains:
        - title, category, description, avg_salary, experience_level
        - match_percentage  (0-100)
        - missing_skills    (list of skills the user lacks)
        - required_skills   (full list for the role)
    """
    jobs = _load_job_data()
    if not jobs:
        return []

    # Build corpus: user query + all job documents
    user_text = _skills_to_text(user_skills)
    job_texts = [_skills_to_text(job.get("required_skills", [])) for job in jobs]
    corpus = [user_text] + job_texts

    # Fit TF-IDF
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=5000,
        sublinear_tf=True,
    )
    try:
        tfidf_matrix = vectorizer.fit_transform(corpus)
    except ValueError as exc:
        logger.error("TF-IDF fitting failed: %s", exc)
        return []

    # Compute cosine similarity between user vector (row 0) and all job rows
    user_vec = tfidf_matrix[0]
    job_vecs = tfidf_matrix[1:]
    similarities = cosine_similarity(user_vec, job_vecs).flatten()

    # Sort by similarity descending
    top_indices = np.argsort(similarities)[::-1][:top_n]

    results = []
    user_skills_lower = {s.lower() for s in user_skills}
    for idx in top_indices:
        job = jobs[idx]
        required = [s.lower() for s in job.get("required_skills", [])]
        missing = [s for s in required if s not in user_skills_lower]
        match_pct = round(float(similarities[idx]) * 100, 1)
        results.append({
            "title": job.get("title", "Unknown"),
            "category": job.get("category", ""),
            "description": job.get("description", ""),
            "avg_salary": job.get("avg_salary", "N/A"),
            "experience_level": job.get("experience_level", ""),
            "required_skills": job.get("required_skills", []),
            "match_percentage": match_pct,
            "missing_skills": [s.title() for s in missing],
        })
    return results


def get_skill_gap(user_skills: list[str], job_title: str) -> dict[str, Any]:
    """
    Compare user skills against a specific job role's requirements.

    Returns
    -------
    dict with keys: required_skills, user_skills, missing_skills, matching_skills
    """
    jobs = _load_job_data()
    target_job = None
    for job in jobs:
        if job["title"].lower() == job_title.lower():
            target_job = job
            break

    if not target_job:
        # Fuzzy match: find closest title
        from difflib import get_close_matches
        titles = [j["title"] for j in jobs]
        matches = get_close_matches(job_title, titles, n=1, cutoff=0.4)
        if matches:
            target_job = next(j for j in jobs if j["title"] == matches[0])

    if not target_job:
        return {
            "error": f"Job role '{job_title}' not found in dataset.",
            "available_roles": [j["title"] for j in jobs],
        }

    required = [s.lower() for s in target_job.get("required_skills", [])]
    user_lower = {s.lower() for s in user_skills}
    missing = [s.title() for s in required if s not in user_lower]
    matching = [s.title() for s in required if s in user_lower]

    match_pct = round(len(matching) / max(len(required), 1) * 100, 1)

    return {
        "job_title": target_job["title"],
        "required_skills": target_job.get("required_skills", []),
        "user_skills": [s.title() for s in sorted(user_lower)],
        "matching_skills": matching,
        "missing_skills": missing,
        "match_percentage": match_pct,
        "description": target_job.get("description", ""),
        "experience_level": target_job.get("experience_level", ""),
    }


def get_all_job_titles() -> list[str]:
    """Return sorted list of all job titles in the dataset."""
    jobs = _load_job_data()
    return sorted(j["title"] for j in jobs)
