from typing import Any, Dict, List
import pandas as pd
import streamlit as st

from core.filters.base import BaseFilter


class NumericRangeFilter(BaseFilter):
    """Filter that allows selecting a numeric range via a slider."""

    @classmethod
    def get_type(cls) -> str:
        return "slider"

    @classmethod
    def get_label(cls) -> str:
        return "🔢 Numeric Range Slider"

    @classmethod
    def get_configurable_properties(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": "step",
                "label": "Step Size",
                "type": "float",
                "default": 1.0,
            }
        ]

    def render(self, df: pd.DataFrame, key_prefix: str = "") -> Any:
        if self.column not in df.columns:
            return None

        series = pd.to_numeric(df[self.column], errors="coerce").dropna()
        if series.empty:
            return None

        min_val = float(series.min())
        max_val = float(series.max())
        if min_val == max_val:
            return (min_val, max_val)

        widget_key = f"{key_prefix}_{self.id}_{self.column}"
        return st.slider(
            self.label,
            min_value=min_val,
            max_value=max_val,
            value=(min_val, max_val),
            help=self.help if self.help else None,
            key=widget_key,
        )

    def apply(self, df: pd.DataFrame, selected_value: Any) -> pd.DataFrame:
        if not selected_value or self.column not in df.columns:
            return df
        if isinstance(selected_value, (list, tuple)) and len(selected_value) == 2:
            low, high = selected_value
            series = pd.to_numeric(df[self.column], errors="coerce")
            return df[(series >= low) & (series <= high)]
        return df
