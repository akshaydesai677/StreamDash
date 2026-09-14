from typing import Any, Dict, List
import pandas as pd
import streamlit as st

from core.filters.base import BaseFilter


class SearchFilter(BaseFilter):
    """Filter that performs text substring matching on a column."""

    @classmethod
    def get_type(cls) -> str:
        return "search"

    @classmethod
    def get_label(cls) -> str:
        return "🔍 Text Search"

    @classmethod
    def get_configurable_properties(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": "case_sensitive",
                "label": "Case Sensitive",
                "type": "bool",
                "default": False,
            }
        ]

    def render(self, df: pd.DataFrame, key_prefix: str = "") -> Any:
        if self.column not in df.columns:
            return ""

        widget_key = f"{key_prefix}_{self.id}_{self.column}"
        return st.text_input(
            self.label,
            value=str(self.default) if self.default else "",
            placeholder=f"Search {self.label}...",
            help=self.help if self.help else None,
            key=widget_key,
        )

    def apply(self, df: pd.DataFrame, selected_value: Any) -> pd.DataFrame:
        if not selected_value or not str(selected_value).strip() or self.column not in df.columns:
            return df
        query = str(selected_value).strip()
        case_sensitive = self.config.get("case_sensitive", False)
        return df[df[self.column].astype(str).str.contains(query, case=case_sensitive, na=False)]
