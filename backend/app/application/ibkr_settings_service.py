from __future__ import annotations

import os
from collections.abc import Callable

from sqlalchemy.orm import Session

from app.adapters.ibkr.client import (
    IBKRRuntimeProfile,
    LiveIBKRClient,
    ibkr_display_name,
    normalize_ibkr_mode,
    normalize_ibkr_profile,
)
from app.adapters.persistence.sqlite.ibkr_settings_repository import IBKRSettingsRepository
from app.config.settings import Settings, get_settings
from app.domains.preferences.models import IBKRSettings
from app.domains.preferences.schemas import (
    IBKRConnectionProfile,
    IBKRConnectionTestRequest,
    IBKRConnectionTestResult,
    IBKRSettingsRead,
    IBKRSettingsUpdate,
)


class IBKRSettingsService:
    def __init__(
        self,
        repository: IBKRSettingsRepository | None = None,
        settings: Settings | None = None,
        live_client_factory: Callable[[Settings, IBKRRuntimeProfile], LiveIBKRClient] | None = None,
    ) -> None:
        self.repository = repository or IBKRSettingsRepository()
        self.settings = settings
        self.live_client_factory = live_client_factory or LiveIBKRClient

    def get_settings(self, db: Session) -> IBKRSettingsRead:
        stored = self.repository.get(db)
        if stored is not None:
            return self._read_from_model(stored)
        return self._read_from_environment()

    def update_settings(self, db: Session, payload: IBKRSettingsUpdate) -> IBKRSettingsRead:
        current = self.get_settings(db)
        stored = self.repository.get(db)
        if stored is None:
            stored = IBKRSettings()

        updates = payload.model_dump(exclude_unset=True)
        stored.mode = normalize_ibkr_mode(updates.get("mode", current.mode))
        stored.active_profile = normalize_ibkr_profile(
            updates.get("active_profile", current.active_profile)
        )

        real = payload.real or current.real
        paper = payload.paper or current.paper
        self._assign_profile(stored, "real", real)
        self._assign_profile(stored, "paper", paper)

        self.repository.save(db, stored)
        db.commit()
        db.refresh(stored)
        return self._read_from_model(stored)

    def resolve_runtime_profile(self, db: Session) -> tuple[str, IBKRRuntimeProfile]:
        settings = self.get_settings(db)
        active = settings.paper if settings.active_profile == "paper" else settings.real
        return settings.mode, IBKRRuntimeProfile(
            name=settings.active_profile,
            display_name=settings.active_display_name,
            host=active.host,
            port=active.port,
            client_id=active.client_id,
            account_id=active.account_id,
        )

    def test_connection(
        self,
        db: Session,
        payload: IBKRConnectionTestRequest,
    ) -> IBKRConnectionTestResult:
        settings = self.get_settings(db)
        profile = settings.paper if payload.profile == "paper" else settings.real
        runtime_profile = IBKRRuntimeProfile(
            name=payload.profile,
            display_name=ibkr_display_name(payload.profile),
            host=profile.host,
            port=profile.port,
            client_id=profile.client_id,
            account_id=profile.account_id,
        )

        client = self.live_client_factory(self._settings, runtime_profile)
        success, accounts, detail = client.test_connection()
        return IBKRConnectionTestResult(
            success=success,
            profile=payload.profile,
            display_name=runtime_profile.display_name,
            host=runtime_profile.host,
            port=runtime_profile.port,
            client_id=runtime_profile.client_id,
            account_id=runtime_profile.account_id,
            accounts=accounts,
            detail=detail,
        )

    def _read_from_model(self, stored: IBKRSettings) -> IBKRSettingsRead:
        active_profile = normalize_ibkr_profile(stored.active_profile)
        return IBKRSettingsRead(
            mode=normalize_ibkr_mode(stored.mode),
            active_profile=active_profile,
            active_display_name=ibkr_display_name(active_profile),
            real=IBKRConnectionProfile(
                host=stored.real_host,
                port=stored.real_port,
                client_id=stored.real_client_id,
                account_id=stored.real_account_id,
            ),
            paper=IBKRConnectionProfile(
                host=stored.paper_host,
                port=stored.paper_port,
                client_id=stored.paper_client_id,
                account_id=stored.paper_account_id,
            ),
            source="database",
        )

    def _read_from_environment(self) -> IBKRSettingsRead:
        mode = normalize_ibkr_mode(self._settings.ibkr_mode)
        active_profile = self._resolve_environment_active_profile()
        real = IBKRConnectionProfile(
            host=self._settings.ibkr_real_host,
            port=self._settings.ibkr_real_port,
            client_id=self._settings.ibkr_real_client_id,
            account_id=self._settings.ibkr_real_account_id,
        )
        paper = IBKRConnectionProfile(
            host=self._settings.ibkr_paper_host,
            port=self._settings.ibkr_paper_port,
            client_id=self._settings.ibkr_paper_client_id,
            account_id=self._settings.ibkr_paper_account_id,
        )

        legacy_profile = IBKRConnectionProfile(
            host=self._settings.ibkr_host,
            port=self._settings.ibkr_port,
            client_id=self._settings.ibkr_client_id,
            account_id=self._settings.ibkr_account_id,
        )
        if self._has_legacy_environment_override():
            if active_profile == "real":
                real = legacy_profile
            else:
                paper = legacy_profile

        return IBKRSettingsRead(
            mode=mode,
            active_profile=active_profile,
            active_display_name=ibkr_display_name(active_profile),
            real=real,
            paper=paper,
            source="environment",
        )

    def _resolve_environment_active_profile(self) -> str:
        explicit_profile = os.environ.get("IBKR_ACTIVE_PROFILE")
        if explicit_profile:
            return normalize_ibkr_profile(explicit_profile)

        legacy_port = os.environ.get("IBKR_PORT")
        if normalize_ibkr_mode(self._settings.ibkr_mode) == "ibkr" and legacy_port == "7496":
            return "real"
        if normalize_ibkr_mode(self._settings.ibkr_mode) == "ibkr" and legacy_port == "7497":
            return "paper"
        return normalize_ibkr_profile(self._settings.ibkr_active_profile)

    def _has_legacy_environment_override(self) -> bool:
        return any(
            key in os.environ
            for key in ("IBKR_HOST", "IBKR_PORT", "IBKR_CLIENT_ID", "IBKR_ACCOUNT_ID")
        )

    def _assign_profile(
        self,
        stored: IBKRSettings,
        prefix: str,
        profile: IBKRConnectionProfile,
    ) -> None:
        setattr(stored, f"{prefix}_host", profile.host)
        setattr(stored, f"{prefix}_port", profile.port)
        setattr(stored, f"{prefix}_client_id", profile.client_id)
        setattr(stored, f"{prefix}_account_id", profile.account_id)

    @property
    def _settings(self) -> Settings:
        return self.settings or get_settings()
