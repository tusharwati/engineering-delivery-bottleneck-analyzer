# Metric Definitions, Event Rules & Scoring Formulas

**Project:** Engineering Delivery Bottleneck Analyzer  
**Upstream System:** Apache DevLake (`v1.0.2`)  

---

## 1. Core Event & Identity Qualifications

To produce accurate engineering metrics, every recorded event must be unambiguously defined and verified against underlying data models.

### 1.1 Pull Request Creation Event ($T_{\text{created}}$)
* **Underlying Field:** `pull_requests.created_date` (UTC).
* **Definition:** The exact timestamp recorded when a developer submits a pull request to the target repository.
* **Exclusion Criteria:** PRs in explicit draft mode (`[Draft]` or `WIP:` in title, or `_tool_github_pull_requests.is_draft = 1`) may be excluded or deprioritized from SLA tracking until marked ready for review.

### 1.2 First Qualifying Review Event ($T_{\text{review}}$)
* **Definition:** The earliest interaction from a human teammate (distinct from the PR author) indicating substantive review evaluation.
* **Qualification Rules:**
  1. **Author Exclusion:** Commenter account ID must not match the PR author (`account_id != pr.author_id` and `user_name != pr.author_name`). Self-comments are strictly excluded.
  2. **Bot Exclusion:** Automated service accounts and bots are excluded by identity inspection:
     - Regex match on username: `.*(\[bot\]|bot$|-ci$|-bot$).*`
     - Known bot usernames: `codecov`, `dependabot`, `github-actions`, `renovate`, `sonarcloud`, `jenkins`, `stale`.
  3. **Event Confidence Levels:**
     - **Tier 1 (Formal Review - High Confidence):** Record in `_tool_github_pull_request_reviews` with state `APPROVED`, `CHANGES_REQUESTED`, or `COMMENTED`, OR domain comment with `type IN ('REVIEW', 'DIFF')`.
     - **Tier 2 (General Comment - Medium Confidence):** Record in `pull_request_comments` with `type = 'NORMAL'` by a non-author human. Included only when configurable setting `INCLUDE_NORMAL_COMMENTS_AS_REVIEW = True`.
* **Labeling Rule:** The system explicitly labels metrics based on the qualifying event detected:
  - *"First Formal Review"* when Tier 1 is present.
  - *"First Human Interaction"* when Tier 2 is used.
  - Never mislabels general discussion as formal review.

---

## 2. Review Delay Metrics

### 2.1 Calendar Wall-Clock Waiting Time ($W_{\text{calendar}}$)
* **Definition:** The unadjusted chronological elapsed time between PR creation and review (or current timestamp $T_{\text{now}}$ if still awaiting review).
$$W_{\text{calendar}} = T_{\text{end}} - T_{\text{created}}$$
where:
$$T_{\text{end}} = \begin{cases} 
T_{\text{review}} & \text{if qualifying review exists} \\
T_{\text{now}} & \text{if PR is currently awaiting review}
\end{cases}$$
* **Unit:** Decimal hours (e.g., $18.5$ hours).

### 2.2 Business-Hours Waiting Time ($W_{\text{business}}$)
* **Definition:** The cumulative duration within configured organization work hours between $T_{\text{created}}$ and $T_{\text{end}}$.
$$W_{\text{business}} = \int_{T_{\text{created}}}^{T_{\text{end}}} \mathbb{I}_{\text{business}}(t) \, dt$$
where $\mathbb{I}_{\text{business}}(t) = 1$ if timestamp $t$ falls within:
1. A designated working day of the week (e.g., Monday through Friday).
2. The working hours window (e.g., 09:30 to 18:30 local time in the configured IANA timezone).
3. Not on a recognized company holiday.
* **Unit:** Decimal hours.

### 2.3 Non-Working Delta ($D_{\text{non-working}}$)
* **Definition:** The portion of elapsed calendar time that occurred outside working hours (weekends, nights, holidays).
$$D_{\text{non-working}} = W_{\text{calendar}} - W_{\text{business}}$$
* **Purpose:** Demonstrates the distortion introduced by standard wall-clock reporting.

---

## 3. SLA Targets & Breach Assessment

### 3.1 Review SLA Target ($SLA_{\text{target}}$)
* **Default Configuration:** $8.0$ business hours (equivalent to 1 business day under a 9-hour workday).
* **Configurable Range:** Typically $4.0$ to $24.0$ business hours.

### 3.2 SLA Breach Status
$$\text{Status} = \begin{cases} 
\text{BREACHED} & \text{if } W_{\text{business}} > SLA_{\text{target}} \\
\text{AT\_RISK} & \text{if } 0.75 \times SLA_{\text{target}} < W_{\text{business}} \le SLA_{\text{target}} \\
\text{HEALTHY} & \text{if } W_{\text{business}} \le 0.75 \times SLA_{\text{target}}
\end{cases}$$

### 3.3 SLA Elapsed Ratio ($R_{\text{SLA}}$)
$$R_{\text{SLA}} = \frac{W_{\text{business}}}{SLA_{\text{target}}}$$
* Example: A PR waiting $16.0$ business hours against an $8.0$ hour SLA has $R_{\text{SLA}} = 2.0$ ($200\%$ of target).

---

## 4. Repository Baselines

### 4.1 Historical Sample Window
* **Lookback Window:** Configurable (default: trailing 30 days or trailing 50 merged/reviewed PRs).
* **Minimum Historical Sample ($N_{\text{min}}$):** Default $10$ qualifying PRs.

### 4.2 Repository Benchmarks
* **Median Review Time ($B_{\text{med}}$):** The 50th percentile of business-hours review pickup times for qualifying PRs in the repository.
* **90th Percentile Review Time ($B_{\text{p90}}$):** The 90th percentile of business-hours review pickup times for qualifying PRs in the repository.
* **Sample Sufficiency Guard:**
  If $N_{\text{sample}} < N_{\text{min}}$:
  $$\text{Baseline Status} = \text{INSUFFICIENT\_SAMPLE}$$
  $$\text{Effective Baseline} = SLA_{\text{target}} \quad (\text{transparent fallback})$$

---

## 5. Explainable Bottleneck Priority Scoring

The priority scoring model computes an urgency score between $0$ and $100$ for open PRs awaiting review. It is an explainable rule-based index designed to help reviewers triage queues. **It strictly measures PR and queue health and does NOT evaluate individual developer performance.**

$$\text{Priority Score} = \min(100, S_{\text{SLA}} + S_{\text{State}} + S_{\text{Baseline}} + S_{\text{Size}} + S_{\text{Backlog}})$$

### Component 1: SLA Breach Factor ($S_{\text{SLA}}$, max 40 points)
Measures the extent of the SLA violation:
$$S_{\text{SLA}} = \begin{cases}
40 & \text{if } R_{\text{SLA}} \ge 2.5 \\
16 \times R_{\text{SLA}} & \text{if } 1.0 \le R_{\text{SLA}} < 2.5 \\
8 \times R_{\text{SLA}} & \text{if } 0.75 \le R_{\text{SLA}} < 1.0 \\
0 & \text{if } R_{\text{SLA}} < 0.75
\end{cases}$$
* **Explanation Output:** e.g., *"Waiting 18.2 business hours (227% of 8h SLA target) [+36 pts]"*

### Component 2: PR State & Readiness ($S_{\text{State}}$, max 20 points)
Rewards actionable, review-ready pull requests:
$$S_{\text{State}} = \begin{cases}
20 & \text{if Open and ready for review (non-draft)} \\
0 & \text{if Draft or marked WIP}
\end{cases}$$
* **Explanation Output:** e.g., *"PR is open and ready for review [+20 pts]"* or *"Draft PR / WIP status [0 pts]"*

### Component 3: Repository Baseline Deviation ($S_{\text{Baseline}}$, max 20 points)
Compares current waiting time against the repository's historical distribution:
$$S_{\text{Baseline}} = \begin{cases}
20 & \text{if } W_{\text{business}} > B_{\text{p90}} \text{ (exceeds 90% of repo history)} \\
10 & \text{if } W_{\text{business}} > B_{\text{med}} \text{ (exceeds repo median)} \\
0 & \text{if within normal repo baseline or sample insufficient}
\end{cases}$$
* **Explanation Output:** e.g., *"Waiting time exceeds repo historical P90 of 12.4h [+20 pts]"*

### Component 4: PR Size & Review Feasibility ($S_{\text{Size}}$, max 10 points)
Small, low-risk changes that can be unblocked in minutes receive higher urgency:
$$L = \text{additions} + \text{deletions}$$
$$S_{\text{Size}} = \begin{cases}
10 & \text{if } L < 100 \text{ lines (Small PR: quick unblock)} \\
5 & \text{if } 100 \le L \le 500 \text{ lines (Medium PR)} \\
2 & \text{if } L > 500 \text{ lines (Large PR: requires scheduled block)}
\end{cases}$$
* **Explanation Output:** e.g., *"Small diff (42 lines) - rapid review opportunity [+10 pts]"*

### Component 5: Repository Backlog Pressure ($S_{\text{Backlog}}$, max 10 points)
Accounts for queue congestion in the same repository:
$$Q = \text{number of overdue PRs in the same repository}$$
$$S_{\text{Backlog}} = \min(10, 2 \times Q)$$
* **Explanation Output:** e.g., *"Repo has 4 overdue PRs creating review queue congestion [+8 pts]"*

