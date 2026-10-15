"""
backend/routers/resume.py
-------------------------
Resume upload, parsing, and retrieval endpoints.
"""

import json
from fastapi import APIRouter, UploadFile, File, HTTPException, Header
from utils.auth import verify_token
from utils.resume_parser import parse_resume
from utils.helpers import save_uploaded_file, calculate_profile_completeness
from database.db import execute, fetchall, fetchone, to_json, from_json

router = APIRouter()


def _auth(authorization: str | None) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing token.")
    payload = verify_token(authorization.split(" ", 1)[1])
    if not payload:
        raise HTTPException(401, "Token expired or invalid.")
    return payload


@router.post("/upload", summary="Upload and parse a PDF resume")
async def upload_resume(
    file: UploadFile = File(...),
    authorization: str | None = Header(default=None),
):
    payload = _auth(authorization)
    user_id = payload["user_id"]

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are accepted.")

    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:  # 10 MB cap
        raise HTTPException(400, "File too large (max 10 MB).")

    # Save and parse
    file_path = save_uploaded_file(file_bytes, file.filename)
    parsed    = parse_resume(file_path)

    if "error" in parsed:
        raise HTTPException(500, f"Failed to parse resume: {parsed['error']}")

    # Persist to DB
    resume_id = execute(
        """INSERT INTO resumes
           (user_id, filename, raw_text, extracted_skills, extracted_education,
            extracted_experience, extracted_projects, extracted_certifications, contact_info)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (
            user_id,
            file.filename,
            parsed["raw_text"],
            to_json(parsed["skills"]),
            to_json(parsed["education"]),
            to_json(parsed["experience"]),
            to_json(parsed["projects"]),
            to_json(parsed["certifications"]),
            to_json(parsed["contact_info"]),
        ),
    )

    completeness = calculate_profile_completeness(parsed)
    return {
        "success":       True,
        "resume_id":     resume_id,
        "completeness":  completeness,
        "data": {
            "skills":          parsed["skills"],
            "education":       parsed["education"],
            "experience":      parsed["experience"],
            "projects":        parsed["projects"],
            "certifications":  parsed["certifications"],
            "contact_info":    parsed["contact_info"],
        },
    }


@router.get("/list", summary="List all resumes for the current user")
def list_resumes(authorization: str | None = Header(default=None)):
    payload = _auth(authorization)
    rows = fetchall(
        "SELECT id, filename, upload_date FROM resumes WHERE user_id=? ORDER BY upload_date DESC",
        (payload["user_id"],),
    )
    return {"success": True, "data": rows}


@router.get("/{resume_id}", summary="Get a specific resume's parsed data")
def get_resume(resume_id: int, authorization: str | None = Header(default=None)):
    payload = _auth(authorization)
    row = fetchone(
        "SELECT * FROM resumes WHERE id=? AND user_id=?",
        (resume_id, payload["user_id"]),
    )
    if not row:
        raise HTTPException(404, "Resume not found.")

    return {
        "success": True,
        "data": {
            "id":              row["id"],
            "filename":        row["filename"],
            "upload_date":     row["upload_date"],
            "skills":          from_json(row["extracted_skills"]),
            "education":       from_json(row["extracted_education"]),
            "experience":      from_json(row["extracted_experience"]),
            "projects":        from_json(row["extracted_projects"]),
            "certifications":  from_json(row["extracted_certifications"]),
            "contact_info":    from_json(row["contact_info"]),
        },
    }
