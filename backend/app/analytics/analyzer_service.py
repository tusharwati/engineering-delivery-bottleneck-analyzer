from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.analytics.baselines import calculate_repository_baseline, RepositoryBaseline
from app.analytics.business_hours import calculate_business_hours
from app.analytics.prioritizer import calculate_bottleneck_priority
from app.analytics.review_detector import extract_qualifying_review
from app.config import settings
from app.logger import logger


class BottleneckAnalyzerService:
    """
    Orchestrates data retrieval from DevLake database and analytical processing.
    """

    def __init__(self, config=None):
        self.config = config or settings

    def get_repositories(self, db: Session) -> List[Dict[str, Any]]:
        """Fetches all repositories from DevLake domain layer."""
        sql = text("""
            SELECT 
                r.id,
                r.name,
                COALESCE(r.url, '') AS url,
                COALESCE(r.description, '') AS description,
                COUNT(pr.id) AS total_prs,
                SUM(CASE WHEN pr.status = 'OPEN' AND pr.merged_date IS NULL AND pr.closed_date IS NULL THEN 1 ELSE 0 END) AS open_prs
            FROM repos r
            LEFT JOIN pull_requests pr ON r.id = pr.base_repo_id
            GROUP BY r.id, r.name, r.url, r.description
            ORDER BY r.name ASC;
        """)
        rows = db.execute(sql).fetchall()
        return [
            {
                "id": str(r[0]),
                "name": str(r[1]),
                "url": str(r[2]),
                "description": str(r[3]),
                "total_prs": int(r[4] or 0),
                "open_prs": int(r[5] or 0),
            }
            for r in rows
        ]

    def _fetch_comments_for_prs(self, db: Session, pr_ids: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Fetches domain comments mapped to their parent pull request IDs."""
        if not pr_ids:
            return {}

        # SQLite/MySQL parameterized IN query
        placeholders = ", ".join([f":id_{i}" for i in range(len(pr_ids))])
        params = {f"id_{i}": pid for i, pid in enumerate(pr_ids)}

        sql = text(f"""
            SELECT 
                id,
                pull_request_id,
                account_id,
                created_date,
                COALESCE(type, 'NORMAL') AS type,
                review_id,
                body
            FROM pull_request_comments
            WHERE pull_request_id IN ({placeholders})
            ORDER BY created_date ASC;
        """)

        rows = db.execute(sql, params).fetchall()
        comments_by_pr: Dict[str, List[Dict[str, Any]]] = {pid: [] for pid in pr_ids}
        for r in rows:
            c_date = r[3]
            if isinstance(c_date, str):
                try:
                    c_date = datetime.fromisoformat(c_date.replace(" ", "T"))
                except Exception:
                    pass
            comments_by_pr[str(r[1])].append({
                "id": str(r[0]),
                "pull_request_id": str(r[1]),
                "account_id": str(r[2]),
                "created_date": c_date,
                "type": str(r[4]),
                "review_id": str(r[5]) if r[5] else None,
                "body": str(r[6]) if r[6] else "",
            })
        return comments_by_pr

    def _fetch_tool_reviews_for_prs(self, db: Session, pr_ids: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Fetches GitHub tool reviews if the table exists."""
        if not pr_ids:
            return {}

        try:
            placeholders = ", ".join([f":id_{i}" for i in range(len(pr_ids))])
            params = {f"id_{i}": pid for i, pid in enumerate(pr_ids)}
            sql = text(f"""
                SELECT 
                    github_id,
                    pull_request_id,
                    user_id,
                    user_name,
                    state,
                    submitted_at,
                    body
                FROM _tool_github_pull_request_reviews
                WHERE pull_request_id IN ({placeholders})
                ORDER BY submitted_at ASC;
            """)
            rows = db.execute(sql, params).fetchall()
            reviews_by_pr: Dict[str, List[Dict[str, Any]]] = {pid: [] for pid in pr_ids}
            for r in rows:
                s_date = r[5]
                if isinstance(s_date, str):
                    try:
                        s_date = datetime.fromisoformat(s_date.replace(" ", "T"))
                    except Exception:
                        pass
                reviews_by_pr[str(r[1])].append({
                    "github_id": str(r[0]),
                    "pull_request_id": str(r[1]),
                    "user_id": str(r[2]),
                    "user_name": str(r[3]),
                    "state": str(r[4]),
                    "submitted_at": s_date,
                    "body": str(r[6]) if r[6] else "",
                })
            return reviews_by_pr
        except Exception:
            # Table might not exist in domain-only installations
            return {pid: [] for pid in pr_ids}

    def get_repo_baselines(self, db: Session, repo_ids: List[str]) -> Dict[str, RepositoryBaseline]:
        """Calculates historical repository benchmarks for the provided repositories."""
        baselines: Dict[str, RepositoryBaseline] = {}
        lookback_date = datetime.now(timezone.utc) - timedelta(days=self.config.BASELINE_LOOKBACK_DAYS)

        for rid in repo_ids:
            # Fetch completed PRs in lookback window
            sql = text("""
                SELECT 
                    pr.id,
                    pr.author_id,
                    pr.author_name,
                    pr.created_date,
                    pr.merged_date
                FROM pull_requests pr
                WHERE pr.base_repo_id = :repo_id
                  AND pr.created_date >= :lookback_date
                  AND (pr.status = 'MERGED' OR pr.merged_date IS NOT NULL)
                ORDER BY pr.created_date DESC
                LIMIT 100;
            """)
            rows = db.execute(sql, {"repo_id": rid, "lookback_date": lookback_date}).fetchall()
            pr_ids = [str(r[0]) for r in rows]

            comments_map = self._fetch_comments_for_prs(db, pr_ids)
            tool_reviews_map = self._fetch_tool_reviews_for_prs(db, pr_ids)

            durations: List[float] = []
            for r in rows:
                pid = str(r[0])
                author_id = str(r[1])
                author_name = str(r[2] or author_id)
                created_dt = r[3]
                if isinstance(created_dt, str):
                    try:
                        created_dt = datetime.fromisoformat(created_dt.replace(" ", "T"))
                    except Exception:
                        pass
                qual_review = extract_qualifying_review(
                    pr_author_id=author_id,
                    pr_author_name=author_name,
                    comments=comments_map.get(pid, []),
                    tool_reviews=tool_reviews_map.get(pid, []),
                )
                if qual_review.has_review and qual_review.review_date:
                    biz_res = calculate_business_hours(created_dt, qual_review.review_date)
                    durations.append(biz_res.business_hours)

            baselines[rid] = calculate_repository_baseline(
                repo_id=rid,
                historical_pr_durations=durations,
                min_sample_size=self.config.MIN_HISTORICAL_SAMPLE_SIZE,
                default_sla_hours=self.config.REVIEW_SLA_HOURS,
            )

        return baselines

    def analyze_bottlenecks(
        self,
        db: Session,
        repo_id: Optional[str] = None,
        now_dt: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Analyzes all active open pull requests, calculates business-hours SLA waiting times,
        qualifies reviews, and assigns explainable priority scores.
        """
        evaluation_now = now_dt or datetime.now(timezone.utc)

        # 1. Fetch open PRs
        repo_filter_clause = "AND pr.base_repo_id = :repo_id" if repo_id and repo_id != "all" else ""
        sql = text(f"""
            SELECT 
                pr.id,
                pr.base_repo_id,
                COALESCE(r.name, pr.base_repo_id) AS repo_name,
                pr.title,
                pr.status,
                pr.author_id,
                pr.author_name,
                pr.created_date,
                COALESCE(pr.additions, 0) AS additions,
                COALESCE(pr.deletions, 0) AS deletions,
                COALESCE(pr.comment_count, 0) AS comment_count
            FROM pull_requests pr
            LEFT JOIN repos r ON pr.base_repo_id = r.id
            WHERE pr.status = 'OPEN'
              AND pr.merged_date IS NULL
              AND pr.closed_date IS NULL
              {repo_filter_clause}
            ORDER BY pr.created_date ASC;
        """)

        params = {"repo_id": repo_id} if repo_id and repo_id != "all" else {}
        open_prs = db.execute(sql, params).fetchall()

        if not open_prs:
            return []

        pr_ids = [str(r[0]) for r in open_prs]
        comments_map = self._fetch_comments_for_prs(db, pr_ids)
        tool_reviews_map = self._fetch_tool_reviews_for_prs(db, pr_ids)

        distinct_repos = list({str(r[1]) for r in open_prs})
        baselines_map = self.get_repo_baselines(db, distinct_repos)

        analyzed_items = []
        repo_overdue_counts: Dict[str, int] = {rid: 0 for rid in distinct_repos}

        # First pass: qualify reviews & calculate business hours
        for pr in open_prs:
            pid = str(pr[0])
            rid = str(pr[1])
            repo_name = str(pr[2])
            title = str(pr[3])
            status = str(pr[4])
            author_id = str(pr[5])
            author_name = str(pr[6] or author_id)
            created_dt = pr[7]
            if isinstance(created_dt, str):
                try:
                    created_dt = datetime.fromisoformat(created_dt.replace(" ", "T"))
                except Exception:
                    pass
            additions = int(pr[8])
            deletions = int(pr[9])
            comment_count = int(pr[10])

            # Check draft
            is_draft = "[draft]" in title.lower() or title.lower().startswith("wip:")

            # Review qualification
            qual_review = extract_qualifying_review(
                pr_author_id=author_id,
                pr_author_name=author_name,
                comments=comments_map.get(pid, []),
                tool_reviews=tool_reviews_map.get(pid, []),
            )

            # Only analyze PRs currently awaiting review
            if not qual_review.has_review:
                biz_time = calculate_business_hours(created_dt, evaluation_now)
                sla_target = self.config.REVIEW_SLA_HOURS
                is_breached = biz_time.business_hours > sla_target
                if is_breached:
                    repo_overdue_counts[rid] += 1

                analyzed_items.append({
                    "id": pid,
                    "repo_id": rid,
                    "repo_name": repo_name,
                    "title": title,
                    "status": status,
                    "author_id": author_id,
                    "author_name": author_name,
                    "created_date": created_dt.isoformat() if created_dt else None,
                    "is_draft": is_draft,
                    "additions": additions,
                    "deletions": deletions,
                    "lines_changed": additions + deletions,
                    "comment_count": comment_count,
                    "business_waiting_hours": round(biz_time.business_hours, 2),
                    "calendar_waiting_hours": round(biz_time.calendar_hours, 2),
                    "non_working_hours": round(biz_time.non_working_hours, 2),
                    "sla_target_hours": sla_target,
                    "sla_breached": is_breached,
                    "sla_status": "BREACHED" if is_breached else ("AT_RISK" if biz_time.business_hours > 0.75 * sla_target else "HEALTHY"),
                    "sla_ratio": round(biz_time.business_hours / sla_target, 2) if sla_target > 0 else 0.0,
                    "is_bot_filtered": qual_review.is_bot_filtered,
                    "raw_created_dt": created_dt,
                })

        # Second pass: calculate priority scores with backlog pressure
        results = []
        for item in analyzed_items:
            rid = item["repo_id"]
            other_overdue = max(0, repo_overdue_counts.get(rid, 0) - (1 if item["sla_breached"] else 0))
            baseline = baselines_map.get(rid)

            priority = calculate_bottleneck_priority(
                business_waiting_hours=item["business_waiting_hours"],
                sla_target_hours=item["sla_target_hours"],
                is_draft=item["is_draft"],
                additions=item["additions"],
                deletions=item["deletions"],
                repo_baseline=baseline,
                other_overdue_in_repo=other_overdue,
            )

            item["priority_score"] = priority.total_score
            item["priority_level"] = priority.priority_level
            item["priority_factors"] = [f.to_dict() for f in priority.factors]
            item["repo_baseline"] = baseline.to_dict() if baseline else None
            results.append(item)

        # Sort by priority score descending, then by business waiting hours descending
        results.sort(key=lambda x: (x["priority_score"], x["business_waiting_hours"]), reverse=True)
        return results

    def get_metrics_summary(self, db: Session, repo_id: Optional[str] = None) -> Dict[str, Any]:
        """Calculates executive summary metrics: breach rate, counts, medians, and distortion."""
        bottlenecks = self.analyze_bottlenecks(db, repo_id=repo_id)
        repos = self.get_repositories(db)

        total_open = sum(r["open_prs"] for r in repos) if not repo_id or repo_id == "all" else next((r["open_prs"] for r in repos if r["id"] == repo_id), 0)
        awaiting_review = len(bottlenecks)
        breached_count = sum(1 for b in bottlenecks if b["sla_breached"])
        breach_rate = round((breached_count / awaiting_review * 100), 1) if awaiting_review > 0 else 0.0

        business_waits = [b["business_waiting_hours"] for b in bottlenecks]
        calendar_waits = [b["calendar_waiting_hours"] for b in bottlenecks]

        import statistics
        median_biz = round(statistics.median(business_waits), 2) if business_waits else 0.0
        median_cal = round(statistics.median(calendar_waits), 2) if calendar_waits else 0.0
        total_non_working_saved = round(sum(b["non_working_hours"] for b in bottlenecks), 1)

        return {
            "total_open_prs": total_open,
            "awaiting_review_count": awaiting_review,
            "sla_breached_count": breached_count,
            "sla_breach_rate": breach_rate,
            "median_business_wait_hours": median_biz,
            "median_calendar_wait_hours": median_cal,
            "non_working_hours_filtered": total_non_working_saved,
            "configured_sla_hours": self.config.REVIEW_SLA_HOURS,
            "timezone": self.config.TIMEZONE,
            "working_hours": f"{self.config.WORK_START_TIME} - {self.config.WORK_END_TIME}",
        }

    def get_backlog_trend(self, db: Session, days: int = 30) -> List[Dict[str, Any]]:
        """Calculates daily PR activity and open backlog trend over the lookback window."""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        sql = text("""
            SELECT 
                DATE(created_date) AS date_str,
                COUNT(id) AS opened_count,
                SUM(CASE WHEN merged_date IS NOT NULL THEN 1 ELSE 0 END) AS merged_count
            FROM pull_requests
            WHERE created_date >= :start_date
            GROUP BY DATE(created_date)
            ORDER BY date_str ASC;
        """)
        rows = db.execute(sql, {"start_date": start_date}).fetchall()

        trend = []
        cumulative_backlog = 0
        for r in rows:
            d_str = str(r[0])
            opened = int(r[1] or 0)
            merged = int(r[2] or 0)
            cumulative_backlog = max(0, cumulative_backlog + opened - merged)
            trend.append({
                "date": d_str,
                "opened": opened,
                "merged": merged,
                "net_change": opened - merged,
                "backlog_estimate": cumulative_backlog,
            })
        return trend
