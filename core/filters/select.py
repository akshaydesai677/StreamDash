from typing import Any, Dict, List
import pandas as pd
import streamlit as st

from core.filters.base import BaseFilter


class SelectFilter(BaseFilter):
    """Filter that allows selecting a single item from a dropdown with optional 'All'."""

    @classmethod
    def get_type(cls) -> str:
        return "selectbox"

    @classmethod
    def get_label(cls) -> str:
        return "🔽 Single Select"

    @classmethod
    def get_configurable_properties(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": "include_all",
                "label": "Include 'All' Option",
                "type": "bool",
                "default": True,
            }
        ]

    def render(self, df: pd.DataFrame, key_prefix: str = "") -> Any:
        if self.column not in df.columns:
            return "All"

        raw_options = sorted(list(df[self.column].dropna().unique().astype(str)))
        include_all = self.config.get("include_all", True)
        options = ["All"] + raw_options if include_all else raw_options

        default_idx = 0
        if self.default and str(self.default) in options:
            default_idx = options.index(str(self.default))

        widget_key = f"{key_prefix}_{self.id}_{self.column}"
        return st.selectbox(
            self.label,
            options=options,
            index=default_idx,
            help=self.help if self.help else None,
            key=widget_key,
        )

    def apply(self, df: pd.DataFrame, selected_value: Any) -> pd.DataFrame:
        if not selected_value or selected_value == "All" or self.column not in df.columns:
            return df
        return df[df[self.column].astype(str) == str(selected_value)]
