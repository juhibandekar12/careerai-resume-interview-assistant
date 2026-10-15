"""
frontend/pages/jobs_page.py
----------------------------
Job recommendations and skill-gap analysis UI.
Uses resume auto-loaded from session — no re-upload needed.
"""

import streamlit as st
import plotly.graph_objects as go
from frontend.utils.api_client import APIClient


def _nav_to(page: str):
    st.session_state.current_page = page
    st.rerun()


def _match_gauge(pct: float, title: str = "Match"):
    color = "#10b981" if pct >= 70 else "#f59e0b" if pct >= 40 else "#ef4444"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct,
        domain={"x": [0, 1], "y": [0, 1]},
        number={"suffix": "%", "font": {"color": "#f1f5f9", "size": 22}},
        gauge={
            "axis":        {"range": [0, 100], "tickcolor": "#94a3b8"},
            "bar":         {"color": color},
            "bgcolor":     "rgba(255,255,255,0.04)",
            "bordercolor": "rgba(255,255,255,0.08)",
        },
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        height=160,
        margin=dict(l=10, r=10, t=10, b=0),
        font=dict(color="#94a3b8"),
    )
    return fig


def render():
    st.markdown(
        """
        <div class='hero-banner'>
            <h1>💼 Job Recommendations</h1>
            <p>AI-powered job matching using TF-IDF cosine similarity on your skill set.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    resume_id    = st.session_state.get("resume_id")
    user_skills  = st.session_state.get("user_skills", [])
    resume_fname = st.session_state.get("resume_filename", "")

    # ── Resume guard ──────────────────────────────────────────────────────────
    if not resume_id:
        st.warning("⚠️ No resume loaded. Please upload your resume first to get job recommendations.")
        col_a, col_b = st.columns([1, 3])
        with col_a:
            if st.button("📄 Upload Resume", use_container_width=True):
                _nav_to("Resume Analysis")
        return

    # Active resume banner
    st.markdown(
        f"""
        <div style='background:rgba(99,102,241,0.1); border:1px solid rgba(99,102,241,0.3);
                    border-radius:8px; padding:.5rem .85rem; margin-bottom:1rem;
                    font-size:.82rem; color:#818cf8;'>
            📄 Matching from: <strong>{resume_fname}</strong>
            &nbsp;·&nbsp; {len(user_skills)} skills
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_rec, tab_gap = st.tabs(["🎯 Job Recommendations", "📚 Skill Gap Analysis"])

    # ──────────────────────────────────────────────────────────────────────────
    # Recommendations Tab
    # ──────────────────────────────────────────────────────────────────────────
    with tab_rec:
        st.markdown(
            f"<div style='color:#94a3b8; margin-bottom:1rem;'>Matching your "
            f"<strong style='color:#818cf8;'>{len(user_skills)}</strong> extracted skills "
            f"against 25+ job roles.</div>",
            unsafe_allow_html=True,
        )

        if st.button("🔍 Get Top 5 Job Matches", use_container_width=False):
            with st.spinner("Running TF-IDF matching…"):
                resp = APIClient.recommend_jobs(resume_id)
            if resp.get("success"):
                st.session_state.recommendations = resp["data"]
                st.success(f"✅ Found {len(resp['data'])} job matches!")
            else:
                st.error(resp.get("detail", "Recommendation failed."))

        recs = st.session_state.get("recommendations", [])
        if recs:
            st.markdown(
                "<div class='section-header'>🏆 Your Top Job Matches</div>",
                unsafe_allow_html=True,
            )
            for i, rec in enumerate(recs, 1):
                pct   = rec["match_percentage"]
                color = "#10b981" if pct >= 70 else "#f59e0b" if pct >= 40 else "#ef4444"
                with st.expander(
                    f"#{i}  {rec['title']}  ·  {pct}% match  ·  {rec.get('experience_level','')}",
                    expanded=(i == 1),
                ):
                    col_l, col_r = st.columns([2, 1])
                    with col_l:
                        st.markdown(
                            f"""
                            <div class='career-card'>
                                <div style='display:flex; justify-content:space-between; margin-bottom:.75rem;'>
                                    <span style='background:rgba(99,102,241,0.15);
                                                 border:1px solid rgba(99,102,241,0.3);
                                                 border-radius:99px; padding:.2rem .75rem;
                                                 font-size:.78rem; color:#818cf8;'>
                                        {rec.get("category","")}
                                    </span>
                                    <span style='color:#94a3b8; font-size:.85rem;'>
                                        💰 {rec.get("avg_salary","N/A")}
                                    </span>
                                </div>
                                <p style='color:#94a3b8; font-size:.88rem; line-height:1.6;'>
                                    {rec.get("description","")}
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        # Missing skills
                        missing = rec.get("missing_skills", [])
                        if missing:
                            st.markdown(
                                "<div style='font-weight:600; margin:.75rem 0 .3rem;'>❌ Missing Skills:</div>",
                                unsafe_allow_html=True,
                            )
                            tags = "".join(
                                f"<span class='skill-tag missing'>{s}</span>"
                                for s in missing
                            )
                            st.markdown(tags, unsafe_allow_html=True)

                        # Matching skills
                        req      = rec.get("required_skills", [])
                        matching = [s for s in req if s.lower() in
                                    {sk.lower() for sk in user_skills}]
                        if matching:
                            st.markdown(
                                "<div style='font-weight:600; margin:.75rem 0 .3rem;'>✅ Matching Skills:</div>",
                                unsafe_allow_html=True,
                            )
                            tags2 = "".join(
                                f"<span class='skill-tag matching'>{s}</span>"
                                for s in matching
                            )
                            st.markdown(tags2, unsafe_allow_html=True)

                    with col_r:
                        st.plotly_chart(_match_gauge(pct), use_container_width=True)
                        if st.button(f"📚 Analyse Gap", key=f"gap_btn_{i}"):
                            st.session_state.selected_job = rec["title"]
                            # Switch to skill gap tab via flag
                            st.session_state._open_gap_tab = True
                            st.rerun()

                    # Interview practice shortcut
                    st.markdown("<div style='height:.25rem'></div>", unsafe_allow_html=True)
                    if st.button(
                        f"🎤 Practice Interview for {rec['title']}",
                        key=f"interview_btn_{i}",
                        use_container_width=True,
                    ):
                        st.session_state._interview_role = rec["title"]
                        _nav_to("Interview Practice")

    # ──────────────────────────────────────────────────────────────────────────
    # Skill Gap Tab
    # ──────────────────────────────────────────────────────────────────────────
    with tab_gap:
        job_titles  = APIClient.get_job_titles()
        default_idx = 0
        selected_job = st.session_state.get("selected_job")
        if selected_job and selected_job in job_titles:
            default_idx = job_titles.index(selected_job)

        chosen = st.selectbox(
            "Select a target job role",
            job_titles,
            index=default_idx,
            key="gap_job_selector",
        )
        if st.button("🔍 Analyse My Skill Gap", use_container_width=False):
            with st.spinner(f"Analysing gap for {chosen}… (Groq AI generating roadmap)"):
                resp = APIClient.get_skill_gap(resume_id, chosen)
            if resp.get("success"):
                st.session_state.skill_gap = resp["data"]
                st.success("✅ Skill gap analysis complete!")
            else:
                st.error(resp.get("detail", "Skill gap analysis failed."))

        gap = st.session_state.get("skill_gap")
        if gap:
            match_pct = gap.get("match_percentage", 0)
            color     = "#10b981" if match_pct >= 70 else "#f59e0b" if match_pct >= 40 else "#ef4444"

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🎯 Match", f"{match_pct}%")
            with col2:
                st.metric("✅ Matching Skills", len(gap.get("matching_skills", [])))
            with col3:
                st.metric("❌ Missing Skills", len(gap.get("missing_skills", [])))

            c_left, c_right = st.columns(2)
            with c_left:
                st.markdown(
                    "<div class='section-header'>❌ Skills to Acquire</div>",
                    unsafe_allow_html=True,
                )
                missing = gap.get("missing_skills", [])
                if missing:
                    st.markdown(
                        "".join(f"<span class='skill-tag missing'>{s}</span>" for s in missing),
                        unsafe_allow_html=True,
                    )
                else:
                    st.success("🎉 You already have all required skills!")

            with c_right:
                st.markdown(
                    "<div class='section-header'>✅ Skills You Have</div>",
                    unsafe_allow_html=True,
                )
                matching_skills = gap.get("matching_skills", [])
                if matching_skills:
                    st.markdown(
                        "".join(f"<span class='skill-tag matching'>{s}</span>" for s in matching_skills),
                        unsafe_allow_html=True,
                    )

            # Radar chart
            if gap.get("matching_skills") or gap.get("missing_skills"):
                labels = ["Match %", "Skills Coverage", "Gap Size (inv)", "Readiness"]
                values = [
                    match_pct / 10,
                    len(gap.get("matching_skills", [])),
                    max(0, 10 - len(gap.get("missing_skills", []))),
                    match_pct / 10,
                ]
                fig_radar = go.Figure(go.Scatterpolar(
                    r=values,
                    theta=labels,
                    fill="toself",
                    fillcolor="rgba(99,102,241,0.2)",
                    line=dict(color="#6366f1", width=2),
                ))
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 10],
                                        gridcolor="rgba(255,255,255,0.1)"),
                        angularaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
                        bgcolor="rgba(0,0,0,0)",
                    ),
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#94a3b8"),
                    showlegend=False,
                    height=300,
                    margin=dict(l=40, r=40, t=20, b=20),
                )
                st.plotly_chart(fig_radar, use_container_width=True)

            # Learning roadmap (Groq-generated)
            roadmap = gap.get("learning_roadmap", {})
            phases  = roadmap.get("phases", [])
            if phases:
                st.markdown(
                    "<div class='section-header'>🗺️ Groq AI – Personalised Learning Roadmap</div>",
                    unsafe_allow_html=True,
                )
                for phase in phases:
                    with st.expander(
                        f"📌 {phase.get('phase','Phase')} — {phase.get('duration','')}",
                        expanded=True,
                    ):
                        skills_p = phase.get("skills", [])
                        if skills_p:
                            st.markdown(
                                "**Skills to learn:** " +
                                " ".join(f"<span class='skill-tag'>{s}</span>" for s in skills_p),
                                unsafe_allow_html=True,
                            )
                        resources = phase.get("resources", [])
                        if resources:
                            st.markdown("**Resources:**")
                            for r in resources:
                                st.markdown(f"- [{r}]({r})")
            elif roadmap.get("message"):
                st.success(roadmap["message"])

            # Practice interview shortcut
            st.markdown("---")
            if st.button(
                f"🎤 Practice Interview for {chosen}", use_container_width=False
            ):
                _nav_to("Interview Practice")
