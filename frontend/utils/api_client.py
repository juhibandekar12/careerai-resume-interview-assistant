"""
frontend/utils/api_client.py
-----------------------------
HTTP client wrapper for the FastAPI backend.
All Streamlit pages use this to communicate with the API.
"""

import requests
import streamlit as st
import logging

logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000/api"


class APIClient:
    """Thin wrapper around requests for the Career Assist backend."""

    # ── Auth ──────────────────────────────────────────────────────────────────

    @staticmethod
    def register(username: str, email: str, password: str, full_name: str = "") -> dict:
        try:
            r = requests.post(
                f"{BASE_URL}/auth/register",
                json={"username": username, "email": email,
                      "password": password, "full_name": full_name},
                timeout=10,
            )
            return r.json()
        except Exception as e:
            return {"success": False, "detail": str(e)}

    @staticmethod
    def login(username: str, password: str) -> dict:
        try:
            r = requests.post(
                f"{BASE_URL}/auth/login",
                json={"username": username, "password": password},
                timeout=10,
            )
            return r.json()
        except Exception as e:
            return {"success": False, "detail": str(e)}

    # ── Resume ─────────────────────────────────────────────────────────────────

    @staticmethod
    def upload_resume(file_bytes: bytes, filename: str) -> dict:
        try:
            token = st.session_state.get("token", "")
            r = requests.post(
                f"{BASE_URL}/resume/upload",
                headers={"Authorization": f"Bearer {token}"},
                files={"file": (filename, file_bytes, "application/pdf")},
                timeout=60,
            )
            return r.json()
        except Exception as e:
            return {"success": False, "detail": str(e)}

    @staticmethod
    def list_resumes() -> dict:
        try:
            token = st.session_state.get("token", "")
            r = requests.get(
                f"{BASE_URL}/resume/list",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            return r.json()
        except Exception as e:
            return {"success": False, "detail": str(e)}

    @staticmethod
    def get_resume(resume_id: int) -> dict:
        try:
            token = st.session_state.get("token", "")
            r = requests.get(
                f"{BASE_URL}/resume/{resume_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            return r.json()
        except Exception as e:
            return {"success": False, "detail": str(e)}

    # ── Jobs ───────────────────────────────────────────────────────────────────

    @staticmethod
    def recommend_jobs(resume_id: int) -> dict:
        try:
            token = st.session_state.get("token", "")
            r = requests.post(
                f"{BASE_URL}/jobs/recommend",
                headers={"Authorization": f"Bearer {token}"},
                json={"resume_id": resume_id},
                timeout=30,
            )
            return r.json()
        except Exception as e:
            return {"success": False, "detail": str(e)}

    @staticmethod
    def get_skill_gap(resume_id: int, job_title: str) -> dict:
        try:
            token = st.session_state.get("token", "")
            r = requests.post(
                f"{BASE_URL}/jobs/skill-gap",
                headers={"Authorization": f"Bearer {token}"},
                json={"resume_id": resume_id, "job_title": job_title},
                timeout=60,
            )
            return r.json()
        except Exception as e:
            return {"success": False, "detail": str(e)}

    @staticmethod
    def get_job_titles() -> list[str]:
        try:
            r = requests.get(f"{BASE_URL}/jobs/titles", timeout=10)
            return r.json().get("data", [])
        except Exception:
            return []

    # ── Interview ──────────────────────────────────────────────────────────────

    @staticmethod
    def start_interview(job_role: str, user_skills: list[str],
                        num_tech: int = 5, num_hr: int = 3) -> dict:
        try:
            token = st.session_state.get("token", "")
            r = requests.post(
                f"{BASE_URL}/interview/start",
                headers={"Authorization": f"Bearer {token}"},
                json={"job_role": job_role, "user_skills": user_skills,
                      "num_technical": num_tech, "num_hr": num_hr},
                timeout=120,
            )
            return r.json()
        except Exception as e:
            return {"success": False, "detail": str(e)}

    @staticmethod
    def submit_answer(session_id: int, question: str,
                      answer: str, job_role: str = "") -> dict:
        try:
            token = st.session_state.get("token", "")
            r = requests.post(
                f"{BASE_URL}/interview/answer",
                headers={"Authorization": f"Bearer {token}"},
                json={"session_id": session_id, "question": question,
                      "answer": answer, "job_role": job_role},
                timeout=120,
            )
            return r.json()
        except Exception as e:
            return {"success": False, "detail": str(e)}

    @staticmethod
    def complete_interview(session_id: int) -> dict:
        try:
            token = st.session_state.get("token", "")
            r = requests.post(
                f"{BASE_URL}/interview/complete",
                headers={"Authorization": f"Bearer {token}"},
                json={"session_id": session_id},
                timeout=10,
            )
            return r.json()
        except Exception as e:
            return {"success": False, "detail": str(e)}

    @staticmethod
    def get_sessions() -> dict:
        try:
            token = st.session_state.get("token", "")
            r = requests.get(
                f"{BASE_URL}/interview/sessions",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            return r.json()
        except Exception as e:
            return {"success": False, "detail": str(e)}

    @staticmethod
    def get_session(session_id: int) -> dict:
        try:
            token = st.session_state.get("token", "")
            r = requests.get(
                f"{BASE_URL}/interview/session/{session_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            return r.json()
        except Exception as e:
            return {"success": False, "detail": str(e)}

    # ── Dashboard ──────────────────────────────────────────────────────────────

    @staticmethod
    def get_dashboard_stats() -> dict:
        try:
            token = st.session_state.get("token", "")
            r = requests.get(
                f"{BASE_URL}/dashboard/stats",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            return r.json()
        except Exception as e:
            return {"success": False, "detail": str(e)}

    @staticmethod
    def get_interview_breakdown(session_id: int) -> dict:
        try:
            token = st.session_state.get("token", "")
            r = requests.get(
                f"{BASE_URL}/dashboard/interview-breakdown/{session_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            return r.json()
        except Exception as e:
            return {"success": False, "detail": str(e)}
