from typing import Any, Dict, List
import pandas as pd
import plotly.express as px
import streamlit as st

from core.charts.base import BaseChart


class PieChart(BaseChart):
    """Pie and Donut Chart implementation."""

    @classmethod
    def get_type(cls) -> str:
        return "pie"

    @classmethod
    def get_label(cls) -> str:
        return "🥧 Pie / Donut"

    @classmethod
    def get_configurable_properties(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": "hole",
                "label": "Donut Hole Size",
                "type": "float_slider",
                "min": 0.0,
                "max": 0.8,
                "step": 0.1,
                "default": 0.4,
            }
        ]

    def render(self, df: pd.DataFrame):
        if df.empty:
            st.info(f"No data available for chart '{self.title}'.")
            return

        hole = float(self.config.get("hole", 0.4))
        color_seq = self.get_color_sequence()
        plot_df, color_col = self.prepare_color(df)
        val_col = self.config.get("values") or self.y
        name_col = self.config.get("names") or self.x or color_col

        fig = px.pie(
            plot_df,
            values=val_col,
            names=name_col,
            hole=hole,
            color_discrete_sequence=color_seq,
        )

        if self.labels == "percentage":
            fig.update_traces(textinfo="label+percent")
        elif self.labels in ["value", True, "show"]:
            fig.update_traces(textinfo="label+value")

        self.apply_standard_layout(fig)
        st.plotly_chart(fig, use_container_width=True)
