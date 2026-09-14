import os
import streamlit as st

# Must be the very first Streamlit command
st.set_page_config(
    page_title="Streamdash | Analytics Portal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

from core.auth import (
    AuthManager,
    get_current_user,
    init_auth_state,
    is_authenticated,
    logout_user,
)
from core.dashboard_loader import DashboardLoader
from views.dashboard_view import render_dashboard_page
from views.home import render_home_page
from views.login import render_login_page
from views.playground import render_playground_page
from views.streamdash_builder import render_streamdash_builder_page


def inject_custom_css():
    css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def main():
    inject_custom_css()
    init_auth_state()

    auth_manager = AuthManager()
    dashboard_loader = DashboardLoader()

    # If user is not authenticated, display login gateway
    if not is_authenticated():
        render_login_page(auth_manager)
        return

    # Authenticated user session
    user = get_current_user()
    dashboards = dashboard_loader.get_dashboards_for_role(user["role"], auth_manager)

    # Sidebar Navigation & User Info
    with st.sidebar:
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 20px;">
                <span style="font-size: 1.8rem;">⚡</span>
                <span style="font-size: 1.4rem; font-weight: 800; background: linear-gradient(135deg, #4f46e5, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    Streamdash
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # User profile chip
        st.markdown(
            f"""
            <div class="user-profile-badge">
                <div class="user-profile-avatar">{user.get('avatar', '👤')}</div>
                <div>
                    <p class="user-profile-name">{user.get('display_name', 'User')}</p>
                    <p class="user-profile-role">{user.get('role', 'Viewer')}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.caption("NAVIGATION")

        # Home button
        is_home = st.session_state.get("current_page", "home") == "home"
        if st.button("🏠  Dashboard Gallery", use_container_width=True, type="primary" if is_home else "secondary"):
            st.session_state.current_page = "home"
            st.rerun()

        # Studio buttons for admin/analyst
        if user.get("role") in ["admin", "analyst"]:
            st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
            is_builder = st.session_state.get("current_page") == "visual_builder"
            if st.button("🎨  Visual Builder", use_container_width=True, type="primary" if is_builder else "secondary"):
                st.session_state.current_page = "visual_builder"
                st.rerun()

            is_playground = st.session_state.get("current_page") == "playground"
            if st.button("📝  YAML Code Studio", use_container_width=True, type="primary" if is_playground else "secondary"):
                st.session_state.current_page = "playground"
                st.rerun()

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        st.caption("YOUR DASHBOARDS")

        active_id = st.session_state.get("active_dashboard_id")
        for dash in dashboards:
            d_id = dash["id"]
            icon = dash.get("icon", "📊")
            title = dash.get("title", d_id)
            is_active = (st.session_state.get("current_page") == "dashboard") and (active_id == d_id)

            if st.button(
                f"{icon}  {title}",
                key=f"nav_dash_{d_id}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state.active_dashboard_id = d_id
                st.session_state.current_page = "dashboard"
                st.rerun()

        st.markdown("---")
        if st.button("🚪 Sign Out", use_container_width=True):
            logout_user()
            st.rerun()

    # Route page content
    current_page = st.session_state.get("current_page", "home")
    if current_page == "home":
        render_home_page(dashboard_loader, auth_manager)
    elif current_page == "visual_builder":
        render_streamdash_builder_page(dashboard_loader, auth_manager)
    elif current_page == "playground":
        render_playground_page(dashboard_loader, auth_manager)
    elif current_page == "dashboard":
        render_dashboard_page(dashboard_loader, auth_manager)
    else:
        render_home_page(dashboard_loader, auth_manager)


if __name__ == "__main__":
    main()
