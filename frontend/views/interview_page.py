"""
frontend/pages/interview_page.py
---------------------------------
AI Interview Practice – question generation, answer submission, and result display.
Powered by Groq AI. Requires an uploaded resume (auto-loaded from session).
"""

import streamlit as st
import plotly.graph_objects as go
from frontend.utils.api_client import APIClient
from utils.helpers import score_to_color, score_to_grade


def _nav_to(page: str):
    st.session_state.current_page = page
    st.rerun()


def _score_bar(label: str, score: float):
    color = score_to_color(score)
    pct = score * 10
    st.markdown(
        f"""
        <div style='margin:.4rem 0;'>
            <div style='display:flex; justify-content:space-between; margin-bottom:.2rem;'>
                <span style='font-size:.85rem; color:#94a3b8;'>{label}</span>
                <span style='font-size:.85rem; font-weight:600; color:{color};'>{score}/10</span>
            </div>
            <div style='background:rgba(255,255,255,0.06); border-radius:99px; height:6px;'>
                <div style='background:{color}; width:{pct}%; height:6px;
                            border-radius:99px; transition:width .5s ease;'></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render():
    st.markdown(
        """
        <div class='hero-banner'>
            <h1>🎤 AI Interview Practice</h1>
            <p>Prepare with Groq AI-generated questions and get instant feedback on your answers.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Resume guard ──────────────────────────────────────────────────────────
    resume_id    = st.session_state.get("resume_id")
    user_skills  = st.session_state.get("user_skills", [])
    resume_fname = st.session_state.get("resume_filename", "")

    if not resume_id:
        st.warning(
            "⚠️ No resume loaded. Please upload your resume first — "
            "it is used to personalise interview questions to your skills."
        )
        col_a, col_b = st.columns([1, 3])
        with col_a:
            if st.button("📄 Upload Resume", use_container_width=True):
                _nav_to("Resume Analysis")
        return

    # Show active resume chip
    st.markdown(
        f"""
        <div style='background:rgba(99,102,241,0.1); border:1px solid rgba(99,102,241,0.3);
                    border-radius:8px; padding:.5rem .85rem; margin-bottom:1rem;
                    font-size:.82rem; color:#818cf8;'>
            📄 Generating questions from: <strong>{resume_fname}</strong>
            &nbsp;·&nbsp; {len(user_skills)} skills detected
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_setup, tab_practice, tab_results = st.tabs(
        ["⚙️ Setup", "🎯 Practice Session", "📊 Results"]
    )

    # ──────────────────────────────────────────────────────────────────────────
    # Setup Tab
    # ──────────────────────────────────────────────────────────────────────────
    with tab_setup:
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
        job_titles = APIClient.get_job_titles()

        col_form, col_info = st.columns([2, 1])
        with col_form:
            chosen_role = st.selectbox(
                "🎯 Select Job Role", job_titles, key="iv_job_role"
            )
            col_nt, col_nh = st.columns(2)
            with col_nt:
                num_tech = st.slider("Technical Questions", 1, 8, 5, key="iv_num_tech")
            with col_nh:
                num_hr = st.slider("HR Questions", 1, 5, 3, key="iv_num_hr")

            use_resume_skills = st.checkbox(
                f"✅ Use skills from my uploaded resume ({len(user_skills)} skills)",
                value=True,
                key="iv_use_skills",
            )
            extra_skills_input = st.text_input(
                "Or add extra skills manually (comma-separated)",
                placeholder="e.g. Docker, Kubernetes, GraphQL…",
                key="iv_extra_skills",
            )

            if user_skills and use_resume_skills:
                # Preview the skills being used
                preview = user_skills[:10]
                tags = " ".join(
                    f"<span style='background:rgba(99,102,241,0.15); border:1px solid rgba(99,102,241,0.3); "
                    f"border-radius:99px; padding:.15rem .6rem; font-size:.75rem; color:#818cf8; "
                    f"margin:.1rem; display:inline-block;'>{s}</span>"
                    for s in preview
                )
                more = f" <span style='color:#94a3b8; font-size:.75rem;'>+{len(user_skills)-10} more</span>" if len(user_skills) > 10 else ""
                st.markdown(
                    f"<div style='margin:.5rem 0;'>{tags}{more}</div>",
                    unsafe_allow_html=True,
                )

            if st.button("🚀 Generate Interview Questions", use_container_width=True):
                if use_resume_skills:
                    skills = user_skills.copy()
                    if extra_skills_input.strip():
                        skills += [s.strip() for s in extra_skills_input.split(",") if s.strip()]
                else:
                    skills = [s.strip() for s in extra_skills_input.split(",") if s.strip()]

                with st.spinner("🤖 Groq AI is generating personalised interview questions…"):
                    resp = APIClient.start_interview(
                        chosen_role, skills, num_tech, num_hr
                    )

                if resp.get("success"):
                    st.session_state.session_id    = resp["session_id"]
                    st.session_state.questions     = resp["questions"]
                    st.session_state.current_q_idx = 0
                    st.session_state.answers       = []
                    st.session_state.evaluations   = []
                    st.session_state.interview_done = False
                    st.session_state._interview_role = chosen_role
                    st.success(
                        f"✅ {len(resp['questions'])} questions generated! "
                        "Switch to the **Practice Session** tab to begin."
                    )
                else:
                    err = resp.get("detail", "Failed to start session.")
                    st.error(f"Error: {err}")
                    if "GROQ_API_KEY" in err:
                        st.info("💡 Make sure your GROQ_API_KEY is set in the .env file.")

        with col_info:
            st.markdown(
                """
                <div class='career-card' style='margin-top:.5rem;'>
                    <div style='font-size:1.5rem; margin-bottom:.5rem;'>💡</div>
                    <div style='font-weight:600; margin-bottom:.5rem;'>Interview Tips</div>
                    <ul style='color:#94a3b8; font-size:.85rem; padding-left:1rem; line-height:1.8;'>
                        <li>Use the <strong>STAR method</strong> for behavioural questions</li>
                        <li>Be concise – aim for <strong>1-3 minutes</strong> per answer</li>
                        <li>Include <strong>specific examples</strong> and metrics</li>
                        <li>Show <strong>problem-solving</strong> thought process</li>
                        <li>Ask clarifying questions when needed</li>
                    </ul>
                    <div style='margin-top:.75rem; padding-top:.75rem; border-top:1px solid rgba(255,255,255,0.08);
                                font-size:.78rem; color:#6366f1;'>
                        ⚡ Powered by Groq AI (llama3-70b-8192)
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ──────────────────────────────────────────────────────────────────────────
    # Practice Session Tab
    # ──────────────────────────────────────────────────────────────────────────
    with tab_practice:
        questions = st.session_state.get("questions", [])
        if not questions:
            st.info("⚙️ Configure and generate questions in the **Setup** tab first.")
            return

        if st.session_state.get("interview_done"):
            st.success("🎉 Interview complete! Check your **Results** tab.")
            return

        idx   = st.session_state.get("current_q_idx", 0)
        total = len(questions)

        # Progress bar
        progress = idx / total
        st.progress(progress)
        st.markdown(
            f"<div style='text-align:right; color:#94a3b8; font-size:.82rem;'>"
            f"Question {idx + 1} of {total}</div>",
            unsafe_allow_html=True,
        )

        if idx >= total:
            with st.spinner("Calculating final score…"):
                comp = APIClient.complete_interview(st.session_state.session_id)
            st.session_state.interview_done = True
            st.session_state._final_score   = comp.get("overall_score", 0)
            st.rerun()

        q       = questions[idx]
        q_type  = q.get("type", "technical")
        q_text  = q.get("text", q) if isinstance(q, dict) else q

        type_color = "#6366f1" if q_type == "technical" else "#06b6d4"
        type_label = "Technical" if q_type == "technical" else "HR / Behavioural"

        st.markdown(
            f"""
            <div class='career-card' style='border-color:{type_color}40; margin-top:.5rem;'>
                <div style='display:flex; align-items:center; gap:.5rem; margin-bottom:.75rem;'>
                    <span style='background:{type_color}20; border:1px solid {type_color}50;
                                 border-radius:99px; padding:.2rem .75rem;
                                 color:{type_color}; font-size:.78rem; font-weight:600;'>
                        {"⚙️ " if q_type == "technical" else "💬 "}{type_label}
                    </span>
                    <span style='color:#94a3b8; font-size:.78rem;'>Q{idx + 1}</span>
                </div>
                <div style='font-size:1.1rem; font-weight:600; line-height:1.6;'>{q_text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        answer = st.text_area(
            "Your Answer",
            placeholder="Type your answer here… Be detailed and specific.",
            height=160,
            key=f"answer_input_{idx}",
        )

        col_skip, col_submit = st.columns([1, 3])
        with col_skip:
            if st.button("⏭ Skip", use_container_width=True):
                st.session_state.current_q_idx += 1
                st.rerun()
        with col_submit:
            if st.button("✅ Submit Answer & Get AI Feedback", use_container_width=True):
                if not answer.strip():
                    st.warning("Please type an answer before submitting.")
                else:
                    with st.spinner("🤖 Groq AI is evaluating your answer…"):
                        role = st.session_state.get("_interview_role", "")
                        resp = APIClient.submit_answer(
                            st.session_state.session_id, q_text, answer, role
                        )

                    if resp.get("success"):
                        ev      = resp["evaluation"]
                        overall = ev.get("overall_score", 0)
                        clr     = score_to_color(overall)
                        grade   = score_to_grade(overall)

                        st.session_state.answers.append(
                            {"question": q_text, "answer": answer, "type": q_type}
                        )
                        st.session_state.evaluations.append(ev)

                        st.markdown(
                            f"""
                            <div style='background:rgba(0,0,0,0.3); border:1px solid {clr}40;
                                        border-radius:12px; padding:1.25rem; margin-top:.75rem;'>
                                <div style='display:flex; justify-content:space-between; align-items:center;
                                            margin-bottom:.75rem;'>
                                    <span style='font-weight:600;'>⚡ Groq AI Evaluation</span>
                                    <span style='font-size:1.4rem; font-weight:800; color:{clr};'>
                                        {overall}/10 · {grade}
                                    </span>
                                </div>
                                <p style='color:#94a3b8; font-size:.88rem; line-height:1.6; margin:0 0 .75rem;'>
                                    {ev.get("feedback","")}
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        _score_bar("Relevance",     ev.get("relevance_score",     0))
                        _score_bar("Clarity",       ev.get("clarity_score",       0))
                        _score_bar("Technical",     ev.get("technical_score",     0))
                        _score_bar("Communication", ev.get("communication_score", 0))

                        tips = ev.get("improvement_tips", [])
                        if tips:
                            with st.expander("💡 Improvement Tips"):
                                for tip in tips:
                                    st.markdown(f"• {tip}")

                        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
                        if st.button("➡️ Next Question", use_container_width=True, key=f"next_{idx}"):
                            st.session_state.current_q_idx += 1
                            st.rerun()
                    else:
                        err = resp.get("detail", "Evaluation failed.")
                        st.error(err)
                        if "GROQ_API_KEY" in str(err):
                            st.info("💡 Ensure GROQ_API_KEY is correctly set in your .env file.")

    # ──────────────────────────────────────────────────────────────────────────
    # Results Tab
    # ──────────────────────────────────────────────────────────────────────────
    with tab_results:
        evaluations = st.session_state.get("evaluations", [])
        answers     = st.session_state.get("answers",     [])
        final_score = st.session_state.get("_final_score", 0)

        if not evaluations:
            st.info("📊 Complete your interview session to see results here.")
            return

        clr   = score_to_color(final_score)
        grade = score_to_grade(final_score)
        st.markdown(
            f"""
            <div style='text-align:center; padding:2rem 1rem;'>
                <div style='font-size:4rem; font-weight:800; color:{clr};
                            text-shadow:0 0 30px {clr}66;'>
                    {final_score}/10
                </div>
                <div style='font-size:1.2rem; color:#94a3b8; margin-top:.5rem;'>
                    Overall Score · Grade <strong style='color:{clr};'>{grade}</strong>
                </div>
                <div style='font-size:.8rem; color:#6366f1; margin-top:.5rem;'>
                    ⚡ Evaluated by Groq AI
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Radar chart
        n = len(evaluations)
        def avg_dim(key):
            return round(sum(e.get(key, 0) for e in evaluations) / max(n, 1), 1)

        dims = {
            "Relevance":     avg_dim("relevance_score"),
            "Clarity":       avg_dim("clarity_score"),
            "Technical":     avg_dim("technical_score"),
            "Communication": avg_dim("communication_score"),
            "Overall":       avg_dim("overall_score"),
        }
        labels = list(dims.keys())
        values = list(dims.values())
        fig = go.Figure(go.Scatterpolar(
            r=values + [values[0]],
            theta=labels + [labels[0]],
            fill="toself",
            fillcolor="rgba(99,102,241,0.2)",
            line=dict(color="#6366f1", width=2),
            marker=dict(size=6, color="#818cf8"),
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 10],
                                gridcolor="rgba(255,255,255,0.1)",
                                tickcolor="#94a3b8"),
                angularaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
                bgcolor="rgba(0,0,0,0)",
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8"),
            showlegend=False,
            height=320,
            margin=dict(l=40, r=40, t=20, b=20),
        )
        col_radar, col_bars = st.columns([1, 1])
        with col_radar:
            st.markdown(
                "<div class='section-header'>📡 Score Breakdown</div>",
                unsafe_allow_html=True,
            )
            st.plotly_chart(fig, use_container_width=True)
        with col_bars:
            st.markdown(
                "<div class='section-header'>📊 Dimension Scores</div>",
                unsafe_allow_html=True,
            )
            st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
            for label, val in dims.items():
                _score_bar(label, val)

        # Per-question breakdown
        st.markdown("---")
        st.markdown(
            "<div class='section-header'>🔍 Question-by-Question Review</div>",
            unsafe_allow_html=True,
        )
        for i, (ans, ev) in enumerate(zip(answers, evaluations), 1):
            score_i = ev.get("overall_score", 0)
            c_i     = score_to_color(score_i)
            q_preview = ans["question"][:80] + ("…" if len(ans["question"]) > 80 else "")
            with st.expander(f"Q{i}: {q_preview}  —  {score_i}/10", expanded=False):
                st.markdown(
                    f"<div style='color:#94a3b8; font-size:.85rem; margin-bottom:.5rem;'>"
                    f"<strong>Your Answer:</strong> {ans['answer']}</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<div style='background:rgba(0,0,0,0.2); border-radius:8px; padding:.75rem; "
                    f"border-left:3px solid {c_i};'>"
                    f"<strong>AI Feedback:</strong><br>"
                    f"<span style='color:#94a3b8;'>{ev.get('feedback','')}</span></div>",
                    unsafe_allow_html=True,
                )
                tips = ev.get("improvement_tips", [])
                if tips:
                    st.markdown("**Improvement Tips:**")
                    for t in tips:
                        st.markdown(f"• {t}")

        # Post-interview actions
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💼 Check Job Recommendations", use_container_width=True):
                _nav_to("Job Recommendations")
        with c2:
            if st.button("🔄 Start New Session", use_container_width=True):
                for key in ("session_id", "questions", "current_q_idx",
                            "answers", "evaluations", "interview_done", "_final_score"):
                    st.session_state.pop(key, None)
                st.rerun()
