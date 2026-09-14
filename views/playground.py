import glob
import os
import pandas as pd
import streamlit as st
import yaml

from core.auth import AuthManager, get_current_user
from core.dashboard_loader import DashboardLoader
from core.renderer import DashboardRenderer

BLANK_TEMPLATE = """id: "my_custom_dashboard"
title: "My Custom Analytics Dashboard"
description: "Live interactive dashboard generated via YAML Playground."
category: "Custom Analytics"
icon: "⚡"
sort_order: 10
roles:
  - "admin"
  - "analyst"

data_source:
  type: "csv"
  path: "data/sales_data.csv"
  date_columns:
    - "Date"

filters:
  - id: "region_filter"
    column: "Region"
    type: "multiselect"
    label: "Filter Regions"
    default: []
  - id: "category_filter"
    column: "Product_Category"
    type: "selectbox"
    label: "Product Category"
    include_all: true

tabs:
  - id: "overview_tab"
    title: "📊 Overview"
    description: "Key metrics and primary category distribution."
    metrics:
      - label: "Total Revenue"
        column: "Revenue"
        agg: "sum"
        format: "currency"
        help: "Aggregated gross sales"
      - label: "Total Units"
        column: "Units_Sold"
        agg: "sum"
        format: "integer"
      - label: "Avg Profit Margin"
        column: "Profit_Margin"
        agg: "mean"
        format: "percent"
    charts:
      - id: "chart_revenue_by_cat"
        title: "Revenue by Product Category"
        type: "bar"
        x: "Product_Category"
        y: "Revenue"
        agg: "sum"
        color: "Region"
        barmode: "group"
        col_width: 7
      - id: "chart_revenue_pie"
        title: "Regional Share"
        type: "pie"
        values: "Revenue"
        names: "Region"
        hole: 0.4
        col_width: 5

  - id: "data_tab"
    title: "📋 Data Records"
    description: "Underlying transaction data."
    table:
      show: true
      title: "Underlying Data Preview"
      columns:
        - "Date"
        - "Region"
        - "Product_Category"
        - "Revenue"
        - "Units_Sold"
"""


def get_available_csvs(data_dir: str = "data") -> list[str]:
    """Return relative paths to CSV files in data directory."""
    if not os.path.exists(data_dir):
        return []
    return glob.glob(os.path.join(data_dir, "*.csv"))


def validate_dashboard_yaml(raw_yaml: str) -> tuple[bool, str, dict]:
    """Validate YAML syntax and mandatory dashboard structure."""
    if not raw_yaml or not raw_yaml.strip():
        return False, "YAML content is empty.", {}

    try:
        data = yaml.safe_load(raw_yaml)
    except yaml.YAMLError as e:
        return False, f"YAML Syntax Error: {e}", {}

    if not isinstance(data, dict):
        return False, "YAML root must be a mapping/dictionary of keys.", {}

    required_keys = ["id", "title", "data_source"]
    missing = [k for k in required_keys if k not in data]
    if missing:
        return False, f"Missing required configuration key(s): {', '.join(missing)}", data

    data_source = data.get("data_source")
    if not isinstance(data_source, dict) or "path" not in data_source:
        return False, "data_source must be a mapping containing a 'path' attribute.", data

    return True, "Valid configuration schema.", data


def render_playground_page(dashboard_loader: DashboardLoader, auth_manager: AuthManager):
    """Renders the interactive YAML Playground & Visual Builder."""
    user = get_current_user()
    if not user or user.get("role") not in ["admin", "analyst"]:
        st.error("Access Restricted: Only Administrators and Analysts may access the Dashboard Playground.")
        return

    # Header
    pg_h1, pg_h2 = st.columns([3, 1.2])
    with pg_h1:
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
                <span style="font-size: 2.2rem;">📝</span>
                <div>
                    <h1 style="margin: 0; font-size: 1.85rem; font-weight: 700;">YAML Code Studio</h1>
                    <p style="margin: 2px 0 0 0; color: #64748b; font-size: 0.95rem;">
                        Direct YAML editor with real-time schema validation and live preview.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with pg_h2:
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        if st.button("🎨 Open Visual Builder", type="primary", use_container_width=True, key="pg_goto_visual_btn"):
            st.session_state.current_page = "visual_builder"
            st.rerun()

    # Initialize session state
    if "playground_yaml" not in st.session_state:
        st.session_state.playground_yaml = BLANK_TEMPLATE

    # Dataset Inspector Helper
    with st.expander("📊 CSV Data Inspector (Explore available columns & sample values)", expanded=False):
        csv_files = get_available_csvs()
        if csv_files:
            inspect_col1, inspect_col2 = st.columns([1, 3])
            with inspect_col1:
                selected_csv = st.selectbox("Select Dataset to Inspect", options=csv_files, key="inspect_csv_picker")
            with inspect_col2:
                try:
                    df_sample = pd.read_csv(selected_csv, nrows=5)
                    st.caption(f"Columns in `{selected_csv}`:")
                    col_pills = " ".join([f"`{c}` ({df_sample[c].dtype})" for c in df_sample.columns])
                    st.markdown(col_pills)
                    st.dataframe(df_sample, use_container_width=True, height=140)
                except Exception as ex:
                    st.error(f"Could not load CSV: {ex}")
        else:
            st.info("No CSV files found in data/ directory.")

    # Template loader bar
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2, 1, 1])
    with ctrl_col1:
        existing_dashboards = dashboard_loader.get_all_dashboards()
        template_options = ["Blank Starter Template"] + [f"Copy from: {d.get('title', k)} ({k})" for k, d in existing_dashboards.items()]
        chosen_template = st.selectbox("Load Template or Existing Dashboard", options=template_options, label_visibility="collapsed")

    with ctrl_col2:
        if st.button("📥 Load Template", use_container_width=True):
            if chosen_template == "Blank Starter Template":
                st.session_state.playground_yaml = BLANK_TEMPLATE
            else:
                dash_id = chosen_template.split("(")[-1].rstrip(")")
                cfg = existing_dashboards.get(dash_id)
                if cfg:
                    clean_cfg = {k: v for k, v in cfg.items() if not k.startswith("_")}
                    st.session_state.playground_yaml = yaml.dump(clean_cfg, sort_keys=False, default_flow_style=False)
            st.rerun()

    with ctrl_col3:
        if st.button("🧹 Reset to Blank", use_container_width=True):
            st.session_state.playground_yaml = BLANK_TEMPLATE
            st.rerun()

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Workspaces: Code Editor & Live Preview
    tab_editor, tab_preview = st.tabs([
        "📝 Raw YAML Editor & Validation",
        "👁️ Live Dashboard Preview",
    ])

    # -------------------------------------------------------------
    # TAB 1: RAW YAML EDITOR & VALIDATION
    # -------------------------------------------------------------
    with tab_editor:
        yaml_input = st.text_area(
            "Dashboard YAML Configuration",
            value=st.session_state.playground_yaml,
            height=480,
            help="Define your dashboard specification according to the Streamdash schema.",
            key="yaml_editor_area",
        )
        st.session_state.playground_yaml = yaml_input

        is_valid, validation_msg, parsed_config = validate_dashboard_yaml(yaml_input)

        val_col, btn_col1, btn_col2 = st.columns([3, 1, 1])
        with val_col:
            if is_valid:
                st.success(f"✅ Configuration Schema: {validation_msg} (ID: `{parsed_config.get('id')}`)")
            else:
                st.error(f"❌ {validation_msg}")

        with btn_col1:
            if st.button("▶️ Test Live Preview", key="test_preview_btn", use_container_width=True, type="primary", disabled=not is_valid):
                st.info("Switch to the '👁️ Live Dashboard Preview' tab above to test the interactive dashboard.")

        with btn_col2:
            if st.button("💾 Save to Dashboards", key="save_from_editor_btn", use_container_width=True, disabled=not is_valid):
                dash_id = parsed_config.get("id")
                target_path = os.path.join("dashboards", f"{dash_id}.yml")
                try:
                    with open(target_path, "w", encoding="utf-8") as f:
                        f.write(yaml_input)
                    dashboard_loader.reload()
                    st.success(f"🎉 Successfully saved dashboard `{dash_id}` to `{target_path}`!")
                except Exception as e:
                    st.error(f"Failed to save file: {e}")

    # -------------------------------------------------------------
    # TAB 2: LIVE DASHBOARD PREVIEW
    # -------------------------------------------------------------
    with tab_preview:
        is_valid, validation_msg, parsed_config = validate_dashboard_yaml(st.session_state.playground_yaml)
        if not is_valid:
            st.warning(f"Cannot render preview. Please fix YAML configuration: {validation_msg}")
        else:
            tabs_count = len(parsed_config.get("tabs", []))
            mode_badge = f"{tabs_count} Tabs" if tabs_count > 0 else "Single Page"
            st.markdown(
                f"""
                <div style="background: rgba(99, 102, 241, 0.08); border-left: 4px solid #6366f1; padding: 10px 14px; border-radius: 4px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
                    <div><b>Live Preview Mode</b>: Testing dashboard <code>{parsed_config.get('id')}</code> ({mode_badge})</div>
                    <span style="font-size: 0.8rem; color: #4f46e5; font-weight: 600;">ACTIVE TEST</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            try:
                renderer = DashboardRenderer(parsed_config)
                renderer.render()
            except Exception as e:
                st.error(f"Rendering Exception: {e}")
                st.exception(e)
