def test_snapshot_endpoint_returns_mock_snapshot(client):
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
    assert payload["meta"]["broker_mode"] == "mock"
    assert payload["meta"]["broker_status"] == "mock"
    assert payload["summary"]["tracked_symbols"] == 2
    assert payload["summary"]["quote_coverage"] == 2
    assert payload["summary"]["symbols_in_position"] == 1
    assert payload["watchlist"][0]["quote"]["source"] == "mock"
    assert payload["watchlist"][0]["fundamentals"]["peg_ratio"] is not None
    assert payload["watchlist"][0]["indicators"]["current_price"] is not None
    assert payload["watchlist"][0]["indicators"]["drawdown_from_52w_high_percent"] is not None
    assert payload["watchlist"][0]["indicators"]["valuation_label"] in {
        "undervalued",
        "fair",
        "overvalued",
    }
    assert payload["watchlist"][0]["state"]["current_label"] in {
        "undervalued",
        "fair",
        "overvalued",
    }
    assert payload["watchlist"][0]["state"]["has_changed"] is False
    assert payload["account"]["account_id"] == "MOCK-ACCOUNT"


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


def test_alerts_endpoint_returns_list(client):
    response = client.get("/api/alerts")

    assert response.status_code == 200
    assert response.json() == []
