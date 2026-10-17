# Feature Gap Analysis & Novel Analytical Specification

**Project:** Engineering Delivery Bottleneck Analyzer  
**Upstream System:** Apache DevLake (`v1.0.2`)  
**Audit Reference:** [SOURCE_AUDIT.md](file:///c:/Users/tshar/OneDrive/Pictures/Documents/GitHub/engineering-delivery-bottleneck-analyzer/docs/SOURCE_AUDIT.md)  

---

## 1. Feature Comparison Matrix

The table below contrasts capabilities natively provided by Apache DevLake against the custom features delivered by the **Engineering Delivery Bottleneck Analyzer**:

| Capability Area | Apache DevLake (v1.0.2 Native) | Bottleneck Analyzer (Our Extension) | Why It Matters |
| :--- | :--- | :--- | :--- |
| **Review Event Qualification** | Treats any comment (`NORMAL`, `DIFF`, `REVIEW`) or bot activity as PR pickup. Author comments count. | Filters out PR authors, automated bots (`[bot]`, `codecov`, `dependabot`), and distinguishes formal reviews (`DIFF`, `REVIEW`, `APPROVED`, `CHANGES_REQUESTED`). | Prevents CI bots and author self-notes from masking review delays. |
| **Time Accounting Model** | Calendar wall-clock difference (`TIMESTAMPDIFF(MINUTE, ...)`). | Configurable Business-Hours Engine (IANA timezone, configurable working days, business hours, holiday exclusion, DST support). | PRs submitted Friday evening are not falsely reported as 60+ hour delays on Monday morning. |
| **Active Queue Analysis** | Primarily retrospective analysis of merged/closed PRs. | Real-time active queue tracking of open, unreviewed PRs against business-hours SLA targets. | Engineering leads can intervene *before* reviews stall, rather than only reporting post-mortem. |
| **SLA & Target Tracking** | Static dashboards with general cycle time averages; no configurable SLA breach logic. | Configurable business-hours SLA thresholds (e.g., 8h, 16h) with breach percentages and elapsed ratio. | Clear pass/fail boundary tailored to team working hours. |
| **Repository Baselines** | Aggregate project-level averages across all repositories. | Repository-specific historical benchmarks (Median, P90) with configurable minimum sample size gating (`min_sample_size >= 10`). | Accounts for repository variances (e.g., microservice vs monolithic core) without false assumptions. |
| **Bottleneck Prioritization** | None. Standard sorting by creation date. | Multi-factor, explainable rule-based bottleneck priority score (0-100) combining SLA ratio, baseline deviation, PR size, and repo backlog pressure. | Directs reviewer attention to the highest-impact blocked PRs with transparent rationale. |
| **Individual Developer Metrics** | Exposes individual contributor commit/PR counts. | **Explicitly prohibits individual developer ranking by review speed.** Focuses strictly on team workflows and queue health. | Protects team psychological safety; avoids perverse incentives like rushed, superficial code reviews. |
| **Actionable Alerting** | None built-in. Alerts must be configured through Grafana alerting rules. | Dedicated alert engine supporting Slack webhooks, dry-run mode, token redaction, and local deduplication state. | Eliminates notification spam; delivers actionable alerts directly into engineering team communication channels. |
| **Interactive Application** | Grafana dashboards + administrative Config UI. | Dedicated lightweight React + Vite web dashboard + REST API + portable Grafana dashboard JSON. | Provides a focused tool for team leads and engineers without requiring Grafana admin access. |
| **Zero-Cloud Demonstration Mode** | Requires a live database and active data sync. | Built-in isolated synthetic demo dataset mode clearly labeled as synthetic. | Enables immediate local evaluation, developer onboarding, and offline testing without cloud or GitHub accounts. |

---

## 2. Detailed Gap Analysis & Custom Feature Architecture

### Feature A: Correctly Identify Review Events
* **The Problem:** In DevLake's default domain layer, `pull_request_comments` stores all comments. In practice:
  - 80%+ of modern repositories use CI bots (`github-actions[bot]`, `codecov[bot]`, `sonarcloud[bot]`) that post comments within 30-180 seconds of PR creation.
  - Authors frequently add follow-up notes, test results, or checklists on their own PRs immediately after creation.
  - Native DevLake queries select `MIN(prc.created_date)`, resulting in a median pickup time of minutes, masking real multi-day human review delays.
* **Our Solution:**
  1. We enforce an identity check: `account_id != pr.author_id` and `author_name != pr.author_name`.
  2. We maintain a configurable bot exclusion filter matching account patterns (`%[bot]%`, `codecov`, `dependabot`, `github-actions`, `renovate`, `sonarcloud`).
  3. We categorize review confidence:
     - **High Confidence:** A formal review in `_tool_github_pull_request_reviews` (`APPROVED`, `CHANGES_REQUESTED`, `COMMENTED`) or a domain comment of type `DIFF` or `REVIEW`.
     - **Medium Confidence:** A `NORMAL` comment by an assigned reviewer or non-author teammate.
  4. If review records are not yet ingested by DevLake, the analyzer documents this limitation and can query the GitHub REST API (`/repos/{owner}/{repo}/pulls/{pull_number}/reviews`) in rate-limit-aware enrichment mode.

### Feature B: Business-Hours-Aware Review SLA
* **The Problem:** Software engineering teams operate during specific working hours. Standard calendar metrics penalize teams unfairly for PRs opened outside office hours or over weekends:
  - PR opened Friday at 18:00, reviewed Monday at 10:00: Calendar time = 64 hours. Actual business hours waiting (with 09:30-18:30 schedule) = 0.5 hours!
* **Our Solution:**
  1. Implement a precise, minute-accurate business-hours calculation engine:
     - **Timezone:** Standard IANA timezone (default `Asia/Kolkata`, configurable to any valid IANA zone like `UTC`, `America/New_York`, `Europe/London`).
     - **Working Days:** Configurable bitmask or list of ISO weekdays (default Monday to Friday, `[0, 1, 2, 3, 4]`).
     - **Working Hours:** Configurable start and end time (default `09:30` to `18:30`).
     - **Holidays:** Configurable list of ISO calendar dates (`YYYY-MM-DD`).
     - **Daylight Saving Time (DST):** Exact UTC conversions using Python 3's native `zoneinfo`.
  2. Produce two metrics for every PR:
     - `calendar_waiting_hours`: Raw elapsed wall-clock hours.
     - `business_waiting_hours`: Work schedule elapsed hours.
  3. SLA Breach Assessment:
     - `sla_breached`: `business_waiting_hours > configured_sla_hours`.
     - `sla_ratio`: `business_waiting_hours / configured_sla_hours`.

### Feature C: Repository-Specific Baselines
* **The Problem:** Different repositories have vastly different review velocities. A 10-line change in a documentation repo should be reviewed within 4 hours; a 1,000-line change in a mission-critical financial ledger service may expect a 24-hour review cycle. Fixed universal thresholds cause high false alert rates.
* **Our Solution:**
  1. Compute historical rolling metrics per repository (Median and P90 review pickup time).
  2. Enforce a minimum sample threshold (`min_sample_size`, default 10 reviewed PRs within the lookback window).
  3. If sample count is insufficient, flag `baseline_status = "INSUFFICIENT_SAMPLE"` and fall back to the global configured SLA, clearly informing the user rather than inventing statistics.

### Feature D: Explainable Bottleneck Prioritization
* **The Problem:** Engineering managers and lead reviewers faced with a list of 20 open PRs cannot easily determine which ones need urgent unblocking. Simple chronological ordering favors the oldest PR, which might be a blocked draft or a massive refactor waiting for architecture sign-off, while small, critical features languish.
* **Our Solution:**
  A rule-based scoring engine computing a 0-100 Bottleneck Urgency Score:
  $$\text{Priority Score} = S_{\text{SLA}} + S_{\text{State}} + S_{\text{Baseline}} + S_{\text{Size}} + S_{\text{Backlog}}$$
  Every point allocation is accompanied by a human-readable explanation string, detailing:
  - How far the PR has exceeded the SLA.
  - Whether the PR is in draft or ready for review.
  - How this PR's delay compares to the repository's historical P90.
  - Whether PR size makes review rapid or demanding.
  - How many other PRs are waiting in the same repo queue.
  - **No developer performance assessment:** The score strictly measures queue health and PR urgency.

### Feature E: Actionable Automated Alerting
* **The Problem:** Continuous polling or unthrottled notifications create alert fatigue. Engineering teams mute noisy Slack channels.
* **Our Solution:**
  1. Configurable alert triggers:
     - PR crossing SLA threshold (first time breach).
     - Rapidly growing backlog (unreviewed PR count exceeds threshold).
     - Repository delay spike (overdue count in a repo exceeds historical threshold).
  2. Local state deduplication store (SQLite):
     - Keyed by `(alert_type, entity_id, date)` or `(alert_type, pr_id, state_hash)`.
     - Configurable cooldown window (default: 24 hours per PR breach).
  3. Safe dry-run mode: logs full JSON payload and target channel without transmitting network packets.
  4. Redaction: Automatically masks sensitive tokens (`ghp_***`, `https://hooks.slack.com/services/***`) in logs and UI.

---

## 3. Assumptions and Unresolved Technical Questions

### 3.1 Assumptions
1. **Database Access:** The analyzer has read-only SQL connectivity (MySQL 8.0 or PostgreSQL 14+) to the DevLake database.
2. **DevLake Schema Stability:** DevLake's core domain tables (`pull_requests`, `pull_request_comments`, `repos`) remain consistent across the `v1.0.x` series.
3. **Time Synchronization:** The host system clock and database server maintain synchronized UTC clocks.
4. **Local Hardware Constraints:** The local development host (Windows 11, 8GB RAM, Core i5/Ryzen 5) cannot comfortably run 10+ Docker containers simultaneously; therefore, the analyzer must support both native local execution (Python + Vite) with a mock/seed database and containerized deployment.

### 3.2 Unresolved Technical Questions & Mitigations
* **Q1: What if `_tool_github_pull_request_reviews` is empty because the user only collected domain-level data?**  
  *Mitigation:* The review detector gracefully degrades to inspecting `pull_request_comments` with `type IN ('REVIEW', 'DIFF')`, filtering out the author and bot identities.
* **Q2: What if draft PR status is not explicit in the domain layer?**  
  *Mitigation:* In GitHub, titles often prefix `[Draft]` or `WIP:`, or the tool table `_tool_github_pull_requests.is_draft` can be queried if available. If neither is available, the PR is treated as standard open and flagged with an explanation.
* **Q3: What if historical data for a newly connected repository is fewer than 10 PRs?**  
  *Mitigation:* Flag the repository baseline as `INSUFFICIENT_DATA` and fall back to the team's standard SLA threshold.
