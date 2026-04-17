from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.core.types.common import AlertDeliveryStatus


class NotificationSettingsUpdate(BaseModel):
    telegram_bot_token: str | None = Field(default=None, max_length=4096)
    telegram_chat_id: str | None = Field(default=None, max_length=128)

    @field_validator("telegram_bot_token", "telegram_chat_id")
    @classmethod
    def trim_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()


class NotificationSettingsRead(BaseModel):
    telegram_enabled: bool
    telegram_bot_token_configured: bool
    telegram_bot_token_masked: str | None = None
    telegram_chat_id: str = ""
    source: Literal["database", "environment", "none"]


class NotificationTestResult(BaseModel):
    success: bool
    delivery_status: AlertDeliveryStatus
    detail: str
