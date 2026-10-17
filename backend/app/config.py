import json
from datetime import date, time
from typing import List, Set
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings for Engineering Delivery Bottleneck Analyzer.
    Loads configurations from environment variables or .env file.
    """

    # Database Connections
    DEVLAKE_DB_URL: str = Field(
        default="sqlite:///./data/mock_devlake.db",
        description="SQLAlchemy database URL for Apache DevLake (read-only)",
    )
    APP_DB_URL: str = Field(
        default="sqlite:///./data/app_state.db",
        description="Local SQLite database URL for alert deduplication and config",
    )

    # Business Hours & Work Schedule Configuration
    TIMEZONE: str = Field(
        default="Asia/Kolkata",
        description="IANA timezone identifier (e.g. Asia/Kolkata, UTC, America/New_York)",
    )
    WORK_DAYS: str = Field(
        default="0,1,2,3,4",
        description="Comma-separated ISO weekday numbers (0=Monday, 6=Sunday)",
    )
    WORK_START_TIME: str = Field(
        default="09:30",
        description="Daily business opening time in HH:MM (24-hour)",
    )
    WORK_END_TIME: str = Field(
        default="18:30",
        description="Daily business closing time in HH:MM (24-hour)",
    )
    REVIEW_SLA_HOURS: float = Field(
        default=8.0,
        description="Target business hours for PR first review SLA",
    )
    HOLIDAYS_JSON: str = Field(
        default='["2026-01-01","2026-01-26","2026-08-15","2026-10-02","2026-12-25"]',
        description="JSON array of recognized holiday dates in YYYY-MM-DD",
    )

    # Review Event & Bot Qualification Filters
    EXCLUDE_BOTS: bool = Field(
        default=True,
        description="Filter automated bot and CI service accounts from qualifying reviews",
    )
    INCLUDE_NORMAL_COMMENTS_AS_REVIEW: bool = Field(
        default=False,
        description="Count non-author general discussion comments as review events",
    )
    MIN_HISTORICAL_SAMPLE_SIZE: int = Field(
        default=10,
        description="Minimum sample size of historical PRs required for learned repo baseline",
    )
    BASELINE_LOOKBACK_DAYS: int = Field(
        default=30,
        description="Trailing lookback window in days for repository historical baseline",
    )

    # Automated Alerts & Slack Integration
    SLACK_WEBHOOK_URL: str = Field(
        default="",
        description="Optional Slack incoming webhook URL for notifications",
    )
    ALERT_DRY_RUN: bool = Field(
        default=True,
        description="Dry run mode: logs payload without sending outbound network requests",
    )
    ALERT_COOLDOWN_HOURS: int = Field(
        default=24,
        description="Hours to wait before resending alert for the same PR breach",
    )
    POLL_INTERVAL_MINUTES: int = Field(
        default=30,
        description="Background polling interval for automated alerts",
    )

    # Server Options
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,*"
    DEMO_MODE: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def work_days_list(self) -> List[int]:
        """Parsed list of working ISO weekday numbers."""
        return [int(d.strip()) for d in self.WORK_DAYS.split(",") if d.strip()]

    @property
    def work_start_parsed(self) -> time:
        """Parsed work start time."""
        parts = [int(p) for p in self.WORK_START_TIME.split(":")]
        return time(hour=parts[0], minute=parts[1])

    @property
    def work_end_parsed(self) -> time:
        """Parsed work end time."""
        parts = [int(p) for p in self.WORK_END_TIME.split(":")]
        return time(hour=parts[0], minute=parts[1])

    @property
    def holidays_set(self) -> Set[date]:
        """Parsed set of holiday dates."""
        try:
            raw = json.loads(self.HOLIDAYS_JSON)
            return {date.fromisoformat(d) for d in raw}
        except Exception:
            return set()

    @property
    def cors_origins_list(self) -> List[str]:
        """Parsed list of allowed CORS origins."""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


# Global singleton settings
settings = Settings()

