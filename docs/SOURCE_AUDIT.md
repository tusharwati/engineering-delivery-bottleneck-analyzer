# Upstream Source Audit & Architectural Analysis

**Project:** Engineering Delivery Bottleneck Analyzer  
**Upstream System:** [Apache DevLake](https://github.com/apache/devlake)  
**Pinned Release:** Apache DevLake `v1.0.2` (Tag: `v1.0.2`, Release date: 2024; compatible with `v1.0.0` and `v1.0.1`)  
**License:** Apache License 2.0  
**Audit Date:** October 2026  

---

## 1. Executive Summary

This audit assesses the upstream architecture, data models, metrics engines, and ingestion plugins of **Apache DevLake** to establish the foundation for the **Engineering Delivery Bottleneck Analyzer**.

Apache DevLake is an open-source devops data platform that aggregates, analyzes, and visualizes software engineering data from tools such as GitHub, GitLab, Jira, and Jenkins. While DevLake provides robust connectors, an extensible ETL pipeline, and standard DORA/engineering metrics (e.g., PR Pickup Time, PR Review Time, and PR Cycle Time), our audit identifies significant gaps in **business-hours context**, **review event qualification**, **active queue bottleneck prioritization**, and **actionable alerting**.

Rather than re-implementing DevLake's data ingestion, data pipelines, or configuration UI, our companion analyzer operates as a non-invasive analytical sidecar connecting directly to DevLake's relational database via parameterized, read-only queries.

---

## 2. Upstream References & Inspected Sources

The following official documentation pages, repositories, and source files were audited:

### 2.1 Official Repositories and Releases
* **Repository:** [https://github.com/apache/devlake](https://github.com/apache/devlake)
* **Release History:** [https://github.com/apache/devlake/releases](https://github.com/apache/devlake/releases) (Target: Pinned release `v1.0.2`)
* **License:** [Apache License 2.0](https://github.com/apache/devlake/blob/main/LICENSE)
* **Official Docker Compose Config:** `docker-compose.yml` and `env.example` from release `v1.0.2` asset bundle.

### 2.2 Documentation & Architecture
* **Overview & Architecture:** [https://devlake.apache.org/docs/Overview/Architecture/](https://devlake.apache.org/docs/Overview/Architecture/)
* **Quick Start Guide:** [https://devlake.apache.org/docs/GettingStarted/QuickStart/](https://devlake.apache.org/docs/GettingStarted/QuickStart/)
* **Domain Layer Schema:** [https://devlake.apache.org/docs/v1.0/DataModels/DevLakeDomainLayerSchema/](https://devlake.apache.org/docs/v1.0/DataModels/DevLakeDomainLayerSchema/)
* **GitHub Plugin Guide:** [https://devlake.apache.org/docs/Plugins/github/](https://devlake.apache.org/docs/Plugins/github/)
* **Project & Metric Plugins:** [https://devlake.apache.org/docs/DeveloperManuals/Project/](https://devlake.apache.org/docs/DeveloperManuals/Project/)
* **Grafana User Guide:** [https://devlake.apache.org/docs/v1.0/Configuration/Dashboards/GrafanaUserGuide/](https://devlake.apache.org/docs/v1.0/Configuration/Dashboards/GrafanaUserGuide/)

### 2.3 Official Metric Specifications
* **PR Pickup Time:** [https://devlake.apache.org/docs/Metrics/PRPickupTime/](https://devlake.apache.org/docs/Metrics/PRPickupTime/)
* **PR Review Time:** [https://devlake.apache.org/docs/Metrics/PRReviewTime/](https://devlake.apache.org/docs/Metrics/PRReviewTime/)
* **PR Cycle Time:** [https://devlake.apache.org/docs/Metrics/PRCycleTime/](https://devlake.apache.org/docs/Metrics/PRCycleTime/)

### 2.4 Upstream Source Code Paths Inspected
* `backend/plugins/github/models/pr.go`: GitHub PR relational model definitions.
* `backend/plugins/github/models/pr_comment.go`: GitHub PR comments and review comment structures.
* `backend/plugins/github/models/pr_review.go`: GitHub PR formal review structures (`_tool_github_pull_request_reviews`).
* `backend/core/models/domainlayer/code/pull_request.go`: Unified domain layer `pull_requests` table.
* `backend/core/models/domainlayer/code/pull_request_comment.go`: Unified domain layer `pull_request_comments` table.
* `backend/plugins/dora/tasks/`: Transformation routines and metric pre-computation.

---

## 3. Existing DevLake Components & Architecture

DevLake's pipeline uses a three-tier layered data model:

```
┌────────────────────────────────────────────────────────┐
│ 1. Raw Layer (_raw_github_api_*)                       │
│    Raw JSON responses stored as received from GitHub   │
├────────────────────────────────────────────────────────┤
│ 2. Tool Layer (_tool_github_*)                         │
│    Relational tables specific to GitHub API structures  │
├────────────────────────────────────────────────────────┤
│ 3. Domain Layer (pull_requests, repos, etc.)            │
│    Normalized cross-platform data model                │
└────────────────────────────────────────────────────────┘
```

### Core Upstream Services:
1. **Config UI (`devlake-config-ui`)**: Web interface for managing data connections, credentials, scope, and sync schedules. Runs on port 4000.
2. **Core Backend (`devlake-be`)**: Go-based API server orchestrating data collector and transformation tasks. Runs on port 8080.
3. **Database (`devlake-db`)**: MySQL 8.0 or PostgreSQL 14+ storing all three data layers.
4. **Grafana (`devlake-grafana`)**: Built-in dashboard server on port 3002 with pre-provisioned DevLake datasources and dashboards.

---

## 4. Existing Schemas & Available Data

### 4.1 Domain Layer: `pull_requests`
Stores normalized PR metadata across Git providers:

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `VARCHAR(255)` (PK) | Compound key (e.g., `github:GithubPullRequest:42:1347`) |
| `base_repo_id` | `VARCHAR(255)` (FK) | Repository ID (`repos.id`) |
| `head_repo_id` | `VARCHAR(255)` | Fork or origin repo ID |
| `status` | `VARCHAR(255)` | `OPEN`, `CLOSED`, `MERGED` |
| `title` | `LONGTEXT` | Pull request title |
| `description` | `LONGTEXT` | PR body content |
| `author_name` | `VARCHAR(255)` | PR creator username/display name |
| `author_id` | `VARCHAR(255)` | PR creator account ID (`accounts.id`) |
| `created_date` | `DATETIME` | Timestamp PR was opened (UTC) |
| `merged_date` | `DATETIME` | Timestamp PR was merged (NULL if unmerged) |
| `closed_date` | `DATETIME` | Timestamp PR was closed (NULL if open) |
| `additions` | `INT` | Lines of code added |
| `deletions` | `INT` | Lines of code deleted |
| `comment_count` | `INT` | Total comment count |
| `commit_count` | `INT` | Total commit count |

### 4.2 Domain Layer: `pull_request_comments`
Stores discussion, review comments, and diff comments:

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `VARCHAR(255)` (PK) | Compound key for the comment |
| `pull_request_id` | `VARCHAR(255)` (FK) | Reference to `pull_requests.id` |
| `body` | `LONGTEXT` | Comment text content |
| `account_id` | `VARCHAR(255)` (FK) | Account ID of author (`accounts.id`) |
| `created_date` | `DATETIME` | Timestamp comment was created (UTC) |
| `type` | `VARCHAR(255)` | `NORMAL` (PR issue comment), `DIFF` (inline diff), `REVIEW` (review body) |
| `review_id` | `VARCHAR(255)` | Links to review object if `DIFF` or `REVIEW` |
| `status` | `VARCHAR(255)` | Provider status |

### 4.3 Tool Layer: `_tool_github_pull_request_reviews` (When Available)
Stores GitHub-specific formal review submissions:

| Column | Type | Description |
| :--- | :--- | :--- |
| `connection_id` | `BIGINT` | DevLake connection ID |
| `github_id` | `BIGINT` | GitHub review database ID |
| `pull_request_id` | `BIGINT` | GitHub PR database ID |
| `user_id` | `BIGINT` | Reviewer user ID |
| `user_name` | `VARCHAR(255)` | Reviewer GitHub login |
| `state` | `VARCHAR(255)` | `APPROVED`, `CHANGES_REQUESTED`, `COMMENTED`, `DISMISSED` |
| `submitted_at` | `DATETIME` | Timestamp review was submitted |
| `body` | `LONGTEXT` | Review submission comment |

### 4.4 Domain Layer: `project_pr_metrics`
DevLake's pre-aggregated metric table:

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | `VARCHAR(255)` (PK) | Reference to `pull_requests.id` |
| `project_name` | `VARCHAR(255)` | DevLake project identifier |
| `pr_pickup_time` | `INT` | Pre-calculated pickup duration in minutes |
| `pr_review_time` | `INT` | Pre-calculated review duration in minutes |
| `pr_cycle_time` | `INT` | Total PR cycle duration in minutes |

---

## 5. Audit of Existing PR Metrics & Deficiencies

### 5.1 PR Pickup Time (`pr_pickup_time`)
* **Upstream Definition:** Measured as the elapsed time from PR creation (`created_date`) until the first comment or review event.
* **Calculation:** `TIMESTAMPDIFF(MINUTE, pr.created_date, MIN(prc.created_date))`
* **Deficiencies Found:**
  1. **Calendar Wall-Clock Only:** DevLake calculates this using raw timestamp difference. A PR created on Friday at 5:00 PM and reviewed on Monday at 10:00 AM records **~65 elapsed hours**, distorting team responsiveness metrics, when in reality only **1.5 business hours** elapsed.
  2. **Contaminated by Bot Comments:** Any automated comment created immediately upon PR creation (e.g., `codecov[bot]`, `github-actions[bot]`, `sonarcloud`) triggers a pickup timestamp within seconds, recording near-zero pickup time and masking true reviewer latency.
  3. **Contaminated by PR Author Self-Comments:** If the PR author comments immediately (e.g. "Draft notes" or "/retest"), DevLake counts it as the PR pickup event.

### 5.2 PR Review Time (`pr_review_time`)
* **Upstream Definition:** Measured as the elapsed time from the first comment/review until the PR is merged (`merged_date`).
* **Deficiencies Found:**
  1. Conflates **review waiting latency** with **author rework duration** and **CI execution/deployment pipeline time**.
  2. Does not measure the review cycle between reviews, changes requested, and approvals.
  3. Does not evaluate open, unmerged PRs that are currently stuck awaiting review.

### 5.3 Active Open PR Bottlenecks
* **Upstream Deficiencies:**
  1. DevLake's standard dashboards focus on historical closed/merged PR averages.
  2. There is no active queue analysis evaluating currently open PRs against business-hours SLA targets.
  3. No rule-based prioritization score to guide engineering managers to the most critical blocked PRs.
  4. No notification mechanism (Slack/webhook) for PRs that cross SLA thresholds.

---

## 6. Code Reuse Strategy

To maintain engineering integrity, performance, and stability:
* **Reuse:** DevLake's core connectors, incremental GitHub sync, token management, schema definitions, and raw data pipeline.
* **Do Not Modify:** DevLake's core database tables, migrations, or backend source code.
* **Separate Analytical Engine:** Implement our business-hours SLA, bot-filtering review detector, historical baseline calculator, explainable prioritizer, and alert engine in a separate, clean Python/FastAPI service with read-only access.
* **Separate State:** Store alert deduplication state, dry-run logs, and custom configuration in a dedicated SQLite database completely separated from DevLake's database.

