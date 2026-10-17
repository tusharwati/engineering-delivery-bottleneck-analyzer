from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo
from app.analytics.business_hours import calculate_business_hours, is_business_time


def test_intraday_business_hours():
    """Tests normal working hour calculation on the same working day."""
    # Wednesday in Asia/Kolkata (UTC+05:30)
    start = datetime(2026, 10, 14, 10, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 10, 14, 14, 30, 0, tzinfo=timezone.utc)

    # 4.5 hours
    res = calculate_business_hours(start, end, tz_name="UTC", work_days=[0, 1, 2, 3, 4], work_start=time(9, 0), work_end=time(18, 0))
    assert res.business_hours == 4.5
    assert res.calendar_hours == 4.5
    assert res.non_working_hours == 0.0


def test_weekend_bridge_edge_case():
    """
    Critical Edge Case:
    PR opened Friday at 18:00 IST (UTC 12:30).
    Reviewed Monday at 10:00 IST (UTC 04:30).
    Work schedule: Mon-Fri, 09:30 - 18:30 IST.
    """
    tz = "Asia/Kolkata"
    # Friday 18:00 IST = 2026-10-16 12:30 UTC
    fri_open = datetime(2026, 10, 16, 12, 30, 0, tzinfo=timezone.utc)
    # Monday 10:00 IST = 2026-10-19 04:30 UTC
    mon_review = datetime(2026, 10, 19, 4, 30, 0, tzinfo=timezone.utc)

    res = calculate_business_hours(
        fri_open,
        mon_review,
        tz_name=tz,
        work_days=[0, 1, 2, 3, 4],
        work_start=time(9, 30),
        work_end=time(18, 30),
    )

    # Friday 18:00-18:30 = 0.5 hours
    # Monday 09:30-10:00 = 0.5 hours
    # Total business hours = 1.0 hour
    assert round(res.business_hours, 2) == 1.0
    # Elapsed calendar time: Friday 18:00 to Monday 10:00 = 64.0 hours
    assert round(res.calendar_hours, 2) == 64.0
    assert round(res.non_working_hours, 2) == 63.0


def test_holiday_exclusion():
    """Tests that designated holidays accrue zero business hours."""
    # Republic Day holiday: Jan 26, 2026 (Monday)
    holidays = {date(2026, 1, 26)}

    # Created Friday Jan 23 at 17:30 IST (1h before 18:30 close)
    start = datetime(2026, 1, 23, 12, 0, 0, tzinfo=timezone.utc)  # Fri 17:30 IST
    # Reviewed Tuesday Jan 27 at 10:30 IST (1h after 09:30 open)
    end = datetime(2026, 1, 27, 5, 0, 0, tzinfo=timezone.utc)  # Tue 10:30 IST

    res = calculate_business_hours(
        start,
        end,
        tz_name="Asia/Kolkata",
        work_days=[0, 1, 2, 3, 4],
        work_start=time(9, 30),
        work_end=time(18, 30),
        holidays=holidays,
    )

    # Friday gives 1.0 hour (17:30 to 18:30)
    # Saturday (weekend) = 0h
    # Sunday (weekend) = 0h
    # Monday (Jan 26 holiday) = 0h
    # Tuesday gives 1.0 hour (09:30 to 10:30)
    # Total business hours = 2.0 hours
    assert round(res.business_hours, 2) == 2.0


def test_off_hours_and_weekend_creation():
    """PR submitted Sunday afternoon starts accruing time only at business open on Monday."""
    # Sunday 14:00 IST
    sun_start = datetime(2026, 10, 18, 8, 30, 0, tzinfo=timezone.utc)
    # Monday 11:30 IST (2 hours after 09:30 open)
    mon_review = datetime(2026, 10, 19, 6, 0, 0, tzinfo=timezone.utc)

    res = calculate_business_hours(
        sun_start,
        mon_review,
        tz_name="Asia/Kolkata",
        work_days=[0, 1, 2, 3, 4],
        work_start=time(9, 30),
        work_end=time(18, 30),
    )

    assert round(res.business_hours, 2) == 2.0


def test_dst_transition_safety():
    """Tests that Daylight Saving Time clock shift does not cause arithmetic error or exception."""
    # US Eastern DST Spring forward on Sunday March 8, 2026
    # Created Friday March 6, 16:00 EST; Reviewed Monday March 9, 10:00 EDT
    fri_open = datetime(2026, 3, 6, 21, 0, 0, tzinfo=timezone.utc)  # Fri 16:00 EST
    mon_review = datetime(2026, 3, 9, 14, 0, 0, tzinfo=timezone.utc)  # Mon 10:00 EDT

    res = calculate_business_hours(
        fri_open,
        mon_review,
        tz_name="America/New_York",
        work_days=[0, 1, 2, 3, 4],
        work_start=time(9, 0),
        work_end=time(17, 0),
    )

    # Fri: 16:00 to 17:00 = 1.0h
    # Mon: 09:00 to 10:00 = 1.0h
    # Total = 2.0h
    assert round(res.business_hours, 2) == 2.0


def test_end_before_start():
    """PR with end before start returns zero durations safely."""
    t1 = datetime(2026, 10, 15, 12, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 10, 15, 11, 0, 0, tzinfo=timezone.utc)
    res = calculate_business_hours(t1, t2)
    assert res.business_hours == 0.0
    assert res.calendar_hours == 0.0
    assert res.non_working_hours == 0.0

