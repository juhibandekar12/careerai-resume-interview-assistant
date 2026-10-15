"""
frontend/app.py
---------------
Main Streamlit application entry point.
Handles routing between pages and global session state.
"""

import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

# ── Page configuration (MUST be first Streamlit call) ─────────────────────────
st.set_page_config(
    page_title="CareerAI – Career Assistance System",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Import pages ───────────────────────────────────────────────────────────────
from frontend.views import (
    login_page,
    dashboard_page,
    resume_page,
    jobs_page,
    interview_page,
    profile_page,
)
from frontend.components.sidebar import render_sidebar
from frontend.utils.api_client import APIClient
from frontend.utils.session import init_session, auto_load_latest_resume

# ── Inject global CSS ──────────────────────────────────────────────────────────
def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()
init_session()

# ── Page map (single source of truth for navigation) ──────────────────────────
PAGE_MAP = {
    "Dashboard":          dashboard_page,
    "Resume Analysis":    resume_page,
    "Job Recommendations":jobs_page,
    "Interview Practice": interview_page,
    "Profile":            profile_page,
}

# ── Routing ────────────────────────────────────────────────────────────────────
def main():
    # If not logged in → show login/register
    if not st.session_state.get("authenticated"):
        login_page.render()
        return

    # Auto-load latest resume once per login (silently)
    auto_load_latest_resume()

    # Sidebar navigation — returns the currently active page name
    page = render_sidebar()

    # Ensure page is always a valid key
    if page not in PAGE_MAP:
        page = "Dashboard"
        st.session_state.current_page = page

    # Render the selected page
    PAGE_MAP[page].render()


if __name__ == "__main__":
    main()
else:
    main()
