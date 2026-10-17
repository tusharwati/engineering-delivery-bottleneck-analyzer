# Troubleshooting & Operational Guide

**Project:** Engineering Delivery Bottleneck Analyzer  
**Environment:** Windows 11 / WSL 2 / Linux  

---

## 1. Windows 11 & PowerShell Issues

### 1.1 `npm.ps1 cannot be loaded because running scripts is disabled`
* **Symptom:** Running `npm install` or `npm run dev` yields `PSSecurityException: UnauthorizedAccess`.
* **Root Cause:** Windows PowerShell script execution policy defaults to `Restricted`.
* **Resolution:**
  - **Option A (Direct execution):** Use `npm.cmd` instead of `npm`:
    ```powershell
    npm.cmd install
    npm.cmd run dev
    ```
  - **Option B (Bypass in current session):**
    ```powershell
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    npm run dev
    ```

### 1.2 Python Virtual Environment Activation in PowerShell
* **Symptom:** `.\venv\Scripts\Activate.ps1` gives a security error.
* **Resolution:** Run:
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .\venv\Scripts\Activate.ps1
  ```
  Or activate using CMD:
  ```cmd
  venv\Scripts\activate.bat
  ```

---

## 2. Docker & WSL 2 Memory Management (8 GB RAM Machines)

### 2.1 WSL 2 Consumes Excessive RAM / Machine Freezes
* **Symptom:** `vmmem` process consumes 6-7 GB RAM, leading to thrashing on an 8 GB RAM system.
* **Resolution:** Create or edit `%USERPROFILE%\.wslconfig` to cap WSL 2 resource usage:
  ```ini
  [wsl2]
  memory=3GB
  processors=2
  swap=2GB
  ```
  Restart WSL in PowerShell:
  ```powershell
  wsl --shutdown
  ```
  Alternatively, **use Native Execution Mode (Mode 1)**, which requires under 150 MB RAM for the entire Python and Vite stack.

---

## 3. Database & Schema Errors

### 3.1 `SchemaValidationError: Table 'pull_requests' does not exist`
* **Symptom:** Backend health check returns 503 or logs missing table warnings on startup.
* **Cause:** DevLake migrations have not completed, or the connected database is empty.
* **Resolution:**
  1. Check DevLake backend logs:
     ```bash
     docker compose -f docker-compose.devlake.yml logs devlake-be
     ```
  2. Verify you have created a connection and triggered a sync in Config UI (`http://localhost:4000`).
  3. If running without a live DevLake database, initialize the mock database:
     ```powershell
     python -m app.fixtures.seed_mock_devlake
     ```

### 3.2 Read-Only Connection Refused
* **Symptom:** `pymysql.err.OperationalError: (2003, "Can't connect to MySQL server on '127.0.0.1'")`
* **Resolution:**
  - Verify port 3306 is listening: `netstat -ano | findstr :3306`
  - Ensure Docker container is running: `docker ps`
  - For Docker Compose environments, use internal network hostname `devlake-db` rather than `localhost`.

---

## 4. GitHub API & Data Collection Issues

### 4.1 GitHub API Rate Limiting (403 Forbidden)
* **Symptom:** DevLake sync fails or stops partway through.
* **Cause:** Unauthenticated GitHub API calls allow only 60 req/hr; authenticated PAT allows 5,000 req/hr.
* **Resolution:**
  - Ensure a valid Personal Access Token (classic or fine-grained) is entered in Config UI.
  - Required scopes for public repos: `public_repo`, `read:org`.
  - Required scopes for private repos: `repo`, `read:org`.
  - If your organization uses SAML SSO, click **Configure SSO** next to the token in GitHub settings to authorize it.

### 4.2 Bot Comments Skewing Data
* **Symptom:** PR pickup time is reported as 0.0h or a few seconds.
* **Resolution:**
  - Verify `EXCLUDE_BOTS=true` is configured in `.env`.
  - Check whether the bot account has an unusual name not captured in default patterns. Custom patterns can be appended to `app/config.py`.

---

## 5. Notifications & Slack Alerting

### 5.1 Slack Webhook Returns 404 or Invalid Payload
* **Symptom:** Alert logs show `Slack notification failed: 404 Client Error`.
* **Resolution:**
  - Test the webhook using curl or PowerShell:
    ```powershell
    Invoke-RestMethod -Uri $env:SLACK_WEBHOOK_URL -Method Post -Body '{"text":"Test"}' -ContentType 'application/json'
    ```
  - Verify the webhook has not been revoked in the Slack App Directory.
  - In development, keep `ALERT_DRY_RUN=true` to test formatting safely without sending external network requests.

