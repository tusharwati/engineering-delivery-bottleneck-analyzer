# System Architecture & Technical Design

**Project:** Engineering Delivery Bottleneck Analyzer  
**Upstream System:** Apache DevLake (`v1.0.2`)  
**Architecture Pattern:** Non-Invasive Analytical Companion / Sidecar  

---

## 1. High-Level Architecture Overview

The **Engineering Delivery Bottleneck Analyzer** operates as an independent companion to **Apache DevLake**. DevLake handles the heavy lifting of authentication, GitHub token rate limiting, webhook/REST/GraphQL polling, and data normalization into standardized domain tables. 

Our analyzer connects directly to DevLake's relational database via **parameterized, read-only SQL queries**, computes context-aware metrics (business-hours SLA, bot-filtered review detection, baseline comparison, and explainable prioritization), serves these metrics through a high-performance **FastAPI REST API**, and renders them in an intuitive **React + Vite** dashboard and a **portable Grafana dashboard**.

```mermaid
flowchart TD
    subgraph GitHub ["GitHub Cloud / Enterprise"]
        GH_API["GitHub API (REST/GraphQL)"]
        GH_HOOKS["Webhooks / Events"]
    end

    subgraph DevLake ["Apache DevLake Platform (v1.0.2)"]
        CONFIG_UI["DevLake Config UI (:4000)"]
        DL_BACKEND["DevLake Core Ingestion Engine (:8080)"]
        DL_DB[("DevLake Database\n(MySQL 8.0 / PostgreSQL 14+)\nDomain & Tool Tables\n[:3306 / :5432]")]
    end

    subgraph AnalyzerBackend ["Bottleneck Analyzer Backend (:8000)"]
        SCHEMA_CHK["Startup Schema Verifier"]
        READ_CONN["Read-Only DB Connector (SQLAlchemy)"]
        REV_DETECTOR["Review Event & Bot Qualifier"]
        BIZ_HOURS["Business-Hours Engine (ZoneInfo)"]
        BASELINES["Repository Baseline Calculator"]
        PRIORITIZER["Explainable Bottleneck Prioritizer"]
        ALERT_ENG["Alert & Notification Engine"]
        FASTAPI["FastAPI REST Endpoints"]
        APP_DB[("Local App Store\n(SQLite)\nConfig & Alert Dedup")]
    end

    subgraph Presentation ["Presentation & Notification Layer"]
        REACT_UI["React + Vite Web App (:5173 / :80)\nLanding Page + Dashboard"]
        GRAFANA["DevLake Grafana (:3002)\nCustom JSON Dashboard"]
        SLACK["Slack Webhook / Channels"]
    end

    GH_API --> DL_BACKEND
    GH_HOOKS --> DL_BACKEND
    CONFIG_UI --> DL_BACKEND
    DL_BACKEND --> DL_DB

    DL_DB -.->|"Read-Only Parameterized SQL"| READ_CONN
    READ_CONN --> SCHEMA_CHK
    READ_CONN --> REV_DETECTOR
    REV_DETECTOR --> BIZ_HOURS
    BIZ_HOURS --> BASELINES
    BASELINES --> PRIORITIZER
    PRIORITIZER --> FASTAPI
    PRIORITIZER --> ALERT_ENG
    ALERT_ENG <--> APP_DB
    ALERT_ENG -->|"Dry-Run / Live Webhook"| SLACK

    FASTAPI <--> REACT_UI
    DL_DB -.->|"Direct Dashboard Queries"| GRAFANA
```

---

## 2. Component Breakdown & Responsibilities

### 2.1 Upstream Platform Components (DevLake)
1. **Config UI (`:4000`):** Manages GitHub personal access tokens (PATs), repository sync scopes, and pipeline scheduling.
2. **Ingestion Engine (`:8080`):** Handles API pagination, incremental syncing, and domain table population.
3. **Database (`:3306` or `:5432`):** Houses the `pull_requests`, `pull_request_comments`, `repos`, and tool-layer tables.

### 2.2 Analyzer Backend Components (`backend/`)
1. **Startup Schema Verifier (`app.database.schema_checker`):**
   - Inspects the connected database before executing metric queries.
   - Validates existence of tables (`pull_requests`, `pull_request_comments`, `repos`) and required columns.
   - Gracefully reports version mismatch or missing tables with actionable setup instructions.
2. **Read-Only Database Connector (`app.database.devlake_session`):**
   - Configured with strict read-only session flags (`SET SESSION TRANSACTION READ ONLY` where supported).
   - Uses parameterized queries to prevent SQL injection.
3. **Review Qualifier & Bot Filter (`app.analytics.review_detector`):**
   - Extracts the first genuine review event.
   - Enforces author exclusion (`comment.account_id != pr.author_id`).
   - Applies regex bot filters (`[bot]`, `codecov`, `dependabot`, `actions`, `renovate`).
   - Identifies high-confidence review types (`DIFF`, `REVIEW`, `APPROVED`, `CHANGES_REQUESTED`).
4. **Business-Hours Engine (`app.analytics.business_hours`):**
   - Built on Python's native `zoneinfo` and `datetime`.
   - Computes minute-accurate business-time delta between timestamps.
   - Configurable timezone (default: `Asia/Kolkata`), working days (`Mon-Fri`), work hours (`09:30-18:30`), and holiday calendar.
   - Handles Daylight Saving Time (DST) transitions safely without timestamp ambiguity.
5. **Repository Baseline Calculator (`app.analytics.baselines`):**
   - Calculates historical median and P90 review pickup times per repository.
   - Enforces a minimum sample size (`min_sample_size >= 10`).
   - Emits transparent `INSUFFICIENT_SAMPLE` state when data is scarce.
6. **Explainable Bottleneck Prioritizer (`app.analytics.prioritizer`):**
   - Generates an urgency score (0 to 100) based on:
     - SLA breach severity (0-40 points)
     - PR state & review readiness (0-20 points)
     - Historical baseline deviation (0-20 points)
     - PR size & review effort (0-10 points)
     - Repository backlog pressure (0-10 points)
   - Emits a full array of rationale explanations for each score.
7. **Alert Engine & Deduplicator (`app.notifications`):**
   - Evaluates active SLA breaches and backlog spikes.
   - Maintains an isolated SQLite database (`data/app_state.db`) for deduplication keys: `(alert_type, pr_id_or_repo_id, date)`.
   - Supports safe dry-run mode (logs sanitized JSON payload without calling external networks).
   - Enforces automatic token/webhook redaction.
8. **Synthetic Demo Seed Generator (`app.fixtures`):**
   - Generates realistic, clearly labeled synthetic test fixtures for offline development and demonstration without a live GitHub or DevLake connection.

### 2.3 Presentation Layer Components (`frontend/`)
1. **Public Landing Page:**
   - One-minute architectural pitch for recruiters, engineering managers, and developers.
   - Clear problem statement, DevLake integration summary, and feature differentiators.
   - Technology stack display and zero-cloud local quickstart instructions.
2. **Main Analytics Dashboard:**
   - Real-time SLA breach summary cards.
   - Wall-clock vs Business-hours comparative analysis chart.
   - Prioritized bottleneck table with expandable scoring explanations.
   - Repository-level comparative metrics.
   - Backlog trend graph.
   - Demonstration mode toggle banner.
3. **Portable Grafana Dashboard (`dashboards/grafana-pr-bottlenecks.json`):**
   - Compatible with DevLake's built-in Grafana instance.
   - Parameterized by `$repo_id` and `$__timeFilter`.

---

## 3. Data Flow & Lifecycles

### 3.1 Review Latency Calculation Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as Engineer / Lead
    participant UI as React Dashboard
    participant API as FastAPI Backend
    participant DB as DevLake Database (Read-Only)
    participant Engine as Business-Hours Engine

    User->>UI: Opens Dashboard
    UI->>API: GET /api/v1/bottlenecks?repo_id=all
    API->>DB: Query open PRs + comments/reviews (parameterized)
    DB-->>API: Returns PR rows & candidate comments
    API->>API: Filter author self-comments & bot accounts
    API->>API: Extract earliest qualifying review event
    loop For each PR
        API->>Engine: calculate_business_hours(created_date, review_date_or_now)
        Engine-->>API: business_hours_waiting, wall_clock_waiting
        API->>API: Compute baseline comparison & priority score
    end
    API-->>UI: Return BottleneckResponse (PRs, SLAs, explanations)
    UI-->>User: Render visual charts & prioritized bottleneck list
```

### 3.2 Alert & Deduplication Flow

```mermaid
sequenceDiagram
    autonumber
    participant Cron as Poller / Scheduled Task
    participant AlertEng as Alert Engine
    participant API as Analytics Service
    participant SQLite as Local App SQLite
    participant Slack as Slack Webhook

    Cron->>AlertEng: check_and_notify(dry_run=False)
    AlertEng->>API: Fetch active SLA breached PRs
    API-->>AlertEng: List of breached PRs (hours_waiting, priority)
    loop For each breached PR
        AlertEng->>SQLite: Check deduplication key (type, pr_id, today)
        alt Key already exists within cooldown window
            AlertEng->>AlertEng: Skip notification (suppressed)
        else Key not found
            AlertEng->>SQLite: Insert deduplication record
            alt dry_run is True
                AlertEng->>AlertEng: Log sanitized payload (DRY_RUN)
            else dry_run is False
                AlertEng->>Slack: POST webhook payload (with retry & timeout)
                Slack-->>AlertEng: 200 OK
            end
        end
    end
```

---

## 4. Security & Isolation Architecture

1. **Read-Only Ingestion Boundary:**  
   The analyzer connects using read-only database credentials. It possesses no `CREATE`, `DROP`, `ALTER`, `INSERT`, or `UPDATE` privileges on DevLake tables.
2. **Isolated Configuration Store:**  
   All analyzer configuration, alert deduplication keys, and notification logs reside in a dedicated local SQLite file (`data/app_state.db`), preventing accidental mutation of DevLake's data models.
3. **No Credential Leakage:**  
   Database connection strings, GitHub tokens, and Slack webhook URLs are loaded strictly from environment variables or a local `.env` file excluded from version control. Sensitive strings are masked in logs (e.g., `https://hooks.slack.com/services/T***/B***/X***`).
4. **Boundary Isolation:**  
   The web dashboard connects to the backend through CORS-restricted APIs and does not receive raw database credentials.
