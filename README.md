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

6. **Authentication & RBAC (`core/auth.py`, `config/access_control.yml`)**:
   - Credentials login protecting all application views.
   - Role-based permissions controlling dashboard access for `admin`, `analyst`, and `viewer`.
   - Default credentials:
     - **Admin**: `admin` / `admin` (Full access to all dashboards & builder)
     - **Analyst**: `analyst` / `analyst123` (Access to Sales & Operations, visual builder)
     - **Viewer**: `viewer` / `viewer123` (Read-only access to Sales Overview)

7. **Interactive YAML Playground (`views/playground.py`)**:
   - Live code editor with real-time YAML syntax & schema validation.
   - One-click template loader, embedded dataset inspector, and live side-by-side preview.

8. **Dashboard Gallery Portal (`views/home.py`)**:
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
│   └── csv_adapter.py          # CSV Data Adapter implementation
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
│   └── customer_insights.yml   # Customer Retention & MRR dashboard
├── data/
│   ├── sales_data.csv          # Sample sales transactions
│   ├── operations_data.csv     # Sample logistics fulfillment
│   └── customer_data.csv       # Sample customer accounts
├── views/
│   ├── home.py                 # Gallery portal view
│   ├── login.py                # Authentication view
│   ├── dashboard_view.py       # Live dashboard renderer view
│   ├── playground.py           # Interactive YAML playground
│   └── streamdash_builder.py   # Visual Studio Canvas Builder
└── tests/
    └── test_streamdash.py      # Automated unit test suite
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
