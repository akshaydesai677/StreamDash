from typing import Any, Dict, List
import pandas as pd
import plotly.express as px
import streamlit as st

from core.charts.base import BaseChart


class ScatterChart(BaseChart):
    """Scatter Plot implementation supporting optional bubble sizing."""

    @classmethod
    def get_type(cls) -> str:
        return "scatter"

    @classmethod
    def get_label(cls) -> str:
        return "✨ Scatter Plot"

    @classmethod
    def get_configurable_properties(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": "size_col",
                "label": "Bubble Size Column",
                "type": "column_picker",
                "default": None,
            }
        ]

    def render(self, df: pd.DataFrame):
        if df.empty:
            st.info(f"No data available for chart '{self.title}'.")
            return

        color_seq = self.get_color_sequence()
        plot_df, color_col = self.prepare_color(df)
        size_col = self.config.get("size") or self.config.get("size_col")
        if size_col and size_col not in plot_df.columns:
            size_col = None

        fig = px.scatter(
            plot_df,
            x=self.x,
            y=self.y,
            color=color_col,
            size=size_col,
            color_discrete_sequence=color_seq,
        )
        self.apply_standard_layout(fig)
        st.plotly_chart(fig, use_container_width=True)
