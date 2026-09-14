from typing import Any, Dict, List
import pandas as pd
import plotly.express as px
import streamlit as st

from core.charts.base import BaseChart


class BoxChart(BaseChart):
    """Box Plot implementation."""

    @classmethod
    def get_type(cls) -> str:
        return "box"

    @classmethod
    def get_label(cls) -> str:
        return "📦 Box Plot"

    @classmethod
    def get_configurable_properties(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": "points",
                "label": "Show Data Points",
                "type": "select",
                "options": ["all", "outliers", "suspectedoutliers", "none"],
                "default": "outliers",
            }
        ]

    def render(self, df: pd.DataFrame):
        if df.empty:
            st.info(f"No data available for chart '{self.title}'.")
            return

        points = self.config.get("points", "outliers")
        color_seq = self.get_color_sequence()
        plot_df, color_col = self.prepare_color(df)
        final_color = color_col if color_col else self.x

        fig = px.box(
            plot_df,
            x=self.x,
            y=self.y,
            color=final_color,
            points=points if points != "none" else False,
            color_discrete_sequence=color_seq,
        )
        self.apply_standard_layout(fig)
        st.plotly_chart(fig, use_container_width=True)
