from app.api import router as router_module


def test_notification_settings_endpoint_defaults_to_empty(client):
    response = client.get("/api/settings/notifications")

    assert response.status_code == 200
    payload = response.json()
    assert payload["telegram_enabled"] is False
    assert payload["telegram_bot_token_configured"] is False
    assert payload["telegram_chat_id"] == ""
    assert payload["feishu_enabled"] is False
    assert payload["feishu_webhook_url_configured"] is False
    assert payload["feishu_secret_configured"] is False
    assert payload["source"] == "none"


def test_notification_settings_can_be_updated(client):
    response = client.put(
        "/api/settings/notifications",
        json={
            "telegram_bot_token": "123456:ABCDEF-secret",
            "telegram_chat_id": "99887766",
            "feishu_webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/test-token",
            "feishu_secret": "feishu-secret",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["telegram_enabled"] is True
    assert payload["telegram_bot_token_configured"] is True
    assert payload["telegram_bot_token_masked"].startswith("123456")
    assert payload["telegram_chat_id"] == "99887766"
    assert payload["feishu_enabled"] is True
    assert payload["feishu_webhook_url_configured"] is True
    assert payload["feishu_webhook_url_masked"].startswith("https://open.feishu.cn")
    assert payload["feishu_secret_configured"] is True
    assert payload["feishu_secret_masked"] is not None
    assert payload["source"] == "database"

    follow_up = client.get("/api/settings/notifications")
    assert follow_up.status_code == 200
    follow_up_payload = follow_up.json()
    assert follow_up_payload["telegram_chat_id"] == "99887766"
    assert follow_up_payload["telegram_enabled"] is True
    assert follow_up_payload["feishu_enabled"] is True


def test_notification_settings_test_message_skips_when_missing_config(client):
    response = client.post("/api/settings/notifications/test")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is False
    assert payload["delivery_status"] == "skipped"


def test_notification_settings_test_message_succeeds_and_logs_alert(client):
    class FakeNotifier:
        def send_message(self, text: str):
            return type("Result", (), {"status": "sent", "external_id": "1"})()

    router_module.notification_service.notifier = FakeNotifier()

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

    events_response = client.get("/api/events")
    assert events_response.status_code == 200
    events_payload = events_response.json()
    assert events_payload[0]["symbol"] == "SYSTEM"
    assert events_payload[0]["title"] == "Telegram 测试消息"
    assert events_payload[0]["status"] == "sent"
    router_module.notification_service.notifier = None
