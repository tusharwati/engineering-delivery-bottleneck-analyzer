from datetime import datetime, timedelta, timezone
from app.database.models_app import AlertAuditLog, AlertDeduplication
from app.logger import redact_sensitive
from app.notifications.alert_service import AlertService
from app.notifications.deduplicator import AlertDeduplicator
from app.notifications.slack import format_slack_payload, send_slack_notification


def test_deduplication_lifecycle(app_db_session):
    """Tests alert suppression within cooldown and expiration behavior."""
    dedup = AlertDeduplicator(cooldown_hours=24)
    entity_id = "test_pr_999"
    alert_type = "SLA_BREACH"

    # 1. First check: should not suppress
    assert dedup.should_suppress_alert(app_db_session, alert_type, entity_id) is False

    # 2. Record alert
    dedup.record_alert(app_db_session, alert_type, entity_id)

    # 3. Second check immediately: MUST suppress
    assert dedup.should_suppress_alert(app_db_session, alert_type, entity_id) is True

    # 4. Simulate expiration by updating expires_at to the past
    rec = app_db_session.query(AlertDeduplication).filter_by(entity_id=entity_id).first()
    rec.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    app_db_session.commit()

    # 5. Check again: expired, should not suppress
    assert dedup.should_suppress_alert(app_db_session, alert_type, entity_id) is False


def test_dry_run_slack_notifier():
    """Tests that dry-run mode returns safe DRY_RUN status without network transmission."""
    payload = format_slack_payload(
        pr_id="test_pr_1",
        pr_title="Fix memory leak in buffer",
        repo_name="apache/devlake-core",
        author_name="alice",
        business_waiting_hours=14.5,
        calendar_waiting_hours=64.0,
        sla_target_hours=8.0,
        priority_score=85,
        priority_level="CRITICAL",
        factors=[{"name": "SLA Severity", "score": 40, "reason": "14.5h wait"}],
    )

    res = send_slack_notification(payload=payload, dry_run=True)
    assert res["status"] == "DRY_RUN"
    assert res["sent"] is False


def test_token_redaction():
    """Tests that Slack webhook URLs and tokens are cleanly masked."""
    sensitive_url = "https://hooks.slack.com/services/T12345/B67890/SECRET_TOKEN_XYZ"
    redacted = redact_sensitive(sensitive_url)
    assert "SECRET_TOKEN_XYZ" not in redacted
    assert "REDACTED" in redacted

    pat = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"
    assert "1234567890abcdef" not in redact_sensitive(pat)


def test_alert_service_run(devlake_db_session, app_db_session):
    """Tests end-to-end AlertService execution with deduplication and audit logging."""
    service = AlertService()
    res = service.run_alert_check(
        devlake_db=devlake_db_session,
        app_db=app_db_session,
        dry_run=True,
        min_priority_score=40,
    )

    assert "alerts_dispatched" in res
    assert res["dry_run"] is True

    # Verify audit log was recorded in SQLite
    audit_logs = app_db_session.query(AlertAuditLog).all()
    assert len(audit_logs) >= res["alerts_dispatched"]
