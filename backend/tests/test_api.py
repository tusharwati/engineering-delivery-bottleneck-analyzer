def test_health_endpoints(test_client):
    """Tests health check and schema validation endpoints."""
    res = test_client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["service"] == "engineering-delivery-bottleneck-analyzer"
    assert data["pinned_devlake_version"] == "v1.0.2"
    assert data["database_connected"] is True

    res_schema = test_client.get("/api/schema-check")
    assert res_schema.status_code == 200
    assert res_schema.json()["status"] == "HEALTHY"


def test_bottlenecks_endpoint(test_client):
    """Tests fetching open pull request bottlenecks."""
    res = test_client.get("/api/bottlenecks")
    assert res.status_code == 200
    data = res.json()
    assert "count" in data
    assert data["count"] > 0
    assert "bottlenecks" in data

    first_item = data["bottlenecks"][0]
    assert "priority_score" in first_item
    assert "priority_factors" in first_item
    assert "business_waiting_hours" in first_item
    assert "calendar_waiting_hours" in first_item
    assert "sla_status" in first_item


def test_metrics_summary_endpoint(test_client):
    """Tests summary KPIs endpoint."""
    res = test_client.get("/api/metrics/summary")
    assert res.status_code == 200
    data = res.json()
    assert "total_open_prs" in data
    assert "awaiting_review_count" in data
    assert "sla_breached_count" in data
    assert "median_business_wait_hours" in data


def test_repositories_endpoint(test_client):
    """Tests repositories listing with learned baselines."""
    res = test_client.get("/api/repositories")
    assert res.status_code == 200
    data = res.json()
    assert "repositories" in data
    assert len(data["repositories"]) > 0

    first_repo = data["repositories"][0]
    assert "baseline" in first_repo
    assert "median_hours" in first_repo["baseline"]


def test_evaluation_compare_endpoint(test_client):
    """Tests side-by-side comparative evaluation endpoint."""
    res = test_client.get("/api/evaluation/compare")
    assert res.status_code == 200
    data = res.json()
    assert "naive_wall_clock" in data
    assert "business_hours_aware" in data
    assert "distortion_analysis" in data
    assert data["distortion_analysis"]["false_positive_alerts_eliminated"] > 0


def test_alerts_and_config_endpoints(test_client):
    """Tests alert triggering, audit history, and config updates."""
    # Trigger dry-run alert check
    trigger_res = test_client.post("/api/alerts/trigger-check", json={"dry_run": True, "min_priority_score": 40})
    assert trigger_res.status_code == 200
    trigger_data = trigger_res.json()
    assert trigger_data["dry_run"] is True

    # Check alert history
    history_res = test_client.get("/api/alerts/history")
    assert history_res.status_code == 200
    assert len(history_res.json()["history"]) > 0

    # Config retrieval
    config_res = test_client.get("/api/config")
    assert config_res.status_code == 200
    assert config_res.json()["timezone"] == "Asia/Kolkata"

    # Config update
    update_res = test_client.post("/api/config", json={"review_sla_hours": 12.0})
    assert update_res.status_code == 200
    assert update_res.json()["config"]["review_sla_hours"] == 12.0
