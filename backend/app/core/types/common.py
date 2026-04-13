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

