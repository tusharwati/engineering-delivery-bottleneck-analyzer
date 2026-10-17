# Deployment, Execution Modes & Setup Guide

**Project:** Engineering Delivery Bottleneck Analyzer  
**Upstream System:** Apache DevLake (`v1.0.2`)  
**Target Environment:** Windows 11 (8 GB RAM, i5/Ryzen 5) / Linux / macOS  

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

### Mode 1: Native Windows 11 Local Execution (Recommended for 8GB RAM Machines)
Requires only **Python 3.11+** and **Node.js 18+**. Runs completely offline using a local SQLite mock DevLake database or a remote DevLake database without requiring Docker.

1. **Backend Setup:**
   ```powershell
   # Navigate to backend directory
   cd backend

   # Create virtual environment
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Install dependencies
   pip install -r requirements.txt

   # Initialize local app store and seed realistic synthetic DevLake database
   python -m app.fixtures.seed_mock_devlake

   # Run FastAPI backend
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Frontend Setup (New PowerShell Window):**
   ```powershell
   cd frontend
   npm.cmd install
   npm.cmd run dev
   ```
   Open `http://localhost:5173` in your browser.

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

Copy `.env.example` to `.env` in the project root:

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

