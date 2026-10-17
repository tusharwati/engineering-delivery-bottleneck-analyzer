from app.analytics.baselines import calculate_repository_baseline


def test_sufficient_sample_baseline():
    """Tests baseline calculation with sufficient historical samples (>= 10)."""
    durations = [2.0, 3.5, 4.0, 5.0, 6.0, 7.5, 8.0, 9.0, 11.0, 14.0, 18.0, 22.0]
    res = calculate_repository_baseline(
        repo_id="test_repo",
        historical_pr_durations=durations,
        min_sample_size=10,
        default_sla_hours=8.0,
    )

    assert res.status == "SUFFICIENT_SAMPLE"
    assert res.sample_count == 12
    # Median of [2.0, 3.5, 4.0, 5.0, 6.0, 7.5, 8.0, 9.0, 11.0, 14.0, 18.0, 22.0] = (7.5 + 8.0) / 2 = 7.75
    assert res.median_hours == 7.75
    assert res.p90_hours > res.median_hours
    assert res.effective_target_hours == 7.75


def test_insufficient_sample_fallback():
    """Tests that sample count < 10 safely falls back to default SLA."""
    durations = [3.0, 4.0, 5.0]  # Only 3 samples
    res = calculate_repository_baseline(
        repo_id="sparse_repo",
        historical_pr_durations=durations,
        min_sample_size=10,
        default_sla_hours=8.0,
    )

    assert res.status == "INSUFFICIENT_SAMPLE"
    assert res.sample_count == 3
    assert res.effective_target_hours == 8.0  # Fallback to configured SLA
    assert res.fallback_sla_hours == 8.0
