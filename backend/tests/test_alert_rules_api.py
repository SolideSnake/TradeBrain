def test_alert_rules_crud_and_reset_counters(client):
    payload = {
        "name": "NVDA 52W 回撤提醒",
        "enabled": True,
        "source": "watchlist",
        "symbol": "nvda",
        "metric": "drawdown_52w",
        "operator": "above",
        "threshold_value": "5",
    }

    create_response = client.post("/api/alert-rules", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["symbol"] == "NVDA"
    assert created["category"] == "threshold"
    assert created["cooldown_seconds"] == 3600
    assert created["edge_only"] is True
    assert created["sent_count"] == 0
    assert created["failed_count"] == 0
    assert created["suppressed_count"] == 0

    list_response = client.get("/api/alert-rules")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    update_response = client.patch(
        f"/api/alert-rules/{created['id']}",
        json={"enabled": False},
    )
    assert update_response.status_code == 200
    assert update_response.json()["enabled"] is False

    reset_response = client.post("/api/alert-rules/reset-counters")
    assert reset_response.status_code == 200
    assert reset_response.json()[0]["sent_count"] == 0
    assert reset_response.json()[0]["failed_count"] == 0

    delete_response = client.delete(f"/api/alert-rules/{created['id']}")
    assert delete_response.status_code == 204


def test_alert_rule_metadata_exposes_templates(client):
    response = client.get("/api/alert-rules/metadata")

    assert response.status_code == 200
    metadata = response.json()
    assert {source["value"] for source in metadata["sources"]} == {"watchlist", "portfolio"}
    assert any(template["id"] == "price_below" for template in metadata["templates"])
    assert any(metric["value"] == "drawdown_52w" for metric in metadata["metrics"])


def test_disabled_alert_rule_does_not_trigger(client):
    client.post(
        "/api/watchlist",
        json={"symbol": "NVDA"},
    )
    client.post(
        "/api/alert-rules",
        json={
            "name": "NVDA 当前价提醒",
            "enabled": False,
            "source": "watchlist",
            "symbol": "NVDA",
            "metric": "current_price",
            "operator": "above",
            "threshold_value": "1",
        },
    )

    refresh_response = client.post("/api/snapshot/refresh")
    assert refresh_response.status_code == 200

    rules_response = client.get("/api/alert-rules")
    rule = rules_response.json()[0]
    assert rule["sent_count"] == 0
    assert rule["failed_count"] == 0
    assert rule["last_triggered_at"] is None
