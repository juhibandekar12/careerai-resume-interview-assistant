"""
frontend/pages/login_page.py
------------------------------
Login and registration UI with premium design.
"""

import streamlit as st
from frontend.utils.api_client import APIClient
from frontend.utils.session import set_user


def render():
    # ── Full-page hero layout ──────────────────────────────────────────────
    st.markdown(
        """
        <style>
        .login-wrap { max-width: 480px; margin: 0 auto; }
        </style>
        <div style='text-align:center; margin-bottom:2rem;'>
            <div style='font-size:3.5rem; margin-bottom:.5rem;'>🚀</div>
            <h1 style='font-family:Poppins,sans-serif; font-weight:800; font-size:2.4rem;
                       background:linear-gradient(135deg,#6366f1,#06b6d4);
                       -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                       margin:0;'>
                CareerAI
            </h1>
            <p style='color:#94a3b8; margin:.5rem 0 0; font-size:1rem;'>
                AI-Powered Career Assistance System
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_login, tab_reg = st.tabs(["🔑  Sign In", "✨  Create Account"])

    # ── Login ──────────────────────────────────────────────────────────────
    with tab_login:
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username", key="li_user")
            password = st.text_input("Password", type="password", placeholder="••••••••", key="li_pass")
            submitted = st.form_submit_button("Sign In →", use_container_width=True)

        if submitted:
            if not username or not password:
                st.error("Please fill in all fields.")
            else:
                with st.spinner("Authenticating…"):
                    resp = APIClient.login(username, password)
                if resp.get("success"):
                    data = resp["data"]
                    set_user(data, data["token"])
                    st.success(f"Welcome back, {data.get('full_name') or data['username']}! 🎉")
                    st.rerun()
                else:
                    st.error(resp.get("detail", "Login failed. Check credentials."))

        st.markdown(
            """
            <div style='text-align:center; margin-top:1.5rem;
                        color:#94a3b8; font-size:.8rem;'>
                Demo credentials: <code>demo</code> / <code>demo123</code>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Register ───────────────────────────────────────────────────────────
    with tab_reg:
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
        with st.form("register_form"):
            full_name = st.text_input("Full Name", placeholder="Jane Doe", key="reg_name")
            email     = st.text_input("Email", placeholder="jane@example.com", key="reg_email")
            username2 = st.text_input("Username", placeholder="janedoe", key="reg_user")
            password2 = st.text_input("Password (min 6 chars)", type="password", key="reg_pass")
            confirm   = st.text_input("Confirm Password", type="password", key="reg_conf")
            submitted2 = st.form_submit_button("Create Account →", use_container_width=True)

        if submitted2:
            if not all([full_name, email, username2, password2, confirm]):
                st.error("Please fill in all fields.")
            elif password2 != confirm:
                st.error("Passwords do not match.")
            elif len(password2) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                with st.spinner("Creating your account…"):
                    resp = APIClient.register(username2, email, password2, full_name)
                if resp.get("success"):
                    st.success("Account created! Please sign in.")
                else:
                    st.error(resp.get("detail", "Registration failed."))

    # ── Feature highlights ─────────────────────────────────────────────────
    st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    features = [
        ("📄", "Resume Analysis", "AI extracts skills & experience"),
        ("💼", "Job Matching",    "TF-IDF powered recommendations"),
        ("📚", "Skill Gap",       "Personalised learning roadmap"),
        ("🎤", "Interview AI",    "Llama 3 practice sessions"),
    ]
    for col, (icon, title, desc) in zip([c1, c2, c3, c4], features):
        with col:
            st.markdown(
                f"""
                <div class='career-card' style='text-align:center;'>
                    <div style='font-size:1.8rem; margin-bottom:.5rem;'>{icon}</div>
                    <div style='font-weight:600; margin-bottom:.25rem;'>{title}</div>
                    <div style='color:#94a3b8; font-size:.8rem;'>{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
