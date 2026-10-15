"""
frontend/pages/resume_page.py
------------------------------
Resume upload and structured analysis display.
One-time upload: once a resume is loaded it persists for the whole session.
"""

import streamlit as st
import plotly.graph_objects as go
from frontend.utils.api_client import APIClient
from utils.helpers import calculate_profile_completeness


def _nav_to(page: str):
    """Helper: navigate to another page."""
    st.session_state.current_page = page
    st.rerun()


def render():
    st.markdown(
        """
        <div class='hero-banner'>
            <h1>📄 Resume Analysis</h1>
            <p>Upload your PDF resume once — all other sections will use it automatically.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Active resume banner ──────────────────────────────────────────────────
    active_resume = st.session_state.get("resume_data")
    active_fname  = st.session_state.get("resume_filename", "")
    if active_resume and active_fname:
        skills_count = len(st.session_state.get("user_skills", []))
        st.markdown(
            f"""
            <div style='background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.35);
                        border-radius:12px; padding:1rem 1.25rem; margin-bottom:1rem;
                        display:flex; justify-content:space-between; align-items:center;'>
                <div>
                    <span style='color:#10b981; font-weight:700; font-size:.95rem;'>
                        ✅ Active Resume:
                    </span>
                    <span style='color:#f1f5f9; margin-left:.5rem;'>{active_fname}</span>
                    <div style='color:#94a3b8; font-size:.8rem; margin-top:.2rem;'>
                        {skills_count} skills extracted · Used by Interview Practice &amp; Job Recommendations
                    </div>
                </div>
                <div style='display:flex; gap:.5rem;'>
                    <span style='font-size:1.5rem;'>📄</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    tab_upload, tab_view = st.tabs(["⬆️  Upload / Change Resume", "📊  Analysis Results"])

    # ──────────────────────────────────────────────────────────────────────────
    # Upload Tab
    # ──────────────────────────────────────────────────────────────────────────
    with tab_upload:
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

        if active_resume:
            st.info(
                "ℹ️ A resume is already loaded and being used across all sections. "
                "You can upload a new one below to replace it, or load a previous one."
            )

        st.markdown(
            """
            <div style='color:#94a3b8; margin-bottom:1rem; font-size:.9rem;'>
                Upload a PDF resume (max 10 MB). Our AI will extract skills, education,
                experience, projects, and certifications automatically.
            </div>
            """,
            unsafe_allow_html=True,
        )

        uploaded_file = st.file_uploader(
            "Drop your resume here or click to browse",
            type=["pdf"],
            key="resume_uploader",
        )

        if uploaded_file:
            col_info, col_btn = st.columns([3, 1])
            with col_info:
                st.markdown(
                    f"""
                    <div class='career-card'>
                        <div style='font-size:1.5rem; margin-bottom:.25rem;'>📎</div>
                        <div style='font-weight:600;'>{uploaded_file.name}</div>
                        <div style='color:#94a3b8; font-size:.8rem;'>
                            {round(uploaded_file.size / 1024, 1)} KB · PDF
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col_btn:
                st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
                analyze = st.button("🔍 Analyse Resume", use_container_width=True)

            if analyze:
                with st.spinner("🤖 Extracting information from your resume…"):
                    resp = APIClient.upload_resume(
                        uploaded_file.read(), uploaded_file.name
                    )

                if resp.get("success"):
                    st.success("✅ Resume analysed successfully!")
                    data = resp["data"]
                    # Store in session — now available to ALL sections
                    st.session_state.resume_id       = resp["resume_id"]
                    st.session_state.resume_data     = data
                    st.session_state.resume_filename = uploaded_file.name
                    st.session_state.user_skills     = data.get("skills", [])
                    st.rerun()
                else:
                    st.error(f"Analysis failed: {resp.get('detail', 'Unknown error')}")

        # ── Previous resumes ──────────────────────────────────────────────────
        st.markdown("---")
        st.markdown(
            "<div class='section-header'>📂 Your Previously Uploaded Resumes</div>",
            unsafe_allow_html=True,
        )
        resumes_resp = APIClient.list_resumes()
        resumes = resumes_resp.get("data", [])
        if resumes:
            for r in resumes:
                is_current = (r["id"] == st.session_state.get("resume_id"))
                col_r, col_load = st.columns([4, 1])
                with col_r:
                    badge = (
                        "<span style='background:rgba(16,185,129,0.2); color:#10b981; "
                        "font-size:.72rem; border-radius:99px; padding:.1rem .5rem; "
                        "margin-left:.5rem;'>● Active</span>"
                        if is_current else ""
                    )
                    st.markdown(
                        f"""
                        <div class='career-card' style='margin-bottom:.5rem;'>
                            <span style='font-weight:600;'>📄 {r["filename"]}</span>{badge}
                            <span style='color:#94a3b8; font-size:.8rem; margin-left:1rem;'>
                                {r["upload_date"][:10]}
                            </span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with col_load:
                    btn_label = "✓ Loaded" if is_current else "Load"
                    if not is_current and st.button(btn_label, key=f"load_resume_{r['id']}"):
                        with st.spinner("Loading…"):
                            detail = APIClient.get_resume(r["id"])
                        if detail.get("success"):
                            d = detail["data"]
                            st.session_state.resume_id       = d["id"]
                            st.session_state.resume_data     = d
                            st.session_state.resume_filename = d.get("filename", "")
                            st.session_state.user_skills     = d.get("skills", [])
                            st.rerun()
                    elif is_current:
                        st.markdown(
                            "<div style='padding:.4rem; color:#10b981; font-size:.85rem;'>✓ Active</div>",
                            unsafe_allow_html=True,
                        )
        else:
            st.info("No resumes uploaded yet.")

        # ── Quick navigation after upload ─────────────────────────────────────
        if st.session_state.get("resume_id"):
            st.markdown("---")
            st.markdown(
                "<div class='section-header'>⚡ What would you like to do next?</div>",
                unsafe_allow_html=True,
            )
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("💼 Get Job Recommendations", use_container_width=True):
                    _nav_to("Job Recommendations")
            with c2:
                if st.button("🎤 Practice Interview", use_container_width=True):
                    _nav_to("Interview Practice")
            with c3:
                if st.button("📊 View Dashboard", use_container_width=True):
                    _nav_to("Dashboard")

    # ──────────────────────────────────────────────────────────────────────────
    # Analysis Results Tab
    # ──────────────────────────────────────────────────────────────────────────
    with tab_view:
        data = st.session_state.get("resume_data")
        if not data:
            st.info("📤 Upload a resume first to see analysis results.")
            return

        # ── Completeness gauge ────────────────────────────────────────────────
        completeness = calculate_profile_completeness(data)
        col_g, col_contact = st.columns([1, 2])
        with col_g:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=completeness,
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": "Profile Completeness", "font": {"color": "#94a3b8", "size": 13}},
                gauge={
                    "axis":        {"range": [0, 100], "tickcolor": "#94a3b8"},
                    "bar":         {"color": "#6366f1"},
                    "bgcolor":     "rgba(255,255,255,0.04)",
                    "bordercolor": "rgba(255,255,255,0.08)",
                    "steps": [
                        {"range": [0,  40],  "color": "rgba(239,68,68,0.15)"},
                        {"range": [40, 70],  "color": "rgba(245,158,11,0.15)"},
                        {"range": [70, 100], "color": "rgba(16,185,129,0.15)"},
                    ],
                },
                number={"suffix": "%", "font": {"color": "#f1f5f9", "size": 28}},
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8"),
                height=220,
                margin=dict(l=20, r=20, t=30, b=0),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_contact:
            st.markdown(
                "<div class='section-header'>👤 Contact Information</div>",
                unsafe_allow_html=True,
            )
            contact = data.get("contact_info", {})
            if contact:
                for k, v in contact.items():
                    icon = {"name": "🧑", "email": "📧", "phone": "📞",
                            "linkedin": "💼", "github": "🐙"}.get(k, "•")
                    st.markdown(
                        f"<div style='margin:.3rem 0;'>{icon} <strong>{k.title()}:</strong> "
                        f"<span style='color:#94a3b8;'>{v}</span></div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No contact info detected.")

        # ── Skills ────────────────────────────────────────────────────────────
        st.markdown("<div class='section-header'>🛠 Extracted Skills</div>", unsafe_allow_html=True)
        skills = data.get("skills", [])
        if skills:
            tags_html = "".join(f"<span class='skill-tag'>{s}</span>" for s in skills)
            st.markdown(tags_html, unsafe_allow_html=True)
            st.caption(f"Total: {len(skills)} skills detected — these are used for interview & job matching")
        else:
            st.warning("No skills extracted. Try a more detailed resume.")

        # ── Education / Experience / Projects / Certs in tabs ─────────────────
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        t1, t2, t3, t4 = st.tabs(["🎓 Education", "💼 Experience", "🚀 Projects", "🏆 Certifications"])

        with t1:
            edu = data.get("education", [])
            if edu:
                for e in edu:
                    st.markdown(
                        f"""
                        <div class='career-card'>
                            <div style='font-weight:600;'>{e.get("degree","")}</div>
                            <div style='color:#94a3b8; font-size:.85rem;'>
                                {e.get("institution","")}
                                {" · " + e["year"] if e.get("year") else ""}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No education entries detected.")

        with t2:
            exp = data.get("experience", [])
            if exp:
                for e in exp:
                    with st.expander(e.get("title", "Experience Entry")):
                        st.write(e.get("description", "").strip() or "No description.")
            else:
                st.info("No work experience entries detected.")

        with t3:
            projs = data.get("projects", [])
            if projs:
                for p in projs:
                    with st.expander(f"🚀 {p.get('name', 'Project')}"):
                        st.write(p.get("description", "").strip() or "No description.")
            else:
                st.info("No projects detected.")

        with t4:
            certs = data.get("certifications", [])
            if certs:
                for c in certs:
                    st.markdown(f"<div style='margin:.3rem 0;'>🏆 {c}</div>", unsafe_allow_html=True)
            else:
                st.info("No certifications detected.")
