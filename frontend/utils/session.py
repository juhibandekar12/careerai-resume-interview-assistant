"""
frontend/utils/session.py
--------------------------
Streamlit session state initialisation, helpers, and auto-resume loader.
"""

import streamlit as st


def init_session():
    """Initialise all session-state keys to safe defaults."""
    defaults = {
        "authenticated":   False,
        "token":           None,
        "user_id":         None,
        "username":        None,
        "full_name":       None,
        "email":           None,
        "current_page":    "Dashboard",
        # Resume
        "resume_id":       None,
        "resume_data":     None,
        "resume_filename": None,
        "user_skills":     [],
        # Interview
        "session_id":      None,
        "questions":       [],
        "current_q_idx":   0,
        "answers":         [],
        "evaluations":     [],
        "interview_done":  False,
        # Jobs
        "recommendations": [],
        "selected_job":    None,
        "skill_gap":       None,
        # Internal flags
        "_resume_autoloaded": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def set_user(user_data: dict, token: str):
    """Populate session state after successful login."""
    st.session_state.authenticated  = True
    st.session_state.token          = token
    st.session_state.user_id        = user_data.get("user_id")
    st.session_state.username       = user_data.get("username")
    st.session_state.full_name      = user_data.get("full_name", "")
    st.session_state.email          = user_data.get("email", "")
    st.session_state._resume_autoloaded = False   # trigger auto-load on next render


def auto_load_latest_resume():
    """
    After login, silently load the most recent resume from the backend
    so all sections work without requiring a manual re-upload.
    Only runs once per login session.
    """
    if st.session_state.get("_resume_autoloaded"):
        return
    if not st.session_state.get("authenticated"):
        return
    if st.session_state.get("resume_id"):          # already loaded
        st.session_state._resume_autoloaded = True
        return

    try:
        from frontend.utils.api_client import APIClient
        resp = APIClient.list_resumes()
        resumes = resp.get("data", [])
        if resumes:
            latest = resumes[0]   # list is ORDER BY upload_date DESC
            detail  = APIClient.get_resume(latest["id"])
            if detail.get("success"):
                d = detail["data"]
                st.session_state.resume_id       = d["id"]
                st.session_state.resume_data     = d
                st.session_state.resume_filename = d.get("filename", "")
                st.session_state.user_skills     = d.get("skills", [])
    except Exception:
        pass   # silent – user can upload manually
    finally:
        st.session_state._resume_autoloaded = True


def logout():
    """Clear all session state."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_session()
