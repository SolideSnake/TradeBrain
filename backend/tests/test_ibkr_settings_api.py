def test_ibkr_settings_endpoint_returns_default_profiles(client):
    response = client.get("/api/settings/ibkr")

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "mock"
    assert payload["active_profile"] == "paper"
    assert payload["active_display_name"] == "模拟 TWS"
    assert payload["paper"]["port"] == 7497
    assert payload["paper"]["client_id"] == 2
    assert payload["real"]["port"] == 7496
    assert payload["real"]["client_id"] == 1


def test_ibkr_settings_can_switch_active_profile_and_mode(client):
    response = client.put(
        "/api/settings/ibkr",
        json={
            "mode": "ibkr",
            "active_profile": "real",
            "real": {
                "host": "127.0.0.1",
                "port": 7496,
                "client_id": 11,
                "account_id": "U123",
            },
            "paper": {
                "host": "127.0.0.1",
                "port": 7497,
                "client_id": 22,
                "account_id": "DU123",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "ibkr"
    assert payload["active_profile"] == "real"
    assert payload["active_display_name"] == "真实 TWS"
    assert payload["real"]["client_id"] == 11
    assert payload["paper"]["account_id"] == "DU123"

    follow_up = client.get("/api/settings/ibkr")
    assert follow_up.status_code == 200
    assert follow_up.json()["active_profile"] == "real"


def test_ibkr_settings_accepts_live_as_compatibility_alias(client):
    response = client.put(
        "/api/settings/ibkr",
        json={
            "mode": "live",
            "active_profile": "paper",
        },
    )

    assert response.status_code == 200
    assert response.json()["mode"] == "ibkr"


def test_ibkr_connection_test_returns_readable_failure(client):
    client.put(
        "/api/settings/ibkr",
        json={
            "mode": "ibkr",
            "active_profile": "paper",
            "paper": {
                "host": "127.0.0.1",
                "port": 1,
                "client_id": 2,
                "account_id": "",
            },
        },
    )

    response = client.post("/api/settings/ibkr/test", json={"profile": "paper"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is False
    assert payload["profile"] == "paper"
    assert payload["display_name"] == "模拟 TWS"
    assert "TWS" in payload["detail"] or "ib_async" in payload["detail"]
