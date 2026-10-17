-- =====================================================================
-- Apache DevLake Schema Verification Query (MySQL / PostgreSQL / SQLite)
-- Pinned Target Release: Apache DevLake v1.0.2
-- Purpose: Pre-flight validation of required domain and tool tables.
-- =====================================================================

-- 1. Check for core domain tables
-- In MySQL:
-- SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name IN ('pull_requests', 'pull_request_comments', 'repos');

-- In PostgreSQL:
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('pull_requests', 'pull_request_comments', 'repos');

-- 2. Verify pull_requests columns
-- Required columns:
--   - id (VARCHAR)
--   - base_repo_id (VARCHAR)
--   - title (TEXT / VARCHAR)
--   - status (VARCHAR)
--   - author_id (VARCHAR)
--   - author_name (VARCHAR)
--   - created_date (DATETIME / TIMESTAMP)
--   - merged_date (DATETIME / TIMESTAMP)
--   - closed_date (DATETIME / TIMESTAMP)
--   - additions (INT)
--   - deletions (INT)

-- 3. Verify pull_request_comments columns
-- Required columns:
--   - id (VARCHAR)
--   - pull_request_id (VARCHAR)
--   - account_id (VARCHAR)
--   - body (TEXT)
--   - created_date (DATETIME / TIMESTAMP)
--   - type (VARCHAR: 'NORMAL', 'DIFF', 'REVIEW')
--   - review_id (VARCHAR)

-- 4. Verify optional tool-layer review table:
--   - _tool_github_pull_request_reviews
--   Columns: connection_id, github_id, pull_request_id, user_id, user_name, state, submitted_at, body
