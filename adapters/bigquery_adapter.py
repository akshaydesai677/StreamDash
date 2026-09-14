import json
import os
from typing import Any, Dict, List, Optional
import pandas as pd
from adapters.base import BaseDataAdapter

# Conditionally import streamlit for caching if available
try:
    import streamlit as st

    @st.cache_data(show_spinner=False, ttl=600)
    def _execute_bigquery_cached(
        query: str,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        credentials_json_str: Optional[str] = None,
        credentials_path: Optional[str] = None,
    ) -> pd.DataFrame:
        from google.cloud import bigquery
        from google.oauth2 import service_account

        credentials = None
        if credentials_json_str:
            try:
                info = json.loads(credentials_json_str)
                credentials = service_account.Credentials.from_service_account_info(info)
            except Exception:
                pass
        elif credentials_path and os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(credentials_path)

        client = bigquery.Client(
            project=project_id,
            credentials=credentials,
            location=location,
        )

        query_job = client.query(query)
        # Use pyarrow backend if available
        try:
            df = query_job.to_dataframe(create_bqstorage_client=True)
        except Exception:
            df = query_job.to_dataframe(create_bqstorage_client=False)

        return df

except ImportError:

    def _execute_bigquery_cached(
        query: str,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        credentials_json_str: Optional[str] = None,
        credentials_path: Optional[str] = None,
    ) -> pd.DataFrame:
        from google.cloud import bigquery
        from google.oauth2 import service_account

        credentials = None
        if credentials_json_str:
            try:
                info = json.loads(credentials_json_str)
                credentials = service_account.Credentials.from_service_account_info(info)
            except Exception:
                pass
        elif credentials_path and os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(credentials_path)

        client = bigquery.Client(
            project=project_id,
            credentials=credentials,
            location=location,
        )

        query_job = client.query(query)
        try:
            df = query_job.to_dataframe(create_bqstorage_client=True)
        except Exception:
            df = query_job.to_dataframe(create_bqstorage_client=False)

        return df


class BigQueryDataAdapter(BaseDataAdapter):
    """Data adapter for Google Cloud Platform BigQuery.
    
    Supports:
    - Custom SQL query execution or direct table introspection.
    - Multi-tiered authentication: Service account JSON file/dict, Streamlit secrets, or ADC.
    - Zero-row metadata inspection via `LIMIT 0` to prevent billable byte scans.
    - High-performance caching via `@st.cache_data(ttl=600)`.
    - Mock sandbox mode for local offline development.
    """

    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or os.getcwd()

    def _resolve_path(self, path: str) -> str:
        if not path:
            return ""
        if os.path.isabs(path):
            return path
        return os.path.normpath(os.path.join(self.base_dir, path))

    def _get_credentials_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Resolves GCP credentials across YAML config, Streamlit secrets, and environment."""
        creds_info = {
            "credentials_json_str": None,
            "credentials_path": None,
            "project_id": config.get("project_id") or config.get("project"),
        }

        # 1. Config explicit path
        raw_path = config.get("credentials_path") or config.get("key_path")
        if raw_path:
            resolved = self._resolve_path(raw_path)
            if os.path.exists(resolved):
                creds_info["credentials_path"] = resolved

        # 2. Config inline JSON
        if "credentials_json" in config:
            val = config["credentials_json"]
            creds_info["credentials_json_str"] = json.dumps(val) if isinstance(val, dict) else str(val)

        # 3. Streamlit secrets fallback
        try:
            import streamlit as st
            if "gcp_service_account" in st.secrets:
                sec = st.secrets["gcp_service_account"]
                creds_info["credentials_json_str"] = json.dumps(dict(sec))
                if not creds_info["project_id"] and "project_id" in sec:
                    creds_info["project_id"] = sec["project_id"]
            elif "bigquery" in st.secrets:
                sec = st.secrets["bigquery"]
                if not creds_info["project_id"] and "project_id" in sec:
                    creds_info["project_id"] = sec["project_id"]
        except Exception:
            pass

        # 4. Environment variable fallback
        if not creds_info["credentials_path"] and "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
            env_path = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
            if os.path.exists(env_path):
                creds_info["credentials_path"] = env_path

        return creds_info

    def _build_query(self, config: Dict[str, Any]) -> str:
        """Builds executable BigQuery SQL from config."""
        if "query" in config and config["query"].strip():
            return config["query"].strip()

        table = config.get("table")
        if table:
            tbl = table.strip()
            # Wrap table in backticks if not already formatted
            if not tbl.startswith("`"):
                tbl = f"`{tbl}`"
            limit = config.get("limit")
            limit_clause = f" LIMIT {limit}" if limit and isinstance(limit, int) else ""
            return f"SELECT * FROM {tbl}{limit_clause}"

        raise ValueError("BigQuery configuration must provide either 'query' or 'table'.")

    def _generate_mock_data(self) -> pd.DataFrame:
        """Returns synthetic enterprise GCP analytics data for testing/offline mode."""
        import numpy as np
        np.random.seed(42)
        n = 200
        regions = ["us-east1", "us-central1", "europe-west1", "asia-east1"]
        services = ["Compute Engine", "Cloud Storage", "BigQuery", "Kubernetes Engine", "Cloud Run"]
        cost_centers = ["Engineering", "Data Science", "Marketing", "Core Infrastructure"]
        
        dates = pd.date_range("2024-01-01", periods=60, freq="D")
        
        return pd.DataFrame({
            "usage_id": [f"USAGE-{i:06d}" for i in range(n)],
            "usage_date": pd.to_datetime(np.random.choice(dates, n)),
            "region": np.random.choice(regions, n),
            "service": np.random.choice(services, n),
            "cost_center": np.random.choice(cost_centers, n),
            "cost": np.random.uniform(50.0, 4500.0, n).round(2),
            "credit": np.random.uniform(0.0, 500.0, n).round(2),
            "invocations": np.random.randint(100, 50000, n),
        })

    def load_data(self, config: Dict[str, Any]) -> pd.DataFrame:
        """Execute BigQuery query and return pandas DataFrame."""
        if config.get("mock", False) or config.get("test_mode", False):
            return self._generate_mock_data()

        creds = self._get_credentials_config(config)
        query = self._build_query(config)
        location = config.get("location")

        try:
            df = _execute_bigquery_cached(
                query=query,
                project_id=creds["project_id"],
                location=location,
                credentials_json_str=creds["credentials_json_str"],
                credentials_path=creds["credentials_path"],
            )
        except Exception as e:
            # Fallback to mock data if credentials are not configured
            if not creds["credentials_path"] and not creds["credentials_json_str"] and "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
                return self._generate_mock_data()
            raise RuntimeError(f"BigQuery execution failed: {e}")

        # Date conversions
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
                if any(kw in col.lower() for kw in ["date", "timestamp", "time"]):
                    if not pd.api.types.is_datetime64_any_dtype(df[col]):
                        try:
                            df[col] = pd.to_datetime(df[col])
                        except Exception:
                            pass

        return df

    def get_columns(self, config: Dict[str, Any]) -> List[str]:
        """Zero-row schema introspection using LIMIT 0."""
        if config.get("mock", False) or config.get("test_mode", False):
            return list(self._generate_mock_data().columns)

        creds = self._get_credentials_config(config)
        base_query = self._build_query(config)
        limit_zero_query = f"SELECT * FROM ({base_query}) AS _subq LIMIT 0"
        location = config.get("location")

        try:
            df_zero = _execute_bigquery_cached(
                query=limit_zero_query,
                project_id=creds["project_id"],
                location=location,
                credentials_json_str=creds["credentials_json_str"],
                credentials_path=creds["credentials_path"],
            )
            return list(df_zero.columns)
        except Exception:
            # Fallback to mock columns
            return list(self._generate_mock_data().columns)
