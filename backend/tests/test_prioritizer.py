from app.analytics.baselines import RepositoryBaseline
from app.analytics.prioritizer import calculate_bottleneck_priority


def test_priority_severe_breach_calculation():
    """Tests priority scoring for a severe SLA breach on an open, small PR."""
    baseline = RepositoryBaseline(
        repo_id="test_repo",
        sample_count=20,
        min_sample_required=10,
        status="SUFFICIENT_SAMPLE",
        median_hours=5.0,
        p90_hours=10.0,
        fallback_sla_hours=8.0,
        effective_target_hours=5.0,
    )

    # 22 business hours wait on an 8.0h SLA (> 2.5x ratio = 40 pts)
    # Open non-draft = 20 pts
    # Exceeds P90 (22h > 10h) = 20 pts
    # Small PR (45 lines) = 10 pts
    # Other overdue = 3 -> 6 pts
    # Total = 40 + 20 + 20 + 10 + 6 = 96 pts (CRITICAL)
    res = calculate_bottleneck_priority(
        business_waiting_hours=22.0,
        sla_target_hours=8.0,
        is_draft=False,
        additions=35,
        deletions=10,
        repo_baseline=baseline,
        other_overdue_in_repo=3,
    )

    assert res.total_score == 96
    assert res.priority_level == "CRITICAL"
    assert len(res.factors) == 5

    # Check that each factor has a descriptive reason
    for f in res.factors:
        assert f.score >= 0
        assert len(f.reason) > 5


def test_draft_pr_lower_urgency():
    """Draft PRs should not receive the 20 readiness points."""
    res = calculate_bottleneck_priority(
        business_waiting_hours=10.0,
        sla_target_hours=8.0,
        is_draft=True,
        additions=100,
        deletions=20,
        repo_baseline=None,
    )

    readiness_factor = next(f for f in res.factors if f.name == "Review Readiness")
    assert readiness_factor.score == 0
    assert "Draft" in readiness_factor.reason

