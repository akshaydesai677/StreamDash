from typing import Any, Dict, List
import pandas as pd
import streamlit as st

from core.charts.base import BaseChart
from core.renderer import compute_aggregation, format_metric_value


class MetricChart(BaseChart):
    """Executive KPI metric card component."""

    @classmethod
    def get_type(cls) -> str:
        return "kpi"

    @classmethod
    def get_label(cls) -> str:
        return "🔢 KPI Metric Card"

    @classmethod
    def get_configurable_properties(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": "format",
                "label": "Display Format",
                "type": "select",
                "options": ["auto", "currency", "integer", "percent", "float"],
                "default": "auto",
            },
            {
                "name": "delta_col",
                "label": "Comparison Target Column",
                "type": "column_picker",
                "default": None,
            },
        ]

    def render(self, df: pd.DataFrame):
        col = self.y or self.x or self.config.get("column")
        if not col or col not in df.columns:
            st.warning("Metric card missing column.")
            return

        fmt = self.config.get("format", "auto")
        if fmt == "auto":
            if any(k in col.lower() for k in ["revenue", "spend", "cost", "price"]):
                fmt = "currency"
            elif self.agg in ["count", "distinct_count"]:
                fmt = "integer"
            else:
                fmt = "float"

        val = compute_aggregation(df, col, self.agg)
        formatted_val = format_metric_value(val, fmt=fmt)

        delta_str = None
        delta_col = self.config.get("delta_col") or self.config.get("delta_compare_col")
        if delta_col and delta_col in df.columns:
            target_val = compute_aggregation(df, delta_col, self.agg)
            if isinstance(val, (int, float)) and isinstance(target_val, (int, float)) and target_val != 0:
                diff = val - target_val
                pct_diff = (diff / target_val) * 100
                delta_str = f"{pct_diff:+.1f}% vs target"

        st.metric(
            label=self.title if self.title else f"{self.agg.upper()} of {col}",
            value=formatted_val,
            delta=delta_str,
            help=self.config.get("help"),
        )
