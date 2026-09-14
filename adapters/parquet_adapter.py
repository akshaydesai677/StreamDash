import os
from typing import Any, Dict, List, Optional
import pandas as pd
from adapters.base import BaseDataAdapter

# Conditionally import streamlit for caching if available
try:
    import streamlit as st

    @st.cache_data(show_spinner=False)
    def _read_parquet_cached(filepath: str, columns: Optional[List[str]] = None) -> pd.DataFrame:
        return pd.read_parquet(filepath, columns=columns if columns else None)

except ImportError:

    def _read_parquet_cached(filepath: str, columns: Optional[List[str]] = None) -> pd.DataFrame:
        return pd.read_parquet(filepath, columns=columns if columns else None)


class ParquetDataAdapter(BaseDataAdapter):
    """High-performance columnar data adapter for Apache Parquet files."""

    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or os.getcwd()

    def _resolve_path(self, path: str) -> str:
        if os.path.isabs(path):
            return path
        return os.path.normpath(os.path.join(self.base_dir, path))

    def load_data(self, config: Dict[str, Any]) -> pd.DataFrame:
        """Load data from a Parquet file specified in config.

        Config keys:
            path: Relative or absolute path to the .parquet file.
            columns: Optional list of columns to load (columnar projection pruning).
            limit: Optional maximum rows to return.
        """
        raw_path = config.get("path")
        if not raw_path:
            raise ValueError("Parquet data source must specify a 'path' attribute.")

        file_path = self._resolve_path(raw_path)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Parquet file not found at: {file_path}")

        columns = config.get("columns")
        df = _read_parquet_cached(file_path, columns=columns)

        limit = config.get("limit")
        if limit and isinstance(limit, int) and len(df) > limit:
            df = df.iloc[:limit].copy()

        return df

    def get_columns(self, config: Dict[str, Any]) -> List[str]:
        """Instant zero-copy schema introspection from Parquet metadata."""
        raw_path = config.get("path")
        if not raw_path:
            raise ValueError("Parquet data source must specify a 'path' attribute.")

        file_path = self._resolve_path(raw_path)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Parquet file not found at: {file_path}")

        try:
            import pyarrow.parquet as pq
            schema = pq.read_schema(file_path)
            return list(schema.names)
        except Exception:
            # Fallback to reading first row
            df = pd.read_parquet(file_path, columns=None)
            return list(df.columns)
