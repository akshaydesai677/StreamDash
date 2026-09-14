import streamlit as st
from typing import Any, Dict, List
from core.auth import AuthManager, get_current_user
from core.dashboard_loader import DashboardLoader


def render_home_page(dashboard_loader: DashboardLoader, auth_manager: AuthManager):
    """Renders the dashboard portal homepage with small preview windows of authorized dashboards."""
    user = get_current_user()
    if not user:
        st.warning("Please sign in to view your dashboards.")
        return

    dashboards = dashboard_loader.get_dashboards_for_role(user["role"], auth_manager)

    # Hero Banner
    st.markdown(
        f"""
        <div style="margin-bottom: 16px;">
            <h1 style="font-size: 2.1rem; font-weight: 800; margin: 0; color: #0f172a; letter-spacing: -0.02em;">Dashboard Portal</h1>
            <p style="color: #64748b; font-size: 1rem; margin-top: 4px;">
                Welcome, <b>{user['display_name']}</b>! You have access to <b>{len(dashboards)}</b> authorized analytical views.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # High-Visibility Studio Action Banner for Creators
    if user.get("role") in ["admin", "analyst"]:
        with st.container(border=True):
            b_icon, b_text, b_act1, b_act2 = st.columns([0.5, 4, 1.5, 1.5])
            with b_icon:
                st.markdown("<div style='font-size: 2.2rem; text-align: center; padding-top: 4px;'>🎨</div>", unsafe_allow_html=True)
            with b_text:
                st.markdown(
                    """
                    <div style="padding-top: 2px;">
                        <h3 style="margin: 0; font-size: 1.15rem; font-weight: 700; color: #1e293b;">Streamdash Visual Builder</h3>
                        <p style="margin: 2px 0 0 0; color: #64748b; font-size: 0.88rem;">
                            Drag & drop Dimensions (Categories) & Measures (Metrics) onto Columns & Rows shelves to visually build and preview live dashboards.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with b_act1:
                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                if st.button("🚀 Open Visual Builder", type="primary", use_container_width=True, key="home_open_builder_btn"):
                    st.session_state.current_page = "visual_builder"
                    st.rerun()
            with b_act2:
                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                if st.button("📝 YAML Code Studio", use_container_width=True, key="home_open_yaml_btn"):
                    st.session_state.current_page = "playground"
                    st.rerun()

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    if not dashboards:
        st.info("No dashboards are currently assigned to your role.")
        return

    # Search & Category Filters Bar
    search_col, cat_col = st.columns([3, 1])
    with search_col:
        search_query = st.text_input("🔍 Search Dashboards", placeholder="Search by title, description, or keyword...", label_visibility="collapsed")
    with cat_col:
        all_categories = ["All Categories"] + sorted(list({d.get("category", "General") for d in dashboards}))
        selected_category = st.selectbox("Category", options=all_categories, label_visibility="collapsed")

    # Filter dashboards based on search & category
    filtered_dashboards = dashboards
    if selected_category != "All Categories":
        filtered_dashboards = [d for d in filtered_dashboards if d.get("category") == selected_category]

    if search_query:
        q = search_query.lower()
        filtered_dashboards = [
            d for d in filtered_dashboards
            if q in d.get("title", "").lower() or q in d.get("description", "").lower() or q in d.get("category", "").lower()
        ]

    st.markdown(f"<p style='color: #94a3b8; font-size: 0.85rem; margin-bottom: 16px;'>Displaying {len(filtered_dashboards)} dashboards</p>", unsafe_allow_html=True)

    # Grid of Dashboard Window Cards (2 cards per row)
    for i in range(0, len(filtered_dashboards), 2):
        row_dashboards = filtered_dashboards[i:i + 2]
        cols = st.columns(2)

        for col_idx, dash in enumerate(row_dashboards):
            with cols[col_idx]:
                dash_id = dash.get("id")
                title = dash.get("title", "Untitled Dashboard")
                desc = dash.get("description", "No description provided.")
                icon = dash.get("icon", "📊")
                cat = dash.get("category", "General")
                source_type = dash.get("data_source", {}).get("type", "csv").upper()
                metric_count = len(dash.get("metrics", []))
                chart_count = len(dash.get("charts", []))

                with st.container(border=True):
                    # Header row with icon and category badge
                    h_col1, h_col2 = st.columns([3, 2])
                    with h_col1:
                        st.markdown(
                            f"""
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span style="font-size: 1.8rem; background: rgba(99, 102, 241, 0.08); padding: 4px 8px; border-radius: 8px;">{icon}</span>
                                <span style="font-size: 1.15rem; font-weight: 700; color: #1e293b;">{title}</span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    with h_col2:
                        st.markdown(
                            f"""
                            <div style="text-align: right;">
                                <span style="background: rgba(99, 102, 241, 0.1); color: #4f46e5; padding: 3px 8px; border-radius: 9999px; font-size: 0.72rem; font-weight: 600; text-transform: uppercase;">
                                    {cat}
                                </span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    st.markdown(
                        f"""
                        <p style="color: #64748b; font-size: 0.88rem; min-height: 48px; margin: 10px 0 12px 0;">
                            {desc}
                        </p>
                        """,
                        unsafe_allow_html=True,
                    )

                    # Quick metadata chips & action button
                    meta_col, btn_col = st.columns([3, 2])
                    with meta_col:
                        st.markdown(
                            f"""
                            <div style="display: flex; gap: 6px; font-size: 0.76rem; color: #64748b; padding-top: 6px;">
                                <span style="background: #f1f5f9; padding: 2px 6px; border-radius: 4px;">📁 {source_type}</span>
                                <span style="background: #f1f5f9; padding: 2px 6px; border-radius: 4px;">🔢 {metric_count} KPIs</span>
                                <span style="background: #f1f5f9; padding: 2px 6px; border-radius: 4px;">📈 {chart_count} Charts</span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    with btn_col:
                        if st.button("Open Dashboard →", key=f"open_dash_{dash_id}", use_container_width=True, type="primary"):
                            st.session_state.active_dashboard_id = dash_id
                            st.session_state.current_page = "dashboard"
                            st.rerun()
