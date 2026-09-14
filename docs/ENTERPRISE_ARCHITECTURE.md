# Streamdash Enterprise Architecture & Scale-Out Guide
**Target: 100+ Concurrent Active Users • 1,000+ Declarative Dashboards**

---

## 1. Executive Summary

Streamdash is uniquely suited for massive enterprise scale because of its **declarative YAML architecture**:
- Dashboards are lightweight configuration files (~2 KB each), not heavy Python codebases.
- The core engine is stateless: rendering components are separated from data storage and warehouse computation.
- Data queries are delegated to high-performance engines (DuckDB, Parquet, Snowflake, BigQuery) rather than raw Python memory.

This blueprint details how to scale Streamdash to support **100+ simultaneous concurrent users** and **1,000+ dynamic dashboards** with sub-second response times, enterprise security, and a GitOps development workflow.

---

## 2. High-Level System Architecture

```mermaid
graph TB
    subgraph Users ["Client Layer (100+ Concurrent Users)"]
        U1[User Browser 1]
        U2[User Browser 2]
        U3[User Browser 100+]
    end

    subgraph Edge ["Edge & Ingress Layer"]
        CDN[Cloudflare / CloudFront CDN<br/>Static Assets, CSS, JS]
        LB[Application Load Balancer<br/>Sticky Sessions Enabled via Cookie]
    end

    subgraph Compute ["Compute Layer (Horizontal Cluster)"]
        C1[Streamdash Container 1<br/>2 vCPU • 4GB RAM]
        C2[Streamdash Container 2<br/>2 vCPU • 4GB RAM]
        C3[Streamdash Container N...<br/>Auto-Scaled (6-12 Replicas)]
    end

    subgraph State ["Shared State & Catalog Layer"]
        Redis[(Redis Cluster<br/>Distributed Query Cache & Sessions)]
        S3[(Object Storage / Git Volume<br/>1,000+ Dashboard YAMLs)]
    end

    subgraph Data ["Data Warehouse & Lakehouse Layer"]
        DuckDB[DuckDB Vectorized File Engine]
        Parquet[(Apache Parquet S3 Data Lake)]
        Snowflake[(Snowflake Data Cloud)]
        BigQuery[(Google Cloud BigQuery)]
    end

    Users --> CDN
    CDN --> LB
    LB -->|WebSocket / HTTP Sticky| Compute
    Compute <--> Redis
    Compute <--> S3
    Compute --> Data
```

---

## 3. Scaling to 1,000+ Dashboards

### The Challenge
Scanning and parsing 1,000 YAML files from disk on every page refresh causes file-descriptor exhaustion, disk I/O bottlenecks, and DOM bloat in the browser.

### The Solution: 3-Tier Catalog Architecture

```mermaid
flowchart LR
    Disk[1,000+ YAML Files] -->|1. Startup Fast-Index| Manifest[Lightweight In-Memory Catalog<br/>200 KB RAM]
    Manifest -->|2. Role Filtering & Search| UI[Sidebar & Gallery View<br/>Paginated: 24 / page]
    UI -->|3. On-Click Lazy Load| Renderer[Full Dashboard YAML Loaded<br/>Only for Active Dashboard]
```

#### 1. Two-Pass Metadata Manifest (Lazy Loading)
- **Pass 1 (Catalog Indexing)**: At boot, scan only the header attributes (`id`, `title`, `category`, `icon`, `roles`, `sort_order`) of each dashboard without parsing chart queries or data blocks. For 1,000 dashboards, this manifest takes **< 250 KB of RAM** and builds in **under 80ms**.
- **Pass 2 (On-Demand Parse)**: Only when a user clicks a dashboard is the full YAML parsed into the active `DashboardRenderer`.

#### 2. Gallery Pagination & Search Indexing
- The Gallery UI (`views/home.py`) uses client-side or server-side pagination (e.g. 24 dashboards per page) with real-time text indexing across `title`, `description`, and `category`.
- The Sidebar shows **Recent Dashboards** (last 8 accessed by user) plus a modal search bar to prevent rendering 1,000 DOM buttons.

#### 3. Shared Catalog Storage
- Store dashboard YAMLs on a shared network file mount (AWS EFS, GCP Cloud Filestore) or sync automatically from an S3/GCS bucket or Git repository.

---

## 4. Scaling to 100+ Concurrent Active Users

### Streamlit Concurrency Realities
- Streamlit runs in Python's asyncio event loop with a thread-pool for script execution.
- A single Streamlit process handles **15 to 25 active concurrent users** before Python GIL contention and memory locks degrade interactive latency.
- **Formula for 100+ Concurrent Users**:
  $$\text{Replicas} = \frac{100\text{ concurrent users}}{15\text{ users/container}} \approx 7 \text{ to } 10 \text{ containers}$$

### Deployment Topology
- **Container Sizing**: 2 vCPU, 4 GB RAM per container.
- **Autoscaling Policy**: Scale based on CPU utilization (> 65%) or active WebSocket connection count:
  - Minimum replicas: 6
  - Maximum replicas: 15
- **Sticky Sessions (MANDATORY)**:
  - Streamlit requires persistent WebSocket connections.
  - The Load Balancer (ALB / Ingress-NGINX / Cloud Run) **must enable Cookie-Based Session Stickiness** (`affinity-cookie`, TTL 12 hours).

```nginx
# Example NGINX Ingress configuration for Streamdash
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: streamdash-ingress
  annotations:
    nginx.ingress.kubernetes.io/affinity: "cookie"
    nginx.ingress.kubernetes.io/session-cookie-name: "streamdash_route"
    nginx.ingress.kubernetes.io/session-cookie-expires: "43200"
    nginx.ingress.kubernetes.io/websocket-services: "streamdash-service"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
```

---

## 5. High-Performance Caching Architecture

| Caching Layer | Technology | Lifetime | Purpose |
| :--- | :--- | :--- | :--- |
| **Layer 1: Browser** | HTTP Cache / ServiceWorker | 7 days | Static CSS, JS, Fonts, Brand Logos |
| **Layer 2: Local Memory** | `@st.cache_data` | 10–60 min | In-container query results & computed Plotly specs |
| **Layer 3: Distributed Cache** | Redis Cluster | 2–24 hours | Pre-aggregated cross-user metrics, dataset schemas |
| **Layer 4: Data Engine Cache** | Snowflake / BigQuery / DuckDB | Native | Warehouse query result reuse (zero warehouse credit burn) |

---

## 6. Development Workflow (GitOps Lifecycle)

```mermaid
sequenceDiagram
    autonumber
    actor Analyst as Analyst / Developer
    participant Studio as Streamdash Visual Studio
    participant Git as GitHub / GitLab (Repo)
    participant CI as CI/CD Pipeline (Actions)
    participant Stage as Staging Cluster
    participant Prod as Production Cluster (100+ Users)

    Analyst->>Studio: Design chart, configure filters & KPI cards
    Studio->>Git: Push dashboard YAML to feature branch
    Git->>CI: Trigger Automated Linting & Unit Tests
    CI->>CI: Validate YAML schema against test_streamdash.py
    CI->>Stage: Deploy preview environment
    Analyst->>Stage: Verify visual rendering & drill-downs
    Analyst->>Git: Open Pull Request & Merge to main
    Git->>CI: Trigger Zero-Downtime Production Sync
    CI->>Prod: Hot-reload catalog volume (No pod restarts required)
    Prod-->>Analyst: Dashboard immediately live to authorized roles
```

### Key Principles:
1. **Zero-Code Contributions**: Business analysts create dashboards via the **Visual Builder** and save directly to YAML.
2. **Automated CI Validation**: `python tests/test_streamdash.py` runs on every Pull Request, validating:
   - Valid YAML syntax and mandatory fields (`id`, `title`, `data_source`).
   - Data adapter connectivity and schema compatibility.
   - User role permissions.
3. **Zero-Downtime Publishing**: Because configurations are loaded dynamically, new dashboards go live instantly without restarting Streamlit servers.

---

## 7. Recommended Production Tech Stack

| Component | Recommended Tooling | Cost-Effective Alternative |
| :--- | :--- | :--- |
| **Container Platform** | AWS ECS Fargate / Google Cloud Run | Docker Swarm / Single High-Spec VM |
| **Orchestration** | Kubernetes (EKS / GKE) | Nomad |
| **Load Balancer** | AWS Application Load Balancer (ALB) | Nginx / Traefik with sticky sessions |
| **Dashboard Storage** | AWS S3 + Mountpoint / Git Sync | Managed NFS (EFS / Filestore) |
| **Data Engine** | DuckDB + Parquet (Lakehouse) | PostgreSQL / SQLite |
| **Cloud Warehouse** | Snowflake / GCP BigQuery | ClickHouse |
| **Distributed Cache** | AWS ElastiCache Redis | KeyDB / In-memory |
| **Authentication** | Okta / Azure AD / Auth0 (SAML/OIDC) | Streamdash Native RBAC |

---

## 8. Summary Checklist for 100+ Users & 1,000+ Dashboards

- [x] **Recent Dashboards Tracking**: Sidebar displays user's 8 most recent dashboards with search modal.
- [x] **PyArrow & Parquet Acceleration**: Sub-50ms reads on compressed datasets.
- [x] **Vectorized Pushdown**: DuckDB, Snowflake, and BigQuery execute compute out-of-core.
- [ ] **Sticky Sessions Configured**: Ensure ALB / NGINX routes WebSocket connections to the same container.
- [ ] **Horizontal Pod Autoscaling**: Min 6, Max 15 replicas based on CPU & WebSocket connections.
- [ ] **GitOps Sync**: Automated webhook or volume mount to sync `dashboards/*.yml` into production containers.
