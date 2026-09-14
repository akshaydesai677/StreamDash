from typing import Any, Dict, List
import pandas as pd
import streamlit as st

from core.filters.base import BaseFilter


class MultiselectFilter(BaseFilter):
    """Filter that allows selecting multiple categorical items."""

    @classmethod
    def get_type(cls) -> str:
        return "multiselect"

    @classmethod
    def get_label(cls) -> str:
        return "☑️ Multi-Select"

    @classmethod
    def get_configurable_properties(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": "include_all_default",
                "label": "Select All by Default",
                "type": "bool",
                "default": False,
            }
        ]

    def render(self, df: pd.DataFrame, key_prefix: str = "") -> Any:
        if self.column not in df.columns:
            return []

        options = sorted(list(df[self.column].dropna().unique().astype(str)))
        default_val = self.default if self.default is not None else []
        if isinstance(default_val, str):
            default_val = [default_val]
        # Filter defaults to only valid options
        valid_defaults = [v for v in default_val if v in options]

        widget_key = f"{key_prefix}_{self.id}_{self.column}"
        return st.multiselect(
            self.label,
            options=options,
            default=valid_defaults,
            help=self.help if self.help else None,
            key=widget_key,
        )

    def apply(self, df: pd.DataFrame, selected_value: Any) -> pd.DataFrame:
        if not selected_value or self.column not in df.columns:
            return df
        return df[df[self.column].astype(str).isin(selected_value)]
