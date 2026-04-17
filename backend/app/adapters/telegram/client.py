from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config.settings import get_settings


@dataclass(slots=True)
class TelegramSendResult:
    status: str
    external_id: str | None = None


class TelegramNotifier:
    def send_message(self, text: str) -> TelegramSendResult:
        raise NotImplementedError


class NoopTelegramNotifier(TelegramNotifier):
    def send_message(self, text: str) -> TelegramSendResult:
        _ = text
        return TelegramSendResult(status="skipped")


class BotTelegramNotifier(TelegramNotifier):
    def __init__(self, bot_token: str, chat_id: str) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send_message(self, text: str) -> TelegramSendResult:
        payload = json.dumps(
            {
                "chat_id": self.chat_id,
                "text": text,
                "disable_web_page_preview": True,
            }
        ).encode("utf-8")
        request = Request(
            url=f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=10) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Telegram send failed: HTTP {exc.code} {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"Telegram send failed: {exc.reason}") from exc

        if not body.get("ok"):
            raise RuntimeError(f"Telegram send failed: {body}")

        message_id = body.get("result", {}).get("message_id")
        return TelegramSendResult(status="sent", external_id=str(message_id) if message_id else None)


def create_telegram_notifier(bot_token: str, chat_id: str) -> TelegramNotifier:
    if bot_token and chat_id:
        return BotTelegramNotifier(bot_token, chat_id)
    return NoopTelegramNotifier()


@lru_cache(maxsize=1)
def get_telegram_notifier() -> TelegramNotifier:
    settings = get_settings()
    return create_telegram_notifier(settings.telegram_bot_token, settings.telegram_chat_id)
