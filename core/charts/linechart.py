from typing import Any, Dict, List
import pandas as pd
import plotly.express as px
import streamlit as st

from core.charts.base import BaseChart


class LineChart(BaseChart):
    """Line Chart implementation supporting markers and curve styles."""

    @classmethod
    def get_type(cls) -> str:
        return "line"

    @classmethod
    def get_label(cls) -> str:
        return "📈 Line Chart"

    @classmethod
    def get_configurable_properties(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": "line_shape",
                "label": "Line Shape",
                "type": "select",
                "options": ["linear", "spline"],
                "default": "linear",
            },
            {
                "name": "show_markers",
                "label": "Show Data Markers",
                "type": "bool",
                "default": True,
            },
        ]

    def render(self, df: pd.DataFrame):
        if df.empty:
            st.info(f"No data available for chart '{self.title}'.")
            return

        line_shape = self.config.get("line_shape", "linear")
        show_markers = self.config.get("show_markers", True)
        color_seq = self.get_color_sequence()
        plot_df, color_col = self.prepare_color(df)

        fig = px.line(
            plot_df,
            x=self.x,
            y=self.y,
            color=color_col,
            markers=show_markers,
            line_shape=line_shape,
            color_discrete_sequence=color_seq,
        )

        has_labels = self.labels not in ["none", False, None]
        if has_labels and self.y:
            fig.update_traces(text=plot_df[self.y], mode="lines+markers+text", textposition="top center")

        self.apply_standard_layout(fig)
        st.plotly_chart(fig, use_container_width=True)
