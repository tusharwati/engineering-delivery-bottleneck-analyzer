from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import declarative_base

BaseApp = declarative_base()


class AlertDeduplication(BaseApp):
    """
    Tracks alert occurrences to prevent spamming notifications for the same PR or event.
    Keyed by (alert_type, entity_id, date_bucket).
    """
    __tablename__ = "alert_deduplication"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dedup_key = Column(String(255), unique=True, index=True, nullable=False)
    alert_type = Column(String(64), nullable=False)
    entity_id = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime, nullable=False)


class AlertAuditLog(BaseApp):
    """
    Permanent audit log of all alerts evaluated, whether sent live or logged in dry-run mode.
    """
    __tablename__ = "alert_audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(String(64), nullable=False)
    entity_id = Column(String(255), nullable=False)
    pr_title = Column(String(500), nullable=True)
    repo_name = Column(String(255), nullable=True)
    hours_waiting = Column(Float, nullable=True)
    message = Column(Text, nullable=False)
    status = Column(String(32), default="SUCCESS")  # SUCCESS, DRY_RUN, FAILED
    dry_run = Column(Boolean, default=True)
    sent_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    payload_json = Column(Text, nullable=True)


class AppSettingRecord(BaseApp):
    """
    Persistent key-value configuration overrides saved through API.
    """
    __tablename__ = "app_settings"

    key = Column(String(128), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

