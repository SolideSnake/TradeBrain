from app.api import router as router_module
from app.application import snapshot_cache_service as snapshot_cache_module


def test_snapshot_endpoint_returns_test_tws_snapshot(client):
    client.post(
        "/api/watchlist",
        json={
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "market": "US",
            "asset_type": "stock",
            "group_name": "core",
            "enabled": True,
            "in_position": False,
            "notes": "",
        },
    )
    client.post(
        "/api/watchlist",
        json={
            "symbol": "TLT",
            "name": "iShares 20+ Year Treasury Bond ETF",
            "market": "US",
            "asset_type": "etf",
            "group_name": "bonds",
            "enabled": True,
            "in_position": True,
            "notes": "rate hedge",
        },
    )

    response = client.get("/api/snapshot")

    assert response.status_code == 200
    payload = response.json()
    assert payload["cache_status"] == "success"
    assert payload["from_cache"] is False
    assert payload["last_success_at"].endswith(("Z", "+00:00"))
    snapshot = payload["snapshot"]
    assert snapshot["meta"]["broker_mode"] == "live"
    assert snapshot["meta"]["broker_status"] == "connected"
    assert snapshot["meta"]["broker_profile"] == "paper"
    assert snapshot["meta"]["broker_display_name"] == "测试 TWS Paper"
    assert snapshot["summary"]["tracked_symbols"] == 2
    assert snapshot["summary"]["quote_coverage"] == 2
    assert snapshot["summary"]["symbols_in_position"] == 1
    assert snapshot["watchlist"][0]["quote"]["source"] == "test"
    assert snapshot["watchlist"][0]["fundamentals"]["peg_ratio"] is not None
    assert snapshot["watchlist"][0]["indicators"]["current_price"] is not None
    assert snapshot["watchlist"][0]["indicators"]["drawdown_from_52w_high_percent"] is not None
    assert snapshot["watchlist"][0]["indicators"]["valuation_label"] in {
        "undervalued",
        "fair",
        "overvalued",
    }
    assert snapshot["watchlist"][0]["state"]["current_label"] in {
        "undervalued",
        "fair",
        "overvalued",
    }
    assert snapshot["watchlist"][0]["state"]["has_changed"] is False
    assert snapshot["account"]["account_id"] == "TEST-ACCOUNT"


def test_snapshot_converts_non_usd_watchlist_quote_to_account_currency(client):
    client.post("/api/watchlist", json={"symbol": "000660"})

    response = client.get("/api/snapshot")

    assert response.status_code == 200
    entry = response.json()["snapshot"]["watchlist"][0]
    assert entry["quote"]["currency"] == "KRW"
    assert entry["quote"]["base_currency"] == "USD"
    assert entry["quote"]["fx_rate_to_base"] == 0.00072
    assert entry["quote"]["last_price"] == 1_976_000
    assert entry["quote"]["last_price_base"] == 1422.72
    assert entry["indicators"]["current_price"] == 1_976_000
    assert entry["indicators"]["current_price_base"] == 1422.72
    assert entry["indicators"]["high_52w"] == 2_331_680


def test_snapshot_endpoint_returns_cached_snapshot_until_refresh(client):
    client.post(
        "/api/watchlist",
        json={
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "market": "US",
            "asset_type": "stock",
            "group_name": "core",
            "enabled": True,
            "in_position": False,
            "notes": "",
        },
    )
    first_response = client.get("/api/snapshot")
    assert first_response.status_code == 200
    assert first_response.json()["snapshot"]["summary"]["tracked_symbols"] == 1

    client.post(
        "/api/watchlist",
        json={
            "symbol": "MSFT",
            "name": "Microsoft",
            "market": "US",
            "asset_type": "stock",
            "group_name": "core",
            "enabled": True,
            "in_position": False,
            "notes": "",
        },
    )

    cached_response = client.get("/api/snapshot")
    assert cached_response.status_code == 200
    cached_payload = cached_response.json()
    assert cached_payload["from_cache"] is True
    assert cached_payload["snapshot"]["summary"]["tracked_symbols"] == 1

    refresh_response = client.post("/api/snapshot/refresh")
    assert refresh_response.status_code == 200
    refresh_payload = refresh_response.json()
    assert refresh_payload["from_cache"] is False
    assert refresh_payload["snapshot"]["summary"]["tracked_symbols"] == 2

    events_response = client.get("/api/events")
    assert events_response.status_code == 200
    events = events_response.json()
    assert events[0]["event_type"] == "snapshot.refresh"
    assert events[0]["status"] == "success"
    assert events[0]["payload"]["trigger"] == "manual"


def test_snapshot_refresh_failure_keeps_previous_snapshot(client, monkeypatch):
    client.post(
        "/api/watchlist",
        json={
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "market": "US",
            "asset_type": "stock",
            "group_name": "core",
            "enabled": True,
            "in_position": False,
            "notes": "",
        },
    )
    assert client.get("/api/snapshot").status_code == 200

    class FailingSnapshotBuilder:
        def build(self, db):
            raise RuntimeError("IBKR timeout")

    monkeypatch.setattr(
        router_module.snapshot_cache_service,
        "snapshot_builder",
        FailingSnapshotBuilder(),
    )

    response = client.post("/api/snapshot/refresh")

    assert response.status_code == 200
    payload = response.json()
    assert payload["cache_status"] == "failed"
    assert payload["from_cache"] is True
    assert payload["snapshot"]["summary"]["tracked_symbols"] == 1
    assert "IBKR timeout" in payload["last_error"]

    events_response = client.get("/api/events")
    assert events_response.status_code == 200
    events = events_response.json()
    assert events[0]["event_type"] == "snapshot.refresh"
    assert events[0]["status"] == "failed"
    assert "IBKR timeout" in events[0]["message"]


def test_snapshot_refresh_returns_cached_payload_when_refresh_already_running(client):
    client.post(
        "/api/watchlist",
        json={
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "market": "US",
            "asset_type": "stock",
            "group_name": "core",
            "enabled": True,
            "in_position": False,
            "notes": "",
        },
    )
    assert client.get("/api/snapshot").status_code == 200

    acquired = snapshot_cache_module._REFRESH_LOCK.acquire(blocking=False)
    assert acquired is True
    try:
        response = client.post("/api/snapshot/refresh")
    finally:
        snapshot_cache_module._REFRESH_LOCK.release()

    assert response.status_code == 200
    payload = response.json()
    assert payload["cache_status"] == "refreshing"
    assert payload["from_cache"] is True
    assert payload["snapshot"]["summary"]["tracked_symbols"] == 1


def test_snapshot_first_build_failure_returns_empty_payload(client, monkeypatch):
    class FailingSnapshotBuilder:
        def build(self, db):
            raise RuntimeError("TWS offline")

    monkeypatch.setattr(
        router_module.snapshot_cache_service,
        "snapshot_builder",
        FailingSnapshotBuilder(),
    )

    response = client.get("/api/snapshot")

    assert response.status_code == 200
    payload = response.json()
    assert payload["snapshot"] is None
    assert payload["cache_status"] == "failed"
    assert payload["from_cache"] is False
    assert "TWS offline" in payload["last_error"]


def test_states_endpoint_returns_persisted_watchlist_states(client):
    client.post(
        "/api/watchlist",
        json={
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "market": "US",
            "asset_type": "stock",
            "group_name": "core",
            "enabled": True,
            "in_position": False,
            "notes": "",
        },
    )

    snapshot_response = client.get("/api/snapshot")
    assert snapshot_response.status_code == 200

    response = client.get("/api/states")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["symbol"] == "AAPL"
    assert payload[0]["current_label"] in {"undervalued", "fair", "overvalued"}


def test_events_endpoint_returns_list(client):
    response = client.get("/api/events")

    assert response.status_code == 200
    assert response.json() == []


def test_legacy_alerts_endpoint_is_removed(client):
    response = client.get("/api/alerts")

    assert response.status_code == 404
