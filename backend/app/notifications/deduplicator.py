from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.config import settings
from app.database.models_app import AlertDeduplication
from app.logger import logger


class AlertDeduplicator:
    """
    Prevents repeated, duplicate alert spamming for the same bottleneck condition
    using local SQLite state.
    """

    def __init__(self, cooldown_hours: int = 24):
        self.cooldown_hours = cooldown_hours

    def make_dedup_key(self, alert_type: str, entity_id: str) -> str:
        """Constructs a deterministic deduplication key."""
        return f"{alert_type}:{entity_id}"

    def should_suppress_alert(self, db: Session, alert_type: str, entity_id: str) -> bool:
        """
        Returns True if an alert of this type for this entity was already dispatched
        within the cooldown window.
        """
        now = datetime.now(timezone.utc)
        key = self.make_dedup_key(alert_type, entity_id)

        # Remove timezone info if comparing with naive SQLite datetimes
        existing = (
            db.query(AlertDeduplication)
            .filter(AlertDeduplication.dedup_key == key)
            .first()
        )

        if not existing:
            return False

        # Check if expired
        expires = existing.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)

        if now >= expires:
            # Expired, clean up record
            db.delete(existing)
            db.commit()
            return False

        return True

    def record_alert(self, db: Session, alert_type: str, entity_id: str):
        """Records that an alert was dispatched and sets the expiration timestamp."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=self.cooldown_hours)
        key = self.make_dedup_key(alert_type, entity_id)

        existing = (
            db.query(AlertDeduplication)
            .filter(AlertDeduplication.dedup_key == key)
            .first()
        )

        if existing:
            existing.created_at = now
            existing.expires_at = expires
        else:
            new_record = AlertDeduplication(
                dedup_key=key,
                alert_type=alert_type,
                entity_id=entity_id,
                created_at=now,
                expires_at=expires,
            )
            db.add(new_record)

        db.commit()

