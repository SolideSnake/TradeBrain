from __future__ import annotations

from sqlalchemy.orm import Session

from app.adapters.persistence.sqlite.notification_settings_repository import (
    NotificationSettingsRepository,
)
from app.config.settings import Settings, get_settings
from app.domains.preferences.models import NotificationSettings
from app.domains.preferences.schemas import (
    NotificationSettingsRead,
    NotificationSettingsUpdate,
)


class NotificationSettingsService:
    def __init__(
        self,
        repository: NotificationSettingsRepository | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.repository = repository or NotificationSettingsRepository()
        self.settings = settings or get_settings()

    def get_settings(self, db: Session) -> NotificationSettingsRead:
        stored = self.repository.get(db)
        stored_token = stored.telegram_bot_token if stored else ""
        stored_chat_id = stored.telegram_chat_id if stored else ""
        stored_feishu_webhook_url = stored.feishu_webhook_url if stored else ""
        stored_feishu_secret = stored.feishu_secret if stored else ""

        token = stored_token or self.settings.telegram_bot_token
        chat_id = stored_chat_id or self.settings.telegram_chat_id
        feishu_webhook_url = stored_feishu_webhook_url or self.settings.feishu_webhook_url
        feishu_secret = stored_feishu_secret or self.settings.feishu_secret

        if stored_token or stored_chat_id or stored_feishu_webhook_url or stored_feishu_secret:
            source = "database"
        elif token or chat_id or feishu_webhook_url or feishu_secret:
            source = "environment"
        else:
            source = "none"

        return NotificationSettingsRead(
            telegram_enabled=bool(token and chat_id),
            telegram_bot_token_configured=bool(token),
            telegram_bot_token_masked=self._mask_token(token) if token else None,
            telegram_chat_id=chat_id or "",
            feishu_enabled=bool(feishu_webhook_url),
            feishu_webhook_url_configured=bool(feishu_webhook_url),
            feishu_webhook_url_masked=(
                self._mask_url(feishu_webhook_url) if feishu_webhook_url else None
            ),
            feishu_secret_configured=bool(feishu_secret),
            feishu_secret_masked=self._mask_token(feishu_secret) if feishu_secret else None,
            source=source,
        )

    def update_settings(
        self,
        db: Session,
        payload: NotificationSettingsUpdate,
    ) -> NotificationSettingsRead:
        stored = self.repository.get(db)
        if stored is None:
            stored = NotificationSettings()

        updates = payload.model_dump(exclude_unset=True)
        if "telegram_bot_token" in updates:
            stored.telegram_bot_token = updates["telegram_bot_token"] or ""
        if "telegram_chat_id" in updates:
            stored.telegram_chat_id = updates["telegram_chat_id"] or ""
        if "feishu_webhook_url" in updates:
            stored.feishu_webhook_url = updates["feishu_webhook_url"] or ""
        if "feishu_secret" in updates:
            stored.feishu_secret = updates["feishu_secret"] or ""

        self.repository.save(db, stored)
        db.commit()
        db.refresh(stored)

        return self.get_settings(db)

    def resolve_telegram_credentials(self, db: Session) -> tuple[str, str]:
        stored = self.repository.get(db)
        stored_token = stored.telegram_bot_token if stored else ""
        stored_chat_id = stored.telegram_chat_id if stored else ""

        token = stored_token or self.settings.telegram_bot_token
        chat_id = stored_chat_id or self.settings.telegram_chat_id
        return token, chat_id

    def resolve_feishu_credentials(self, db: Session) -> tuple[str, str]:
        stored = self.repository.get(db)
        stored_webhook_url = stored.feishu_webhook_url if stored else ""
        stored_secret = stored.feishu_secret if stored else ""

        webhook_url = stored_webhook_url or self.settings.feishu_webhook_url
        secret = stored_secret or self.settings.feishu_secret
        return webhook_url, secret

    def _mask_token(self, token: str) -> str:
        if len(token) <= 10:
            return "*" * len(token)
        return f"{token[:6]}...{token[-4:]}"

    def _mask_url(self, url: str) -> str:
        if len(url) <= 18:
            return "*" * len(url)
        return f"{url[:24]}...{url[-8:]}"
