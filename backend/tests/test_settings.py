from __future__ import annotations

from pathlib import Path

from app.config.settings import PROJECT_ROOT, get_settings


def test_database_url_resolves_from_project_root(
    monkeypatch,
):
    monkeypatch.chdir(PROJECT_ROOT / "backend")
    monkeypatch.delenv("DB_PATH", raising=False)
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.database_url.endswith("/backend/tradebrain.db")
    assert "/backend/backend/tradebrain.db" not in settings.database_url

    get_settings.cache_clear()
