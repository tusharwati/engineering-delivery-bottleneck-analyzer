-- =====================================================================
-- Engineering Delivery Bottleneck Analyzer: Core Parameterized Queries
-- Compatible with Apache DevLake v1.0.2 Schema (MySQL / PostgreSQL / SQLite)
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. Fetch Open Pull Requests for Active Queue Analysis
-- Parameter: :repo_id (Optional; filter by base_repo_id or ALL)
-- ---------------------------------------------------------------------
SELECT 
    pr.id,
    pr.base_repo_id,
    r.name AS repo_name,
    pr.title,
    pr.status,
    pr.author_id,
    pr.author_name,
    pr.created_date,
    pr.comment_count,
    pr.commit_count,
    COALESCE(pr.additions, 0) AS additions,
    COALESCE(pr.deletions, 0) AS deletions
FROM pull_requests pr
LEFT JOIN repos r ON pr.base_repo_id = r.id
WHERE pr.status = 'OPEN'
  AND pr.merged_date IS NULL
  AND pr.closed_date IS NULL
ORDER BY pr.created_date ASC;

-- ---------------------------------------------------------------------
-- 2. Fetch Review Events & Comments for Candidate Pull Requests
-- Parameter: List of pull_request_ids
-- ---------------------------------------------------------------------
SELECT 
    c.id AS comment_id,
    c.pull_request_id,
    c.account_id,
    c.created_date,
    c.type AS comment_type,
    c.review_id,
    c.body
FROM pull_request_comments c
WHERE c.pull_request_id IN (:pr_ids)
ORDER BY c.created_date ASC;

-- ---------------------------------------------------------------------
-- 3. Fetch Historical Completed PRs for Repository Baseline Calculation
-- Parameters: :repo_id, :lookback_start_date
-- ---------------------------------------------------------------------
SELECT 
    pr.id,
    pr.base_repo_id,
    pr.created_date,
    pr.merged_date,
    pr.closed_date,
    pr.author_id,
    pr.author_name
FROM pull_requests pr
WHERE pr.base_repo_id = :repo_id
  AND pr.created_date >= :lookback_start_date
  AND (pr.status = 'MERGED' OR pr.merged_date IS NOT NULL)
ORDER BY pr.created_date DESC;

-- ---------------------------------------------------------------------
-- 4. Fetch All Connected Repositories
-- ---------------------------------------------------------------------
SELECT 
    r.id,
    r.name,
    r.url,
    r.description,
    COUNT(pr.id) AS total_prs,
    SUM(CASE WHEN pr.status = 'OPEN' AND pr.merged_date IS NULL AND pr.closed_date IS NULL THEN 1 ELSE 0 END) AS open_prs
FROM repos r
LEFT JOIN pull_requests pr ON r.id = pr.base_repo_id
GROUP BY r.id, r.name, r.url, r.description
ORDER BY r.name ASC;

-- ---------------------------------------------------------------------
-- 5. Backlog Trend Over Time (Daily Cumulative Open PRs)
-- ---------------------------------------------------------------------
SELECT 
    DATE(pr.created_date) AS date,
    COUNT(pr.id) AS opened_count,
    SUM(CASE WHEN pr.merged_date IS NOT NULL THEN 1 ELSE 0 END) AS merged_count
FROM pull_requests pr
WHERE pr.created_date >= :start_date
GROUP BY DATE(pr.created_date)
ORDER BY date ASC;
