from __future__ import annotations

from datetime import UTC, datetime
from functools import lru_cache
from typing import Sequence

from app.config.settings import Settings, get_settings
from app.domains.market.schemas import QuoteSnapshot
from app.domains.portfolio.schemas import AccountSnapshot, PositionSnapshot
from app.domains.snapshot.schemas import BrokerSnapshotEnvelope


class IBKRClient:
    def fetch_snapshot(self, tracked_symbols: Sequence[str]) -> BrokerSnapshotEnvelope:
        raise NotImplementedError


class MockIBKRClient(IBKRClient):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def fetch_snapshot(self, tracked_symbols: Sequence[str]) -> BrokerSnapshotEnvelope:
        now = datetime.now(UTC)
        quotes = {
            symbol: self._build_quote(symbol, now)
            for symbol in sorted({symbol.strip().upper() for symbol in tracked_symbols if symbol})
        }
        account = AccountSnapshot(
            account_id=self.settings.ibkr_account_id or "MOCK-ACCOUNT",
            net_liquidation=250000.0,
            available_funds=82000.0,
            buying_power=164000.0,
            currency="USD",
            source="mock",
            updated_at=now,
        )
        return BrokerSnapshotEnvelope(
            mode="mock",
            status="mock",
            account=account,
            positions=[],
            quotes=quotes,
            warnings=["IBKR mock mode is active. Connect TWS/Gateway and switch IBKR_MODE=live for real data."],
        )

    def _build_quote(self, symbol: str, now: datetime) -> QuoteSnapshot:
        seed = sum(ord(character) for character in symbol)
        previous_close = round(20 + (seed % 240) + ((seed % 17) / 10), 2)
        drift = ((seed % 9) - 4) / 100
        last_price = round(previous_close * (1 + drift), 2)
        change_percent = round(((last_price - previous_close) / previous_close) * 100, 2)
        bid = round(last_price - 0.05, 2)
        ask = round(last_price + 0.05, 2)
        return QuoteSnapshot(
            symbol=symbol,
            last_price=last_price,
            previous_close=previous_close,
            change_percent=change_percent,
            bid=bid,
            ask=ask,
            as_of=now,
            source="mock",
        )


class LiveIBKRClient(IBKRClient):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def fetch_snapshot(self, tracked_symbols: Sequence[str]) -> BrokerSnapshotEnvelope:
        warnings: list[str] = []
        now = datetime.now(UTC)

        try:
            from ib_async import IB, Stock
        except ImportError:
            return BrokerSnapshotEnvelope(
                mode="live",
                status="error",
                account=AccountSnapshot(
                    account_id=self.settings.ibkr_account_id,
                    source="live",
                    updated_at=now,
                ),
                positions=[],
                quotes={},
                warnings=[
                    "ib_async is not installed. Install it before using live IBKR mode.",
                ],
            )

        ib = IB()
        quotes: dict[str, QuoteSnapshot] = {}
        positions: list[PositionSnapshot] = []

        try:
            ib.connect(
                self.settings.ibkr_host,
                self.settings.ibkr_port,
                clientId=self.settings.ibkr_client_id,
            )

            if self.settings.ibkr_market_data_type == "delayed":
                ib.reqMarketDataType(3)
            elif self.settings.ibkr_market_data_type == "delayed_frozen":
                ib.reqMarketDataType(4)
            else:
                ib.reqMarketDataType(1)

            accounts = list(ib.managedAccounts())
            account_id = self.settings.ibkr_account_id or (accounts[0] if accounts else "")

            account = self._build_account_snapshot(ib, account_id, now)
            positions = self._build_positions(ib, account_id)
            quotes = self._build_quotes(ib, Stock, tracked_symbols, now)

            return BrokerSnapshotEnvelope(
                mode="live",
                status="connected",
                account=account,
                positions=positions,
                quotes=quotes,
                warnings=warnings,
            )
        except ConnectionRefusedError:
            warnings.append("Could not connect to IBKR. Check TWS/Gateway, API port, and trusted IP settings.")
        except Exception as exc:
            warnings.append(f"IBKR live snapshot failed: {exc}")
        finally:
            if getattr(ib, "isConnected", lambda: False)():
                ib.disconnect()

        return BrokerSnapshotEnvelope(
            mode="live",
            status="error",
            account=AccountSnapshot(
                account_id=self.settings.ibkr_account_id,
                source="live",
                updated_at=now,
            ),
            positions=[],
            quotes={},
            warnings=warnings,
        )

    def _build_account_snapshot(self, ib, account_id: str, now: datetime) -> AccountSnapshot:
        summary_items = ib.accountSummary(account_id) if account_id else []
        summary = {item.tag: item.value for item in summary_items}
        currency = next(
            (
                item.currency
                for item in summary_items
                if getattr(item, "tag", "") == "NetLiquidation" and getattr(item, "currency", "")
            ),
            "USD",
        )

        return AccountSnapshot(
            account_id=account_id,
            net_liquidation=self._to_float(summary.get("NetLiquidation")),
            available_funds=self._to_float(summary.get("AvailableFunds")),
            buying_power=self._to_float(summary.get("BuyingPower")),
            currency=currency,
            source="live",
            updated_at=now,
        )

    def _build_positions(self, ib, account_id: str) -> list[PositionSnapshot]:
        rows: list[PositionSnapshot] = []
        for raw_position in ib.positions():
            raw_account = getattr(raw_position, "account", "")
            if account_id and raw_account and raw_account != account_id:
                continue

            contract = getattr(raw_position, "contract", None)
            symbol = getattr(contract, "symbol", "")
            if not symbol:
                continue

            rows.append(
                PositionSnapshot(
                    symbol=symbol,
                    quantity=self._to_float(getattr(raw_position, "position", 0)) or 0.0,
                    average_cost=self._to_float(getattr(raw_position, "avgCost", None)),
                    currency=getattr(contract, "currency", "USD") or "USD",
                    account_id=raw_account,
                )
            )
        return rows

    def _build_quotes(self, ib, stock_cls, tracked_symbols: Sequence[str], now: datetime) -> dict[str, QuoteSnapshot]:
        tickers = []
        unique_symbols = sorted({symbol.strip().upper() for symbol in tracked_symbols if symbol})
        for symbol in unique_symbols:
            contract = stock_cls(symbol, "SMART", "USD")
            ticker = ib.reqMktData(contract, "", False, False)
            tickers.append((symbol, ticker))

        ib.sleep(self.settings.ibkr_market_data_wait_seconds)

        quotes: dict[str, QuoteSnapshot] = {}
        for symbol, ticker in tickers:
            last_price = self._resolve_last_price(ticker)
            previous_close = self._to_float(getattr(ticker, "close", None))
            change_percent = None
            if last_price is not None and previous_close not in (None, 0):
                change_percent = round(((last_price - previous_close) / previous_close) * 100, 2)

            quotes[symbol] = QuoteSnapshot(
                symbol=symbol,
                last_price=last_price,
                previous_close=previous_close,
                change_percent=change_percent,
                bid=self._to_float(getattr(ticker, "bid", None)),
                ask=self._to_float(getattr(ticker, "ask", None)),
                as_of=now,
                source="live",
            )
        return quotes

    def _resolve_last_price(self, ticker) -> float | None:
        last = self._to_float(getattr(ticker, "last", None))
        if last is not None:
            return last

        close = self._to_float(getattr(ticker, "close", None))
        if close is not None:
            return close

        bid = self._to_float(getattr(ticker, "bid", None))
        ask = self._to_float(getattr(ticker, "ask", None))
        if bid is not None and ask is not None:
            return round((bid + ask) / 2, 2)
        return None

    def _to_float(self, value: object) -> float | None:
        if value in (None, "", "N/A"):
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None


@lru_cache(maxsize=1)
def get_ibkr_client() -> IBKRClient:
    settings = get_settings()
    if settings.ibkr_mode.lower() == "live":
        return LiveIBKRClient(settings)
    return MockIBKRClient(settings)
