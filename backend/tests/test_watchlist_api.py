def test_watchlist_crud(client):
    payload = {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "market": "US",
        "asset_type": "stock",
        "group_name": "core",
        "enabled": True,
        "in_position": False,
        "notes": "starter entry",
    }

    create_response = client.post("/api/watchlist", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["symbol"] == "AAPL"

    list_response = client.get("/api/watchlist")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    patch_response = client.patch(
        f"/api/watchlist/{created['id']}",
        json={"enabled": False, "in_position": True},
    )
    assert patch_response.status_code == 200
    updated = patch_response.json()
    assert updated["enabled"] is False
    assert updated["in_position"] is True

    delete_response = client.delete(f"/api/watchlist/{created['id']}")
    assert delete_response.status_code == 204

    final_list_response = client.get("/api/watchlist")
    assert final_list_response.status_code == 200
    assert final_list_response.json() == []


def test_watchlist_create_accepts_symbol_only(client):
    create_response = client.post("/api/watchlist", json={"symbol": "aapl"})

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["symbol"] == "AAPL"
    assert created["name"] == "Apple Inc."
    assert created["market"] == "US"
    assert created["asset_type"] == "stock"
    assert created["group_name"] == "default"
    assert created["enabled"] is True
    assert created["in_position"] is False


def test_watchlist_create_infers_korean_market_for_six_digit_symbol(client):
    create_response = client.post("/api/watchlist", json={"symbol": "000660"})

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["symbol"] == "000660"
    assert created["name"] == "SK hynix Inc."
    assert created["market"] == "KR"


def test_watchlist_create_uses_symbol_as_unknown_name_fallback(client):
    create_response = client.post("/api/watchlist", json={"symbol": "xyzq"})

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["symbol"] == "XYZQ"
    assert created["name"] == "XYZQ"


def test_watchlist_rejects_duplicate_symbol(client):
    payload = {
        "symbol": "msft",
        "name": "Microsoft",
        "market": "US",
        "asset_type": "stock",
        "group_name": "leaders",
        "enabled": True,
        "in_position": False,
        "notes": "",
    }

    first_response = client.post("/api/watchlist", json=payload)
    assert first_response.status_code == 201
    assert first_response.json()["symbol"] == "MSFT"

    duplicate_response = client.post("/api/watchlist", json=payload)
    assert duplicate_response.status_code == 409
    assert "already contains symbol" in duplicate_response.json()["detail"]
