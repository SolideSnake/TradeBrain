def test_target_position_crud(client):
    create_response = client.post(
        "/api/target-positions",
        json={"symbol": "aapl", "target_value_usd": 10000, "notes": "core target"},
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["symbol"] == "AAPL"
    assert created["target_value_usd"] == 10000
    assert created["notes"] == "core target"

    list_response = client.get("/api/target-positions")
    assert list_response.status_code == 200
    assert [position["symbol"] for position in list_response.json()] == ["AAPL"]

    patch_response = client.patch(
        f"/api/target-positions/{created['id']}",
        json={"target_value_usd": 12500},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["target_value_usd"] == 12500

    delete_response = client.delete(f"/api/target-positions/{created['id']}")
    assert delete_response.status_code == 204

    final_response = client.get("/api/target-positions")
    assert final_response.status_code == 200
    assert final_response.json() == []


def test_target_positions_are_sorted_by_value_desc(client):
    client.post("/api/target-positions", json={"symbol": "MSFT", "target_value_usd": 5000})
    client.post("/api/target-positions", json={"symbol": "AAPL", "target_value_usd": 15000})
    client.post("/api/target-positions", json={"symbol": "NVDA", "target_value_usd": 10000})

    response = client.get("/api/target-positions")

    assert response.status_code == 200
    assert [position["symbol"] for position in response.json()] == ["AAPL", "NVDA", "MSFT"]


def test_target_position_rejects_non_positive_value(client):
    response = client.post(
        "/api/target-positions",
        json={"symbol": "AAPL", "target_value_usd": 0},
    )

    assert response.status_code == 422


def test_target_position_rejects_duplicate_symbol(client):
    first_response = client.post(
        "/api/target-positions",
        json={"symbol": "aapl", "target_value_usd": 10000},
    )
    duplicate_response = client.post(
        "/api/target-positions",
        json={"symbol": "AAPL", "target_value_usd": 12000},
    )

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409
    assert "already contains symbol" in duplicate_response.json()["detail"]


def test_target_position_update_rejects_duplicate_symbol(client):
    first_response = client.post(
        "/api/target-positions",
        json={"symbol": "AAPL", "target_value_usd": 10000},
    )
    second_response = client.post(
        "/api/target-positions",
        json={"symbol": "MSFT", "target_value_usd": 12000},
    )

    duplicate_update = client.patch(
        f"/api/target-positions/{second_response.json()['id']}",
        json={"symbol": first_response.json()["symbol"]},
    )

    assert duplicate_update.status_code == 409

