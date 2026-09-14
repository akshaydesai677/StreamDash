from typing import Any, Dict, List
import pandas as pd
import streamlit as st

from core.charts.base import BaseChart


class TableChart(BaseChart):
    """Data Table visualizer."""

    @classmethod
    def get_type(cls) -> str:
        return "table"

    @classmethod
    def get_label(cls) -> str:
        return "📋 Data Table"

    @classmethod
    def get_configurable_properties(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": "max_rows",
                "label": "Display Rows Limit",
                "type": "select",
                "options": [10, 25, 50, 100, 500],
                "default": 50,
            }
        ]

    def render(self, df: pd.DataFrame):
        if df.empty:
            st.info("No data to display in table.")
            return

        cols = self.config.get("columns")
        if cols:
            valid_cols = [c for c in cols if c in df.columns]
            display_df = df[valid_cols] if valid_cols else df
        else:
            display_df = df

        max_rows = self.config.get("max_rows", 50)
        st.dataframe(display_df.head(max_rows), use_container_width=True, height=self.height)
