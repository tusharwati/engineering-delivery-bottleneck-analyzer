from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from app.analytics.baselines import RepositoryBaseline
from app.config import settings


@dataclass
class FactorExplanation:
    name: str
    score: int
    max_score: int
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "score": self.score,
            "max_score": self.max_score,
            "reason": self.reason,
        }


@dataclass
class PriorityBreakdown:
    total_score: int
    priority_level: str  # CRITICAL, HIGH, MEDIUM, LOW
    factors: List[FactorExplanation] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_score": self.total_score,
            "priority_level": self.priority_level,
            "factors": [f.to_dict() for f in self.factors],
        }


def calculate_bottleneck_priority(
    business_waiting_hours: float,
    sla_target_hours: float,
    is_draft: bool,
    additions: int,
    deletions: int,
    repo_baseline: Optional[RepositoryBaseline],
    other_overdue_in_repo: int = 0,
) -> PriorityBreakdown:
    """
    Computes a transparent, rule-based bottleneck priority score (0-100)
    with human-readable explainability for each contributing factor.
    Note: Strictly measures PR urgency and queue health; does NOT rank developers.
    """
    factors: List[FactorExplanation] = []
    total = 0

    # 1. SLA Breach Factor (Max 40 pts)
    sla_ratio = (business_waiting_hours / sla_target_hours) if sla_target_hours > 0 else 0.0
    if sla_ratio >= 2.5:
        sla_score = 40
        sla_reason = f"Severely overdue: {business_waiting_hours:.1f}h business wait ({int(sla_ratio*100)}% of {sla_target_hours:.0f}h SLA)"
    elif sla_ratio >= 1.0:
        sla_score = min(40, int(16 * sla_ratio))
        sla_reason = f"Exceeded review SLA: {business_waiting_hours:.1f}h business wait ({int(sla_ratio*100)}% of target)"
    elif sla_ratio >= 0.75:
        sla_score = int(8 * sla_ratio)
        sla_reason = f"At risk of SLA breach: {business_waiting_hours:.1f}h business wait ({int(sla_ratio*100)}% of target)"
    else:
        sla_score = 0
        sla_reason = f"Within SLA window: {business_waiting_hours:.1f}h business wait ({int(sla_ratio*100)}% of target)"

    factors.append(FactorExplanation("SLA Breach Severity", sla_score, 40, sla_reason))
    total += sla_score

    # 2. PR State & Readiness Factor (Max 20 pts)
    if is_draft:
        state_score = 0
        state_reason = "PR marked as Draft/WIP (lower triage urgency until marked ready)"
    else:
        state_score = 20
        state_reason = "PR is open and ready for immediate review"

    factors.append(FactorExplanation("Review Readiness", state_score, 20, state_reason))
    total += state_score

    # 3. Repository Baseline Deviation Factor (Max 20 pts)
    baseline_score = 0
    if repo_baseline and repo_baseline.status == "SUFFICIENT_SAMPLE":
        if business_waiting_hours > repo_baseline.p90_hours:
            baseline_score = 20
            baseline_reason = (
                f"Exceeds 90% of repository historical reviews (P90: {repo_baseline.p90_hours:.1f}h)"
            )
        elif business_waiting_hours > repo_baseline.median_hours:
            baseline_score = 10
            baseline_reason = (
                f"Exceeds repository historical median review time ({repo_baseline.median_hours:.1f}h)"
            )
        else:
            baseline_score = 0
            baseline_reason = f"Within normal repository velocity (Median: {repo_baseline.median_hours:.1f}h)"
    else:
        baseline_score = 0
        baseline_reason = "Repository baseline has insufficient historical sample (transparent fallback)"

    factors.append(FactorExplanation("Repo Benchmark Deviation", baseline_score, 20, baseline_reason))
    total += baseline_score

    # 4. PR Size & Review Feasibility Factor (Max 10 pts)
    lines_changed = max(0, additions + deletions)
    if lines_changed < 100:
        size_score = 10
        size_reason = f"Compact diff ({lines_changed} lines) - quick review unblock opportunity"
    elif lines_changed <= 500:
        size_score = 5
        size_reason = f"Moderate diff ({lines_changed} lines) - standard review effort"
    else:
        size_score = 2
        size_reason = f"Large diff ({lines_changed} lines) - requires extensive architectural review"

    factors.append(FactorExplanation("Diff Size & Review Effort", size_score, 10, size_reason))
    total += size_score

    # 5. Repository Backlog Pressure Factor (Max 10 pts)
    backlog_score = min(10, other_overdue_in_repo * 2)
    if other_overdue_in_repo > 0:
        backlog_reason = f"{other_overdue_in_repo} other overdue PR(s) in this repository causing queue congestion"
    else:
        backlog_reason = "No other overdue PRs in this repository queue"

    factors.append(FactorExplanation("Queue Congestion", backlog_score, 10, backlog_reason))
    total += backlog_score

    # Clamping
    final_score = min(100, max(0, total))

    if final_score >= 75:
        level = "CRITICAL"
    elif final_score >= 50:
        level = "HIGH"
    elif final_score >= 25:
        level = "MEDIUM"
    else:
        level = "LOW"

    return PriorityBreakdown(
        total_score=final_score,
        priority_level=level,
        factors=factors,
    )

