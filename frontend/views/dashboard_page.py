"""
frontend/pages/dashboard_page.py
----------------------------------
Main dashboard showing resume stats, interview history, and skill progress.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from frontend.utils.api_client import APIClient
from utils.helpers import format_date, score_to_color, score_to_grade


def _nav_to(page: str):
    """Navigate to a page by updating session state and rerunning."""
    st.session_state.current_page = page
    st.rerun()


def render():
    # ── Hero banner ───────────────────────────────────────────────────────────
    name = st.session_state.get("full_name") or st.session_state.get("username", "there")
    resume_fname = st.session_state.get("resume_filename", "")
    st.markdown(
        f"""
        <div class='hero-banner'>
            <h1>Welcome back, {name.split()[0]}! 👋</h1>
            <p>Here's your career progress at a glance.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Resume status notice ───────────────────────────────────────────────────
    if st.session_state.get("resume_id"):
        st.markdown(
            f"""
            <div style='background:rgba(16,185,129,0.08); border:1px solid rgba(16,185,129,0.25);
                        border-radius:8px; padding:.6rem 1rem; margin-bottom:1rem;
                        font-size:.82rem; color:#10b981;'>
                ✅ Active resume: <strong>{resume_fname}</strong>
                &nbsp;·&nbsp; {len(st.session_state.get("user_skills", []))} skills ready
                &nbsp;·&nbsp; All sections are ready to use
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style='background:rgba(245,158,11,0.08); border:1px solid rgba(245,158,11,0.25);
                        border-radius:8px; padding:.6rem 1rem; margin-bottom:1rem;
                        font-size:.82rem; color:#f59e0b;'>
                ⚠️ No resume uploaded yet. Upload once and all features unlock automatically.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Fetch stats ───────────────────────────────────────────────────────────
    with st.spinner("Loading dashboard…"):
        resp = APIClient.get_dashboard_stats()

    if not resp.get("success"):
        st.warning("Could not load dashboard data. Is the backend running?")
        st.code(resp.get("detail", "Unknown error"))
        return

    data = resp["data"]

    # ── Top KPI cards ──────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("📄 Resumes Uploaded",  data.get("total_resumes",  0))
    with c2:
        st.metric("🛠 Skills Detected",   data.get("total_skills",   0))
    with c3:
        st.metric("🎤 Interview Sessions", data.get("total_sessions", 0))
    with c4:
        avg = data.get("avg_interview_score", 0)
        st.metric("⭐ Avg Interview Score", f"{avg}/10")

    st.markdown("---")

    col_left, col_right = st.columns([3, 2])

    # ── Score trend chart ──────────────────────────────────────────────────────
    with col_left:
        st.markdown(
            "<div class='section-header'>📈 Interview Score Trend</div>",
            unsafe_allow_html=True,
        )
        trend = data.get("score_trend", [])
        if trend:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[t["date"]  for t in trend],
                y=[t["score"] for t in trend],
                mode="lines+markers",
                line=dict(color="#6366f1", width=3, shape="spline"),
                marker=dict(size=8, color="#818cf8",
                            line=dict(color="#fff", width=2)),
                fill="tozeroy",
                fillcolor="rgba(99,102,241,0.12)",
                name="Score",
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8", size=11),
                xaxis=dict(showgrid=False, color="#94a3b8"),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)",
                           range=[0, 10], color="#94a3b8"),
                margin=dict(l=0, r=0, t=10, b=0),
                showlegend=False,
                height=220,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Complete interview sessions to see your score trend.")

    # ── Skill breakdown ────────────────────────────────────────────────────────
    with col_right:
        st.markdown(
            "<div class='section-header'>🛠 Top Skills</div>",
            unsafe_allow_html=True,
        )
        top_skills = data.get("top_skills", [])
        if top_skills:
            fig2 = go.Figure(go.Bar(
                x=list(range(1, len(top_skills) + 1)),
                y=[1] * len(top_skills),
                text=top_skills,
                textposition="inside",
                marker_color=[
                    f"hsl({(i * 36) % 360},70%,60%)"
                    for i in range(len(top_skills))
                ],
            ))
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                xaxis=dict(showticklabels=False, showgrid=False),
                yaxis=dict(showticklabels=False, showgrid=False),
                height=220,
                margin=dict(l=0, r=0, t=10, b=0),
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Upload a resume to see your skills here.")

    st.markdown("---")

    col_a, col_b = st.columns(2)

    # ── Recent interview sessions ──────────────────────────────────────────────
    with col_a:
        st.markdown(
            "<div class='section-header'>🎤 Recent Sessions</div>",
            unsafe_allow_html=True,
        )
        sessions = data.get("recent_sessions", [])
        if sessions:
            for s in sessions:
                score       = s.get("overall_score") or 0
                color       = score_to_color(score)
                grade       = score_to_grade(score)
                status_icon = "✅" if s["status"] == "completed" else "🔄"
                st.markdown(
                    f"""
                    <div class='career-card' style='display:flex; justify-content:space-between; align-items:center;'>
                        <div>
                            <div style='font-weight:600;'>{status_icon} {s["job_role"]}</div>
                            <div style='color:#94a3b8; font-size:.8rem;'>{s["started_at"][:10]}</div>
                        </div>
                        <div style='text-align:right;'>
                            <div style='font-size:1.3rem; font-weight:700; color:{color};'>{score}/10</div>
                            <div style='color:#94a3b8; font-size:.75rem;'>Grade {grade}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No interview sessions yet. Start practising! 🎤")

    # ── Skill gap summary ──────────────────────────────────────────────────────
    with col_b:
        st.markdown(
            "<div class='section-header'>📚 Skill Gap History</div>",
            unsafe_allow_html=True,
        )
        gaps = data.get("gap_summary", [])
        if gaps:
            for g in gaps:
                missing   = g["missing_count"]
                bar_color = "#10b981" if missing == 0 else "#f59e0b" if missing < 5 else "#ef4444"
                st.markdown(
                    f"""
                    <div class='career-card' style='display:flex; justify-content:space-between; align-items:center;'>
                        <div>
                            <div style='font-weight:600;'>💼 {g["job_role"]}</div>
                            <div style='color:#94a3b8; font-size:.8rem;'>{g["date"]}</div>
                        </div>
                        <div style='text-align:right;'>
                            <div style='font-size:1.2rem; font-weight:700; color:{bar_color};'>{missing}</div>
                            <div style='color:#94a3b8; font-size:.75rem;'>missing skills</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("Run skill-gap analysis to see results here.")

    # ── Quick action buttons ───────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        "<div class='section-header'>⚡ Quick Actions</div>",
        unsafe_allow_html=True,
    )
    qa1, qa2, qa3, qa4 = st.columns(4)
    with qa1:
        if st.button("📄 Upload Resume", use_container_width=True, key="dash_upload"):
            _nav_to("Resume Analysis")
    with qa2:
        if st.button("💼 Find Jobs", use_container_width=True, key="dash_jobs"):
            _nav_to("Job Recommendations")
    with qa3:
        if st.button("🎤 Practice Interview", use_container_width=True, key="dash_interview"):
            _nav_to("Interview Practice")
    with qa4:
        if st.button("🔄 Refresh Stats", use_container_width=True, key="dash_refresh"):
            st.rerun()
