import glob
import os
import pandas as pd
import plotly.express as px
import streamlit as st
import yaml

from core.auth import AuthManager, get_current_user
from core.dashboard_loader import DashboardLoader
from core.renderer import compute_aggregation, format_metric_value, PALETTES
from core.charts.registry import ChartRegistry
from core.filters.registry import FilterRegistry

BUILDER_PALETTES = {
    "streamdash": ("⚡ Streamdash Modern", PALETTES["streamdash"]),
    "emerald": ("🌿 Emerald & Mint", PALETTES["emerald"]),
    "sunset": ("🌅 Sunset Crimson", PALETTES["sunset"]),
    "ocean": ("🌊 Ocean Sapphire", PALETTES["ocean"]),
    "indigo": ("🔮 Royal Indigo", PALETTES["indigo"]),
    "cyberpunk": ("🚀 Cyberpunk Neon", PALETTES["cyberpunk"]),
    "pastel": ("🌸 Pastel Soft", PALETTES["pastel"]),
    "prism": ("💎 Prism Vivid", PALETTES["prism"]),
}

BUILDER_THEMES = {
    "plotly_white": "🌟 Clean Light",
    "plotly_dark": "🌙 Midnight Dark",
    "seaborn": "🌊 Ocean Breeze",
    "simple_white": "🏛️ Minimalist",
    "ggplot2": "📊 Executive Corporate",
}


def get_available_csvs(data_dir: str = "data") -> list[str]:
    if not os.path.exists(data_dir):
        return []
    return glob.glob(os.path.join(data_dir, "*.csv"))


def categorize_fields(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Split DataFrame columns into Dimensions (categorical/date) and Measures (numeric)."""
    dimensions = []
    measures = []
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            if "id" in col.lower() or "code" in col.lower():
                dimensions.append(col)
            else:
                measures.append(col)
        else:
            dimensions.append(col)
    return dimensions, measures


def init_builder_state():
    """Initialize session state for Streamdash visual canvas builder."""
    if "sdb_dataset" not in st.session_state:
        csvs = get_available_csvs()
        st.session_state.sdb_dataset = csvs[0] if csvs else "data/sales_data.csv"
    if "sdb_columns" not in st.session_state:
        st.session_state.sdb_columns = []
    if "sdb_rows" not in st.session_state:
        st.session_state.sdb_rows = []
    if "sdb_colors" not in st.session_state:
        st.session_state.sdb_colors = []
    if "sdb_filters" not in st.session_state:
        # Interactive live worksheet filters
        st.session_state.sdb_filters = []
    if "sdb_mark" not in st.session_state:
        st.session_state.sdb_mark = "bar"
    if "sdb_chart_options" not in st.session_state:
        # Dynamic options for active chart type
        st.session_state.sdb_chart_options = {}
    if "sdb_labels" not in st.session_state:
        st.session_state.sdb_labels = "none"
    if "sdb_theme" not in st.session_state:
        st.session_state.sdb_theme = "plotly_white"
    if "sdb_palette" not in st.session_state:
        st.session_state.sdb_palette = "streamdash"
    if "sdb_dashboard_widgets" not in st.session_state:
        st.session_state.sdb_dashboard_widgets = []
    if "sdb_dashboard_filters" not in st.session_state:
        st.session_state.sdb_dashboard_filters = []
    if "sdb_save_mode" not in st.session_state:
        st.session_state.sdb_save_mode = "new"
    if "sdb_dash_id" not in st.session_state:
        st.session_state.sdb_dash_id = "custom_visual_dashboard"
    if "sdb_dash_title" not in st.session_state:
        st.session_state.sdb_dash_title = "Custom Visual Analytics Dashboard"


def render_streamdash_builder_page(dashboard_loader: DashboardLoader, auth_manager: AuthManager):
    """Renders the Streamdash Drag-and-Drop Visual Canvas Builder."""
    user = get_current_user()
    if not user or user.get("role") not in ["admin", "analyst"]:
        st.error("Access Restricted: Only Administrators and Analysts may access the Visual Canvas Builder.")
        return

    init_builder_state()

    # Styling for Streamdash Visual Canvas & Shelves - ultra-compact
    st.markdown(
        """
        <style>
        .sdb-shelf-label {
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #475569;
            margin-bottom: 2px;
        }
        .pill-dim {
            background: #e0f2fe;
            color: #0369a1;
            border: 1px solid #7dd3fc;
            padding: 3px 8px;
            border-radius: 9999px;
            font-size: 0.76rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            white-space: nowrap;
        }
        .pill-measure {
            background: #dcfce7;
            color: #15803d;
            border: 1px solid #86efac;
            padding: 3px 8px;
            border-radius: 9999px;
            font-size: 0.76rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            white-space: nowrap;
        }
        .pill-filter {
            background: #fef3c7;
            color: #b45309;
            border: 1px solid #fde68a;
            padding: 3px 8px;
            border-radius: 9999px;
            font-size: 0.76rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }
        .sdb-field-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 8px;
            margin-bottom: 8px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        }
        .sdb-field-name {
            font-size: 0.8rem;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 6px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Render Persistent Flash Message (survives page reruns)
    if "builder_flash_msg" in st.session_state and st.session_state.builder_flash_msg:
        flash = st.session_state.builder_flash_msg
        f_type = flash.get("type", "success")
        f_title = flash.get("title", "")
        f_detail = flash.get("detail", "")
        f_id = flash.get("dash_id", "")

        if f_type == "success":
            banner_col1, banner_col2, banner_col3 = st.columns([6.5, 2.5, 1])
            with banner_col1:
                st.success(f"**{f_title}** {f_detail}")
            with banner_col2:
                if f_id and st.button(f"👉 Launch '{f_id}' Live", key="flash_open_live", type="primary", use_container_width=True):
                    st.session_state.active_dashboard_id = f_id
                    st.session_state.current_page = "dashboard"
                    del st.session_state["builder_flash_msg"]
                    st.rerun()
            with banner_col3:
                if st.button("✖", key="flash_dismiss_top", use_container_width=True, help="Dismiss notification"):
                    del st.session_state["builder_flash_msg"]
                    st.rerun()
        else:
            st.error(f"**{f_title}**: {f_detail}")
            if st.button("✖ Dismiss", key="flash_dismiss_err"):
                del st.session_state["builder_flash_msg"]
                st.rerun()

    # Modern Studio Header with Premium Finishing
    curr_csv = os.path.basename(st.session_state.get("sdb_dataset", "sales_data.csv"))
    staged_n = len(st.session_state.get("sdb_dashboard_widgets", []))
    active_mark_label = ChartRegistry.get(st.session_state.sdb_mark).get_label()

    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border-radius: 12px; padding: 12px 20px; margin-bottom: 14px; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15); border-left: 4px solid #06b6d4; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
            <div style="display: flex; align-items: center; gap: 14px;">
                <div style="background: linear-gradient(135deg, #4f46e5, #06b6d4); width: 42px; height: 42px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.4rem; box-shadow: 0 2px 6px rgba(6, 182, 212, 0.3);">
                    🎨
                </div>
                <div>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 1.2rem; font-weight: 800; color: #ffffff; letter-spacing: -0.01em;">Streamdash Visual Studio</span>
                        <span style="font-size: 0.65rem; font-weight: 700; background: linear-gradient(135deg, #06b6d4, #3b82f6); color: #ffffff; padding: 2px 8px; border-radius: 9999px; letter-spacing: 0.05em;">PRO CANVAS</span>
                        <span style="font-size: 0.68rem; font-weight: 600; color: #34d399; display: flex; align-items: center; gap: 4px;">● Live Synced</span>
                    </div>
                    <div style="font-size: 0.78rem; color: #94a3b8; margin-top: 2px;">
                        Drag or assign fields to shelves &bull; Live Plotly charts &bull; Append to existing dashboards or publish new boards
                    </div>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                <div style="background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.15); color: #e2e8f0; padding: 5px 12px; border-radius: 8px; font-size: 0.76rem; font-weight: 600; display: flex; align-items: center; gap: 6px;">
                    <span style="color: #38bdf8;">📁 Data:</span> {curr_csv}
                </div>
                <div style="background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.15); color: #e2e8f0; padding: 5px 12px; border-radius: 8px; font-size: 0.76rem; font-weight: 600; display: flex; align-items: center; gap: 6px;">
                    <span style="color: #a78bfa;">📊 Mark:</span> {active_mark_label}
                </div>
                <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.35); color: #6ee7b7; padding: 5px 12px; border-radius: 8px; font-size: 0.76rem; font-weight: 700; display: flex; align-items: center; gap: 6px;">
                    <span>📦 Staged:</span> {staged_n}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Main Canvas Layout: Left (Data Pane) | Right (Drop Shelves + Worksheet Canvas)
    left_col, right_col = st.columns([1.15, 2.85])

    # =========================================================================
    # LEFT COLUMN: DATA PANE (Dimensions & Measures with Action Buttons)
    # =========================================================================
    with left_col:
        with st.container(border=True):
            csv_files = get_available_csvs()
            selected_csv = st.selectbox(
                "Active Dataset",
                options=csv_files,
                index=csv_files.index(st.session_state.sdb_dataset) if st.session_state.sdb_dataset in csv_files else 0,
                key="sdb_csv_selector",
                label_visibility="visible",
            )
            if selected_csv != st.session_state.sdb_dataset:
                st.session_state.sdb_dataset = selected_csv
                st.session_state.sdb_columns = []
                st.session_state.sdb_rows = []
                st.session_state.sdb_colors = []
                st.session_state.sdb_filters = []
                st.rerun()

            try:
                df = pd.read_csv(selected_csv)
                dimensions, measures = categorize_fields(df)
            except Exception as e:
                st.error(f"Error loading dataset: {e}")
                return

            st.caption(f"**{len(df):,}** rows &bull; **{len(df.columns)}** fields")
            search_filter = st.text_input("Filter fields...", placeholder="Search fields...", label_visibility="collapsed").lower()

            # 🔤 DIMENSIONS
            st.markdown(
                """
                <div style="font-size: 0.74rem; font-weight: 700; color: #0284c7; text-transform: uppercase; margin-top: 10px; margin-bottom: 6px;">
                    🔤 Dimensions (Categories, Dates)
                </div>
                """,
                unsafe_allow_html=True,
            )
            matched_dims = [d for d in dimensions if search_filter in d.lower()]
            for dim in matched_dims:
                with st.container():
                    st.markdown(f"<div class='sdb-field-name'><span class='pill-dim'>🔤</span> <span>{dim}</span></div>", unsafe_allow_html=True)
                    # 2-Row Action Buttons: clear, spacious, never truncated
                    b_r1_1, b_r1_2 = st.columns(2)
                    with b_r1_1:
                        if st.button("➕ X (Col)", key=f"sdb_col_{dim}", use_container_width=True, help=f"Assign {dim} to Columns (X-Axis)"):
                            if dim not in st.session_state.sdb_columns:
                                st.session_state.sdb_columns.append(dim)
                                st.rerun()
                    with b_r1_2:
                        if st.button("➕ Y (Count)", key=f"sdb_cnt_{dim}", use_container_width=True, help=f"Assign COUNT({dim}) to Rows"):
                            if not any(r["field"] == dim for r in st.session_state.sdb_rows):
                                st.session_state.sdb_rows.append({"field": dim, "agg": "count"})
                                st.rerun()

                    b_r2_1, b_r2_2 = st.columns(2)
                    with b_r2_1:
                        if st.button("🎨 Color", key=f"sdb_color_{dim}", use_container_width=True, help=f"Add {dim} to Color Shelf"):
                            if dim not in st.session_state.sdb_colors:
                                st.session_state.sdb_colors.append(dim)
                                st.rerun()
                    with b_r2_2:
                        if st.button("🔍 Filter", key=f"sdb_fltr_btn_{dim}", use_container_width=True, help=f"Add {dim} to Interactive Filters"):
                            if not any(f["column"] == dim for f in st.session_state.sdb_filters):
                                st.session_state.sdb_filters.append({
                                    "id": f"filter_{dim.lower()}",
                                    "column": dim,
                                    "type": "multiselect",
                                    "label": dim,
                                })
                                st.rerun()
                    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

            # # MEASURES
            st.markdown(
                """
                <div style="font-size: 0.74rem; font-weight: 700; color: #16a34a; text-transform: uppercase; margin-top: 16px; margin-bottom: 6px;">
                    # Measures (Numeric Metrics)
                </div>
                """,
                unsafe_allow_html=True,
            )
            matched_measures = [m for m in measures if search_filter in m.lower()]
            for meas in matched_measures:
                with st.container():
                    st.markdown(f"<div class='sdb-field-name'><span class='pill-measure'>#</span> <span>{meas}</span></div>", unsafe_allow_html=True)
                    # KPI button removed as requested; only Row and Filter
                    m_c1, m_c2 = st.columns(2)
                    with m_c1:
                        if st.button("➕ Y (Row)", key=f"sdb_row_{meas}", use_container_width=True, help=f"Assign {meas} to Rows (Y-Axis)"):
                            if not any(r["field"] == meas for r in st.session_state.sdb_rows):
                                st.session_state.sdb_rows.append({"field": meas, "agg": "sum"})
                                st.rerun()
                    with m_c2:
                        if st.button("🔍 Filter", key=f"sdb_fltr_m_{meas}", use_container_width=True, help=f"Add {meas} to Interactive Filters"):
                            if not any(f["column"] == meas for f in st.session_state.sdb_filters):
                                st.session_state.sdb_filters.append({
                                    "id": f"filter_{meas.lower()}",
                                    "column": meas,
                                    "type": "slider",
                                    "label": meas,
                                })
                                st.rerun()
                    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

    # =========================================================================
    # RIGHT COLUMN: DROP SHELVES, WORKSHEET CANVAS & DASHBOARD STAGING
    # =========================================================================
    with right_col:
        # 1. DROP SHELVES CONTAINER
        with st.container(border=True):
            # Row 1: Columns Shelf (X)
            c_sh1, c_sh2 = st.columns([1.1, 7])
            with c_sh1:
                st.markdown("<div style='padding-top: 4px;'><span class='sdb-shelf-label'>Columns (X)</span></div>", unsafe_allow_html=True)
            with c_sh2:
                if not st.session_state.sdb_columns:
                    st.caption("👈 Click **Col** on any dimension to set X-Axis.")
                else:
                    cp_cols = st.columns(len(st.session_state.sdb_columns) + 1)
                    for idx, c_name in enumerate(st.session_state.sdb_columns):
                        with cp_cols[idx]:
                            if st.button(f"🔤 {c_name} ✖", key=f"sdb_rm_col_{idx}"):
                                st.session_state.sdb_columns.remove(c_name)
                                st.rerun()

            # Row 2: Rows Shelf (Y) with Aggregation Options (including COUNT & DISTINCT_COUNT)
            r_sh1, r_sh2 = st.columns([1.1, 7])
            with r_sh1:
                st.markdown("<div style='padding-top: 4px;'><span class='sdb-shelf-label'>Rows (Y)</span></div>", unsafe_allow_html=True)
            with r_sh2:
                if not st.session_state.sdb_rows:
                    st.caption("👈 Click **Row** or **Count** on any field to set Y-Axis values.")
                else:
                    rp_cols = st.columns(len(st.session_state.sdb_rows) + 1)
                    for idx, r_item in enumerate(st.session_state.sdb_rows):
                        with rp_cols[idx]:
                            rf = r_item["field"]
                            ra = r_item["agg"]
                            r1, r2 = st.columns([3.5, 1])
                            with r1:
                                agg_options = ["sum", "mean", "count", "distinct_count", "min", "max", "median"]
                                if ra not in agg_options:
                                    ra = "count"
                                new_agg = st.selectbox(
                                    f"agg_{idx}",
                                    options=agg_options,
                                    format_func=lambda a: f"{a.upper().replace('_', ' ')}({rf})",
                                    index=agg_options.index(ra),
                                    key=f"sdb_agg_{idx}_{rf}",
                                    label_visibility="collapsed",
                                )
                                if new_agg != ra:
                                    r_item["agg"] = new_agg
                                    st.rerun()
                            with r2:
                                if st.button("✖", key=f"sdb_rm_row_{idx}"):
                                    st.session_state.sdb_rows.remove(r_item)
                                    st.rerun()

            # Row 3: Visual Marks, Multi-Colors, Labels, Theme, and Reset
            t_c1, t_c2, t_c3, t_c4, t_c5, t_c6 = st.columns([2.2, 2.8, 1.8, 2.2, 2.2, 1.2])

            with t_c1:
                st.markdown("<span class='sdb-shelf-label'>Marks Type</span>", unsafe_allow_html=True)
                available_marks = ChartRegistry.list_types()
                mark_type_ids = [m["type"] for m in available_marks]
                mark_map = {m["type"]: m["label"] for m in available_marks}

                if st.session_state.sdb_mark not in mark_type_ids:
                    st.session_state.sdb_mark = "bar"

                selected_mark = st.selectbox(
                    "Marks",
                    options=mark_type_ids,
                    format_func=lambda x: mark_map.get(x, x.title()),
                    index=mark_type_ids.index(st.session_state.sdb_mark),
                    label_visibility="collapsed",
                )
                if selected_mark != st.session_state.sdb_mark:
                    st.session_state.sdb_mark = selected_mark
                    st.rerun()

            with t_c2:
                st.markdown("<span class='sdb-shelf-label'>Color Shelf (Multi)</span>", unsafe_allow_html=True)
                if st.session_state.sdb_colors:
                    clr_cols = st.columns(len(st.session_state.sdb_colors) + 1)
                    for c_idx, c_name in enumerate(st.session_state.sdb_colors):
                        with clr_cols[c_idx]:
                            if st.button(f"🎨 {c_name} ✖", key=f"sdb_rm_clr_{c_idx}"):
                                st.session_state.sdb_colors.remove(c_name)
                                st.rerun()
                else:
                    st.caption("Click **Color** on dimension.")

            with t_c3:
                st.markdown("<span class='sdb-shelf-label'>Data Labels</span>", unsafe_allow_html=True)
                label_opts = ["none", "value", "percentage"]
                label_names = {"none": "🚫 None", "value": "🔢 Values", "percentage": "% Percentage"}
                st.session_state.sdb_labels = st.selectbox(
                    "Labels",
                    options=label_opts,
                    format_func=lambda x: label_names[x],
                    index=label_opts.index(st.session_state.sdb_labels),
                    label_visibility="collapsed",
                )

            with t_c4:
                st.markdown("<span class='sdb-shelf-label'>Palette</span>", unsafe_allow_html=True)
                palette_keys = list(BUILDER_PALETTES.keys())
                st.session_state.sdb_palette = st.selectbox(
                    "Palette",
                    options=palette_keys,
                    format_func=lambda k: BUILDER_PALETTES[k][0],
                    index=palette_keys.index(st.session_state.sdb_palette) if st.session_state.sdb_palette in palette_keys else 0,
                    label_visibility="collapsed",
                )

            with t_c5:
                st.markdown("<span class='sdb-shelf-label'>Visual Theme</span>", unsafe_allow_html=True)
                theme_keys = list(BUILDER_THEMES.keys())
                st.session_state.sdb_theme = st.selectbox(
                    "Theme",
                    options=theme_keys,
                    format_func=lambda k: BUILDER_THEMES[k],
                    index=theme_keys.index(st.session_state.sdb_theme) if st.session_state.sdb_theme in theme_keys else 0,
                    label_visibility="collapsed",
                )

            with t_c6:
                st.markdown("<span class='sdb-shelf-label'>Reset</span>", unsafe_allow_html=True)
                if st.button("🧹 Clear", use_container_width=True, help="Clear active drop shelves"):
                    st.session_state.sdb_columns = []
                    st.session_state.sdb_rows = []
                    st.session_state.sdb_colors = []
                    st.session_state.sdb_filters = []
                    st.session_state.sdb_labels = "none"
                    st.session_state.sdb_chart_options = {}
                    st.rerun()

            # Dynamic Chart-Type Specific Controls (Polymorphic OOP Feature)
            active_chart_cls = ChartRegistry.get(st.session_state.sdb_mark)
            dynamic_props = active_chart_cls.get_configurable_properties()
            if dynamic_props:
                st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
                st.caption(f"⚙️ **{active_chart_cls.get_label()} Specific Options**:")
                prop_cols = st.columns(min(len(dynamic_props), 4))
                for p_idx, prop in enumerate(dynamic_props):
                    p_name = prop["name"]
                    p_label = prop["label"]
                    p_type = prop.get("type", "select")
                    current_val = st.session_state.sdb_chart_options.get(p_name, prop.get("default"))

                    with prop_cols[p_idx % len(prop_cols)]:
                        if p_type == "select":
                            opts = prop["options"]
                            def_idx = opts.index(current_val) if current_val in opts else 0
                            new_val = st.selectbox(p_label, options=opts, index=def_idx, key=f"sdb_dyn_{p_name}")
                            st.session_state.sdb_chart_options[p_name] = new_val
                        elif p_type == "float_slider":
                            new_val = st.slider(
                                p_label,
                                min_value=float(prop["min"]),
                                max_value=float(prop["max"]),
                                step=float(prop["step"]),
                                value=float(current_val) if current_val is not None else float(prop.get("default", 0.4)),
                                key=f"sdb_dyn_{p_name}",
                            )
                            st.session_state.sdb_chart_options[p_name] = new_val
                        elif p_type == "bool":
                            new_val = st.checkbox(p_label, value=bool(current_val), key=f"sdb_dyn_{p_name}")
                            st.session_state.sdb_chart_options[p_name] = new_val
                        elif p_type == "column_picker":
                            num_cols = ["None"] + measures
                            def_idx = num_cols.index(current_val) if current_val in num_cols else 0
                            new_val = st.selectbox(p_label, options=num_cols, index=def_idx, key=f"sdb_dyn_{p_name}")
                            st.session_state.sdb_chart_options[p_name] = None if new_val == "None" else new_val

        # 2. INTERACTIVE FILTERS SHELF (Live Filtering on Canvas)
        filtered_df = df.copy()
        if st.session_state.sdb_filters:
            with st.container(border=True):
                st.markdown(
                    """
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                        <span class='sdb-shelf-label' style='font-size: 0.8rem; color: #b45309;'>🔍 Interactive Filters Shelf (Live Worksheet Test)</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                fltr_cols = st.columns(min(len(st.session_state.sdb_filters), 4))
                for f_idx, fltr in enumerate(st.session_state.sdb_filters):
                    with fltr_cols[f_idx % len(fltr_cols)]:
                        f_col_name = fltr["column"]
                        header_c1, header_c2 = st.columns([3, 1])
                        with header_c1:
                            st.markdown(f"<span class='pill-filter'>🔍 {f_col_name}</span>", unsafe_allow_html=True)
                        with header_c2:
                            if st.button("✖", key=f"sdb_rm_fltr_{f_idx}", help=f"Remove filter on {f_col_name}"):
                                st.session_state.sdb_filters.pop(f_idx)
                                st.rerun()

                        # Select filter type polymorphically from FilterRegistry
                        available_fltr_types = FilterRegistry.list_types()
                        type_ids = [t["type"] for t in available_fltr_types]
                        type_map = {t["type"]: t["label"] for t in available_fltr_types}

                        curr_type = fltr.get("type", "multiselect")
                        if curr_type not in type_ids:
                            curr_type = "multiselect"

                        new_type = st.selectbox(
                            f"Type ({f_col_name})",
                            options=type_ids,
                            format_func=lambda x: type_map[x],
                            index=type_ids.index(curr_type),
                            key=f"sdb_fltr_type_{f_idx}",
                            label_visibility="collapsed",
                        )
                        if new_type != curr_type:
                            fltr["type"] = new_type
                            st.rerun()

                        # Instantiate BaseFilter object and render live
                        try:
                            fltr_obj = FilterRegistry.create(fltr)
                            val = fltr_obj.render(df, key_prefix="builder_test")
                            filtered_df = fltr_obj.apply(filtered_df, val)
                        except Exception as ex:
                            st.error(f"Filter error: {ex}")

        # 3. LIVE WORKSHEET CANVAS (Rendered using Polymorphic BaseChart)
        with st.container(border=True):
            # Header Bar for Live Canvas
            c_h1, c_h2, c_h3 = st.columns([3.8, 2.2, 2])
            with c_h1:
                cols_str = ", ".join(st.session_state.sdb_columns) if st.session_state.sdb_columns else "None"
                rows_str = ", ".join([f"{r['agg'].upper()}({r['field']})" for r in st.session_state.sdb_rows]) if st.session_state.sdb_rows else "None"
                st.markdown(
                    f"""
                    <div style="display: flex; align-items: center; gap: 8px; font-size: 0.85rem; font-weight: 700; color: #1e293b; padding: 4px 0;">
                        <span>📊 Live Plotly Canvas</span>
                        <span style="font-size: 0.7rem; font-weight: 600; background: #e0f2fe; color: #0369a1; padding: 2px 7px; border-radius: 4px;">
                            X: {cols_str} | Y: {rows_str}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with c_h2:
                if st.button("➕ Stage to Board", key="quick_stage_btn", use_container_width=True, help="Stage this chart into multi-widget board"):
                    auto_w_title = f"{st.session_state.sdb_rows[0]['agg'].upper()} of {st.session_state.sdb_rows[0]['field']} by {st.session_state.sdb_columns[0]}" if (st.session_state.sdb_rows and st.session_state.sdb_columns) else "Analytical View"
                    add_current_shelf_to_dashboard(auto_w_title, 6, "Visual Summary")
                    st.session_state.builder_flash_msg = {
                        "type": "success",
                        "title": "Widget Staged!",
                        "detail": f"Added '{auto_w_title}' to staged widgets.",
                        "dash_id": "",
                    }
                    st.rerun()
            with c_h3:
                st.toggle("📥 Quick Append", key="toggle_quick_append", help="Toggle fast 1-click append panel")

            if st.session_state.get("toggle_quick_append"):
                with st.expander("⚡ 1-Click Fast Append Current Chart to Dashboard", expanded=True):
                    q_dashboards = dashboard_loader.get_dashboards_for_role(user["role"], auth_manager)
                    active_ds_name = os.path.basename(st.session_state.get("sdb_dataset", "")).lower()

                    q_dash_ids = [d["id"] for d in q_dashboards]
                    q_dash_ids.sort(key=lambda d_id: 0 if os.path.basename((dashboard_loader.get_dashboard(d_id) or {}).get("data_source", {}).get("path", "")).lower() == active_ds_name else 1)

                    qa_col1, qa_col2, qa_col3 = st.columns([3, 2.5, 2])
                    with qa_col1:
                        target_d_id = st.selectbox(
                            "Target Dashboard",
                            options=q_dash_ids,
                            format_func=lambda d_id: f"{(dashboard_loader.get_dashboard(d_id) or {}).get('icon', '📊')} {(dashboard_loader.get_dashboard(d_id) or {}).get('title', d_id)}",
                            key="quick_append_target_dash",
                        )
                    with qa_col2:
                        t_dash = dashboard_loader.get_dashboard(target_d_id) or {}
                        t_tabs = [t.get("title", f"Tab {t_i+1}") for t_i, t in enumerate(t_dash.get("tabs", []))]
                        if t_tabs:
                            q_target_tab = st.selectbox("Target Tab", options=t_tabs + ["➕ New Tab..."], key="quick_append_tab_choice")
                            if q_target_tab == "➕ New Tab...":
                                q_target_tab = st.text_input("New Tab Name", value="Analytics Deep Dive", key="quick_append_custom_tab")
                        else:
                            q_target_tab = st.text_input("Target Tab Name", value="Visual Summary", key="quick_append_default_tab")
                    with qa_col3:
                        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                        if st.button("🚀 Append Now", key="quick_append_confirm_btn", type="primary", use_container_width=True):
                            appended = append_to_existing_dashboard(dashboard_loader, target_d_id, filtered_df, target_tab_name=q_target_tab)
                            if appended:
                                st.rerun()

            render_live_canvas(filtered_df)

        # 4. ADVANCED DASHBOARD ASSEMBLY & PERSISTENCE ENGINE
        with st.container(border=True):
            st.markdown(
                """
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 1.2rem;">🚀</span>
                        <span style="font-size: 1.05rem; font-weight: 700; color: #1e293b;">Dashboard Assembly & Publishing</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # A. Widget staging configuration
            default_widget_title = "Analytical View"
            if st.session_state.sdb_rows and st.session_state.sdb_columns:
                r_title = f"{st.session_state.sdb_rows[0]['agg'].upper()} of {st.session_state.sdb_rows[0]['field']}"
                default_widget_title = f"{r_title} by {st.session_state.sdb_columns[0]}"
            elif st.session_state.sdb_rows:
                default_widget_title = f"{st.session_state.sdb_rows[0]['agg'].upper()} of {st.session_state.sdb_rows[0]['field']}"

            w_row1, w_row2, w_row3, w_row4 = st.columns([3, 2, 2, 2.5])
            with w_row1:
                w_title = st.text_input("Widget Title", value=default_widget_title, key="sdb_w_title")
            with w_row2:
                w_width = st.selectbox("Grid Width", options=[6, 12, 4, 8], format_func=lambda w: f"{w}/12 ({'Half' if w==6 else ('Full' if w==12 else ('1/3' if w==4 else '2/3'))})")
            with w_row3:
                w_tab = st.text_input("Target Tab Name", value="Visual Summary", key="sdb_w_tab")
            with w_row4:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                if st.button("➕ Add to Staging", type="secondary", use_container_width=True):
                    add_current_shelf_to_dashboard(w_title, w_width, w_tab)
                    st.success(f"Added '{w_title}' to dashboard staging!")
                    st.rerun()

            # B. Staged Widgets Overview
            staged = st.session_state.sdb_dashboard_widgets
            if staged:
                st.markdown(f"**Staged Widgets ({len(staged)})**:")
                s_cols = st.columns(min(len(staged), 4))
                for w_i, w in enumerate(staged):
                    with s_cols[w_i % len(s_cols)]:
                        with st.container(border=True):
                            icon = "📊" if w.get("type") == "chart" else ("🔢" if w.get("type") == "metric" else "📋")
                            st.markdown(f"**{icon} {w.get('title')}**")
                            st.caption(f"Type: `{w.get('chart_type', w.get('type'))}` &bull; Tab: `{w.get('tab', 'Main')}` &bull; Width: `{w.get('col_width', 6)}/12`")
                            btn_c1, btn_c2, btn_c3 = st.columns([1, 1, 1])
                            with btn_c1:
                                if w_i > 0 and st.button("◀", key=f"sdb_mv_l_{w_i}", help="Move left"):
                                    staged[w_i - 1], staged[w_i] = staged[w_i], staged[w_i - 1]
                                    st.rerun()
                            with btn_c2:
                                if w_i < len(staged) - 1 and st.button("▶", key=f"sdb_mv_r_{w_i}", help="Move right"):
                                    staged[w_i + 1], staged[w_i] = staged[w_i], staged[w_i + 1]
                                    st.rerun()
                            with btn_c3:
                                if st.button("🗑️", key=f"sdb_del_{w_i}", help="Remove widget"):
                                    staged.pop(w_i)
                                    st.rerun()

            # C. Dashboard Filters Management
            with st.expander("🎯 Dashboard-Level Filters Configuration", expanded=True):
                st.caption("Configure interactive filters that will appear on this dashboard for viewers:")
                
                # Prepopulate dashboard filters from active worksheet filters if empty
                if not st.session_state.sdb_dashboard_filters and st.session_state.sdb_filters:
                    st.session_state.sdb_dashboard_filters = [dict(f) for f in st.session_state.sdb_filters]

                d_fltrs = st.session_state.sdb_dashboard_filters
                if d_fltrs:
                    for d_i, d_f in enumerate(d_fltrs):
                        f_r1, f_r2, f_r3, f_r4 = st.columns([3, 3, 3, 1])
                        with f_r1:
                            st.markdown(f"Column: **`{d_f.get('column')}`**")
                        with f_r2:
                            d_f["label"] = st.text_input(f"Label ({d_i})", value=d_f.get("label", d_f.get("column")), key=f"df_lbl_{d_i}", label_visibility="collapsed")
                        with f_r3:
                            fltr_types = [t["type"] for t in FilterRegistry.list_types()]
                            d_f["type"] = st.selectbox(f"Type ({d_i})", options=fltr_types, index=fltr_types.index(d_f.get("type", "multiselect")) if d_f.get("type") in fltr_types else 0, key=f"df_type_{d_i}", label_visibility="collapsed")
                        with f_r4:
                            if st.button("🗑️", key=f"df_del_{d_i}", help="Remove dashboard filter"):
                                d_fltrs.pop(d_i)
                                st.rerun()

                # Add filter to dashboard
                add_col_opt = st.selectbox("Add Field as Dashboard Filter", options=["Select field..."] + list(df.columns), key="df_add_sel")
                if add_col_opt != "Select field...":
                    if not any(f["column"] == add_col_opt for f in d_fltrs):
                        d_fltrs.append({
                            "id": f"filter_{add_col_opt.lower()}",
                            "column": add_col_opt,
                            "type": "slider" if pd.api.types.is_numeric_dtype(df[add_col_opt]) else "multiselect",
                            "label": add_col_opt,
                        })
                        st.rerun()

            # D. Save Mode Selection: New vs Existing Dashboard
            st.markdown("---")
            save_mode = st.radio(
                "Publishing Target:",
                options=["Create New Dashboard", "Append to Existing Dashboard"],
                horizontal=True,
                key="sdb_save_mode_radio",
            )

            if save_mode == "Create New Dashboard":
                meta_c1, meta_c2, meta_c3, meta_c4 = st.columns([2.5, 2.5, 1.5, 2])
                with meta_c1:
                    new_title = st.text_input("Dashboard Title", value=st.session_state.sdb_dash_title)
                    st.session_state.sdb_dash_title = new_title
                with meta_c2:
                    default_id = new_title.lower().replace(" ", "_").replace("-", "_")
                    new_id = st.text_input("Dashboard Slug ID", value=default_id)
                    st.session_state.sdb_dash_id = new_id
                with meta_c3:
                    new_icon = st.selectbox("Icon", options=["🎨", "⚡", "📊", "📈", "🎯", "💼", "🚀", "✨"])
                with meta_c4:
                    new_cat = st.selectbox("Category", options=["Executive", "Sales", "Operations", "Finance", "Customer Analytics"])

                save_c1, save_c2 = st.columns([2, 2])
                with save_c1:
                    if st.button("💾 Publish New Dashboard", type="primary", use_container_width=True):
                        saved_id = save_new_streamdash_dashboard(dashboard_loader, df, new_id, new_title, new_icon, new_cat)
                        if saved_id:
                            st.session_state.just_saved_id = saved_id
                            st.rerun()
                with save_c2:
                    if st.session_state.get("just_saved_id"):
                        if st.button(f"👉 Launch Dashboard '{st.session_state.just_saved_id}' Live", type="primary", use_container_width=True):
                            st.session_state.active_dashboard_id = st.session_state.just_saved_id
                            st.session_state.current_page = "dashboard"
                            st.rerun()

            else:
                existing_dashboards = dashboard_loader.get_dashboards_for_role(user["role"], auth_manager)
                active_ds = os.path.basename(st.session_state.get("sdb_dataset", "")).lower()

                def format_dash_option(d_id):
                    d = dashboard_loader.get_dashboard(d_id) or {}
                    icon = d.get("icon", "📊")
                    title = d.get("title", d_id)
                    ds_path = os.path.basename(d.get("data_source", {}).get("path", "")).lower()
                    match_indicator = " ⭐ [Matches Active Data]" if ds_path == active_ds else ""
                    return f"{icon} {title}{match_indicator}"

                ext_c1, ext_c2 = st.columns([3, 2])
                with ext_c1:
                    dash_ids = [d["id"] for d in existing_dashboards]
                    dash_ids.sort(key=lambda d_id: 0 if os.path.basename((dashboard_loader.get_dashboard(d_id) or {}).get("data_source", {}).get("path", "")).lower() == active_ds else 1)
                    chosen_ext_id = st.selectbox(
                        "Select Existing Dashboard to Update",
                        options=dash_ids,
                        format_func=format_dash_option,
                        key="sdb_append_target_dash_sel",
                    )

                chosen_dash = dashboard_loader.get_dashboard(chosen_ext_id) or {}
                chosen_ds = os.path.basename(chosen_dash.get("data_source", {}).get("path", "")).lower()
                if chosen_ds and chosen_ds != active_ds:
                    st.info(f"💡 Note: Dashboard `{chosen_ext_id}` uses dataset `{chosen_dash.get('data_source', {}).get('path')}`, while current builder dataset is `{st.session_state.get('sdb_dataset')}`.")

                # Tab selection if existing dashboard has multiple tabs
                existing_tabs = []
                if "tabs" in chosen_dash and chosen_dash["tabs"]:
                    existing_tabs = [t.get("title", f"Tab {t_i+1}") for t_i, t in enumerate(chosen_dash["tabs"])]

                tab_sel_col1, tab_sel_col2 = st.columns([3, 2])
                with tab_sel_col1:
                    if existing_tabs:
                        target_tab_choice = st.selectbox(
                            f"Target Tab in '{chosen_ext_id}'",
                            options=existing_tabs + ["➕ Create New Tab..."],
                            key="sdb_append_target_tab_sel",
                        )
                        if target_tab_choice == "➕ Create New Tab...":
                            target_tab_name = st.text_input("New Tab Title", value="Analytics Deep Dive", key="sdb_append_new_tab_title")
                        else:
                            target_tab_name = target_tab_choice
                    else:
                        target_tab_name = st.text_input("Target Tab Name", value="Visual Summary", key="sdb_append_default_tab_name")

                with tab_sel_col2:
                    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                    if st.button(f"📥 Append to '{chosen_ext_id}'", key="sdb_append_main_submit", type="primary", use_container_width=True):
                        success = append_to_existing_dashboard(dashboard_loader, chosen_ext_id, df, target_tab_name=target_tab_name)
                        if success:
                            st.session_state.just_saved_id = chosen_ext_id
                            st.rerun()

                if st.session_state.get("just_saved_id") == chosen_ext_id:
                    st.success(f"🎉 Updated '{chosen_ext_id}' successfully! Ready to preview live.")
                    if st.button(f"👉 View Updated Dashboard '{chosen_ext_id}' Live", key="sdb_btn_view_updated_ext", type="primary", use_container_width=True):
                        st.session_state.active_dashboard_id = chosen_ext_id
                        st.session_state.current_page = "dashboard"
                        st.rerun()

            # E. YAML Code Inspector & Download
            with st.expander("📄 View Live Compiled Dashboard YAML Specification"):
                compiled_yaml = generate_streamdash_yaml(df)
                st.code(compiled_yaml, language="yaml")
                st.download_button(
                    label="📥 Download YAML File",
                    data=compiled_yaml,
                    file_name=f"{st.session_state.sdb_dash_id}.yml",
                    mime="text/yaml",
                )


def render_live_canvas(df: pd.DataFrame):
    """Renders the interactive chart or KPI based on the drop shelves using BaseChart polymorphism."""
    cols = st.session_state.sdb_columns
    rows = st.session_state.sdb_rows
    colors = st.session_state.sdb_colors
    mark = st.session_state.sdb_mark
    labels = st.session_state.sdb_labels
    theme = st.session_state.sdb_theme
    palette_key = st.session_state.sdb_palette
    chart_opts = st.session_state.sdb_chart_options

    if not cols and not rows:
        st.info("👈 Assign fields from the Data Pane to Columns (X) and Rows (Y) to plot charts in real-time.")
        st.dataframe(df.head(6), use_container_width=True)
        return

    # Multi-color column creation
    plot_df = df.copy()
    color_col = None
    if len(colors) == 1:
        color_col = colors[0]
    elif len(colors) > 1:
        color_col = " • ".join(colors)
        plot_df[color_col] = plot_df[colors[0]].astype(str)
        for c_extra in colors[1:]:
            plot_df[color_col] = plot_df[color_col] + " • " + plot_df[c_extra].astype(str)

    # Build chart configuration dictionary
    chart_conf = {
        "id": "live_worksheet",
        "title": "",
        "type": mark,
        "x": cols[0] if cols else None,
        "y": rows[0]["field"] if rows else None,
        "agg": rows[0]["agg"] if rows else "sum",
        "color": color_col,
        "theme": theme,
        "palette": palette_key,
        "labels": labels,
        "height": 380,
    }
    # Merge dynamic options (barmode, hole, orientation, line_shape, etc.)
    chart_conf.update(chart_opts)

    try:
        chart_obj = ChartRegistry.create(chart_conf)
        chart_obj.render(plot_df)
    except Exception as e:
        st.error(f"Worksheet Canvas Rendering Error: {e}")


def add_current_shelf_to_dashboard(title: str, col_width: int, tab_name: str):
    """Add the currently configured worksheet as a staged widget to the dashboard."""
    cols = st.session_state.sdb_columns
    rows = st.session_state.sdb_rows
    colors = st.session_state.sdb_colors
    mark = st.session_state.sdb_mark
    labels = st.session_state.sdb_labels
    palette = st.session_state.sdb_palette
    chart_opts = dict(st.session_state.sdb_chart_options)

    color_val = colors[0] if len(colors) == 1 else (colors if len(colors) > 1 else None)

    widget_def = {
        "title": title,
        "col_width": col_width,
        "tab": tab_name,
    }

    if mark == "kpi" and rows:
        r = rows[0]
        widget_def.update({
            "type": "metric",
            "label": title,
            "column": r["field"],
            "agg": r["agg"],
            "format": chart_opts.get("format", "auto"),
        })
    elif mark == "table":
        widget_def.update({
            "type": "table",
            "columns": cols + [r["field"] for r in rows] + colors,
        })
    else:
        widget_def.update({
            "type": "chart",
            "chart_type": mark,
            "x": cols[0] if cols else None,
            "y": rows[0]["field"] if rows else None,
            "agg": rows[0]["agg"] if rows else None,
            "color": color_val,
            "show_labels": (labels != "none"),
            "labels": labels,
            "palette": palette,
        })
        # Add dynamic chart-specific properties into widget definition
        widget_def.update(chart_opts)

    st.session_state.sdb_dashboard_widgets.append(widget_def)


def generate_streamdash_yaml(df: pd.DataFrame, csv_path: str = None, dash_id: str = None, dash_title: str = None) -> str:
    """Generate comprehensive YAML specification from shelves, filters, and assembled widgets."""
    csv_path = csv_path or st.session_state.get("sdb_dataset", "data/sales_data.csv")
    dash_id = dash_id or st.session_state.get("sdb_dash_id", "custom_visual_dashboard")
    dash_title = dash_title or st.session_state.get("sdb_dash_title", "Custom Visual Analytics Dashboard")
    widgets = st.session_state.get("sdb_dashboard_widgets", [])
    cols = st.session_state.get("sdb_columns", [])
    rows = st.session_state.get("sdb_rows", [])
    colors = st.session_state.get("sdb_colors", [])
    mark = st.session_state.get("sdb_mark", "bar")
    theme = st.session_state.get("sdb_theme", "plotly_white")
    palette = st.session_state.get("sdb_palette", "streamdash")
    labels = st.session_state.get("sdb_labels", "none")
    dash_filters = st.session_state.get("sdb_dashboard_filters", [])

    date_cols = [c for c in df.columns if any(k in c.lower() for k in ["date", "time", "year"])]

    # Filters YAML specification
    if dash_filters:
        filters_yaml = [
            {
                "id": f.get("id", f"filter_{f['column'].lower()}"),
                "column": f["column"],
                "type": f.get("type", "multiselect"),
                "label": f.get("label", f["column"]),
                "default": f.get("default", []),
            }
            for f in dash_filters
        ]
    else:
        # Fallback to top 2 categorical dimensions
        dimensions, _ = categorize_fields(df)
        filters_yaml = [
            {
                "id": f"filter_{d.lower()}",
                "column": d,
                "type": "multiselect",
                "label": f"Filter {d}",
                "default": [],
            }
            for d in dimensions[:min(2, len(dimensions))]
        ]

    # Organize widgets by target tab
    tabs_dict = {}

    if widgets:
        for w in widgets:
            t_name = w.get("tab", "Visual Summary")
            if t_name not in tabs_dict:
                tabs_dict[t_name] = {"metrics": [], "charts": [], "tables": []}

            w_type = w.get("type")
            if w_type == "metric":
                tabs_dict[t_name]["metrics"].append({
                    "label": w["label"],
                    "column": w["column"],
                    "agg": w["agg"],
                    "format": w.get("format", "auto"),
                })
            elif w_type == "chart":
                c_dict = {
                    "id": f"chart_{len(tabs_dict[t_name]['charts']) + 1}",
                    "title": w["title"],
                    "type": w["chart_type"],
                    "x": w["x"],
                    "y": w["y"],
                    "agg": w.get("agg"),
                    "color": w.get("color"),
                    "col_width": w.get("col_width", 6),
                    "show_labels": w.get("show_labels", False),
                    "labels": w.get("labels", "none"),
                    "palette": w.get("palette", palette),
                }
                # Copy any dynamic properties (e.g. barmode, hole, line_shape)
                for k in ["barmode", "orientation", "hole", "line_shape", "show_markers", "groupnorm", "points", "size_col"]:
                    if k in w:
                        c_dict[k] = w[k]
                tabs_dict[t_name]["charts"].append({k: v for k, v in c_dict.items() if v is not None})
            elif w_type == "table":
                tabs_dict[t_name]["tables"].append({
                    "show": True,
                    "title": w["title"],
                    "columns": w.get("columns", list(df.columns[:6])),
                })
    else:
        # Fallback to currently active worksheet
        tabs_dict["Visual Summary"] = {"metrics": [], "charts": [], "tables": []}
        if rows:
            tabs_dict["Visual Summary"]["metrics"].append({
                "label": f"Total {rows[0]['field']}",
                "column": rows[0]["field"],
                "agg": rows[0]["agg"],
                "format": "currency" if "revenue" in rows[0]["field"].lower() else "integer",
            })
        if cols and rows:
            tabs_dict["Visual Summary"]["charts"].append({
                "id": "chart_active_worksheet",
                "title": f"{rows[0]['field']} by {cols[0]}",
                "type": mark,
                "x": cols[0],
                "y": rows[0]["field"],
                "agg": rows[0]["agg"],
                "color": colors[0] if colors else None,
                "col_width": 7,
                "show_labels": (labels != "none"),
                "labels": labels,
                "palette": palette,
            })

    # Build tabs YAML list
    tabs_yaml = []
    for tab_name, tab_content in tabs_dict.items():
        tab_slug = tab_name.lower().replace(" ", "_").replace("&", "and")
        tab_obj = {
            "id": f"tab_{tab_slug}",
            "title": f"📊 {tab_name}",
            "description": f"Dashboard analytics for {tab_name}.",
        }
        if tab_content["metrics"]:
            tab_obj["metrics"] = tab_content["metrics"]
        if tab_content["charts"]:
            tab_obj["charts"] = tab_content["charts"]
        if tab_content["tables"]:
            tab_obj["table"] = tab_content["tables"][0]
        tabs_yaml.append(tab_obj)

    # Always ensure a data records tab exists
    tabs_yaml.append({
        "id": "tab_data_records",
        "title": "📋 Underlying Records",
        "description": "Exploration grid of raw source data records.",
        "table": {
            "show": True,
            "title": "Raw Data Grid",
            "columns": list(df.columns[:min(8, len(df.columns))]),
        },
    })

    assembled = {
        "id": dash_id,
        "title": dash_title,
        "description": "Interactive visual dashboard published via Streamdash Visual Builder.",
        "category": "Visual Analytics",
        "icon": "🎨",
        "sort_order": 5,
        "roles": ["admin", "analyst"],
        "theme": theme,
        "palette": palette,
        "data_source": {
            "type": "csv",
            "path": csv_path,
        },
        "filters": filters_yaml,
        "tabs": tabs_yaml,
    }
    if date_cols:
        assembled["data_source"]["date_columns"] = date_cols

    return yaml.dump(assembled, sort_keys=False, default_flow_style=False)


def save_new_streamdash_dashboard(dashboard_loader: DashboardLoader, df: pd.DataFrame, dash_id: str, title: str, icon: str, category: str) -> str:
    """Save as a brand new dashboard YAML."""
    raw_yaml = generate_streamdash_yaml(df, dash_id=dash_id, dash_title=title)
    target_path = os.path.join("dashboards", f"{dash_id}.yml")

    try:
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(raw_yaml)
        dashboard_loader.reload()
        st.success(f"🎉 Successfully published new dashboard `{dash_id}` to `{target_path}`!")
        return dash_id
    except Exception as ex:
        st.error(f"Failed to publish dashboard: {ex}")
        return ""


def append_to_existing_dashboard(dashboard_loader: DashboardLoader, existing_id: str, df: pd.DataFrame, target_tab_name: str = "Visual Summary") -> bool:
    """Append staged widgets and filters into an existing dashboard YAML file with full fidelity."""
    dash = dashboard_loader.get_dashboard(existing_id)
    if not dash:
        st.error(f"Dashboard `{existing_id}` not found.")
        return False

    # Resolve path using both _filepath and fallback to dashboards dir
    raw_path = dash.get("_filepath") or dash.get("_file_path") or os.path.join("dashboards", f"{existing_id}.yml")
    if not os.path.isabs(raw_path) and not os.path.exists(raw_path):
        raw_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dashboards", f"{existing_id}.yml")

    if not os.path.exists(raw_path):
        st.error(f"Dashboard file `{raw_path}` could not be located on disk.")
        return False

    try:
        with open(raw_path, "r", encoding="utf-8") as f:
            existing_spec = yaml.safe_load(f) or {}

        staged = list(st.session_state.get("sdb_dashboard_widgets", []))
        dash_filters = st.session_state.get("sdb_dashboard_filters", [])

        # Auto-stage current worksheet if user hasn't clicked 'Add to Staging'
        if not staged:
            cols = st.session_state.get("sdb_columns", [])
            rows = st.session_state.get("sdb_rows", [])
            if cols or rows:
                agg_name = rows[0]["agg"].upper() if rows else ""
                field_name = rows[0]["field"] if rows else ""
                col_name = cols[0] if cols else ""
                auto_title = f"{agg_name} of {field_name} by {col_name}" if (cols and rows) else (f"{agg_name} of {field_name}" if rows else f"Distribution of {col_name}")
                user_title = st.session_state.get("sdb_w_title")
                title_to_use = user_title if (user_title and user_title != "Analytical View") else auto_title

                add_current_shelf_to_dashboard(
                    title=title_to_use,
                    col_width=6,
                    tab_name=target_tab_name,
                )
                staged = list(st.session_state.get("sdb_dashboard_widgets", []))

        if not staged and not dash_filters:
            st.warning("Nothing to append. Add fields to Rows/Columns or add Dashboard Filters first.")
            return False

        # Append any new filters
        if "filters" not in existing_spec:
            existing_spec["filters"] = []
        existing_cols = [f.get("column") for f in existing_spec["filters"]]
        for d_f in dash_filters:
            if d_f["column"] not in existing_cols:
                existing_spec["filters"].append({
                    "id": d_f.get("id", f"filter_{d_f['column'].lower()}"),
                    "column": d_f["column"],
                    "type": d_f.get("type", "multiselect"),
                    "label": d_f.get("label", d_f["column"]),
                    "default": [],
                })

        # Append widgets to tabs or root
        if "tabs" in existing_spec and existing_spec["tabs"]:
            # Locate target tab or create if new
            target_tab = None
            for t in existing_spec["tabs"]:
                t_title_clean = t.get("title", "").replace("📊", "").strip().lower()
                req_title_clean = target_tab_name.replace("📊", "").strip().lower()
                if t.get("title") == target_tab_name or t.get("id") == target_tab_name or t_title_clean == req_title_clean:
                    target_tab = t
                    break

            if not target_tab:
                # Create the target tab
                tab_slug = target_tab_name.lower().replace(" ", "_").replace("&", "and").replace("📊", "").strip()
                tab_title_formatted = target_tab_name if target_tab_name.startswith("📊") else f"📊 {target_tab_name}"
                target_tab = {
                    "id": f"tab_{tab_slug}",
                    "title": tab_title_formatted,
                    "description": f"Analytics view for {target_tab_name}.",
                    "charts": [],
                    "metrics": [],
                }
                existing_spec["tabs"].append(target_tab)

            if "charts" not in target_tab:
                target_tab["charts"] = []
            if "metrics" not in target_tab:
                target_tab["metrics"] = []

            for w in staged:
                if w.get("type") == "chart":
                    c_dict = {
                        "id": f"chart_added_{len(target_tab['charts']) + 1}",
                        "title": w["title"],
                        "type": w["chart_type"],
                        "x": w["x"],
                        "y": w["y"],
                        "agg": w.get("agg"),
                        "color": w.get("color"),
                        "col_width": w.get("col_width", 6),
                        "show_labels": w.get("show_labels", False),
                        "labels": w.get("labels", "none"),
                        "palette": w.get("palette", "streamdash"),
                    }
                    for k in ["barmode", "orientation", "hole", "line_shape", "show_markers", "groupnorm", "points", "size_col"]:
                        if k in w:
                            c_dict[k] = w[k]
                    target_tab["charts"].append({k: v for k, v in c_dict.items() if v is not None})
                elif w.get("type") == "metric":
                    target_tab["metrics"].append({
                        "label": w["label"],
                        "column": w["column"],
                        "agg": w["agg"],
                        "format": w.get("format", "auto"),
                    })
        else:
            # Single flat dashboard without tabs (e.g. customer_insights.yml)
            if "charts" not in existing_spec:
                existing_spec["charts"] = []
            if "metrics" not in existing_spec:
                existing_spec["metrics"] = []

            for w in staged:
                if w.get("type") == "chart":
                    c_dict = {
                        "id": f"chart_added_{len(existing_spec['charts']) + 1}",
                        "title": w["title"],
                        "type": w["chart_type"],
                        "x": w["x"],
                        "y": w["y"],
                        "agg": w.get("agg"),
                        "color": w.get("color"),
                        "col_width": w.get("col_width", 6),
                        "show_labels": w.get("show_labels", False),
                        "labels": w.get("labels", "none"),
                        "palette": w.get("palette", "streamdash"),
                    }
                    for k in ["barmode", "orientation", "hole", "line_shape", "show_markers", "groupnorm", "points", "size_col"]:
                        if k in w:
                            c_dict[k] = w[k]
                    existing_spec["charts"].append({k: v for k, v in c_dict.items() if v is not None})
                elif w.get("type") == "metric":
                    existing_spec["metrics"].append({
                        "label": w["label"],
                        "column": w["column"],
                        "agg": w["agg"],
                        "format": w.get("format", "auto"),
                    })

        # Strip runtime internal keys
        existing_spec.pop("_filepath", None)
        existing_spec.pop("_file_path", None)

        with open(raw_path, "w", encoding="utf-8") as f:
            yaml.dump(existing_spec, f, sort_keys=False, default_flow_style=False)

        dashboard_loader.reload()
        
        tab_label = f"tab '{target_tab_name}'" if ("tabs" in existing_spec and existing_spec["tabs"]) else "main view"
        dash_title = existing_spec.get("title", existing_id)

        st.session_state.builder_flash_msg = {
            "type": "success",
            "title": f"🎉 Successfully Appended to '{dash_title}'!",
            "detail": f"Appended {len(staged)} widget(s) to '{dash_title}' ({tab_label}).",
            "dash_id": existing_id,
        }
        st.session_state.sdb_dashboard_widgets = []
        return True
    except Exception as ex:
        st.session_state.builder_flash_msg = {
            "type": "error",
            "title": f"Append Failed",
            "detail": str(ex),
            "dash_id": existing_id,
        }
        return False
