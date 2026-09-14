from typing import Any, Dict, List
import pandas as pd
import plotly.express as px
import streamlit as st

from core.charts.base import BaseChart


class BarChart(BaseChart):
    """Bar Chart implementation supporting grouping, stacking, orientations, and aggregations."""

    @classmethod
    def get_type(cls) -> str:
        return "bar"

    @classmethod
    def get_label(cls) -> str:
        return "📊 Bar Chart"

    @classmethod
    def get_configurable_properties(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": "barmode",
                "label": "Bar Mode",
                "type": "select",
                "options": ["group", "stack", "relative"],
                "default": "group",
            },
            {
                "name": "orientation",
                "label": "Orientation",
                "type": "select",
                "options": ["vertical", "horizontal"],
                "default": "vertical",
            },
        ]

    def render(self, df: pd.DataFrame):
        if df.empty:
            st.info(f"No data available for chart '{self.title}'.")
            return

        barmode = self.config.get("barmode", "group")
        orientation = self.config.get("orientation", "vertical")
        color_seq = self.get_color_sequence()
        plot_df, color_col = self.prepare_color(df)

        # Grouping & Aggregation
        if self.x and self.y and self.agg:
            group_cols = [self.x]
            if color_col and color_col != self.x:
                group_cols.append(color_col)

            if self.agg == "sum":
                plot_df = plot_df.groupby(group_cols, as_index=False)[self.y].sum()
            elif self.agg in ["mean", "avg"]:
                plot_df = plot_df.groupby(group_cols, as_index=False)[self.y].mean()
            elif self.agg == "count":
                plot_df = plot_df.groupby(group_cols, as_index=False)[self.y].count()
            elif self.agg in ["distinct_count", "nunique"]:
                plot_df = plot_df.groupby(group_cols, as_index=False)[self.y].nunique()

        has_labels = self.labels not in ["none", False, None]
        if orientation == "horizontal" and self.x and self.y:
            fig = px.bar(
                plot_df,
                x=self.y,
                y=self.x,
                color=color_col,
                barmode=barmode,
                orientation="h",
                color_discrete_sequence=color_seq,
                text_auto=True if has_labels else False,
            )
        else:
            fig = px.bar(
                plot_df,
                x=self.x,
                y=self.y,
                color=color_col,
                barmode=barmode,
                color_discrete_sequence=color_seq,
                text_auto=True if has_labels else False,
            )

        self.apply_standard_layout(fig)
        if has_labels:
            fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)
