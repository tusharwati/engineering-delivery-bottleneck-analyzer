import time
from datetime import datetime, timezone
from app.analytics.analyzer_service import BottleneckAnalyzerService


def test_comparative_evaluation_execution(devlake_db_session):
    """
    Executes a formal, repeatable benchmark comparison between:
    1. Naive Wall-Clock Model
    2. Business-Hours-Aware Model
    Records execution latency, false alarm reductions, and distortion filtering.
    """
    service = BottleneckAnalyzerService()

    start_timer = time.perf_counter()
    bottlenecks = service.analyze_bottlenecks(devlake_db_session)
    elapsed_ms = (time.perf_counter() - start_timer) * 1000.0

    assert len(bottlenecks) > 0

    sla_hours = service.config.REVIEW_SLA_HOURS

    # 1. Naive wall-clock breaches
    naive_breaches = [b for b in bottlenecks if b["calendar_waiting_hours"] > sla_hours]

    # 2. Business-hours breaches
    business_breaches = [b for b in bottlenecks if b["business_waiting_hours"] > sla_hours]

    # 3. False positive alerts (PRs flagged as breaches by wall-clock that were actually within business SLA)
    false_positives = [
        b for b in bottlenecks
        if b["calendar_waiting_hours"] > sla_hours and b["business_waiting_hours"] <= sla_hours
    ]

    # Verification:
    # Business-hours calculation should eliminate weekend/off-hour false alarms
    assert len(false_positives) > 0
    assert len(naive_breaches) > len(business_breaches)

    # Verification of bot unmasking
    bot_filtered_prs = [b for b in bottlenecks if b.get("is_bot_filtered")]
    assert len(bot_filtered_prs) > 0

    # Verification of performance: sub-100ms execution across sample PRs
    assert elapsed_ms < 100.0
