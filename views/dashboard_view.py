import streamlit as st
from core.auth import AuthManager, get_current_user
from core.dashboard_loader import DashboardLoader
from core.renderer import DashboardRenderer


def render_dashboard_page(dashboard_loader: DashboardLoader, auth_manager: AuthManager):
    """Renders the active YAML-configured dashboard with access control verification."""
    user = get_current_user()
    if not user:
        st.warning("Please sign in to view this dashboard.")
        return

    active_id = st.session_state.get("active_dashboard_id")
    dashboards = dashboard_loader.get_dashboards_for_role(user["role"], auth_manager)
    valid_ids = [d["id"] for d in dashboards]

    if not active_id or active_id not in valid_ids:
        if valid_ids:
            active_id = valid_ids[0]
            st.session_state.active_dashboard_id = active_id
        else:
            st.error("You do not have access to any dashboards.")
            if st.button("← Return to Gallery"):
                st.session_state.current_page = "home"
                st.rerun()
            return

    # Top Control Bar (Navigation Back + Dashboard Switcher)
    nav_col1, nav_col2 = st.columns([1, 4])
    with nav_col1:
        if st.button("← Gallery", use_container_width=True):
            st.session_state.current_page = "home"
            st.rerun()

    with nav_col2:
        dash_options = {d["id"]: f"{d.get('icon', '📊')} {d.get('title', d['id'])}" for d in dashboards}
        selected_id = st.selectbox(
            "Switch Dashboard",
            options=list(dash_options.keys()),
            format_func=lambda x: dash_options[x],
            index=list(dash_options.keys()).index(active_id) if active_id in dash_options else 0,
            label_visibility="collapsed",
        )
        if selected_id != active_id:
            st.session_state.active_dashboard_id = selected_id
            st.rerun()

    # Load and Render Dashboard
    dash_config = dashboard_loader.get_dashboard(active_id)
    if not dash_config:
        st.error(f"Dashboard configuration for '{active_id}' could not be loaded.")
        return

    renderer = DashboardRenderer(dash_config)
    renderer.render()
