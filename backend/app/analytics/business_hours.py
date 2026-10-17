from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, List, Optional, Set
from zoneinfo import ZoneInfo
from app.config import settings


@dataclass
class BusinessHoursResult:
    business_hours: float
    calendar_hours: float
    non_working_hours: float

    def to_dict(self):
        return {
            "business_hours": round(self.business_hours, 2),
            "calendar_hours": round(self.calendar_hours, 2),
            "non_working_hours": round(self.non_working_hours, 2),
        }


def ensure_timezone_aware(dt: Any, tz: ZoneInfo) -> datetime:
    """Ensures datetime is timezone-aware and normalized to the target timezone."""
    if isinstance(dt, str):
        # Handle string timestamps from SQLite (e.g. '2026-10-09 03:00:00.000000')
        clean_str = dt.replace(" ", "T")
        dt = datetime.fromisoformat(clean_str)

    if dt.tzinfo is None:
        # Naive datetime from DB is assumed to be stored in UTC
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(tz)


def is_business_time(
    dt: datetime,
    tz_name: Optional[str] = None,
    work_days: Optional[List[int]] = None,
    work_start: Optional[time] = None,
    work_end: Optional[time] = None,
    holidays: Optional[Set[date]] = None,
) -> bool:
    """Returns True if the given timestamp falls strictly within configured business hours."""
    tz = ZoneInfo(tz_name or settings.TIMEZONE)
    local_dt = ensure_timezone_aware(dt, tz)

    w_days = work_days if work_days is not None else settings.work_days_list
    h_set = holidays if holidays is not None else settings.holidays_set
    w_start = work_start or settings.work_start_parsed
    w_end = work_end or settings.work_end_parsed

    if local_dt.weekday() not in w_days:
        return False
    if local_dt.date() in h_set:
        return False
    return w_start <= local_dt.time() < w_end


def calculate_business_hours(
    start_dt: datetime,
    end_dt: datetime,
    tz_name: Optional[str] = None,
    work_days: Optional[List[int]] = None,
    work_start: Optional[time] = None,
    work_end: Optional[time] = None,
    holidays: Optional[Set[date]] = None,
) -> BusinessHoursResult:
    """
    Computes exact business hours between two timestamps.
    Correctly excludes weekends, off-hours, and recognized holidays,
    and safely handles Daylight Saving Time (DST) shifts.
    """
    tz = ZoneInfo(tz_name or settings.TIMEZONE)
    local_start = ensure_timezone_aware(start_dt, tz)
    local_end = ensure_timezone_aware(end_dt, tz)

    if local_end <= local_start:
        return BusinessHoursResult(0.0, 0.0, 0.0)

    total_calendar_seconds = (local_end - local_start).total_seconds()
    calendar_hours = total_calendar_seconds / 3600.0

    w_days = set(work_days if work_days is not None else settings.work_days_list)
    h_set = holidays if holidays is not None else settings.holidays_set
    w_start = work_start or settings.work_start_parsed
    w_end = work_end or settings.work_end_parsed

    total_business_seconds = 0.0
    current_date = local_start.date()
    end_date = local_end.date()

    while current_date <= end_date:
        if current_date.weekday() in w_days and current_date not in h_set:
            # Construct daily business window in target timezone
            day_biz_start = datetime.combine(current_date, w_start, tzinfo=tz)
            day_biz_end = datetime.combine(current_date, w_end, tzinfo=tz)

            overlap_start = max(local_start, day_biz_start)
            overlap_end = min(local_end, day_biz_end)

            if overlap_end > overlap_start:
                total_business_seconds += (overlap_end - overlap_start).total_seconds()

        current_date += timedelta(days=1)

    business_hours = total_business_seconds / 3600.0
    non_working_hours = max(0.0, calendar_hours - business_hours)

    return BusinessHoursResult(
        business_hours=business_hours,
        calendar_hours=calendar_hours,
        non_working_hours=non_working_hours,
    )
