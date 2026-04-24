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


IBKRMode = Literal["mock", "ibkr"]
IBKRProfileName = Literal["real", "paper"]
IBKRSettingsSource = Literal["database", "environment"]


class IBKRConnectionProfile(BaseModel):
    host: str = Field(default="127.0.0.1", min_length=1, max_length=128)
    port: int = Field(default=7497, ge=1, le=65535)
    client_id: int = Field(default=1, ge=0, le=2_147_483_647)
    account_id: str = Field(default="", max_length=64)

    @field_validator("host", "account_id")
    @classmethod
    def trim_profile_text(cls, value: str) -> str:
        return value.strip()


class IBKRSettingsUpdate(BaseModel):
    mode: IBKRMode | Literal["live"] | None = None
    active_profile: IBKRProfileName | None = None
    real: IBKRConnectionProfile | None = None
    paper: IBKRConnectionProfile | None = None

    @field_validator("mode")
    @classmethod
    def normalize_mode(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized == "live":
            return "ibkr"
        return normalized


class IBKRSettingsRead(BaseModel):
    mode: IBKRMode
    active_profile: IBKRProfileName
    active_display_name: str
    real: IBKRConnectionProfile
    paper: IBKRConnectionProfile
    source: IBKRSettingsSource


class IBKRConnectionTestRequest(BaseModel):
    profile: IBKRProfileName


class IBKRConnectionTestResult(BaseModel):
    success: bool
    profile: IBKRProfileName
    display_name: str
    host: str
    port: int
    client_id: int
    account_id: str
    accounts: list[str] = Field(default_factory=list)
    detail: str


class SnapshotRefreshSettingsUpdate(BaseModel):
    enabled: bool | None = None
    interval_seconds: int | None = Field(default=None, ge=300, le=3600)


class SnapshotRefreshSettingsRead(BaseModel):
    enabled: bool
    interval_seconds: int
