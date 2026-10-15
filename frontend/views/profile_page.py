"""
frontend/pages/profile_page.py
--------------------------------
User profile page showing account info and interview history.
"""

import streamlit as st
import plotly.express as px
from frontend.utils.api_client import APIClient
from utils.helpers import format_date, score_to_color, score_to_grade


def render():
    st.markdown(
        """
        <div class='hero-banner'>
            <h1>👤 My Profile</h1>
            <p>Your account details, performance history, and career progress.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    name     = st.session_state.get("full_name") or st.session_state.get("username", "User")
    username = st.session_state.get("username", "")
    email    = st.session_state.get("email", "")

    col_avatar, col_info = st.columns([1, 3])
    with col_avatar:
        st.markdown(
            f"""
            <div style='text-align:center; padding:1.5rem;'>
                <div style='width:100px; height:100px; border-radius:50%; margin:0 auto 1rem;
                            background:linear-gradient(135deg,#6366f1,#06b6d4);
                            display:flex; align-items:center; justify-content:center;
                            font-size:2.5rem; font-weight:800; color:#fff;
                            box-shadow:0 0 30px rgba(99,102,241,0.4);'>
                    {name[0].upper()}
                </div>
                <div style='font-weight:700; font-size:1.15rem;'>{name}</div>
                <div style='color:#94a3b8; font-size:.85rem;'>@{username}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_info:
        st.markdown("<div class='section-header'>Account Details</div>", unsafe_allow_html=True)
        col_e, col_u = st.columns(2)
        with col_e:
            st.markdown(
                f"<div class='career-card'><div style='color:#94a3b8;font-size:.78rem;'>EMAIL</div>"
                f"<div style='font-weight:600;'>{email or 'N/A'}</div></div>",
                unsafe_allow_html=True,
            )
        with col_u:
            st.markdown(
                f"<div class='career-card'><div style='color:#94a3b8;font-size:.78rem;'>USERNAME</div>"
                f"<div style='font-weight:600;'>{username}</div></div>",
                unsafe_allow_html=True,
            )

        resume_id = st.session_state.get("resume_id")
        skills    = st.session_state.get("user_skills", [])
        col_r, col_s = st.columns(2)
        with col_r:
            st.markdown(
                f"<div class='career-card'><div style='color:#94a3b8;font-size:.78rem;'>ACTIVE RESUME</div>"
                f"<div style='font-weight:600;'>{'Resume #' + str(resume_id) if resume_id else 'None uploaded'}</div></div>",
                unsafe_allow_html=True,
            )
        with col_s:
            st.markdown(
                f"<div class='career-card'><div style='color:#94a3b8;font-size:.78rem;'>SKILLS DETECTED</div>"
                f"<div style='font-weight:600;'>{len(skills)}</div></div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # ── Interview history ─────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>🎤 Interview History</div>", unsafe_allow_html=True)
    resp = APIClient.get_sessions()
    sessions = resp.get("data", [])

    if not sessions:
        st.info("No interview sessions yet. Start practising!")
    else:
        for s in sessions:
            score  = s.get("overall_score") or 0
            color  = score_to_color(score)
            grade  = score_to_grade(score)
            status = "✅ Completed" if s["status"] == "completed" else "🔄 In Progress"

            with st.expander(
                f"💼 {s['job_role']}  ·  {score}/10  ·  {s['started_at'][:10]}",
                expanded=False,
            ):
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(
                        f"<div class='career-card' style='text-align:center;'>"
                        f"<div style='color:#94a3b8;font-size:.75rem;'>STATUS</div>"
                        f"<div style='font-weight:600;'>{status}</div></div>",
                        unsafe_allow_html=True,
                    )
                with c2:
                    st.markdown(
                        f"<div class='career-card' style='text-align:center;'>"
                        f"<div style='color:#94a3b8;font-size:.75rem;'>SCORE</div>"
                        f"<div style='font-weight:700; font-size:1.3rem; color:{color};'>{score}/10</div></div>",
                        unsafe_allow_html=True,
                    )
                with c3:
                    st.markdown(
                        f"<div class='career-card' style='text-align:center;'>"
                        f"<div style='color:#94a3b8;font-size:.75rem;'>GRADE</div>"
                        f"<div style='font-weight:700; font-size:1.3rem; color:{color};'>{grade}</div></div>",
                        unsafe_allow_html=True,
                    )

                # Detailed breakdown
                if s["status"] == "completed":
                    break_resp = APIClient.get_interview_breakdown(s["id"])
                    breakdown  = break_resp.get("data", {})
                    if breakdown:
                        labels = ["Relevance", "Clarity", "Technical", "Overall"]
                        vals   = [
                            breakdown.get("relevance", 0),
                            breakdown.get("clarity",   0),
                            breakdown.get("technical", 0),
                            breakdown.get("overall",   0),
                        ]
                        fig = px.bar(
                            x=labels, y=vals,
                            color=vals,
                            color_continuous_scale=["#ef4444", "#f59e0b", "#10b981"],
                            range_color=[0, 10],
                        )
                        fig.update_layout(
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="#94a3b8"),
                            xaxis=dict(showgrid=False),
                            yaxis=dict(range=[0, 10], showgrid=True,
                                       gridcolor="rgba(255,255,255,0.05)"),
                            coloraxis_showscale=False,
                            height=200,
                            margin=dict(l=0, r=0, t=10, b=0),
                            showlegend=False,
                        )
                        st.plotly_chart(fig, use_container_width=True)

    # ── Skills in profile ─────────────────────────────────────────────────────
    if skills:
        st.markdown("---")
        st.markdown("<div class='section-header'>🛠 My Skills</div>", unsafe_allow_html=True)
        tags = "".join(f"<span class='skill-tag'>{s}</span>" for s in skills)
        st.markdown(tags, unsafe_allow_html=True)
