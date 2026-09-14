import streamlit as st
from core.auth import AuthManager, login_user


def render_login_page(auth_manager: AuthManager):
    """Renders the authentication gateway entry page."""

    # Center-aligned container
    _, col, _ = st.columns([1, 2, 1])

    with col:
        st.markdown(
            """
            <div class="login-header">
                <div style="font-size: 3rem; margin-bottom: 8px;">⚡</div>
                <h1 class="login-brand">Streamdash</h1>
                <p class="login-sub">Enterprise YAML Dashboard & Analytics Gateway</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="admin", help="Enter your Streamdash username")
            password = st.text_input("Password", type="password", placeholder="••••••••", help="Enter your password")
            
            submit_btn = st.form_submit_button("Sign In →", use_container_width=True, type="primary")

            if submit_btn:
                if not username or not password:
                    st.warning("Please enter both username and password.")
                else:
                    user_data = auth_manager.authenticate(username.strip(), password.strip())
                    if user_data:
                        login_user(user_data)
                        st.success(f"Welcome back, {user_data['display_name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Please check username and password.")

        # Hint box with accepted credentials for easy testing
        st.markdown(
            """
            <div class="creds-hint-box">
                <div style="font-weight: 600; margin-bottom: 6px; color: #1e293b;">🔑 Demo Credentials:</div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px; font-family: monospace; font-size: 0.8rem;">
                    <div>• <b>admin</b> / admin</div>
                    <div style="color: #64748b;">(Full system access)</div>
                    <div>• <b>analyst</b> / analyst123</div>
                    <div style="color: #64748b;">(Sales & Operations)</div>
                    <div>• <b>viewer</b> / viewer123</div>
                    <div style="color: #64748b;">(Sales only)</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
