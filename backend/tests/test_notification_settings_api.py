from app.api import router as router_module


def test_notification_settings_endpoint_defaults_to_empty(client):
    response = client.get("/api/settings/notifications")

    assert response.status_code == 200
    payload = response.json()
    assert payload["telegram_enabled"] is False
    assert payload["telegram_bot_token_configured"] is False
    assert payload["telegram_chat_id"] == ""
    assert payload["source"] == "none"


def test_notification_settings_can_be_updated(client):
    response = client.put(
        "/api/settings/notifications",
        json={
            "telegram_bot_token": "123456:ABCDEF-secret",
            "telegram_chat_id": "99887766",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["telegram_enabled"] is True
    assert payload["telegram_bot_token_configured"] is True
    assert payload["telegram_bot_token_masked"].startswith("123456")
    assert payload["telegram_chat_id"] == "99887766"
    assert payload["source"] == "database"

    follow_up = client.get("/api/settings/notifications")
    assert follow_up.status_code == 200
    follow_up_payload = follow_up.json()
    assert follow_up_payload["telegram_chat_id"] == "99887766"
    assert follow_up_payload["telegram_enabled"] is True


def test_notification_settings_test_message_skips_when_missing_config(client):
    response = client.post("/api/settings/notifications/test")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is False
    assert payload["delivery_status"] == "skipped"


def test_notification_settings_test_message_succeeds_and_logs_alert(client, monkeypatch):
    class FakeNotifier:
        def send_message(self, text: str):
            return type("Result", (), {"status": "sent", "external_id": "1"})()

    monkeypatch.setattr(
        router_module.notification_settings_service,
        "notifier_factory",
        lambda bot_token, chat_id: FakeNotifier(),
    )

    save_response = client.put(
        "/api/settings/notifications",
        json={
            "telegram_bot_token": "123456:ABCDEF-secret",
            "telegram_chat_id": "99887766",
        },
    )
    assert save_response.status_code == 200

    response = client.post("/api/settings/notifications/test")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["delivery_status"] == "sent"

    alerts_response = client.get("/api/alerts")
    assert alerts_response.status_code == 200
    alerts_payload = alerts_response.json()
    assert alerts_payload[0]["symbol"] == "SYSTEM"
    assert alerts_payload[0]["title"] == "Telegram 测试消息"
