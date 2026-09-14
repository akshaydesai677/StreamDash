# 🛠️ Streamdash Setup & Installation Guide

Comprehensive instructions for setting up, configuring, and running **Streamdash** on Windows, macOS, or Linux.

---

## 📋 Prerequisites

Ensure the following tools are installed on your machine:

* **Python 3.10 or higher** (Python 3.10, 3.11, or 3.12 recommended).
  * Check version: `python --version`
* **Git**:
  * Check version: `git --version`
* A web browser (Google Chrome, Microsoft Edge, Firefox, or Safari).

---

## 🚀 Step-by-Step Installation

### 1. Clone the Repository

Open your terminal or PowerShell and clone the project:

```bash
git clone https://github.com/akshaydesai677/StreamDash.git
cd StreamDash
```

---

### 2. Create and Activate a Virtual Environment

Isolate project dependencies using Python's built-in `venv`:

#### Windows (PowerShell):
```powershell
# Create virtual environment
python -m venv .venv

# If PowerShell script execution is restricted, run:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Activate environment
.\.venv\Scripts\Activate.ps1
```

#### Windows (Command Prompt `cmd.exe`):
```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

#### macOS / Linux (Bash or Zsh):
```bash
python3 -m venv .venv
source .venv/bin/activate
```

*(You should now see `(.venv)` in your terminal prompt).*

---

### 3. Install Dependencies

Install all required Python packages specified in `requirements.txt`:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Included Core Libraries:
* **`streamlit>=1.36.0`**: Core multi-page web application framework.
* **`pyyaml>=6.0`**: Fast parser for declarative YAML dashboard specs.
* **`pandas>=2.0.0`**: High-performance data manipulation and aggregation.
* **`plotly>=5.18.0`**: Interactive charting and visual analytics engine.

---

### 4. (Optional) Generate or Refresh Sample Datasets

Streamdash comes preloaded with three realistic enterprise datasets in `data/`:
* `data/sales_data.csv` (1,000 transaction records)
* `data/operations_data.csv` (800 logistics fulfillment orders)
* `data/customer_data.csv` (300 customer accounts & MRR metrics)

If you ever want to regenerate or customize the sample datasets, run:

```bash
python generate_sample_data.py
```

---

## 🏃 Running the Application

Start the local Streamlit server:

```bash
streamlit run app.py
```

Streamdash will launch and automatically open your default browser at:
👉 **`http://localhost:8501`**

To specify a custom port:
```bash
streamlit run app.py --server.port 8080
```

---

## 🔐 Default User Roles & Credentials

Streamdash includes built-in credentials authentication and Role-Based Access Control (RBAC):

| Role | Username | Password | Dashboard Permissions | Capabilities |
| :--- | :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `admin` | Full access to all dashboards | Gallery, Visual Studio, Playground, Publishing, Role Management |
| **Analyst** | `analyst` | `analyst123` | Sales Overview, Operations KPI | Gallery, Visual Studio, Live Analytics |
| **Viewer** | `viewer` | `viewer123` | Sales Overview only | Read-only access to authorized dashboards |

---

## ⚙️ Configuration & Customization

### Managing Users & Roles (`config/access_control.yml`)
To add a new user or modify role permissions, edit `config/access_control.yml`:

```yaml
users:
  - username: "new_analyst"
    password: "secure_password"
    role: "analyst"
    name: "Alex Taylor"

roles:
  analyst:
    allowed_dashboards:
      - "sales_overview"
      - "operations_kpi"
      - "customer_insights"
```

### Adding New Datasets (CSV)
1. Drop any CSV file into the `data/` folder (e.g. `data/finance_q4.csv`).
2. Open the **Streamdash Visual Studio** in the app.
3. Select `finance_q4.csv` from the **Active Dataset** dropdown to begin building charts immediately.

### Connecting to Snowflake Data Warehouse
Streamdash includes a native Snowflake Data Adapter. You can connect to Snowflake either via dashboard YAML files or via Streamlit secrets.

#### Option A: In Dashboard YAML (`dashboards/my_snowflake_dashboard.yml`)
```yaml
data_source:
  type: "snowflake"
  account: "xy12345.us-east-1"      # Or use ${SNOWFLAKE_ACCOUNT}
  user: "ANALYTICS_USER"
  password: "${SNOWFLAKE_PASSWORD}"  # Injected from environment variable
  warehouse: "COMPUTE_WH"
  database: "ANALYTICS_DB"
  schema: "PUBLIC"
  role: "ANALYST_ROLE"
  query: "SELECT ID, REGION, REVENUE, TRANSACTION_DATE FROM SALES_ANALYTICS"
  date_columns: ["TRANSACTION_DATE"]
  cache_ttl: 600                     # Cache query results for 10 minutes
```

#### Option B: Via Streamlit Secrets (`.streamlit/secrets.toml`)
```toml
[snowflake]
account = "xy12345.us-east-1"
user = "ANALYTICS_USER"
password = "my_secret_password"
warehouse = "COMPUTE_WH"
database = "ANALYTICS_DB"
schema = "PUBLIC"
```
When configured in `secrets.toml`, your dashboard YAML only needs:
```yaml
data_source:
  type: "snowflake"
  query: "SELECT * FROM my_table"
```

---

## 🧪 Running Automated Tests

Streamdash includes an automated unit test suite verifying:
* CSV data loading and date parsing.
* Aggregation calculations (`sum`, `mean`, `count`, `distinct_count`, `min`, `max`, `median`).
* Metric delta comparisons.
* Role-based access filtering.
* Custom dashboard YAML generation and validation.
* Filter subsystem dynamic query handling.

Run tests with:

```bash
python tests/test_streamdash.py
```

Expected output:
```
----------------------------------------------------------------------
Ran 12 tests in 0.25s

OK
```

---

## ❓ Troubleshooting & FAQs

### 1. PowerShell Script Execution Error
**Error**: `...execution of scripts is disabled on this system.`
**Solution**:
Run the following in PowerShell before activating:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 2. Port 8501 Already in Use
**Solution**:
Launch on an alternate port:
```powershell
streamlit run app.py --server.port 8502
```

### 3. ModuleNotFoundError
**Solution**:
Ensure your virtual environment is active (`(.venv)` visible in prompt) and run:
```powershell
pip install -r requirements.txt
```

---

## 👤 Author & Support
* **Author**: Akshay Desai
* **Email**: [akshaydesai677@gmail.com](mailto:akshaydesai677@gmail.com)
* **GitHub**: [https://github.com/akshaydesai677/StreamDash](https://github.com/akshaydesai677/StreamDash)
