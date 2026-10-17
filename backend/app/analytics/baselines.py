import statistics
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from app.analytics.business_hours import calculate_business_hours
from app.config import settings


@dataclass
class RepositoryBaseline:
    repo_id: str
    sample_count: int
    min_sample_required: int
    status: str  # SUFFICIENT_SAMPLE, INSUFFICIENT_SAMPLE
    median_hours: float
    p90_hours: float
    fallback_sla_hours: float
    effective_target_hours: float
    unit: str = "business_hours"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repo_id": self.repo_id,
            "sample_count": self.sample_count,
            "min_sample_required": self.min_sample_required,
            "status": self.status,
            "median_hours": round(self.median_hours, 2),
            "p90_hours": round(self.p90_hours, 2),
            "fallback_sla_hours": round(self.fallback_sla_hours, 2),
            "effective_target_hours": round(self.effective_target_hours, 2),
            "unit": self.unit,
        }


def calculate_repository_baseline(
    repo_id: str,
    historical_pr_durations: List[float],
    min_sample_size: Optional[int] = None,
    default_sla_hours: Optional[float] = None,
) -> RepositoryBaseline:
    """
    Computes statistical benchmarks (Median, P90) for a repository.
    Enforces minimum sample size gating to avoid deceptive metrics on sparse data.
    """
    min_sample = (
        min_sample_size
        if min_sample_size is not None
        else settings.MIN_HISTORICAL_SAMPLE_SIZE
    )
    fallback_sla = (
        default_sla_hours
        if default_sla_hours is not None
        else settings.REVIEW_SLA_HOURS
    )

    clean_durations = [d for d in historical_pr_durations if d >= 0.0]
    sample_count = len(clean_durations)

    if sample_count < min_sample:
        return RepositoryBaseline(
            repo_id=repo_id,
            sample_count=sample_count,
            min_sample_required=min_sample,
            status="INSUFFICIENT_SAMPLE",
            median_hours=fallback_sla,
            p90_hours=fallback_sla * 1.5,
            fallback_sla_hours=fallback_sla,
            effective_target_hours=fallback_sla,
        )

    clean_durations.sort()
    median_val = statistics.median(clean_durations)

    # Compute 90th percentile
    p90_index = int(0.90 * (sample_count - 1))
    p90_val = clean_durations[p90_index]

    return RepositoryBaseline(
        repo_id=repo_id,
        sample_count=sample_count,
        min_sample_required=min_sample,
        status="SUFFICIENT_SAMPLE",
        median_hours=median_val,
        p90_hours=p90_val,
        fallback_sla_hours=fallback_sla,
        effective_target_hours=median_val,
    )

