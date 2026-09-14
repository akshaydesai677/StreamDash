# ⚡ Streamdash

A modern, enterprise-grade multipage Streamlit platform for building, visualizing, and running declarative YAML-driven dashboards with CSV data adapters, authentication gating, role-based access control (RBAC), an interactive visual canvas builder, and an interactive dashboard gallery.

> 📖 **Quick Start**: For complete installation and setup instructions, see [SETUP.md](SETUP.md).

---

## 🚀 Key Features

1. **Streamdash Visual Studio (`views/streamdash_builder.py`)**:
   - **Interactive Shelf-Based Canvas**: Assign Dimensions and Measures to Columns (X), Rows (Y), and Color Shelves with real-time live Plotly updates.
   - **Polymorphic Mark Selector**: Switch between Bar, Line, Area, Pie/Donut, Scatter, Box, Metric KPI, and Data Table views.
   - **Dynamic Chart Options**: Configurable bar modes (stacked/grouped/relative), orientations, line smoothing, donut hole sizes, outlier point controls, and data label formats.
   - **Dashboard-Level Filtering**: Interactively test and configure filters directly from the canvas.
   - **Multi-Widget Staging & Publishing**: Stage multiple visual worksheets into comprehensive dashboards, or append charts directly to existing dashboards.
   - **1-Click Quick Append**: Fast-append charts directly to specific dashboard tabs with automated state management and instant live preview links.

2. **Object-Oriented Chart Engine (`core/charts/`)**:
   - Clean OOP design with `BaseChart` abstract base class and polymorphic implementations:
     - `BarChart`: Horizontal/vertical, group/stack/relative, aggregations (`sum`, `mean`, `count`, `distinct_count`).
     - `LineChart`: Markers, linear/spline shapes, multi-series colors.
     - `AreaChart`: Cumulative volume, fraction/percent normalization.
     - `PieChart`: Donut/pie charts with custom hole sizes and label formatting.
     - `ScatterChart`: Multi-variable correlation with dynamic bubble sizing.
     - `BoxChart`: Statistical distributions with quartile markers and outlier points.
     - `MetricChart`: KPI scorecards with delta comparison indicators.
     - `TableChart`: Paginated interactive data table views.
   - Centralized `ChartRegistry` for dynamic registration and instantiation.

3. **Object-Oriented Filter Engine (`core/filters/`)**:
   - Extensible `BaseFilter` hierarchy with dynamic UI rendering and query application:
     - `MultiselectFilter`: Multi-value tag filtering.
     - `SelectFilter`: Single-selection dropdown with optional "All" selector.
     - `RadioFilter`: Single-choice radio buttons.
     - `CheckboxFilter`: Multi-selection checkboxes.
     - `DateRangeFilter`: Temporal boundaries with start/end date inputs.
     - `NumericRangeFilter`: Dual-handle slider for numeric bounds.
     - `SearchFilter`: Case-insensitive text search.
   - Centralized `FilterRegistry` for polymorphic filter creation and dispatch.

4. **Declarative YAML Dashboards (`dashboards/*.yml`)**:
   - Define full multi-tab or single-page dashboards in human-readable YAML.
   - Configure title, icon, category, allowed roles, KPI cards, filters, Plotly charts, and data tables.

5. **CSV Data Adapter (`adapters/csv_adapter.py`)**:
   - Extensible data layer inheriting from `BaseDataAdapter`.
   - Built-in caching (`st.cache_data`), date parsing, and dynamic in-memory filtering.

6. **Snowflake Data Adapter (`adapters/snowflake_adapter.py`)**:
   - Cloud data warehouse adapter using `snowflake-connector-python`.
   - Supports direct SQL queries or table bindings, configurable row limits, and date parsing.
   - Built-in intelligent credential resolution: YAML config, Streamlit secrets (`st.secrets["snowflake"]`), or environment variables.
   - In-memory Streamlit caching (`@st.cache_data(ttl=600)`) prevents redundant cloud warehouse roundtrips.
   - Mock/sandbox mode for testing without live Snowflake credentials (`mock: true`).

7. **GCP BigQuery Cloud Adapter (`adapters/bigquery_adapter.py`)**:
   - Enterprise cloud data warehouse adapter using `google-cloud-bigquery`.
   - Supports custom SQL queries or dataset table binding with PyArrow fast zero-copy deserialization.
   - Multi-tier credential resolution: Service account JSON file/dict, Streamlit secrets (`st.secrets["gcp_service_account"]`), or Application Default Credentials (ADC).
   - Zero-row `LIMIT 0` schema introspection prevents billable byte scans.
   - In-memory Streamlit query caching (`@st.cache_data(ttl=600)`).
   - Built-in mock sandbox mode for offline UI development.

8. **Parquet Data Adapter (`adapters/parquet_adapter.py`)**:
   - High-performance columnar data adapter for Apache Parquet files.
   - Sub-50ms query speeds on large datasets with zero text-parsing CPU overhead.
   - Column projection pruning (`columns: [...]`) to only load required metrics and dimensions into RAM.
   - Zero-copy schema introspection directly from Parquet file metadata.

9. **DuckDB Vectorized SQL Adapter (`adapters/duckdb_adapter.py`)**:
   - Vectorized, out-of-core SQL engine for querying massive datasets larger than server RAM.
   - Queries Parquet, CSV, and JSON directly on disk without full in-memory loading (`SELECT ... FROM 'data.parquet'`).
   - Supports embedded/persistent `.duckdb` databases or transient in-memory analytics.
   - Pushdown filtering and multi-threaded analytical aggregations.

10. **PyArrow SIMD CSV Optimization (`adapters/csv_adapter.py`)**:
   - Automatic PyArrow SIMD parsing engine delivering 8x–19x faster cold loads over standard CSV parsers.
   - Instant zero-copy schema introspection using `nrows=0`.
   - Column pruning (`usecols`) support to minimize memory footprint.

11. **Authentication & RBAC (`core/auth.py`, `config/access_control.yml`)**:
   - Credentials login protecting all application views.
   - Role-based permissions controlling dashboard access for `admin`, `analyst`, and `viewer`.
   - Default credentials:
     - **Admin**: `admin` / `admin` (Full access to all dashboards & builder)
     - **Analyst**: `analyst` / `analyst123` (Access to Sales & Operations, visual builder)
     - **Viewer**: `viewer` / `viewer123` (Read-only access to Sales Overview)

12. **Interactive YAML Playground (`views/playground.py`)**:
   - Live code editor with real-time YAML syntax & schema validation.
   - One-click template loader, embedded dataset inspector, and live side-by-side preview.

13. **Dashboard Gallery Portal (`views/home.py`)**:
   - Homepage presenting window preview cards for authorized dashboards.
   - Live search bar and category filtering.

---

## 📁 Project Structure

```
Streamdash/
├── app.py                      # Main application entry point & router
├── requirements.txt            # Python dependencies
├── generate_sample_data.py     # Sample data generator
├── .gitignore                  # Git ignore specifications
├── assets/
│   └── style.css               # Modern UI styling & card effects
├── config/
│   └── access_control.yml      # User accounts & role permissions
├── adapters/
│   ├── base.py                 # Abstract BaseDataAdapter
│   ├── csv_adapter.py          # PyArrow-accelerated CSV adapter
│   ├── parquet_adapter.py      # Columnar Apache Parquet adapter
│   ├── duckdb_adapter.py       # Vectorized DuckDB SQL engine adapter
│   ├── snowflake_adapter.py    # Snowflake Cloud Warehouse adapter
│   └── bigquery_adapter.py     # GCP BigQuery Cloud Warehouse adapter
├── core/
│   ├── auth.py                 # Authentication & RBAC engine
│   ├── dashboard_loader.py     # YAML scanner and parser
│   ├── renderer.py             # YAML-to-Streamlit UI renderer
│   ├── charts/                 # OOP Chart Subsystem
│   │   ├── base.py             # BaseChart ABC
│   │   ├── registry.py         # ChartRegistry
│   │   ├── barchart.py         # BarChart implementation
│   │   ├── linechart.py        # LineChart implementation
│   │   ├── areachart.py        # AreaChart implementation
│   │   ├── piechart.py         # PieChart implementation
│   │   ├── scatterchart.py     # ScatterChart implementation
│   │   ├── boxchart.py         # BoxChart implementation
│   │   ├── metricchart.py      # MetricChart implementation
│   │   └── tablechart.py       # TableChart implementation
│   └── filters/                # OOP Filter Subsystem
│       ├── base.py             # BaseFilter ABC
│       ├── registry.py         # FilterRegistry
│       ├── multiselect.py      # MultiselectFilter
│       ├── select.py           # SelectFilter
│       ├── radio.py            # RadioFilter
│       ├── checkbox.py         # CheckboxFilter
│       ├── date_range.py       # DateRangeFilter
│       ├── numeric_range.py    # NumericRangeFilter
│       └── search.py           # SearchFilter
├── dashboards/
│   ├── sales_overview.yml      # Sales & Revenue dashboard
│   ├── operations_kpi.yml      # Logistics & Operations dashboard
│   ├── customer_insights.yml   # Customer Retention & MRR dashboard
│   ├── customer_master_dashboard.yml # 25k Customer master analytics
│   ├── snowflake_analytics.yml # Snowflake Enterprise Analytics
│   ├── bigquery_analytics.yml  # GCP BigQuery Cloud Intelligence
│   ├── parquet_analytics.yml   # Parquet Big Data Hub
│   └── duckdb_analytics.yml    # DuckDB Vectorized Analytics

├── data/
│   ├── sales_data.csv          # Sample sales transactions
│   ├── sales_data.parquet      # Compressed columnar sales transactions
│   ├── operations_data.csv     # Sample logistics fulfillment
│   └── customer_data.csv       # Sample customer accounts
├── views/
│   ├── home.py                 # Gallery portal view
│   ├── login.py                # Authentication view
│   ├── dashboard_view.py       # Live dashboard renderer view
│   ├── playground.py           # Interactive YAML playground
│   └── streamdash_builder.py   # Visual Studio Canvas Builder
└── tests/
    ├── test_streamdash.py      # Automated unit test suite (16 tests)
    └── benchmark_big_data.py   # Empirical Big Data 1M row benchmark

```

---

## 🏃 Running the Application

### 1. Activate Environment
In PowerShell from the `Streamdash` directory:
```powershell
.\.venv\Scripts\activate
```

### 2. Launch Streamlit
```powershell
streamlit run app.py
```
Open **`http://localhost:8501`** in your browser.

### 3. Log In
- **Admin**: `admin` / `admin`
- **Analyst**: `analyst` / `analyst123`
- **Viewer**: `viewer` / `viewer123`

---

## 🧪 Running Unit Tests
```powershell
.\.venv\Scripts\python.exe tests/test_streamdash.py
```

---

## 👤 Author
**Akshay Desai** - [akshaydesai677@gmail.com](mailto:akshaydesai677@gmail.com)
