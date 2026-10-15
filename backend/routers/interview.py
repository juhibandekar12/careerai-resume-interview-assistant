"""
backend/routers/interview.py
-----------------------------
Interview session management, question generation, and answer evaluation.
"""

import json
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from utils.auth import verify_token
from utils.llm_service import generate_interview_questions, evaluate_answer
from database.db import execute, fetchall, fetchone, to_json, from_json

router = APIRouter()


def _auth(authorization: str | None) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing token.")
    payload = verify_token(authorization.split(" ", 1)[1])
    if not payload:
        raise HTTPException(401, "Token expired or invalid.")
    return payload


class StartSessionRequest(BaseModel):
    job_role:      str
    user_skills:   list[str] = []
    num_technical: int = 5
    num_hr:        int = 3


class SubmitAnswerRequest(BaseModel):
    session_id: int
    question:   str
    answer:     str
    job_role:   str = ""


class CompleteSessionRequest(BaseModel):
    session_id: int


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/start", summary="Start a new interview session and get questions")
def start_session(req: StartSessionRequest, authorization: str | None = Header(default=None)):
    payload = _auth(authorization)
    user_id = payload["user_id"]

    questions_dict = generate_interview_questions(
        req.job_role, req.user_skills, req.num_technical, req.num_hr
    )

    all_questions = (
        [{"type": "technical", "text": q} for q in questions_dict.get("technical", [])]
        + [{"type": "hr",        "text": q} for q in questions_dict.get("hr", [])]
    )

    session_id = execute(
        """INSERT INTO interview_sessions (user_id, job_role, questions, status)
           VALUES (?,?,?,?)""",
        (user_id, req.job_role, to_json(all_questions), "in_progress"),
    )

    return {
        "success":    True,
        "session_id": session_id,
        "questions":  all_questions,
    }


@router.post("/answer", summary="Submit an answer and get AI evaluation")
def submit_answer(req: SubmitAnswerRequest, authorization: str | None = Header(default=None)):
    payload = _auth(authorization)
    user_id = payload["user_id"]

    # Verify session belongs to user
    session = fetchone(
        "SELECT id, job_role FROM interview_sessions WHERE id=? AND user_id=?",
        (req.session_id, user_id),
    )
    if not session:
        raise HTTPException(404, "Session not found.")

    job_role = req.job_role or session["job_role"]
    evaluation = evaluate_answer(req.question, req.answer, job_role)

    answer_id = execute(
        """INSERT INTO interview_answers
           (session_id, question, answer, score, feedback,
            relevance_score, clarity_score, technical_score)
           VALUES (?,?,?,?,?,?,?,?)""",
        (
            req.session_id,
            req.question,
            req.answer,
            evaluation.get("overall_score", 0),
            evaluation.get("feedback", ""),
            evaluation.get("relevance_score", 0),
            evaluation.get("clarity_score", 0),
            evaluation.get("technical_score", 0),
        ),
    )

    return {
        "success":    True,
        "answer_id":  answer_id,
        "evaluation": evaluation,
    }


@router.post("/complete", summary="Complete an interview session and compute final score")
def complete_session(req: CompleteSessionRequest, authorization: str | None = Header(default=None)):
    payload = _auth(authorization)
    user_id = payload["user_id"]

    session = fetchone(
        "SELECT id FROM interview_sessions WHERE id=? AND user_id=?",
        (req.session_id, user_id),
    )
    if not session:
        raise HTTPException(404, "Session not found.")

    answers = fetchall(
        "SELECT score FROM interview_answers WHERE session_id=?",
        (req.session_id,),
    )
    if answers:
        avg_score = sum(a["score"] for a in answers) / len(answers)
    else:
        avg_score = 0.0

    execute(
        """UPDATE interview_sessions
           SET status='completed', overall_score=?, completed_at=CURRENT_TIMESTAMP
           WHERE id=?""",
        (round(avg_score, 2), req.session_id),
    )

    return {
        "success":       True,
        "overall_score": round(avg_score, 2),
        "total_answers": len(answers),
    }


@router.get("/sessions", summary="Get all interview sessions for current user")
def get_sessions(authorization: str | None = Header(default=None)):
    payload = _auth(authorization)
    sessions = fetchall(
        """SELECT id, job_role, overall_score, status, started_at, completed_at
           FROM interview_sessions WHERE user_id=? ORDER BY started_at DESC""",
        (payload["user_id"],),
    )
    return {"success": True, "data": sessions}


@router.get("/session/{session_id}", summary="Get full details of an interview session")
def get_session(session_id: int, authorization: str | None = Header(default=None)):
    payload = _auth(authorization)
    session = fetchone(
        "SELECT * FROM interview_sessions WHERE id=? AND user_id=?",
        (session_id, payload["user_id"]),
    )
    if not session:
        raise HTTPException(404, "Session not found.")

    answers = fetchall(
        "SELECT * FROM interview_answers WHERE session_id=? ORDER BY answered_at",
        (session_id,),
    )
    return {
        "success": True,
        "session": {
            "id":            session["id"],
            "job_role":      session["job_role"],
            "status":        session["status"],
            "overall_score": session["overall_score"],
            "started_at":    session["started_at"],
            "completed_at":  session["completed_at"],
            "questions":     from_json(session["questions"]),
        },
        "answers": [dict(a) for a in answers],
    }
