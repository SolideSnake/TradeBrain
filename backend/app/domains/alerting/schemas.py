from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel
from pydantic import Field, field_validator

from app.core.types.common import (
    AlertChannel,
    AlertLevel,
    AlertRuleCategory,
    AlertRuleMetric,
    AlertRuleOperator,
    AlertRuleSource,
)


class AlertCandidate(BaseModel):
    rule_id: int | None = None
    symbol: str
    channel: AlertChannel = AlertChannel.TELEGRAM
    level: AlertLevel = AlertLevel.INFO
    title: str
    message: str


class AlertRuleEvaluation(BaseModel):
    rule_id: int
    observed_value: str
    matched: bool
    should_notify: bool
    suppression_reason: str = ""
    candidate: AlertCandidate | None = None


class AlertRuleBase(BaseModel):
    schema_version: int = 1
    name: str = Field(min_length=1, max_length=128)
    enabled: bool = True
    category: AlertRuleCategory = AlertRuleCategory.THRESHOLD
    source: AlertRuleSource
    symbol: str = Field(default="", max_length=32)
    metric: AlertRuleMetric
    operator: AlertRuleOperator
    threshold_value: str = Field(min_length=1, max_length=64)
    cooldown_seconds: int = Field(default=3600, ge=60, le=86400)
    edge_only: bool = True
    message_template: str = Field(default="", max_length=1000)

    @field_validator("name", "threshold_value")
    @classmethod
    def trim_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()


class AlertRuleCreate(AlertRuleBase):
    pass


class AlertRuleUpdate(BaseModel):
    schema_version: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=128)
    enabled: bool | None = None
    category: AlertRuleCategory | None = None
    source: AlertRuleSource | None = None
    symbol: str | None = Field(default=None, max_length=32)
    metric: AlertRuleMetric | None = None
    operator: AlertRuleOperator | None = None
    threshold_value: str | None = Field(default=None, min_length=1, max_length=64)
    cooldown_seconds: int | None = Field(default=None, ge=60, le=86400)
    edge_only: bool | None = None
    message_template: str | None = Field(default=None, max_length=1000)

    @field_validator("name", "threshold_value")
    @classmethod
    def trim_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else value

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str | None) -> str | None:
        return value.strip().upper() if value is not None else value


class AlertRuleRead(AlertRuleBase):
    id: int
    last_observed_value: str
    last_evaluated_at: datetime | None = None
    last_matched: bool
    last_suppressed_at: datetime | None = None
    suppressed_count: int
    sent_count: int
    failed_count: int
    last_triggered_at: datetime | None = None
    last_sent_at: datetime | None = None
    last_failed_at: datetime | None = None
    last_error: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AlertRuleOption(BaseModel):
    value: str
    label: str


class AlertRuleMetricOption(AlertRuleOption):
    source: AlertRuleSource
    value_type: str
    default_operator: AlertRuleOperator
    default_threshold: str
    unit: str


class AlertRuleTemplate(BaseModel):
    id: str
    label: str
    description: str
    source: AlertRuleSource
    metric: AlertRuleMetric
    operator: AlertRuleOperator
    threshold_value: str
    cooldown_seconds: int = 3600
    edge_only: bool = True


class AlertRuleMetadataRead(BaseModel):
    sources: list[AlertRuleOption]
    operators: list[AlertRuleOption]
    metrics: list[AlertRuleMetricOption]
    templates: list[AlertRuleTemplate]
