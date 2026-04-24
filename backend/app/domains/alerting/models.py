from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.adapters.persistence.sqlite.db import Base
from app.core.types.common import (
    AlertRuleCategory,
    AlertRuleMetric,
    AlertRuleOperator,
    AlertRuleSource,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    category: Mapped[AlertRuleCategory] = mapped_column(
        Enum(AlertRuleCategory, native_enum=False),
        nullable=False,
        default=AlertRuleCategory.THRESHOLD,
    )
    source: Mapped[AlertRuleSource] = mapped_column(
        Enum(AlertRuleSource, native_enum=False),
        nullable=False,
    )
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    metric: Mapped[AlertRuleMetric] = mapped_column(
        Enum(AlertRuleMetric, native_enum=False),
        nullable=False,
    )
    operator: Mapped[AlertRuleOperator] = mapped_column(
        Enum(AlertRuleOperator, native_enum=False),
        nullable=False,
    )
    threshold_value: Mapped[str] = mapped_column(String(64), nullable=False)
    cooldown_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=3600)
    edge_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    message_template: Mapped[str] = mapped_column(Text, nullable=False, default="")
    last_observed_value: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    last_evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_matched: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_suppressed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    suppressed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sent_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
