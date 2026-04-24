from enum import StrEnum


class Market(StrEnum):
    US = "US"
    HK = "HK"
    OTHER = "OTHER"


class AssetType(StrEnum):
    STOCK = "stock"
    ETF = "etf"
    BOND = "bond"
    OTHER = "other"


class TaskStatus(StrEnum):
    WATCHING = "watching"
    NEAR_TRIGGER = "near_trigger"
    READY = "ready"
    DONE = "done"
    IGNORED = "ignored"
    EXPIRED = "expired"


class AlertLevel(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertChannel(StrEnum):
    TELEGRAM = "telegram"


class AlertDeliveryStatus(StrEnum):
    SENT = "sent"
    SKIPPED = "skipped"
    FAILED = "failed"


class AlertRuleCategory(StrEnum):
    THRESHOLD = "threshold"
    EVENT = "event"
    SCHEDULE = "schedule"
    COMPOSITE = "composite"


class AlertRuleSource(StrEnum):
    WATCHLIST = "watchlist"
    PORTFOLIO = "portfolio"
    CUSTOM = "custom"


class AlertRuleMetric(StrEnum):
    CURRENT_PRICE = "current_price"
    DAY_CHANGE_PERCENT = "day_change_percent"
    DRAWDOWN_52W = "drawdown_52w"
    DRAWDOWN_90D = "drawdown_90d"
    VALUATION_LABEL = "valuation_label"
    NET_LIQUIDATION = "net_liquidation"
    AVAILABLE_FUNDS = "available_funds"
    BUYING_POWER = "buying_power"
    CUSTOM_VALUE = "custom_value"


class AlertRuleOperator(StrEnum):
    ABOVE = "above"
    BELOW = "below"
    EQUALS = "equals"
    BECOMES = "becomes"
    GTE = "gte"
    LTE = "lte"
    NOT_EQUALS = "not_equals"
    CROSS_ABOVE = "cross_above"
    CROSS_BELOW = "cross_below"
    CHANGE_TO = "change_to"


class ValuationLabel(StrEnum):
    UNDERVALUED = "undervalued"
    FAIR = "fair"
    OVERVALUED = "overvalued"


class StrategyPlanStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class ScannerCandidateReason(StrEnum):
    LARGE_DROP = "large_drop"
    PULLBACK_52W = "pullback_52w"
    UNDERVALUED = "undervalued"

