from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.config import settings
from app.database.app_session import get_app_db
from app.database.devlake_session import get_devlake_db
from app.database.models_app import AlertAuditLog
from app.notifications.alert_service import AlertService

router = APIRouter(prefix="/api", tags=["Alerts & Configuration"])
alert_service = AlertService()


class AlertTriggerRequest(BaseModel):
    dry_run: Optional[bool] = Field(None, description="Set True to log without sending network packets")
    min_priority_score: Optional[int] = Field(50, description="Minimum priority score required to alert")


class ConfigUpdateRequest(BaseModel):
    review_sla_hours: Optional[float] = Field(None, ge=1.0, le=168.0)
    work_start_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    work_end_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    timezone: Optional[str] = None
    alert_dry_run: Optional[bool] = None


@router.get("/alerts/history", summary="Fetch Alert Notification Audit History")
def get_alert_history(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_app_db),
):
    """
    Returns recent alert audit logs recorded in the local SQLite store.
    """
    records = (
        db.query(AlertAuditLog)
        .order_by(AlertAuditLog.sent_at.desc())
        .limit(limit)
        .all()
    )

    return {
        "count": len(records),
        "history": [
            {
                "id": r.id,
                "alert_type": r.alert_type,
                "entity_id": r.entity_id,
                "pr_title": r.pr_title,
                "repo_name": r.repo_name,
                "hours_waiting": r.hours_waiting,
                "message": r.message,
                "status": r.status,
                "dry_run": r.dry_run,
                "sent_at": r.sent_at.isoformat() if r.sent_at else None,
            }
            for r in records
        ],
    }


@router.post("/alerts/trigger-check", summary="Trigger On-Demand Bottleneck Alert Check")
def trigger_alert_check(
    req: AlertTriggerRequest = AlertTriggerRequest(),
    devlake_db: Session = Depends(get_devlake_db),
    app_db: Session = Depends(get_app_db),
):
    """
    Executes an on-demand review SLA breach scan, applies deduplication,
    dispatches Slack alerts (or dry-run logs), and records audit entries.
    """
    result = alert_service.run_alert_check(
        devlake_db=devlake_db,
        app_db=app_db,
        dry_run=req.dry_run,
        min_priority_score=req.min_priority_score or 50,
    )
    return result


@router.get("/config", summary="Fetch Active Working Schedule & SLA Settings")
def get_config():
    """
    Returns active working schedule, SLA threshold, and notification settings.
    """
    return {
        "timezone": settings.TIMEZONE,
        "work_days": settings.WORK_DAYS,
        "work_start_time": settings.WORK_START_TIME,
        "work_end_time": settings.WORK_END_TIME,
        "review_sla_hours": settings.REVIEW_SLA_HOURS,
        "holidays": list(settings.holidays_set),
        "exclude_bots": settings.EXCLUDE_BOTS,
        "include_normal_comments": settings.INCLUDE_NORMAL_COMMENTS_AS_REVIEW,
        "min_historical_sample_size": settings.MIN_HISTORICAL_SAMPLE_SIZE,
        "baseline_lookback_days": settings.BASELINE_LOOKBACK_DAYS,
        "slack_configured": bool(settings.SLACK_WEBHOOK_URL),
        "alert_dry_run": settings.ALERT_DRY_RUN,
        "alert_cooldown_hours": settings.ALERT_COOLDOWN_HOURS,
    }


@router.post("/config", summary="Update Runtime Settings")
def update_config(req: ConfigUpdateRequest):
    """
    Updates runtime settings for this session.
    """
    if req.review_sla_hours is not None:
        settings.REVIEW_SLA_HOURS = req.review_sla_hours
    if req.work_start_time is not None:
        settings.WORK_START_TIME = req.work_start_time
    if req.work_end_time is not None:
        settings.WORK_END_TIME = req.work_end_time
    if req.timezone is not None:
        settings.TIMEZONE = req.timezone
    if req.alert_dry_run is not None:
        settings.ALERT_DRY_RUN = req.alert_dry_run

    return {
        "status": "UPDATED",
        "message": "Runtime configuration updated successfully.",
        "config": get_config(),
    }
