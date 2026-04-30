from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config.settings import PROJECT_ROOT, get_settings


class Base(DeclarativeBase):
    pass


@lru_cache(maxsize=1)
def get_engine():
    settings = get_settings()
    db_path = Path(settings.db_path)
    if not db_path.is_absolute():
        db_path = PROJECT_ROOT / db_path
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
    import app.domains.alerting.models  # noqa: F401
    import app.domains.events.models  # noqa: F401
    import app.domains.fx.models  # noqa: F401
    import app.domains.preferences.models  # noqa: F401
    import app.domains.snapshot.models  # noqa: F401
    import app.domains.state.models  # noqa: F401
    import app.domains.watchlist.models  # noqa: F401

    engine = get_engine()
    with engine.begin() as connection:
        connection.exec_driver_sql("PRAGMA journal_mode=WAL;")
    Base.metadata.create_all(bind=engine)
    _drop_legacy_alert_events(engine)
    _migrate_alert_rules(engine)
    _migrate_notification_settings(engine)
    _migrate_known_watchlist_markets(engine)


def _drop_legacy_alert_events(engine) -> None:
    with engine.begin() as connection:
        connection.exec_driver_sql("DROP TABLE IF EXISTS alert_events")


def _migrate_alert_rules(engine) -> None:
    columns = {
        "schema_version": "INTEGER NOT NULL DEFAULT 1",
        "category": "VARCHAR(32) NOT NULL DEFAULT 'threshold'",
        "cooldown_seconds": "INTEGER NOT NULL DEFAULT 3600",
        "edge_only": "BOOLEAN NOT NULL DEFAULT 1",
        "message_template": "TEXT NOT NULL DEFAULT ''",
        "last_observed_value": "VARCHAR(128) NOT NULL DEFAULT ''",
        "last_evaluated_at": "DATETIME",
        "last_matched": "BOOLEAN NOT NULL DEFAULT 0",
        "last_suppressed_at": "DATETIME",
        "suppressed_count": "INTEGER NOT NULL DEFAULT 0",
    }
    with engine.begin() as connection:
        existing = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(alert_rules)").fetchall()
        }
        for name, definition in columns.items():
            if name not in existing:
                connection.exec_driver_sql(f"ALTER TABLE alert_rules ADD COLUMN {name} {definition}")


def _migrate_notification_settings(engine) -> None:
    columns = {
        "feishu_webhook_url": "TEXT NOT NULL DEFAULT ''",
        "feishu_secret": "TEXT NOT NULL DEFAULT ''",
    }
    with engine.begin() as connection:
        existing = {
            row[1]
            for row in connection.exec_driver_sql(
                "PRAGMA table_info(notification_settings)"
            ).fetchall()
        }
        for name, definition in columns.items():
            if name not in existing:
                connection.exec_driver_sql(
                    f"ALTER TABLE notification_settings ADD COLUMN {name} {definition}"
                )


def _migrate_known_watchlist_markets(engine) -> None:
    with engine.begin() as connection:
        connection.exec_driver_sql(
            """
            UPDATE watchlist_entries
            SET name = CASE WHEN name = '000660' THEN 'SK hynix Inc.' ELSE name END,
                market = 'KR'
            WHERE symbol = '000660'
            """
        )

