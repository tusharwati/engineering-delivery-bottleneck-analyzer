# Deployment, Execution Modes & Setup Guide

**Project:** Engineering Delivery Bottleneck Analyzer  
**Upstream System:** Apache DevLake (`v1.0.2`)  
**Target Environment:** Windows 11 (8 GB RAM, i5/Ryzen 5) / Linux / macOS  

## Windows 11 Quick Start (Native, No Docker)

This is the recommended way to run the analyzer locally with its bundled mock DevLake database. Docker and a cloud account are not required.

### Prerequisites

- Python 3.11 or later
- Node.js 18 or later and npm
- The repository's bundled database at `backend/data/mock_devlake.db`

The project maintainer reports having verified this setup with Python 3.11, Node.js 24.18, a pre-seeded mock database, and 27 passing backend tests. Versions and test results may differ on other machines or after code changes.

### 1. Start the backend

Open PowerShell at the repository root. In one terminal:

```powershell
Set-Location backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend initializes its local application database, seeds the mock DevLake database only if that database file is missing, and checks the DevLake schema at startup. If port `8000` is already in use by a running backend, use that instance instead of starting a second one.

- API root: <http://127.0.0.1:8000>
- Interactive API documentation: <http://127.0.0.1:8000/docs>
- Health and schema status: <http://127.0.0.1:8000/api/health>

### 2. Start the frontend

Open a second PowerShell terminal at the repository root:

```powershell
Set-Location frontend
npm.cmd install
npm.cmd run dev
```

Open <http://localhost:5173>.

### 3. Explore the dashboard

- **Queue dashboard:** PR queue metrics, business-hours versus calendar waiting time, and prioritized PRs with an explanation of each score.
- **SLA Benchmark:** Evaluation results comparing business-hours-aware analysis with wall-clock measurements.
- **Alert Center:** Alert testing and dry-run Slack notification controls.
- **Architecture:** Project overview and integration architecture.

### 4. Run backend tests

From a PowerShell terminal at the repository root:

```powershell
Set-Location backend
python -m pytest -v
```

The maintainer reports 27 passing tests in the verified environment. The suite covers business-hours calculations, holidays, daylight-saving transitions, review qualification, repository baselines, priority scoring, and alert deduplication.

### Local configuration

The native run uses the mock database and application SQLite database by default, so no `.env` file is needed. For local overrides, place a `.env` file in `backend` (the backend loads `.env` from its current working directory). For example, to connect to DevLake running in Docker on the same machine:

```ini
DEVLAKE_DB_URL=mysql+pymysql://<user>:<password>@127.0.0.1:3306/lake?charset=utf8mb4
```

Use credentials matching your DevLake database configuration. Keep secrets out of source control.

---

## 1. Port Allocation Map

| Service | Internal Port | Host Port | Purpose | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Analyzer Backend (FastAPI)** | `8000` | `8000` | Analytics API & Health checks | Read-only connection to DevLake DB |
| **Analyzer Frontend (Vite)** | `5173` | `5173` | Landing Page & Web Dashboard | Interacts with Backend on `:8000` |
| **DevLake Config UI** | `4000` | `4000` | GitHub PAT & Data sync management | Official Apache DevLake service |
| **DevLake Core Backend** | `8080` | `8080` | Data collection & transformation | Official Apache DevLake service |
| **DevLake Grafana** | `3002` | `3002` | Provisioned dashboards | Official Apache DevLake service |
| **DevLake MySQL DB** | `3306` | `3306` | Domain & Tool Layer DB | Read-only credentials for Analyzer |

---

## 2. Execution Modes

To respect local machine resource constraints (e.g., Windows 11 with 8 GB RAM without Docker Desktop installed), the application provides two primary operational modes:

### Mode 1: Native Local Execution
Requires only **Python 3.11+** and **Node.js 18+**. Runs offline using the bundled SQLite mock DevLake database, or can connect to a remote DevLake database without requiring Docker.

1. **Backend Setup:**
   ```powershell
   cd backend

   # Optional: create and activate a virtual environment
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Install backend dependencies
   pip install -r requirements.txt

   # Start the FastAPI backend (mock data is seeded automatically if its DB file is absent)
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

2. **Frontend Setup (New PowerShell Window):**
   ```powershell
   cd frontend
   npm.cmd install
   npm.cmd run dev
   ```
   Open `http://localhost:5173` in your browser. The API is available at `http://127.0.0.1:8000`; interactive API documentation is at `http://127.0.0.1:8000/docs`.

---

### Mode 2: Full Docker Compose with Official Apache DevLake v1.0.2
For machines with Docker Desktop and WSL 2 enabled:

1. **Deploy DevLake Platform (v1.0.2):**
   ```bash
   # From project root
   docker compose -f docker-compose.devlake.yml up -d
   ```
   *Wait 60-90 seconds for MySQL and DevLake backend migrations to initialize.*

2. **Configure GitHub Ingestion:**
   - Open DevLake Config UI at `http://localhost:4000`.
   - Go to **Connections** > **GitHub** > **Add Connection**.
   - Input your GitHub Personal Access Token (PAT).
   - Create a Project, select your target public repository (e.g. `owner/repo`), and click **Sync Now**.

3. **Deploy the Bottleneck Analyzer Companion:**
   ```bash
   docker compose -f docker-compose.app.yml up -d
   ```
   - Access the Analyzer Dashboard at `http://localhost:5173`.
   - Access DevLake Grafana at `http://localhost:3002` (Credentials: `admin`/`admin`).
   - Import `dashboards/grafana-pr-bottlenecks.json` into Grafana.

---

## 3. Configuration & Environment Variables

The native backend reads `.env` from its working directory, which is normally `backend` when following the local run instructions. The Docker Compose files read the project-root `.env`. The default settings work with the local mock database and do not require an environment file.

```ini
# ==========================================================
# DevLake Database Connection (Read-Only)
# ==========================================================
# For native mock SQLite:
DEVLAKE_DB_URL=sqlite:///./data/mock_devlake.db
# For live DevLake MySQL:
# DEVLAKE_DB_URL=mysql+pymysql://merico_ro:merico_ro_pass@127.0.0.1:3306/lake?charset=utf8mb4
# For live DevLake PostgreSQL:
# DEVLAKE_DB_URL=postgresql+psycopg2://merico_ro:merico_ro_pass@127.0.0.1:5432/lake

# ==========================================================
# Application Configuration & Alert State DB (SQLite)
# ==========================================================
APP_DB_URL=sqlite:///./data/app_state.db

# ==========================================================
# Business-Hours SLA Engine Settings
# ==========================================================
TIMEZONE=Asia/Kolkata
WORK_DAYS=0,1,2,3,4
WORK_START_TIME=09:30
WORK_END_TIME=18:30
REVIEW_SLA_HOURS=8.0
HOLIDAYS_JSON=["2026-01-01","2026-01-26","2026-08-15","2026-10-02","2026-12-25"]

# ==========================================================
# Review Event & Bot Qualification Settings
# ==========================================================
EXCLUDE_BOTS=true
INCLUDE_NORMAL_COMMENTS_AS_REVIEW=false
MIN_HISTORICAL_SAMPLE_SIZE=10

# ==========================================================
# Notifications & Alerting (Optional Slack Webhook)
# ==========================================================
SLACK_WEBHOOK_URL=
ALERT_DRY_RUN=true
ALERT_COOLDOWN_HOURS=24
POLL_INTERVAL_MINUTES=30

# ==========================================================
# Server Configuration
# ==========================================================
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173
```

---

## 4. Production Hardening & Cloud Deployment

When deploying to AWS, Google Cloud, Azure, or Kubernetes:
1. **Network Segregation:** DevLake's MySQL database must reside in a private VPC subnet. Never expose port 3306 to the public internet.
2. **Dedicated Read-Only Role:** Create a dedicated database user with `GRANT SELECT ON lake.* TO 'analyzer_ro'@'%'` without write permissions.
3. **Reverse Proxy & TLS:** Place Nginx or Traefik in front of the FastAPI backend and React frontend with valid TLS/SSL certificates.
4. **Secret Management:** Inject `SLACK_WEBHOOK_URL` and `DEVLAKE_DB_URL` via AWS Secrets Manager, GCP Secret Manager, or Kubernetes Secrets.
5. **CORS Restriction:** Restrict `CORS_ORIGINS` strictly to the production frontend domain name.
