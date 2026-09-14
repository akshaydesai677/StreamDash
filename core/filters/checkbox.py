from typing import Any, Dict, List
import pandas as pd
import streamlit as st

from core.filters.base import BaseFilter


class CheckboxFilter(BaseFilter):
    """Filter that allows toggling options via checkboxes."""

    @classmethod
    def get_type(cls) -> str:
        return "checkbox"

    @classmethod
    def get_label(cls) -> str:
        return "☑️ Checkboxes"

    @classmethod
    def get_configurable_properties(cls) -> List[Dict[str, Any]]:
        return []

    def render(self, df: pd.DataFrame, key_prefix: str = "") -> Any:
        if self.column not in df.columns:
            return []

        raw_options = sorted(list(df[self.column].dropna().unique().astype(str)))
        if not raw_options:
            return []

        st.markdown(f"<div style='font-size: 0.85rem; font-weight: 600; margin-bottom: 4px;'>{self.label}</div>", unsafe_allow_html=True)

        selected_values = []
        # Render checkboxes in a responsive horizontal row
        cols = st.columns(min(len(raw_options), 4))
        for idx, opt in enumerate(raw_options):
            col_target = cols[idx % len(cols)]
            widget_key = f"{key_prefix}_{self.id}_{self.column}_{opt}"
            is_checked = col_target.checkbox(opt, value=True, key=widget_key)
            if is_checked:
                selected_values.append(opt)

        return selected_values

    def apply(self, df: pd.DataFrame, selected_value: Any) -> pd.DataFrame:
        if self.column not in df.columns or selected_value is None:
            return df
        if isinstance(selected_value, list):
            if not selected_value:
                # If all unchecked, return empty
                return df.iloc[0:0]
            return df[df[self.column].astype(str).isin(selected_value)]
        return df
