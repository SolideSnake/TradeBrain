from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config.settings import get_settings


class Base(DeclarativeBase):
    pass


@lru_cache(maxsize=1)
def get_engine():
    settings = get_settings()
    db_path = Path(settings.db_path)
    if not db_path.is_absolute():
        db_path = Path.cwd() / db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
    )
    return engine


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)


def get_db():
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    import app.domains.watchlist.models  # noqa: F401

    engine = get_engine()
    with engine.begin() as connection:
        connection.exec_driver_sql("PRAGMA journal_mode=WAL;")
    Base.metadata.create_all(bind=engine)

