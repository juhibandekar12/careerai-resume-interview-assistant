"""
frontend/components/sidebar.py
-------------------------------
Renders the left sidebar navigation and returns the selected page name.
"""

import streamlit as st
from frontend.utils.session import logout


def render_sidebar() -> str:
    """Draw sidebar and return the active page name."""

    with st.sidebar:
        # ── Brand ──────────────────────────────────────────────────────────
        st.markdown(
            """
            <div style='text-align:center; margin-bottom:1.5rem;'>
                <div style='font-size:2.5rem;'>🚀</div>
                <div style='font-family:Poppins,sans-serif; font-weight:800;
                            font-size:1.4rem; background:linear-gradient(135deg,#6366f1,#06b6d4);
                            -webkit-background-clip:text; -webkit-text-fill-color:transparent;'>
                    CareerAI
                </div>
                <div style='color:#94a3b8; font-size:.75rem; letter-spacing:.1em; text-transform:uppercase;'>
                    Career Assistance System
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── User chip ───────────────────────────────────────────────────────
        name = st.session_state.get("full_name") or st.session_state.get("username", "User")
        st.markdown(
            f"""
            <div style='background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08);
                        border-radius:10px; padding:.75rem 1rem; margin-bottom:1rem;
                        display:flex; align-items:center; gap:.75rem;'>
                <div style='width:36px; height:36px; border-radius:50%;
                            background:linear-gradient(135deg,#6366f1,#06b6d4);
                            display:flex; align-items:center; justify-content:center;
                            font-weight:700; font-size:.95rem; color:#fff; flex-shrink:0;'>
                    {name[0].upper()}
                </div>
                <div>
                    <div style='font-weight:600; font-size:.9rem; color:#f1f5f9;'>{name}</div>
                    <div style='font-size:.75rem; color:#94a3b8;'>Signed in</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Resume status badge ──────────────────────────────────────────────
        has_resume   = bool(st.session_state.get("resume_id"))
        resume_fname = st.session_state.get("resume_filename", "")
        if has_resume and resume_fname:
            st.markdown(
                f"""
                <div style='background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3);
                            border-radius:8px; padding:.5rem .75rem; margin-bottom:1rem;
                            font-size:.78rem; color:#10b981; display:flex; align-items:center; gap:.4rem;'>
                    <span>✅</span>
                    <span style='overflow:hidden; text-overflow:ellipsis; white-space:nowrap;'
                          title='{resume_fname}'>
                        {resume_fname[:28] + "…" if len(resume_fname) > 28 else resume_fname}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div style='background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.3);
                            border-radius:8px; padding:.5rem .75rem; margin-bottom:.5rem;
                            font-size:.78rem; color:#ef4444;'>
                    ⚠️ No resume loaded
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("📤 Upload Resume Now", use_container_width=True, key="sidebar_upload_btn"):
                st.session_state.current_page = "Resume Analysis"
                st.rerun()

        # ── Navigation ──────────────────────────────────────────────────────
        nav_items = [
            ("📊", "Dashboard",           "Overview of your career progress"),
            ("📄", "Resume Analysis",     "Upload & analyse your resume"),
            ("💼", "Job Recommendations", "Discover matching job roles"),
            ("🎤", "Interview Practice",  "AI-powered interview simulator"),
            ("👤", "Profile",             "Your account settings"),
        ]

        if "current_page" not in st.session_state:
            st.session_state.current_page = "Dashboard"

        st.markdown(
            "<div style='color:#94a3b8; font-size:.72rem; text-transform:uppercase; "
            "letter-spacing:.1em; margin-bottom:.5rem;'>Navigation</div>",
            unsafe_allow_html=True,
        )

        for icon, label, desc in nav_items:
            is_active = st.session_state.current_page == label
            if st.button(
                f"{icon}  {label}",
                key=f"nav_{label}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state.current_page = label
                st.rerun()

        st.markdown("---")

        # ── Logout ──────────────────────────────────────────────────────────
        st.markdown("<div style='margin-top:.5rem;'></div>", unsafe_allow_html=True)
        if st.button("🚪  Sign Out", use_container_width=True, type="secondary"):
            logout()
            st.rerun()

    return st.session_state.current_page
