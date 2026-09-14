from typing import Any, Dict, List, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from adapters.csv_adapter import CSVDataAdapter
from adapters.snowflake_adapter import SnowflakeDataAdapter
from adapters.parquet_adapter import ParquetDataAdapter
from adapters.duckdb_adapter import DuckDBDataAdapter

# Adapter registry
ADAPTER_MAP = {
    "csv": CSVDataAdapter,
    "snowflake": SnowflakeDataAdapter,
    "parquet": ParquetDataAdapter,
    "duckdb": DuckDBDataAdapter,
}


PALETTES = {
    "streamdash": ["#4f46e5", "#06b6d4", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"],
    "emerald": ["#059669", "#10b981", "#34d399", "#6ee7b7", "#047857", "#065f46"],
    "sunset": ["#f97316", "#ef4444", "#ec4899", "#f59e0b", "#fbbf24", "#db2777"],
    "ocean": ["#0284c7", "#0ea5e9", "#38bdf8", "#0369a1", "#075985", "#22d3ee"],
    "indigo": ["#4f46e5", "#6366f1", "#818cf8", "#4338ca", "#3730a3", "#a5b4fc"],
    "cyberpunk": ["#06b6d4", "#ec4899", "#a855f7", "#3b82f6", "#10b981", "#f43f5e"],
    "pastel": px.colors.qualitative.Pastel,
    "prism": px.colors.qualitative.Prism,
}


def get_data_adapter(source_type: str):
    adapter_cls = ADAPTER_MAP.get(source_type.lower())
    if not adapter_cls:
        raise ValueError(f"Unsupported data source type: '{source_type}'")
    return adapter_cls()


def format_metric_value(val: Any, fmt: str = "auto", unit: str = "") -> str:
    """Format numeric values according to metric definition."""
    if pd.isna(val) or val is None:
        return "N/A"

    if fmt == "currency":
        if abs(val) >= 1_000_000:
            return f"${val / 1_000_000:.2f}M"
        elif abs(val) >= 1_000:
            return f"${val / 1_000:.1f}k"
        else:
            return f"${val:,.2f}"
    elif fmt == "percent":
        return f"{val * 100:.1f}%" if abs(val) <= 1.0 else f"{val:.1f}%"
    elif fmt == "integer":
        return f"{int(round(val)):,}"
    elif fmt == "float":
        return f"{val:,.2f}{unit}"
    else:
        if isinstance(val, (int, float)):
            return f"{val:,.2f}{unit}"
        return f"{val}{unit}"


def compute_aggregation(df: pd.DataFrame, col: str, agg: str) -> Any:
    """Safely compute aggregation on a DataFrame column."""
    if col not in df.columns or df.empty:
        return 0

    series = df[col]
    agg_lower = str(agg).lower()
    if agg_lower == "sum":
        return pd.to_numeric(series, errors="coerce").sum()
    elif agg_lower in ["mean", "avg", "average"]:
        return pd.to_numeric(series, errors="coerce").mean()
    elif agg_lower == "count":
        return series.count()
    elif agg_lower in ["nunique", "distinct_count", "count_distinct", "unique"]:
        return series.nunique()
    elif agg_lower == "min":
        return pd.to_numeric(series, errors="coerce").min() if pd.api.types.is_numeric_dtype(series) else series.min()
    elif agg_lower == "max":
        return pd.to_numeric(series, errors="coerce").max() if pd.api.types.is_numeric_dtype(series) else series.max()
    elif agg_lower == "median":
        return pd.to_numeric(series, errors="coerce").median()
    return series.iloc[0] if not series.empty else 0


class DashboardRenderer:
    """Renders a YAML-configured dashboard dynamically into the Streamlit UI."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_source_config = config.get("data_source", {})
        self.adapter = get_data_adapter(self.data_source_config.get("type", "csv"))

    def render(self):
        """Main rendering pipeline for the dashboard."""
        self._render_header()

        # 1. Load baseline data
        try:
            raw_df = self.adapter.load_data(self.data_source_config)
        except Exception as e:
            st.error(f"Failed to load dataset: {e}")
            return

        if raw_df is None or raw_df.empty:
            st.warning("The selected data source returned zero records.")
            return

        # 2. Render interactive filters via OOP FilterRegistry
        active_filters, df = self._render_filters(raw_df)

        st.caption(f"Showing **{len(df):,}** of **{len(raw_df):,}** records matching current filters.")

        tabs_config = self.config.get("tabs")
        if tabs_config and isinstance(tabs_config, list) and len(tabs_config) > 0:
            tab_titles = [t.get("title", f"Tab {idx + 1}") for idx, t in enumerate(tabs_config)]
            rendered_tabs = st.tabs(tab_titles)
            for idx, tab_obj in enumerate(rendered_tabs):
                with tab_obj:
                    t_conf = tabs_config[idx]
                    if t_conf.get("description"):
                        st.caption(t_conf["description"])
                    if "metrics" in t_conf:
                        self._render_metrics(df, raw_df, metrics_config=t_conf["metrics"])
                        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                    if "charts" in t_conf:
                        self._render_charts(df, charts_config=t_conf["charts"])
                    if "table" in t_conf:
                        self._render_table(df, table_config=t_conf["table"])
        else:
            # 4. Render default root KPI Metric cards
            self._render_metrics(df, raw_df)
            st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
            # 5. Render default root charts
            self._render_charts(df)
            # 6. Render default root data table if enabled
            self._render_table(df)

    def _render_header(self):
        title = self.config.get("title", "Dashboard")
        desc = self.config.get("description", "")
        icon = self.config.get("icon", "📊")
        category = self.config.get("category", "General")

        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 6px;">
                    <span style="font-size: 2.2rem;">{icon}</span>
                    <div>
                        <h1 style="margin: 0; font-size: 1.9rem; font-weight: 700; letter-spacing: -0.02em;">{title}</h1>
                        <p style="margin: 2px 0 0 0; color: #64748b; font-size: 0.95rem;">{desc}</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f"""
                <div style="text-align: right; padding-top: 10px;">
                    <span style="background: rgba(99, 102, 241, 0.12); color: #6366f1; padding: 4px 10px; border-radius: 9999px; font-size: 0.8rem; font-weight: 600; border: 1px solid rgba(99, 102, 241, 0.25);">
                        {category}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<hr style='margin: 12px 0 20px 0; border: 0; border-top: 1px solid rgba(148, 163, 184, 0.2);' />", unsafe_allow_html=True)

    def _render_filters(self, df: pd.DataFrame) -> tuple[Dict[str, Any], pd.DataFrame]:
        from core.filters.registry import FilterRegistry

        filters_config = self.config.get("filters", [])
        if not filters_config:
            return {}, df

        active_filter_values = {}
        filtered_df = df.copy()

        with st.expander("🔍 Interactive Filters & Parameters", expanded=True):
            cols = st.columns(min(len(filters_config), 4))
            for i, f_conf in enumerate(filters_config):
                col_widget = cols[i % len(cols)]
                with col_widget:
                    try:
                        filter_obj = FilterRegistry.create(f_conf)
                        selected_val = filter_obj.render(df, key_prefix=f"filter_{self.config.get('id', 'dash')}")
                        active_filter_values[filter_obj.column] = selected_val
                        filtered_df = filter_obj.apply(filtered_df, selected_val)
                    except Exception as e:
                        st.error(f"Filter error on '{f_conf.get('column')}': {e}")

        return active_filter_values, filtered_df

    def _render_metrics(self, df: pd.DataFrame, raw_df: pd.DataFrame, metrics_config: List[Dict[str, Any]] = None):
        if metrics_config is None:
            metrics_config = self.config.get("metrics", [])
        if not metrics_config:
            return

        cols = st.columns(len(metrics_config))
        for i, m in enumerate(metrics_config):
            with cols[i]:
                label = m.get("label", "Metric")
                col = m.get("column")
                agg = m.get("agg", "sum")
                fmt = m.get("format", "auto")
                unit = m.get("unit", "")
                help_text = m.get("help", "")

                current_val = compute_aggregation(df, col, agg)
                formatted_val = format_metric_value(current_val, fmt=fmt, unit=unit)

                delta_str = None
                delta_col = m.get("delta_compare_col")
                if delta_col and delta_col in df.columns:
                    target_val = compute_aggregation(df, delta_col, agg)
                    if isinstance(current_val, (int, float)) and isinstance(target_val, (int, float)):
                        diff = current_val - target_val
                        pct_diff = (diff / target_val * 100) if target_val != 0 else 0
                        delta_str = f"{pct_diff:+.1f}% vs target"

                st.metric(
                    label=label,
                    value=formatted_val,
                    delta=delta_str,
                    help=help_text,
                )

    def _render_charts(self, df: pd.DataFrame, charts_config: List[Dict[str, Any]] = None):
        if charts_config is None:
            charts_config = self.config.get("charts", [])
        if not charts_config:
            return

        # Render charts in a responsive two-column grid or single column
        chart_pairs = [charts_config[i:i + 2] for i in range(0, len(charts_config), 2)]

        for pair in chart_pairs:
            if len(pair) == 2:
                col_a_width = pair[0].get("col_width", 6)
                col_b_width = pair[1].get("col_width", 6)
                c1, c2 = st.columns([col_a_width, col_b_width])
                with c1:
                    self._render_single_chart(pair[0], df)
                with c2:
                    self._render_single_chart(pair[1], df)
            else:
                self._render_single_chart(pair[0], df)

    def _render_single_chart(self, c_conf: Dict[str, Any], df: pd.DataFrame):
        from core.charts.registry import ChartRegistry

        if df.empty:
            st.info("No data available to plot chart.")
            return

        title = c_conf.get("title", "Chart")
        st.markdown(f"<h4 style='font-size: 1.05rem; font-weight: 600; margin-bottom: 8px;'>{title}</h4>", unsafe_allow_html=True)

        try:
            chart_conf = dict(c_conf)
            if "theme" not in chart_conf and "theme" in self.config:
                chart_conf["theme"] = self.config["theme"]
            if "palette" not in chart_conf and "palette" in self.config:
                chart_conf["palette"] = self.config["palette"]

            chart_obj = ChartRegistry.create(chart_conf)
            chart_obj.render(df)
        except Exception as e:
            st.error(f"Error rendering chart '{title}': {e}")

    def _render_table(self, df: pd.DataFrame, table_config: Dict[str, Any] = None):
        t_conf = table_config if table_config is not None else self.config.get("table", {})
        if not t_conf.get("show", True):
            return

        st.markdown("<hr style='margin: 24px 0 16px 0; border: 0; border-top: 1px solid rgba(148, 163, 184, 0.2);' />", unsafe_allow_html=True)
        
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"<h4 style='font-size: 1.1rem; font-weight: 600; margin: 0;'>{t_conf.get('title', 'Dataset Preview')}</h4>", unsafe_allow_html=True)
        with col2:
            csv_bytes = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Export CSV",
                data=csv_bytes,
                file_name=f"{self.config.get('id', 'export')}_data.csv",
                mime="text/csv",
                use_container_width=True,
            )

        cols_to_show = t_conf.get("columns")
        display_df = df[cols_to_show] if cols_to_show else df
        st.dataframe(display_df, use_container_width=True, height=280)
