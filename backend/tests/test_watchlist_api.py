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
