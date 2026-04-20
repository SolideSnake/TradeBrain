from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "TradeBrain"
    app_env: str = "development"
    app_port: int = 8000
    db_path: str = "backend/tradebrain.db"

    ibkr_mode: str = "mock"
    ibkr_active_profile: str = "paper"
    ibkr_host: str = "127.0.0.1"
    ibkr_port: int = 7497
    ibkr_client_id: int = 1
    ibkr_account_id: str = ""
    ibkr_real_host: str = "127.0.0.1"
    ibkr_real_port: int = 7496
    ibkr_real_client_id: int = 1
    ibkr_real_account_id: str = ""
    ibkr_paper_host: str = "127.0.0.1"
    ibkr_paper_port: int = 7497
    ibkr_paper_client_id: int = 2
    ibkr_paper_account_id: str = ""
    ibkr_market_data_type: str = "delayed"
    ibkr_market_data_wait_seconds: float = 1.0

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @computed_field
    @property
    def database_url(self) -> str:
        db_path = Path(self.db_path)
        if not db_path.is_absolute():
            db_path = PROJECT_ROOT / db_path
        return f"sqlite:///{db_path.as_posix()}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
