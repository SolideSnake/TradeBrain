from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from functools import lru_cache
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config.settings import get_settings


@dataclass(slots=True)
class FeishuSendResult:
    status: str
    external_id: str | None = None


class FeishuNotifier:
    def send_message(self, text: str) -> FeishuSendResult:
        raise NotImplementedError


class NoopFeishuNotifier(FeishuNotifier):
    def send_message(self, text: str) -> FeishuSendResult:
        _ = text
        return FeishuSendResult(status="skipped")


class BotFeishuNotifier(FeishuNotifier):
    def __init__(self, webhook_url: str, secret: str = "") -> None:
        self.webhook_url = webhook_url
        self.secret = secret

    def send_message(self, text: str) -> FeishuSendResult:
        payload = {
            "msg_type": "text",
            "content": {
                "text": text,
            },
        }
        if self.secret:
            timestamp = str(int(time.time()))
            payload["timestamp"] = timestamp
            payload["sign"] = self._build_sign(timestamp)

        request = Request(
            url=self.webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=10) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Feishu send failed: HTTP {exc.code} {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"Feishu send failed: {exc.reason}") from exc

        if not self._is_success(body):
            raise RuntimeError(f"Feishu send failed: {body}")

        external_id = (
            body.get("data", {}).get("message_id")
            or body.get("Data", {}).get("message_id")
            or body.get("Extra")
        )
        return FeishuSendResult(
            status="sent",
            external_id=str(external_id) if external_id else None,
        )

    def _build_sign(self, timestamp: str) -> str:
        string_to_sign = f"{timestamp}\n{self.secret}"
        digest = hmac.new(
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        return base64.b64encode(digest).decode("utf-8")

    def _is_success(self, body: dict) -> bool:
        if body.get("StatusCode") == 0:
            return True
        if body.get("code") == 0:
            return True
        if body.get("status_code") == 0:
            return True
        return False


def create_feishu_notifier(webhook_url: str, secret: str = "") -> FeishuNotifier:
    if webhook_url:
        return BotFeishuNotifier(webhook_url, secret)
    return NoopFeishuNotifier()


@lru_cache(maxsize=1)
def get_feishu_notifier() -> FeishuNotifier:
    settings = get_settings()
    return create_feishu_notifier(settings.feishu_webhook_url, settings.feishu_secret)
