import os
from typing import Any, Dict, List, Optional
import yaml

try:
    import streamlit as st
except ImportError:
    st = None


class AuthManager:
    """Manages user authentication and role-based permissions from access_control.yml."""

    def __init__(self, config_path: str = None):
        if config_path is None:
            # Default to config/access_control.yml relative to project root
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_dir, "config", "access_control.yml")
        self.config_path = config_path
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Access control config not found at {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def reload(self):
        """Reload configuration from file."""
        self._config = self._load_config()

    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Validate user credentials against configured users."""
        users = self._config.get("users", [])
        for u in users:
            if u.get("username") == username and str(u.get("password")) == str(password):
                # Return sanitized user record without password
                return {
                    "username": u.get("username"),
                    "role": u.get("role", "viewer"),
                    "display_name": u.get("display_name", username),
                    "email": u.get("email", ""),
                    "avatar": u.get("avatar", "👤"),
                }
        return None

    def get_role_info(self, role: str) -> Dict[str, Any]:
        roles = self._config.get("roles", {})
        return roles.get(role, {"name": role, "allowed_dashboards": []})

    def get_allowed_dashboards(self, role: str, all_dashboard_ids: List[str]) -> List[str]:
        """Return dashboard IDs that the given role is authorized to view."""
        role_info = self.get_role_info(role)
        allowed = role_info.get("allowed_dashboards", [])
        if "*" in allowed:
            return list(all_dashboard_ids)
        return [dash_id for dash_id in all_dashboard_ids if dash_id in allowed]

    def has_dashboard_access(self, role: str, dashboard_id: str) -> bool:
        """Check if role can view specific dashboard ID."""
        role_info = self.get_role_info(role)
        allowed = role_info.get("allowed_dashboards", [])
        return "*" in allowed or dashboard_id in allowed


# Streamlit session state integration helpers
def init_auth_state():
    """Ensure session state variables for authentication exist."""
    if st is None:
        return
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "current_page" not in st.session_state:
        st.session_state.current_page = "home"
    if "active_dashboard_id" not in st.session_state:
        st.session_state.active_dashboard_id = None


def is_authenticated() -> bool:
    if st is None:
        return False
    return st.session_state.get("authenticated", False)


def get_current_user() -> Optional[Dict[str, Any]]:
    if st is None:
        return None
    return st.session_state.get("user")


def login_user(user_data: Dict[str, Any]):
    if st is None:
        return
    st.session_state.authenticated = True
    st.session_state.user = user_data
    st.session_state.current_page = "home"


def logout_user():
    if st is None:
        return
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.active_dashboard_id = None
    st.session_state.current_page = "login"
