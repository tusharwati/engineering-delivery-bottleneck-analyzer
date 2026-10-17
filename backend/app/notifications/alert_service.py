import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.analytics.analyzer_service import BottleneckAnalyzerService
from app.config import settings
from app.database.models_app import AlertAuditLog
from app.logger import logger
from app.notifications.deduplicator import AlertDeduplicator
from app.notifications.slack import format_slack_payload, send_slack_notification


class AlertService:
    """
    Coordinates evaluation of bottleneck SLA alerts, deduplication state, and notification dispatch.
    """

    def __init__(self, analyzer: Optional[BottleneckAnalyzerService] = None):
        self.analyzer = analyzer or BottleneckAnalyzerService()
        self.deduplicator = AlertDeduplicator(cooldown_hours=settings.ALERT_COOLDOWN_HOURS)

    def run_alert_check(
        self,
        devlake_db: Session,
        app_db: Session,
        dry_run: Optional[bool] = None,
        min_priority_score: int = 50,
    ) -> Dict[str, Any]:
        """
        Scans all open PRs, identifies SLA breaches, filters via deduplication,
        dispatches Slack notifications (or logs dry run), and records audit history.
        """
        is_dry_run = dry_run if dry_run is not None else settings.ALERT_DRY_RUN
        bottlenecks = self.analyzer.analyze_bottlenecks(devlake_db)

        # Filter to breached PRs exceeding min priority threshold (defaults to HIGH/CRITICAL >= 50)
        breached_prs = [
            b for b in bottlenecks
            if b["sla_breached"] and b["priority_score"] >= min_priority_score
        ]

        total_breaches = len(breached_prs)
        alerts_dispatched = 0
        alerts_suppressed = 0
        dispatched_details: List[Dict[str, Any]] = []

        for pr in breached_prs:
            pid = pr["id"]
            alert_type = "SLA_BREACH"

            # Check deduplication
            if self.deduplicator.should_suppress_alert(app_db, alert_type, pid):
                alerts_suppressed += 1
                continue

            # Format notification payload
            payload = format_slack_payload(
                pr_id=pid,
                pr_title=pr["title"],
                repo_name=pr["repo_name"],
                author_name=pr["author_name"],
                business_waiting_hours=pr["business_waiting_hours"],
                calendar_waiting_hours=pr["calendar_waiting_hours"],
                sla_target_hours=pr["sla_target_hours"],
                priority_score=pr["priority_score"],
                priority_level=pr["priority_level"],
                factors=pr["priority_factors"],
            )

            # Send or dry-run
            result = send_slack_notification(payload=payload, dry_run=is_dry_run)

            # Record deduplication state so this PR isn't re-alerted repeatedly
            self.deduplicator.record_alert(app_db, alert_type, pid)

            # Log audit entry in SQLite
            audit_entry = AlertAuditLog(
                alert_type=alert_type,
                entity_id=pid,
                pr_title=pr["title"],
                repo_name=pr["repo_name"],
                hours_waiting=pr["business_waiting_hours"],
                message=f"PR {pr['title']} exceeded review SLA with {pr['business_waiting_hours']}h business wait ({pr['priority_score']} pts)",
                status=result["status"],
                dry_run=is_dry_run,
                sent_at=datetime.now(timezone.utc),
                payload_json=json.dumps(payload),
            )
            app_db.add(audit_entry)
            app_db.commit()

            alerts_dispatched += 1
            dispatched_details.append({
                "pr_id": pid,
                "title": pr["title"],
                "repo_name": pr["repo_name"],
                "business_waiting_hours": pr["business_waiting_hours"],
                "priority_score": pr["priority_score"],
                "delivery_status": result["status"],
            })

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_breaches_evaluated": total_breaches,
            "alerts_dispatched": alerts_dispatched,
            "alerts_suppressed_by_dedup": alerts_suppressed,
            "dry_run": is_dry_run,
            "dispatched_details": dispatched_details,
        }
