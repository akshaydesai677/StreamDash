from typing import Any, Dict, List
import pandas as pd
import plotly.express as px
import streamlit as st

from core.charts.base import BaseChart


class AreaChart(BaseChart):
    """Area Chart implementation."""

    @classmethod
    def get_type(cls) -> str:
        return "area"

    @classmethod
    def get_label(cls) -> str:
        return "🌊 Area Chart"

    @classmethod
    def get_configurable_properties(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": "groupnorm",
                "label": "Normalization",
                "type": "select",
                "options": ["none", "fraction", "percent"],
                "default": "none",
            }
        ]

    def render(self, df: pd.DataFrame):
        if df.empty:
            st.info(f"No data available for chart '{self.title}'.")
            return

        norm = self.config.get("groupnorm", "none")
        groupnorm = norm if norm in ["fraction", "percent"] else None
        color_seq = self.get_color_sequence()
        plot_df, color_col = self.prepare_color(df)

        fig = px.area(
            plot_df,
            x=self.x,
            y=self.y,
            color=color_col,
            groupnorm=groupnorm,
            color_discrete_sequence=color_seq,
        )
        self.apply_standard_layout(fig)
        st.plotly_chart(fig, use_container_width=True)
