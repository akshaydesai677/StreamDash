import os
import sys
import unittest

# Ensure Streamdash root is on path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from core.auth import AuthManager
from core.dashboard_loader import DashboardLoader
from adapters.csv_adapter import CSVDataAdapter
from core.renderer import compute_aggregation, format_metric_value


class TestStreamdashCore(unittest.TestCase):

    def setUp(self):
        self.auth_manager = AuthManager()
        self.dashboard_loader = DashboardLoader()
        self.csv_adapter = CSVDataAdapter(base_dir=BASE_DIR)

    def test_01_admin_authentication(self):
        user = self.auth_manager.authenticate("admin", "admin")
        self.assertIsNotNone(user, "Admin login with 'admin'/'admin' must succeed")
        self.assertEqual(user["role"], "admin")
        self.assertEqual(user["username"], "admin")

    def test_02_invalid_authentication(self):
        user = self.auth_manager.authenticate("admin", "wrong_password")
        self.assertIsNone(user, "Authentication with wrong password must fail")

        non_user = self.auth_manager.authenticate("unknown_user", "admin")
        self.assertIsNone(non_user, "Authentication with non-existent user must fail")

    def test_03_dashboard_loading(self):
        dashboards = self.dashboard_loader.get_all_dashboards()
        self.assertGreaterEqual(len(dashboards), 3, "At least 3 dashboards should be discovered")
        self.assertIn("sales_overview", dashboards)
        self.assertIn("operations_kpi", dashboards)
        self.assertIn("customer_insights", dashboards)

    def test_04_role_based_access_control(self):
        # Admin gets all
        admin_dashboards = self.dashboard_loader.get_dashboards_for_role("admin", self.auth_manager)
        admin_ids = [d["id"] for d in admin_dashboards]
        self.assertIn("sales_overview", admin_ids)
        self.assertIn("operations_kpi", admin_ids)
        self.assertIn("customer_insights", admin_ids)

        # Analyst gets sales & operations
        analyst_dashboards = self.dashboard_loader.get_dashboards_for_role("analyst", self.auth_manager)
        analyst_ids = [d["id"] for d in analyst_dashboards]
        self.assertIn("sales_overview", analyst_ids)
        self.assertIn("operations_kpi", analyst_ids)
        self.assertNotIn("customer_insights", analyst_ids)

        # Viewer gets only sales
        viewer_dashboards = self.dashboard_loader.get_dashboards_for_role("viewer", self.auth_manager)
        viewer_ids = [d["id"] for d in viewer_dashboards]
        self.assertIn("sales_overview", viewer_ids)
        self.assertNotIn("operations_kpi", viewer_ids)
        self.assertNotIn("customer_insights", viewer_ids)

    def test_05_csv_data_adapter(self):
        sales_dash = self.dashboard_loader.get_dashboard("sales_overview")
        self.assertIsNotNone(sales_dash)
        df = self.csv_adapter.load_data(sales_dash["data_source"])
        self.assertFalse(df.empty, "Sales data should have records")
        self.assertIn("Revenue", df.columns)
        self.assertIn("Region", df.columns)

        # Test filtering
        regions = df["Region"].unique()
        selected_region = regions[0]
        filtered_df = self.csv_adapter.filter_data(df, {"Region": [selected_region]})
        self.assertEqual(len(filtered_df[filtered_df["Region"] != selected_region]), 0)

    def test_06_aggregations_and_formatting(self):
        sales_dash = self.dashboard_loader.get_dashboard("sales_overview")
        df = self.csv_adapter.load_data(sales_dash["data_source"])
        
        total_rev = compute_aggregation(df, "Revenue", "sum")
        self.assertGreater(total_rev, 0)

        fmt_rev = format_metric_value(total_rev, fmt="currency")
        self.assertTrue(fmt_rev.startswith("$"))

        margin_avg = compute_aggregation(df, "Profit_Margin", "mean")
        fmt_margin = format_metric_value(margin_avg, fmt="percent")
        self.assertTrue(fmt_margin.endswith("%"))

    def test_07_playground_yaml_validation(self):
        from views.playground import validate_dashboard_yaml, BLANK_TEMPLATE

        # 1. Valid template test
        is_valid, msg, parsed = validate_dashboard_yaml(BLANK_TEMPLATE)
        self.assertTrue(is_valid, f"Template should be valid: {msg}")
        self.assertEqual(parsed["id"], "my_custom_dashboard")

        # 2. Syntax error test
        invalid_yaml = "id: test\n  bad_indent: 123\n wrong_key: [}"
        is_valid, msg, _ = validate_dashboard_yaml(invalid_yaml)
        self.assertFalse(is_valid)

        # 3. Missing required key test
        missing_keys_yaml = "id: test\ndescription: missing title and data_source"
        is_valid, msg, _ = validate_dashboard_yaml(missing_keys_yaml)
        self.assertFalse(is_valid)
        self.assertIn("Missing required", msg)

    def test_08_tabbed_dashboard_support(self):
        sales_dash = self.dashboard_loader.get_dashboard("sales_overview")
        self.assertIsNotNone(sales_dash)
        self.assertIn("tabs", sales_dash, "sales_overview should define tabs")
        tabs = sales_dash["tabs"]
        self.assertGreaterEqual(len(tabs), 2, "sales_overview should contain multiple tabs")

        # Verify tabs structure
        tab_titles = [t.get("title") for t in tabs]
        self.assertTrue(any("Executive Summary" in t for t in tab_titles))
        self.assertTrue(any("Transaction Records" in t for t in tab_titles))

    def test_09_visual_builder_module(self):
        from views.visual_builder import get_available_csvs
        csvs = get_available_csvs()
        self.assertGreaterEqual(len(csvs), 1, "Visual builder should discover available CSVs")

    def test_10_streamdash_builder(self):
        import pandas as pd
        import yaml
        from views.streamdash_builder import categorize_fields, generate_streamdash_yaml

        df = pd.read_csv("data/sales_data.csv")
        dims, meas = categorize_fields(df)
        self.assertIn("Region", dims)
        self.assertIn("Revenue", meas)

        # Generate YAML and validate schema
        raw_yaml = generate_streamdash_yaml(df)
        parsed = yaml.safe_load(raw_yaml)
        self.assertIn("id", parsed)
        self.assertIn("tabs", parsed)
        self.assertIn("data_source", parsed)

    def test_11_dimension_metrics_and_theming(self):
        import pandas as pd
        from core.renderer import compute_aggregation, PALETTES

        df = pd.read_csv("data/sales_data.csv")
        # Count non-numeric dimension column
        count_region = compute_aggregation(df, "Region", "count")
        self.assertEqual(count_region, len(df))

        # Distinct count of non-numeric dimension column
        nunique_region = compute_aggregation(df, "Region", "distinct_count")
        self.assertEqual(nunique_region, df["Region"].nunique())

        # Verify palettes
        self.assertIn("streamdash", PALETTES)
        self.assertIn("emerald", PALETTES)
        self.assertIn("sunset", PALETTES)
        self.assertIn("ocean", PALETTES)

    def test_12_oop_filters_and_charts(self):
        import pandas as pd
        from core.filters.registry import FilterRegistry
        from core.charts.registry import ChartRegistry

        df = pd.read_csv("data/sales_data.csv")

        # 1. FilterRegistry tests
        fltr_types = [t["type"] for t in FilterRegistry.list_types()]
        self.assertIn("multiselect", fltr_types)
        self.assertIn("selectbox", fltr_types)
        self.assertIn("radio", fltr_types)
        self.assertIn("checkbox", fltr_types)
        self.assertIn("slider", fltr_types)
        self.assertIn("search", fltr_types)
        self.assertIn("date_range", fltr_types)

        # Test MultiselectFilter apply
        m_filter = FilterRegistry.create({"type": "multiselect", "column": "Region"})
        filtered_df = m_filter.apply(df, ["North America"])
        self.assertTrue((filtered_df["Region"] == "North America").all())

        # Test RadioFilter apply
        r_filter = FilterRegistry.create({"type": "radio", "column": "Region"})
        filtered_radio = r_filter.apply(df, "Europe")
        self.assertTrue((filtered_radio["Region"] == "Europe").all())

        # Test CheckboxFilter apply
        cb_filter = FilterRegistry.create({"type": "checkbox", "column": "Region"})
        filtered_cb = cb_filter.apply(df, ["Europe", "Latin America"])
        self.assertTrue(filtered_cb["Region"].isin(["Europe", "Latin America"]).all())

        # Test SearchFilter apply
        s_filter = FilterRegistry.create({"type": "search", "column": "Region"})
        filtered_search = s_filter.apply(df, "North")
        self.assertTrue((filtered_search["Region"] == "North America").all())

        # Test SliderFilter apply
        num_filter = FilterRegistry.create({"type": "slider", "column": "Revenue"})
        filtered_num = num_filter.apply(df, (20000, 40000))
        self.assertTrue((filtered_num["Revenue"] >= 20000).all())
        self.assertTrue((filtered_num["Revenue"] <= 40000).all())

        # 2. ChartRegistry tests
        chart_types = [c["type"] for c in ChartRegistry.list_types()]
        self.assertIn("bar", chart_types)
        self.assertIn("line", chart_types)
        self.assertIn("pie", chart_types)
        self.assertIn("scatter", chart_types)
        self.assertIn("box", chart_types)
        self.assertIn("area", chart_types)

        # Verify dynamic configurable properties
        bar_cls = ChartRegistry.get("bar")
        bar_props = bar_cls.get_configurable_properties()
        bar_prop_names = [p["name"] for p in bar_props]
        self.assertIn("barmode", bar_prop_names)
        self.assertIn("orientation", bar_prop_names)

        pie_cls = ChartRegistry.get("pie")
        pie_props = pie_cls.get_configurable_properties()
        pie_prop_names = [p["name"] for p in pie_props]
        self.assertIn("hole", pie_prop_names)


if __name__ == "__main__":
    unittest.main()


