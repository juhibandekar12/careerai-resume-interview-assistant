"""
backend/routers/jobs.py
-----------------------
Job recommendation and skill-gap analysis endpoints.
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from utils.auth import verify_token
from utils.job_matcher import recommend_jobs, get_skill_gap, get_all_job_titles
from utils.llm_service import generate_learning_roadmap
from database.db import fetchone, execute, to_json, from_json

router = APIRouter()


def _auth(authorization: str | None) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing token.")
    payload = verify_token(authorization.split(" ", 1)[1])
    if not payload:
        raise HTTPException(401, "Token expired or invalid.")
    return payload


class RecommendRequest(BaseModel):
    resume_id: int


class SkillGapRequest(BaseModel):
    resume_id: int
    job_title:  str


@router.post("/recommend", summary="Get top-5 job recommendations for a resume")
def recommend(req: RecommendRequest, authorization: str | None = Header(default=None)):
    payload   = _auth(authorization)
    user_id   = payload["user_id"]

    row = fetchone(
        "SELECT extracted_skills FROM resumes WHERE id=? AND user_id=?",
        (req.resume_id, user_id),
    )
    if not row:
        raise HTTPException(404, "Resume not found.")

    skills = from_json(row["extracted_skills"])
    if not skills:
        raise HTTPException(400, "No skills extracted from resume. Please re-upload.")

    recommendations = recommend_jobs(skills, top_n=5)

    # Persist recommendations
    for rec in recommendations:
        # Get job_role_id from job_roles table (if it exists)
        from database.db import fetchone as fone
        job_row = fone("SELECT id FROM job_roles WHERE title=?", (rec["title"],))
        job_role_id = job_row["id"] if job_row else 0
        execute(
            """INSERT OR REPLACE INTO job_recommendations
               (user_id, resume_id, job_role_id, match_percentage, missing_skills)
               VALUES (?,?,?,?,?)""",
            (user_id, req.resume_id, job_role_id,
             rec["match_percentage"], to_json(rec["missing_skills"])),
        )

    return {"success": True, "data": recommendations}


@router.post("/skill-gap", summary="Analyse skill gap for a specific job role")
def skill_gap(req: SkillGapRequest, authorization: str | None = Header(default=None)):
    payload = _auth(authorization)
    user_id = payload["user_id"]

    row = fetchone(
        "SELECT extracted_skills FROM resumes WHERE id=? AND user_id=?",
        (req.resume_id, user_id),
    )
    if not row:
        raise HTTPException(404, "Resume not found.")

    skills = from_json(row["extracted_skills"])
    gap    = get_skill_gap(skills, req.job_title)

    if "error" in gap:
        raise HTTPException(404, gap["error"])

    # Generate learning roadmap
    roadmap = generate_learning_roadmap(
        gap["missing_skills"], req.job_title, skills
    )
    gap["learning_roadmap"] = roadmap

    # Persist analysis
    execute(
        """INSERT INTO skill_gap_analysis
           (user_id, resume_id, target_job_role, user_skills,
            required_skills, missing_skills, learning_roadmap)
           VALUES (?,?,?,?,?,?,?)""",
        (
            user_id, req.resume_id, req.job_title,
            to_json(gap["user_skills"]),
            to_json(gap["required_skills"]),
            to_json(gap["missing_skills"]),
            to_json(roadmap),
        ),
    )

    return {"success": True, "data": gap}


@router.get("/titles", summary="Get all available job titles")
def job_titles():
    titles = get_all_job_titles()
    return {"success": True, "data": titles}
