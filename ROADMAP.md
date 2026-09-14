# 🗺️ Streamdash Product & Engineering Roadmap

This document outlines the strategic engineering roadmap for Streamdash, detailing key architectural features, their business motivations, and concrete technical implementation plans.

---

## Roadmap Summary

| # | Initiative | Category | Target Release | Status |
| :-: | :--- | :--- | :-: | :-: |
| **1** | [OAuth 2.0 with Microsoft Entra ID (Azure AD)](#1-oauth-20-with-microsoft-entra-id-azure-ad) | Enterprise Security | v1.1.0 | Planned |
| **2** | [Easy Setup Guide for Open Source Enterprise](#2-easy-setup-guide-for-open-source-enterprise) | DevOps & Deployment | v1.1.0 | In Progress |
| **3** | [Dataset Research Mode & YData Profiling](#3-dataset-research-mode--ydata-profiling) | Advanced Analytics | v1.2.0 | Planned |
| **4** | [Dashboard Recommendation Engine](#4-dashboard-recommendation-engine) | Personalization & UX | v1.2.0 | Planned |
| **5** | [Strict User & Role Separation (RBAC + RLS)](#5-strict-user--role-separation-rbac--rls) | Security & Governance | v1.2.0 | Planned |
| **6** | [Enrich Map-Type Charts (Choropleth & ScatterGeo)](#6-enrich-map-type-charts-geospatial-analytics) | Visualization | v1.3.0 | Planned |
| **7** | [Declarative Chart & Dashboard Contracts](#7-declarative-chart--dashboard-contracts) | Quality & Reliability | v1.3.0 | Planned |
| **8** | [KPI Notification Triggers & Automated Alerting](#8-kpi-notification-triggers--automated-alerting) | Observability & Action | v1.4.0 | Planned |
| **9** | [Advanced Chart Sizing & Responsive Grid Control](#9-advanced-chart-sizing--responsive-grid-control) | UI / Layout Engine | v1.4.0 | Planned |
| **10** | [Automated Rules Miner (Association Mining)](#10-automated-rules-miner-association-mining) | Automated Intelligence | v1.5.0 | Planned |
| **11** | [Outlier Detection & Anomaly Highlighter](#11-outlier-detection--anomaly-highlighter) | Statistical ML | v1.5.0 | Planned |

---

## Detailed Implementation Plans

### 1. OAuth 2.0 with Microsoft Entra ID (Azure AD)
* **Goal**: Enable seamless corporate Single Sign-On (SSO) so employees sign in using corporate Microsoft 365 accounts with zero password sharing.
* **How We Will Implement**:
  - Integrate `msal-python` (Microsoft Authentication Library) within `core/auth.py` to handle the OAuth2 authorization code flow with PKCE.
  - Store configuration in `.streamlit/secrets.toml`:
    ```toml
    [azure_ad]
    client_id = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    client_secret = "..."
    tenant_id = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    redirect_uri = "https://analytics.yourcompany.com/oauth2callback"
    ```
  - Map Entra ID Security Groups directly to Streamdash roles (`admin`, `analyst`, `viewer`) extracted from the decoded JWT claims (`groups` claim).
  - Persist encrypted session tokens in secure HTTP-only cookies to support load-balanced cluster environments.

---

### 2. Easy Setup Guide for Open Source Enterprise
* **Goal**: Provide a turnkey, production-ready on-premise / bare-metal deployment stack with zero cloud licensing fees.
* **How We Will Implement**:
  - Deliver a dedicated `docs/OPEN_SOURCE_ENTERPRISE.md` guide and accompanying `deploy/docker-compose.enterprise.yml`.
  - Package an automated multi-service topology:
    - **Streamdash Application Workers**: Multi-container setup with auto-restarts.
    - **Traefik Reverse Proxy**: Automatic Let's Encrypt SSL certificates and WebSocket sticky-session routing.
    - **KeyDB / Redis**: Shared distributed cache for query results.
    - **MinIO**: High-speed S3-compatible data lake storage for Parquet files.
  - Include bash/PowerShell deployment scripts (`deploy.sh`, `deploy.ps1`) for single-command provisioning.

---

### 3. Dataset Research Mode & YData Profiling
* **Goal**: Give data analysts instant deep-dive exploratory data analysis (EDA) and automated data profiling for any active dataset.
* **How We Will Implement**:
  - Create a new view: `views/dataset_research.py` ("Research Studio") accessible from the sidebar.
  - Integrate `ydata-profiling` in headless mode to compute comprehensive dataset diagnostics:
    - Missing value heatmaps and cardinality ratios.
    - Pearson, Spearman, and Kendall tau correlation matrices with interactive heatmaps.
    - Distribution skewness, quantile metrics, and high-correlation warnings.
  - Cache generated profiles via `@st.cache_data(ttl=3600)` to ensure instantaneous subsequent visits.
  - Provide 1-click export of data health reports to HTML and JSON.

---

### 4. Dashboard Recommendation Engine
* **Goal**: Surface the most relevant analytics to users automatically, reducing discovery fatigue across 1,000+ dashboards.
* **How We Will Implement**:
  - **Engagement Tracker**: Record lightweight telemetry in session state/Redis (dashboard opens, time spent, filter interactions).
  - **Collaborative & Content Filtering Algorithm**:
    - *Role Affinity*: Dashboards most frequently accessed by users sharing the same role.
    - *Data Lineage Similarity*: If a user frequently analyzes `customer_data.csv`, recommend other dashboards utilizing the same data source.
    - *Trending*: Boards with the highest velocity of views in the last 7 days.
  - **UI Integration**: Render personalized `"Recommended for You"` and `"Trending Dashboards"` carousels at the top of `views/home.py`.

---

### 5. Strict User & Role Separation (RBAC + RLS)
* **Goal**: Decouple identity from permissions for enterprise governance, auditing, and multi-tenant security.
* **How We Will Implement**:
  - Modernize `config/access_control.yml` and `core/auth.py` into a relational model:
    - **Users**: Identity records (`id`, `username`, `email`, `assigned_roles`).
    - **Roles**: Permission sets (`id`, `role_name`, `permissions`, `allowed_dashboards`, `row_filters`).
    - **Permissions**: Granular actions (`dashboards.view`, `dashboards.create`, `dashboards.edit`, `data.export_raw`, `admin.manage_users`).
  - **Row-Level Security (RLS)**: Support dynamic role data filters:
    ```yaml
    roles:
      emea_analyst:
        permissions: ["dashboards.view"]
        row_level_filters:
          region: "EMEA"
    ```
    The data engine automatically injects `WHERE region = 'EMEA'` into all underlying queries.

---

### 6. Enrich Map-Type Charts (Geospatial Analytics)
* **Goal**: Provide native geographic charts to visualize territory sales, logistics fulfillment, and regional performance.
* **How We Will Implement**:
  - Extend the OOP Chart subsystem (`core/charts/`) with three new chart classes:
    - `ChoroplethChart` (`choropleth`): Boundary maps filled with metric heat gradients for ISO countries, US states, and custom GeoJSON shapes.
    - `ScatterGeoChart` (`scatter_geo`): Latitude/longitude bubble plots where marker size maps to metric volume (e.g. Revenue) and marker color maps to status.
    - `DensityMapboxChart` (`density_mapbox`): High-speed GPU-accelerated heatmaps for dense geospatial coordinate clusters.
  - Register in `ChartRegistry` with dynamic controls in the **Visual Studio Builder**.

---

### 7. Declarative Chart & Dashboard Contracts
* **Goal**: Enforce strict schema validation so malformed YAML or missing database columns fail fast with helpful error messages rather than breaking the UI.
* **How We Will Implement**:
  - Implement Pydantic v2 validation contracts in `core/contracts/`:
    - `DashboardContract`: Validates `id`, `title`, and verified `data_source` keys.
    - `ChartContract`: Validates that `x`, `y`, `color`, and `agg` columns actually exist in the target dataset schema before rendering.
    - `FilterContract`: Ensures filter column types match target column data types.
  - **CI Linter Tool**: Provide a CLI command (`python -m core.linter dashboards/*.yml`) integrated into GitHub Actions to block pull requests with invalid configurations.

---

### 8. KPI Notification Triggers & Automated Alerting
* **Goal**: Proactively alert stakeholders when business metrics breach defined thresholds without requiring manual dashboard checks.
* **How We Will Implement**:
  - Support declarative alert definitions in dashboard YAML:
    ```yaml
    alerts:
      - id: "revenue_drop_alert"
        metric: "Revenue"
        condition: "< 25000"
        schedule: "hourly"
        channels: ["slack", "email", "webhook"]
    ```
  - Implement a background scheduler worker (`core/alerts/worker.py`) using lightweight timer polling or cron.
  - Add dispatch adapters for **Slack Webhooks**, **Microsoft Teams Webhooks**, and **SMTP Email** with direct links back to the active dashboard view.

---

### 9. Advanced Chart Sizing & Responsive Grid Control
* **Goal**: Provide fine-grained control over chart heights, aspect ratios, and responsive multi-column layouts across desktop, tablet, and mobile.
* **How We Will Implement**:
  - Upgrade the grid engine in `core/renderer.py` from basic 2-column layouts to a flexible **12-column responsive grid**:
    ```yaml
    charts:
      - id: "revenue_chart"
        col_span: 8            # 8 of 12 columns on desktop, full width on mobile
        height: 420            # Pixel height override
        aspect_ratio: "16:9"   # Dynamic aspect ratio
    ```
  - Implement CSS Container Queries (`@container`) in `assets/style.css` so chart fonts, legends, and axis labels automatically adapt to their allocated card width.

---

### 10. Automated Rules Miner (Association Mining)
* **Goal**: Surface hidden business insights automatically (e.g. *"Customers in the East Region purchasing Enterprise tiers have 3.8x higher renewal rates"*).
* **How We Will Implement**:
  - Create `core/analytics/rules_miner.py` implementing the FP-Growth / Apriori association algorithm.
  - Automatically discretize continuous numerical metrics into quantile buckets (`High`, `Medium`, `Low`).
  - Compute **Support**, **Confidence**, and **Lift** metrics across multi-dimensional feature combinations.
  - Add a `"Smart Insights"` drawer in the UI displaying top-ranked rules with a 1-click `"Apply as Filter"` button.

---

### 11. Outlier Detection & Anomaly Highlighter
* **Goal**: Automatically detect and visually highlight anomalies in charts and KPI metric cards.
* **How We Will Implement**:
  - Implement statistical and machine-learning outlier detectors in `core/analytics/anomaly.py`:
    - **Z-Score & IQR (Interquartile Range)**: Flags extreme variance on categorical and distribution charts.
    - **Isolation Forest**: Detects multi-dimensional multivariate outliers across paired metrics.
    - **Seasonal-Trend Decomposition (STL)**: Flags sudden unexpected spikes or dips in time-series data.
  - **Visual Highlighting**:
    - Time-series & scatter points identified as anomalies render with glowing red halos or alert badges.
    - KPI metric cards display a badge (`⚠️ +3.2σ Spiking`) when current metrics diverge significantly from historical baselines.
