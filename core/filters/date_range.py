from typing import Any, Dict, List
import datetime
import pandas as pd
import streamlit as st

from core.filters.base import BaseFilter


class DateRangeFilter(BaseFilter):
    """Filter that allows selecting a date range using calendar pickers."""

    @classmethod
    def get_type(cls) -> str:
        return "date_range"

    @classmethod
    def get_label(cls) -> str:
        return "📅 Date Range"

    @classmethod
    def get_configurable_properties(cls) -> List[Dict[str, Any]]:
        return []

    def render(self, df: pd.DataFrame, key_prefix: str = "") -> Any:
        if self.column not in df.columns:
            return None

        series = pd.to_datetime(df[self.column], errors="coerce").dropna()
        if series.empty:
            return None

        min_date = series.min().date()
        max_date = series.max().date()
        widget_key = f"{key_prefix}_{self.id}_{self.column}"

        val = st.date_input(
            self.label,
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            help=self.help if self.help else None,
            key=widget_key,
        )
        return val

    def apply(self, df: pd.DataFrame, selected_value: Any) -> pd.DataFrame:
        if not selected_value or self.column not in df.columns:
            return df

        if isinstance(selected_value, (list, tuple)) and len(selected_value) == 2:
            start_date, end_date = selected_value
            dt_series = pd.to_datetime(df[self.column], errors="coerce")
            start_ts = pd.to_datetime(start_date)
            end_ts = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(nanoseconds=1)
            return df[(dt_series >= start_ts) & (dt_series <= end_ts)]
        return df
