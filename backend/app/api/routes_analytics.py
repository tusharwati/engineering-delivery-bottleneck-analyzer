from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.analytics.analyzer_service import BottleneckAnalyzerService
from app.database.devlake_session import get_devlake_db

router = APIRouter(prefix="/api", tags=["Analytics & Bottlenecks"])
service = BottleneckAnalyzerService()


@router.get("/bottlenecks", summary="Fetch Prioritized Open Pull Request Bottlenecks")
def get_bottlenecks(
    repo_id: Optional[str] = Query(None, description="Repository ID or 'all'"),
    sla_status: Optional[str] = Query(None, description="Filter: BREACHED, AT_RISK, HEALTHY"),
    min_priority: Optional[int] = Query(0, description="Minimum priority score (0-100)"),
    db: Session = Depends(get_devlake_db),
):
    """
    Returns open pull requests currently waiting for a qualifying code review,
    scored and ordered by bottleneck urgency with full explainability breakdown.
    """
    bottlenecks = service.analyze_bottlenecks(db, repo_id=repo_id)

    if sla_status:
        bottlenecks = [b for b in bottlenecks if b["sla_status"] == sla_status.upper()]
    if min_priority and min_priority > 0:
        bottlenecks = [b for b in bottlenecks if b["priority_score"] >= min_priority]

    return {
        "count": len(bottlenecks),
        "repo_id_filter": repo_id or "all",
        "bottlenecks": bottlenecks,
    }


@router.get("/metrics/summary", summary="Executive Review Queue Summary KPIs")
def get_metrics_summary(
    repo_id: Optional[str] = Query(None, description="Repository ID or 'all'"),
    db: Session = Depends(get_devlake_db),
):
    """
    Returns high-level KPI cards: total open, waiting, SLA breach count, breach rate,
    medians, and non-working hours distortion filtered.
    """
    return service.get_metrics_summary(db, repo_id=repo_id)


@router.get("/repositories", summary="Repository-Level Benchmark Overviews")
def get_repositories(db: Session = Depends(get_devlake_db)):
    """
    Returns all connected repositories along with their learned historical baselines (Median, P90).
    """
    repos = service.get_repositories(db)
    repo_ids = [r["id"] for r in repos]
    baselines = service.get_repo_baselines(db, repo_ids)

    results = []
    for r in repos:
        rid = r["id"]
        b = baselines.get(rid)
        r_copy = dict(r)
        r_copy["baseline"] = b.to_dict() if b else None
        results.append(r_copy)

    return {"repositories": results}


@router.get("/backlog/trend", summary="Review Backlog Trend Over Time")
def get_backlog_trend(
    days: int = Query(30, ge=7, le=90, description="Trailing lookback days"),
    db: Session = Depends(get_devlake_db),
):
    """
    Returns daily PR arrivals, merges, and estimated active backlog curve.
    """
    trend = service.get_backlog_trend(db, days=days)
    return {"days": days, "trend": trend}


@router.get("/evaluation/compare", summary="Comparative Evaluation: Wall-Clock vs Business-Hours")
def get_comparative_evaluation(db: Session = Depends(get_devlake_db)):
    """
    Provides a real-time side-by-side comparative evaluation of the naive wall-clock SLA
    versus the business-hours-aware SLA across current pull requests.
    """
    bottlenecks = service.analyze_bottlenecks(db)

    total_evaluated = len(bottlenecks)
    sla_hours = service.config.REVIEW_SLA_HOURS

    # Naive wall-clock: breached if calendar_waiting_hours > sla_hours
    naive_breaches = [b for b in bottlenecks if b["calendar_waiting_hours"] > sla_hours]
    # Business-hours: breached if business_waiting_hours > sla_hours
    biz_breaches = [b for b in bottlenecks if b["business_waiting_hours"] > sla_hours]

    # False positive alerts produced by naive wall-clock (e.g. over weekend)
    false_positives = [
        b for b in bottlenecks
        if b["calendar_waiting_hours"] > sla_hours and b["business_waiting_hours"] <= sla_hours
    ]

    import statistics
    cal_times = [b["calendar_waiting_hours"] for b in bottlenecks]
    biz_times = [b["business_waiting_hours"] for b in bottlenecks]

    return {
        "dataset_size": total_evaluated,
        "configured_sla_target_hours": sla_hours,
        "naive_wall_clock": {
            "total_breaches": len(naive_breaches),
            "breach_rate_pct": round(len(naive_breaches) / total_evaluated * 100, 1) if total_evaluated else 0,
            "mean_waiting_hours": round(statistics.mean(cal_times), 1) if cal_times else 0,
            "median_waiting_hours": round(statistics.median(cal_times), 1) if cal_times else 0,
        },
        "business_hours_aware": {
            "total_breaches": len(biz_breaches),
            "breach_rate_pct": round(len(biz_breaches) / total_evaluated * 100, 1) if total_evaluated else 0,
            "mean_waiting_hours": round(statistics.mean(biz_times), 1) if biz_times else 0,
            "median_waiting_hours": round(statistics.median(biz_times), 1) if biz_times else 0,
        },
        "distortion_analysis": {
            "false_positive_alerts_eliminated": len(false_positives),
            "false_alert_reduction_pct": (
                round(len(false_positives) / len(naive_breaches) * 100, 1)
                if len(naive_breaches) > 0 else 0.0
            ),
            "bot_comments_filtered_count": sum(1 for b in bottlenecks if b.get("is_bot_filtered")),
            "total_non_working_hours_filtered": round(sum(b["non_working_hours"] for b in bottlenecks), 1),
        },
        "false_positive_examples": [
            {
                "id": b["id"],
                "title": b["title"],
                "repo_name": b["repo_name"],
                "calendar_hours": b["calendar_waiting_hours"],
                "business_hours": b["business_waiting_hours"],
                "explanation": "Flagged by wall-clock due to non-working hours / weekend; within business SLA.",
            }
            for b in false_positives[:5]
        ],
    }

