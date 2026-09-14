import glob
import os
from typing import Any, Dict, List, Optional
import yaml


class DashboardLoader:
    """Discovers, parses, and manages YAML dashboard configurations."""

    def __init__(self, dashboards_dir: str = None):
        if dashboards_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            dashboards_dir = os.path.join(base_dir, "dashboards")
        self.dashboards_dir = dashboards_dir
        self._cache: Dict[str, Dict[str, Any]] = {}

    def reload(self) -> Dict[str, Dict[str, Any]]:
        """Scans the dashboards directory and loads all .yml / .yaml files."""
        self._cache.clear()
        if not os.path.exists(self.dashboards_dir):
            return self._cache

        pattern = os.path.join(self.dashboards_dir, "*.y*ml")
        for filepath in glob.glob(pattern):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                    if not isinstance(config, dict):
                        continue

                    # If 'id' not explicitly provided, default to file stem
                    if "id" not in config:
                        base_stem = os.path.splitext(os.path.basename(filepath))[0]
                        config["id"] = base_stem

                    dash_id = config["id"]
                    config["_filepath"] = filepath
                    self._cache[dash_id] = config
            except Exception as e:
                print(f"Error loading dashboard config from {filepath}: {e}")

        return self._cache

    def get_all_dashboards(self) -> Dict[str, Dict[str, Any]]:
        if not self._cache:
            self.reload()
        return self._cache

    def get_dashboard(self, dashboard_id: str) -> Optional[Dict[str, Any]]:
        dashboards = self.get_all_dashboards()
        return dashboards.get(dashboard_id)

    def get_dashboards_for_role(
        self, role: str, auth_manager: Any
    ) -> List[Dict[str, Any]]:
        """Filter dashboards that the given role has access to."""
        all_dashboards = self.get_all_dashboards()
        allowed_ids = auth_manager.get_allowed_dashboards(role, list(all_dashboards.keys()))

        authorized = []
        for dash_id in allowed_ids:
            dash = all_dashboards.get(dash_id)
            if dash:
                # Also check dashboard-level roles filter if defined
                dashboard_roles = dash.get("roles")
                if dashboard_roles and role != "admin" and role not in dashboard_roles:
                    continue
                authorized.append(dash)

        # Sort alphabetically or by sort_order
        authorized.sort(key=lambda d: (d.get("sort_order", 999), d.get("title", "")))
        return authorized
