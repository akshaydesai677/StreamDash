import os
import re
from typing import Any, Dict, List, Optional
import pandas as pd
from adapters.base import BaseDataAdapter

# Check if snowflake connector is installed
try:
    import snowflake.connector
    HAS_SNOWFLAKE = True
except ImportError:
    HAS_SNOWFLAKE = False

# Conditionally import streamlit for caching if available
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False


def _get_secret_or_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Retrieve credential from Streamlit secrets, environment variable, or default."""
    if HAS_STREAMLIT:
        try:
            # Check st.secrets["snowflake"][key]
            if "snowflake" in st.secrets and key in st.secrets["snowflake"]:
                return str(st.secrets["snowflake"][key])
            # Check st.secrets[key]
            if key in st.secrets:
                return str(st.secrets[key])
        except Exception:
            pass

    # Check environment variable
    env_val = os.environ.get(key.upper()) or os.environ.get(f"SNOWFLAKE_{key.upper()}")
    if env_val:
        return env_val

    return default


def _resolve_connection_params(config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract connection parameters from config, environment, or secrets."""
    params = {}
    standard_keys = [
        "account",
        "user",
        "password",
        "warehouse",
        "database",
        "schema",
        "role",
        "authenticator",
        "token",
        "connection_name",
        "host",
        "port",
    ]

    for key in standard_keys:
        val = config.get(key)
        # Expand environment variables like ${SNOWFLAKE_PASSWORD}
        if isinstance(val, str) and val.startswith("${") and val.endswith("}"):
            env_var = val[2:-1]
            val = os.environ.get(env_var, "")
        if val is None or val == "":
            val = _get_secret_or_env(key)
        if val is not None and val != "":
            params[key] = val

    return params


def _run_query_raw(conn_params: Dict[str, Any], query: str) -> pd.DataFrame:
    """Execute SQL query using snowflake-connector-python and return DataFrame."""
    if not HAS_SNOWFLAKE:
        raise ImportError(
            "Snowflake connector is not installed. "
            "Please install it using: pip install snowflake-connector-python[pandas]"
        )

    # Filter connection parameters accepted by snowflake.connector.connect
    allowed_conn_args = {
        "user", "password", "account", "database", "schema", "warehouse",
        "role", "authenticator", "token", "connection_name", "host", "port"
    }
    filtered_params = {k: v for k, v in conn_params.items() if k in allowed_conn_args}

    conn = snowflake.connector.connect(**filtered_params)
    try:
        cur = conn.cursor()
        try:
            cur.execute(query)
            # Use arrow/pandas integration if available, otherwise fetchall
            try:
                df = cur.fetch_pandas_all()
            except Exception:
                rows = cur.fetchall()
                cols = [desc[0] for desc in cur.description] if cur.description else []
                df = pd.DataFrame(rows, columns=cols)
            return df
        finally:
            cur.close()
    finally:
        conn.close()


# Cached query executor
if HAS_STREAMLIT:
    @st.cache_data(show_spinner=False, ttl=600)
    def _execute_cached_query(conn_params_tuple: tuple, query: str) -> pd.DataFrame:
        conn_params = dict(conn_params_tuple)
        return _run_query_raw(conn_params, query)
else:
    def _execute_cached_query(conn_params_tuple: tuple, query: str) -> pd.DataFrame:
        conn_params = dict(conn_params_tuple)
        return _run_query_raw(conn_params, query)


class SnowflakeDataAdapter(BaseDataAdapter):
    """Enterprise Data Adapter for connecting, querying, and caching data from Snowflake."""

    def __init__(self, default_config: Optional[Dict[str, Any]] = None):
        self.default_config = default_config or {}

    def load_data(self, config: Dict[str, Any]) -> pd.DataFrame:
        """Load data from Snowflake based on query or table specification.

        Configuration options:
            - account: Snowflake account identifier (e.g. 'xy12345.us-east-1').
            - user: Snowflake username.
            - password: User password (supports ${ENV_VAR} syntax).
            - warehouse: Compute warehouse (e.g. 'COMPUTE_WH').
            - database: Target database name.
            - schema: Target schema name (e.g. 'PUBLIC').
            - role: Snowflake role (e.g. 'ANALYST_ROLE').
            - query: Direct SQL SELECT query to execute.
            - table: Table name to query (if query is not provided).
            - limit: Optional row limit (integer).
            - date_columns: List of columns to parse as datetime.
            - cache_ttl: Cache expiration in seconds (default: 600s).
            - mock: If True, returns synthetic mock data for sandbox testing.
        """
        merged_config = dict(self.default_config)
        merged_config.update(config)

        # 1. Mock / Sandbox Mode (useful for offline testing or without live credentials)
        if merged_config.get("mock") or merged_config.get("test_mode"):
            return self._generate_mock_data(merged_config)

        # 2. Build SQL query
        query = self._build_query(merged_config)

        # 3. Resolve connection parameters
        conn_params = _resolve_connection_params(merged_config)
        if not conn_params.get("account") and not conn_params.get("connection_name"):
            raise ValueError(
                "Snowflake configuration must specify an 'account' or 'connection_name'. "
                "You can provide it in dashboard YAML, environment variable 'SNOWFLAKE_ACCOUNT', or Streamlit secrets."
            )

        # 4. Execute query with caching
        # Convert params dict to hashable tuple for caching
        cache_key = tuple(sorted(conn_params.items()))
        df = _execute_cached_query(cache_key, query)

        # 5. Process Date Columns
        date_columns = merged_config.get("date_columns", [])
        if date_columns:
            for col in date_columns:
                if col in df.columns:
                    try:
                        df[col] = pd.to_datetime(df[col])
                    except Exception:
                        pass
        else:
            # Auto-detect date/datetime columns
            for col in df.columns:
                if any(kw in col.lower() for kw in ["date", "timestamp", "time", "created_at"]):
                    try:
                        df[col] = pd.to_datetime(df[col])
                    except Exception:
                        pass

        return df

    def get_columns(self, config: Dict[str, Any]) -> List[str]:
        """Fetch column names from Snowflake without loading the entire dataset."""
        merged_config = dict(self.default_config)
        merged_config.update(config)

        if merged_config.get("mock") or merged_config.get("test_mode"):
            df = self._generate_mock_data(merged_config)
            return list(df.columns)

        # If a table is specified, execute zero-row query to get schema quickly
        table = merged_config.get("table")
        if table:
            zero_row_config = dict(merged_config)
            zero_row_config["query"] = f"SELECT * FROM {table} LIMIT 0"
            df = self.load_data(zero_row_config)
            return list(df.columns)

        # Otherwise execute the configured query with limit 0
        user_query = merged_config.get("query", "")
        if user_query:
            zero_row_config = dict(merged_config)
            clean_q = user_query.strip().rstrip(";")
            zero_row_config["query"] = f"SELECT * FROM ({clean_q}) AS _subq LIMIT 0"
            try:
                df = self.load_data(zero_row_config)
                return list(df.columns)
            except Exception:
                pass

        df = self.load_data(merged_config)
        return list(df.columns)

    def _build_query(self, config: Dict[str, Any]) -> str:
        """Construct the SQL query from config parameters."""
        if config.get("query"):
            query = config["query"].strip()
            limit = config.get("limit")
            if limit and not re.search(r"\blimit\b", query, re.IGNORECASE):
                query = f"{query.rstrip(';')} LIMIT {int(limit)}"
            return query

        table = config.get("table")
        if not table:
            raise ValueError("Snowflake data source requires either 'query' or 'table' attribute.")

        columns = config.get("columns")
        cols_clause = ", ".join(columns) if columns and isinstance(columns, list) else "*"
        limit = config.get("limit")
        limit_clause = f" LIMIT {int(limit)}" if limit else ""

        return f"SELECT {cols_clause} FROM {table}{limit_clause}"

    def _generate_mock_data(self, config: Dict[str, Any]) -> pd.DataFrame:
        """Generates representative mock dataset for testing and verification."""
        data = {
            "ID": [101, 102, 103, 104, 105],
            "REGION": ["North America", "EMEA", "APAC", "North America", "LATAM"],
            "CATEGORY": ["Cloud Infrastructure", "Security", "Analytics", "Cloud Infrastructure", "Security"],
            "REVENUE": [145000.0, 89000.0, 112000.0, 210000.0, 75000.0],
            "TRANSACTION_DATE": pd.to_datetime(["2026-01-15", "2026-02-10", "2026-03-05", "2026-04-20", "2026-05-12"]),
        }
        return pd.DataFrame(data)
