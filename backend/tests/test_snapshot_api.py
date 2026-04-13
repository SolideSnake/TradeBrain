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
    assert payload["account"]["account_id"] == "MOCK-ACCOUNT"
