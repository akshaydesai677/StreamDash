import os
from typing import Any, Dict, List, Optional
import pandas as pd
from adapters.base import BaseDataAdapter

# Conditionally import streamlit for caching if available
try:
    import streamlit as st

    @st.cache_data(show_spinner=False, ttl=600)
    def _execute_duckdb_query_cached(
        db_path: str,
        query: str,
        read_only: bool = True,
    ) -> pd.DataFrame:
        import duckdb

        # Connect to DuckDB database or in-memory
        conn = duckdb.connect(database=db_path, read_only=read_only)
        try:
            df = conn.execute(query).df()
            return df
        finally:
            conn.close()

except ImportError:

    def _execute_duckdb_query_cached(
        db_path: str,
        query: str,
        read_only: bool = True,
    ) -> pd.DataFrame:
        import duckdb

        conn = duckdb.connect(database=db_path, read_only=read_only)
        try:
            df = conn.execute(query).df()
            return df
        finally:
            conn.close()


class DuckDBDataAdapter(BaseDataAdapter):
    """High-performance analytical data adapter powered by DuckDB.
    
    Supports:
    - Out-of-core SQL queries directly on CSV, Parquet, and JSON files without full RAM loads.
    - Embedded and persistent DuckDB database files (.duckdb, .db).
    - In-memory analytics engine with pushdown filtering and vectorization.
    """

    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or os.getcwd()

    def _resolve_path(self, path: str) -> str:
        if not path or path == ":memory:":
            return ":memory:"
        if os.path.isabs(path):
            return path
        return os.path.normpath(os.path.join(self.base_dir, path))

    def _build_sql_query(self, config: Dict[str, Any]) -> str:
        """Constructs executable SQL from config (explicit query, table, or file path)."""
        # 1. Explicit SQL query provided
        if "query" in config and config["query"].strip():
            return config["query"].strip()

        # 2. Querying a specific table in the database
        if "table" in config:
            tbl = config["table"].strip()
            limit = config.get("limit")
            if limit and isinstance(limit, int):
                return f"SELECT * FROM {tbl} LIMIT {limit}"
            return f"SELECT * FROM {tbl}"

        # 3. Querying a direct file (Parquet or CSV) via DuckDB's vectorized file scanner
        raw_path = config.get("path") or config.get("file")
        if raw_path:
            resolved_path = self._resolve_path(raw_path).replace("\\", "/")
            limit = config.get("limit")
            limit_clause = f" LIMIT {limit}" if limit and isinstance(limit, int) else ""
            
            if resolved_path.endswith(".parquet"):
                return f"SELECT * FROM read_parquet('{resolved_path}'){limit_clause}"
            elif resolved_path.endswith(".csv"):
                return f"SELECT * FROM read_csv_auto('{resolved_path}'){limit_clause}"
            else:
                return f"SELECT * FROM '{resolved_path}'{limit_clause}"

        raise ValueError(
            "DuckDB data source must specify either 'query', 'table', or 'path'/'file'."
        )

    def load_data(self, config: Dict[str, Any]) -> pd.DataFrame:
        """Execute DuckDB analytical query and return a pandas DataFrame."""
        db_raw = config.get("database", ":memory:")
        db_path = self._resolve_path(db_raw) if db_raw != ":memory:" else ":memory:"

        # If database file does not exist and path is not :memory:, verify
        read_only = True
        if db_path != ":memory:":
            if not os.path.exists(db_path):
                # Create parent directory if needed
                os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
                read_only = False

        query = self._build_sql_query(config)
        if db_path == ":memory:":
            read_only = False
        df = _execute_duckdb_query_cached(db_path, query, read_only=read_only)

        # Date auto-detection & conversion if needed
        date_columns = config.get("date_columns", [])
        if date_columns:
            for col in date_columns:
                if col in df.columns and not pd.api.types.is_datetime64_any_dtype(df[col]):
                    try:
                        df[col] = pd.to_datetime(df[col])
                    except Exception:
                        pass
        else:
            for col in df.columns:
                if any(kw in col.lower() for kw in ["date", "timestamp", "created_at"]):
                    if not pd.api.types.is_datetime64_any_dtype(df[col]):
                        try:
                            df[col] = pd.to_datetime(df[col])
                        except Exception:
                            pass

        return df

    def get_columns(self, config: Dict[str, Any]) -> List[str]:
        """Instant zero-row schema introspection using LIMIT 0."""
        import duckdb

        db_raw = config.get("database", ":memory:")
        db_path = self._resolve_path(db_raw) if db_raw != ":memory:" else ":memory:"
        base_query = self._build_sql_query(config)
        inspect_query = f"SELECT * FROM ({base_query}) AS _subq LIMIT 0"

        read_only = True if db_path != ":memory:" and os.path.exists(db_path) else False
        conn = duckdb.connect(database=db_path, read_only=read_only)
        try:
            desc = conn.execute(inspect_query).description
            return [col[0] for col in desc]
        except Exception:
            # Fallback to full load
            df = self.load_data(config)
            return list(df.columns)
        finally:
            conn.close()
