"""
backend/routers/dashboard.py
-----------------------------
Aggregated dashboard statistics for the current user.
"""

from fastapi import APIRouter, HTTPException, Header
from utils.auth import verify_token
from database.db import fetchall, fetchone, from_json

router = APIRouter()


def _auth(authorization: str | None) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing token.")
    payload = verify_token(authorization.split(" ", 1)[1])
    if not payload:
        raise HTTPException(401, "Token expired or invalid.")
    return payload


@router.get("/stats", summary="Get aggregated dashboard statistics")
def get_stats(authorization: str | None = Header(default=None)):
    payload = _auth(authorization)
    user_id = payload["user_id"]

    # ── Resume stats ───────────────────────────────────────────────────────────
    resumes = fetchall(
        "SELECT id, filename, upload_date, extracted_skills FROM resumes WHERE user_id=?",
        (user_id,),
    )
    latest_skills = []
    latest_resume_id = None
    if resumes:
        latest = resumes[0]
        latest_resume_id = latest["id"]
        latest_skills = from_json(latest["extracted_skills"])

    # ── Interview stats ────────────────────────────────────────────────────────
    sessions = fetchall(
        """SELECT overall_score, job_role, status, started_at
           FROM interview_sessions WHERE user_id=? ORDER BY started_at DESC""",
        (user_id,),
    )
    completed = [s for s in sessions if s["status"] == "completed"]
    avg_interview_score = (
        round(sum(s["overall_score"] or 0 for s in completed) / len(completed), 2)
        if completed else 0.0
    )

    # Score trend (last 10 completed sessions)
    score_trend = [
        {"date": s["started_at"][:10], "score": round(s["overall_score"] or 0, 2)}
        for s in completed[:10]
    ][::-1]  # chronological

    # ── Skill gap history ──────────────────────────────────────────────────────
    gap_records = fetchall(
        """SELECT target_job_role, missing_skills, analyzed_at
           FROM skill_gap_analysis WHERE user_id=? ORDER BY analyzed_at DESC LIMIT 5""",
        (user_id,),
    )
    gap_summary = [
        {
            "job_role":      g["target_job_role"],
            "missing_count": len(from_json(g["missing_skills"])),
            "date":          g["analyzed_at"][:10],
        }
        for g in gap_records
    ]

    return {
        "success": True,
        "data": {
            "total_resumes":         len(resumes),
            "latest_resume_id":      latest_resume_id,
            "total_skills":          len(latest_skills),
            "top_skills":            latest_skills[:10],
            "total_sessions":        len(sessions),
            "completed_sessions":    len(completed),
            "avg_interview_score":   avg_interview_score,
            "score_trend":           score_trend,
            "gap_summary":           gap_summary,
            "recent_sessions":       sessions[:5],
        },
    }


@router.get("/interview-breakdown/{session_id}", summary="Score breakdown for an interview session")
def interview_breakdown(session_id: int, authorization: str | None = Header(default=None)):
    payload = _auth(authorization)
    answers = fetchall(
        """SELECT relevance_score, clarity_score, technical_score, score
           FROM interview_answers WHERE session_id=?""",
        (session_id,),
    )
    if not answers:
        return {"success": True, "data": {}}

    n = len(answers)
    breakdown = {
        "relevance":    round(sum(a["relevance_score"] or 0 for a in answers) / n, 2),
        "clarity":      round(sum(a["clarity_score"]   or 0 for a in answers) / n, 2),
        "technical":    round(sum(a["technical_score"] or 0 for a in answers) / n, 2),
        "overall":      round(sum(a["score"]           or 0 for a in answers) / n, 2),
    }
    return {"success": True, "data": breakdown}
