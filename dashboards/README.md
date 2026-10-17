# Grafana Dashboard Provisioning & Verification Guide

This directory contains the portable Grafana dashboard JSON file for the **Engineering Delivery Bottleneck Analyzer**, designed for Apache DevLake's built-in Grafana instance (`v1.0.2`).

---

## 1. Dashboard Details

* **File:** `grafana-pr-bottlenecks.json`
* **Dashboard UID:** `devlake-pr-bottlenecks`
* **Title:** Engineering Delivery Bottleneck Analyzer (DevLake)
* **Default Datasource:** `DevLake` (the default MySQL/PostgreSQL datasource provisioned by DevLake)
* **Variables:**
  * `$repo_id`: Dynamically populates with all synchronized repositories from `repos`. Includes an `All` option.
  * Time range filter: Default past 30 days.

---

## 2. Import Instructions into DevLake Grafana

1. Open Apache DevLake Grafana in your web browser:
   `http://localhost:3002`
2. Log in using default DevLake credentials:
   - **Username:** `admin`
   - **Password:** `admin`
3. In the left navigation menu, click **Dashboards** > **New** > **Import**.
4. Click **Upload dashboard JSON file** and select `dashboards/grafana-pr-bottlenecks.json` (or paste the JSON content directly into the text box).
5. Select the **DevLake** datasource from the dropdown when prompted.
6. Click **Import**.

---

## 3. Verifying Panels Against Data

Once imported, verify each panel:
* **Total Open PRs:** Should match the count of rows in `pull_requests` where `status = 'OPEN' AND merged_date IS NULL AND closed_date IS NULL`.
* **Awaiting Qualifying Review:** Verified against non-author human reviews (`type IN ('DIFF', 'REVIEW')`).
* **Overdue (>24h Calendar Time):** Highlights PRs needing immediate triage in Grafana.
* **Unreviewed Queue Table:** Shows the PR title, author, age, and size (additions/deletions).
* **Repository Comparison:** Visually surfaces which repositories hold the highest review bottleneck backlog.

