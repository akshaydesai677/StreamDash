import os
from typing import Any, Dict, List
import pandas as pd
from adapters.base import BaseDataAdapter

# Conditionally import streamlit for caching if available
try:
    import streamlit as st

    @st.cache_data(show_spinner=False)
    def _read_csv_cached(filepath: str, parse_dates: List[str] = None) -> pd.DataFrame:
        if parse_dates:
            return pd.read_csv(filepath, parse_dates=parse_dates)
        return pd.read_csv(filepath)

except ImportError:

    def _read_csv_cached(filepath: str, parse_dates: List[str] = None) -> pd.DataFrame:
        if parse_dates:
            return pd.read_csv(filepath, parse_dates=parse_dates)
        return pd.read_csv(filepath)


class CSVDataAdapter(BaseDataAdapter):
    """Data adapter for loading and querying CSV files."""

    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or os.getcwd()

    def _resolve_path(self, path: str) -> str:
        if os.path.isabs(path):
            return path
        return os.path.normpath(os.path.join(self.base_dir, path))

    def load_data(self, config: Dict[str, Any]) -> pd.DataFrame:
        """Load data from a CSV file specified in config.

        Config keys:
            path: Relative or absolute path to the CSV file.
            date_columns: Optional list of column names to parse as dates.
        """
        raw_path = config.get("path")
        if not raw_path:
            raise ValueError("CSV data source must specify a 'path' attribute.")

        file_path = self._resolve_path(raw_path)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found at: {file_path}")

        date_columns = config.get("date_columns", [])
        df = _read_csv_cached(file_path, parse_dates=date_columns if date_columns else None)

        # Auto-detect date/datetime columns if not specified
        if not date_columns:
            for col in df.columns:
                if any(kw in col.lower() for kw in ["date", "timestamp", "time", "created_at"]):
                    try:
                        df[col] = pd.to_datetime(df[col])
                    except Exception:
                        pass

        return df

    def get_columns(self, config: Dict[str, Any]) -> List[str]:
        df = self.load_data(config)
        return list(df.columns)
