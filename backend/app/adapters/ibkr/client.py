from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from functools import lru_cache
from math import isnan
from typing import Literal, Sequence
from xml.etree import ElementTree

from app.config.settings import Settings, get_settings
from app.domains.fundamentals.schemas import FundamentalSnapshot
from app.domains.indicators.schemas import PriceReferenceLevels
from app.domains.market.schemas import QuoteSnapshot
from app.domains.portfolio.schemas import AccountSnapshot, PositionSnapshot
from app.domains.snapshot.schemas import BrokerSnapshotEnvelope

IBKRProfileName = Literal["real", "paper"]


@dataclass(frozen=True)
class IBKRRuntimeProfile:
    name: IBKRProfileName
    display_name: str
    host: str
    port: int
    client_id: int
    account_id: str = ""


def normalize_ibkr_mode(value: str) -> Literal["mock", "ibkr"]:
    normalized = value.strip().lower()
    if normalized in {"ibkr", "live"}:
        return "ibkr"
    return "mock"


def normalize_ibkr_profile(value: str) -> IBKRProfileName:
    return "real" if value.strip().lower() == "real" else "paper"


def ibkr_display_name(profile: str) -> str:
    return "真实 TWS" if normalize_ibkr_profile(profile) == "real" else "模拟 TWS"


def resolve_legacy_runtime_profile(settings: Settings) -> IBKRRuntimeProfile:
    profile_name = normalize_ibkr_profile(settings.ibkr_active_profile)
    return IBKRRuntimeProfile(
        name=profile_name,
        display_name=ibkr_display_name(profile_name),
        host=settings.ibkr_host,
        port=settings.ibkr_port,
        client_id=settings.ibkr_client_id,
        account_id=settings.ibkr_account_id,
    )


class IBKRClient:
    def fetch_snapshot(self, tracked_symbols: Sequence[str]) -> BrokerSnapshotEnvelope:
        raise NotImplementedError


class MockIBKRClient(IBKRClient):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def fetch_snapshot(self, tracked_symbols: Sequence[str]) -> BrokerSnapshotEnvelope:
        now = datetime.now(UTC)
        unique_symbols = sorted({symbol.strip().upper() for symbol in tracked_symbols if symbol})
        quotes = {symbol: self._build_quote(symbol, now) for symbol in unique_symbols}
        reference_levels = {
            symbol: self._build_reference_levels(symbol, now) for symbol in unique_symbols
        }
        fundamentals = {
            symbol: self._build_fundamentals(symbol, now) for symbol in unique_symbols
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
            profile="mock",
            display_name="Mock 数据",
            account=account,
            positions=[],
            quotes=quotes,
            reference_levels=reference_levels,
            fundamentals=fundamentals,
            warnings=[
                "IBKR mock mode is active. Connect TWS/Gateway and switch IBKR_MODE=live for real data."
            ],
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

    def _build_reference_levels(self, symbol: str, now: datetime) -> PriceReferenceLevels:
        quote = self._build_quote(symbol, now)
        last_price = quote.last_price or 0.0
        return PriceReferenceLevels(
            high_52w=round(last_price * 1.18, 2) if last_price else None,
            low_52w=round(last_price * 0.72, 2) if last_price else None,
            high_90d=round(last_price * 1.08, 2) if last_price else None,
            low_90d=round(last_price * 0.88, 2) if last_price else None,
            source="mock",
            as_of=now,
        )

    def _build_fundamentals(self, symbol: str, now: datetime) -> FundamentalSnapshot:
        seed = sum(ord(character) for character in symbol)
        pe_ratio = round(10 + (seed % 18) + ((seed % 10) / 10), 2)
        growth = round(8 + (seed % 28) + ((seed % 9) / 10), 2)
        peg_ratio = round(pe_ratio / growth, 2) if growth > 0 else None
        return FundamentalSnapshot(
            pe_ratio=pe_ratio,
            earnings_growth_rate_percent=growth,
            peg_ratio=peg_ratio,
            source="mock",
            as_of=now,
        )


class LiveIBKRClient(IBKRClient):
    PEG_KEYS = ("peg", "pegratio", "ratiopeg", "pegtm", "peg5y")
    PE_KEYS = (
        "pe",
        "peratio",
        "ttmpe",
        "priceearnings",
        "priceearningsratio",
        "apeexclxor",
        "pettm",
    )
    GROWTH_KEYS = (
        "epsgrowth",
        "epsgrowthrate",
        "projectedepsgrowthrate",
        "projectedepsgrowth",
        "earningsgrowth",
        "ltgrowthrate",
        "fiveyearepsgrowth",
        "projlongtermgrowth",
        "expectedgrowthrate",
    )

    def __init__(self, settings: Settings, profile: IBKRRuntimeProfile | None = None) -> None:
        self.settings = settings
        self.profile = profile or resolve_legacy_runtime_profile(settings)

    def fetch_snapshot(self, tracked_symbols: Sequence[str]) -> BrokerSnapshotEnvelope:
        warnings: list[str] = []
        now = datetime.now(UTC)

        try:
            from ib_async import IB, StartupFetch, Stock
        except ImportError:
            return BrokerSnapshotEnvelope(
                mode="live",
                status="error",
                profile=self.profile.name,
                display_name=self.profile.display_name,
                account=AccountSnapshot(
                    account_id=self.profile.account_id,
                    source="live",
                    updated_at=now,
                ),
                positions=[],
                quotes={},
                reference_levels={},
                fundamentals={},
                warnings=["ib_async is not installed. Install it before using live IBKR mode."],
            )

        ib = IB()
        quotes: dict[str, QuoteSnapshot] = {}
        positions: list[PositionSnapshot] = []
        reference_levels: dict[str, PriceReferenceLevels] = {}
        fundamentals: dict[str, FundamentalSnapshot] = {}

        try:
            startup_fetch = (
                StartupFetch.POSITIONS
                | StartupFetch.ACCOUNT_UPDATES
                | StartupFetch.SUB_ACCOUNT_UPDATES
            )
            ib.RequestTimeout = self._request_timeout_seconds()
            ib.connect(
                self.profile.host,
                self.profile.port,
                clientId=self.profile.client_id,
                timeout=self._connect_timeout_seconds(),
                readonly=True,
                account=self.profile.account_id,
                fetchFields=startup_fetch,
            )

            if self.settings.ibkr_market_data_type == "delayed":
                ib.reqMarketDataType(3)
            elif self.settings.ibkr_market_data_type == "delayed_frozen":
                ib.reqMarketDataType(4)
            else:
                ib.reqMarketDataType(1)

            accounts = list(ib.managedAccounts())
            account_id = self.profile.account_id or (accounts[0] if accounts else "")

            account = self._build_account_snapshot(ib, account_id, now)
            positions = self._build_positions(ib, account_id)
            symbols = sorted(
                {
                    *{symbol.strip().upper() for symbol in tracked_symbols if symbol},
                    *{position.symbol for position in positions},
                }
            )
            contracts_by_symbol = self._build_stock_contracts(ib, Stock, symbols, warnings)
            quotes, ratio_payloads = self._build_quotes_and_ratio_payloads(
                ib,
                contracts_by_symbol,
                now,
            )
            reference_levels = self._build_reference_levels(
                ib,
                contracts_by_symbol,
                now,
                warnings,
            )
            fundamentals = self._build_fundamentals(
                ib,
                contracts_by_symbol,
                symbols,
                ratio_payloads,
                now,
                warnings,
            )

            return BrokerSnapshotEnvelope(
                mode="live",
                status="connected",
                profile=self.profile.name,
                display_name=self.profile.display_name,
                account=account,
                positions=positions,
                quotes=quotes,
                reference_levels=reference_levels,
                fundamentals=fundamentals,
                warnings=warnings,
            )
        except ConnectionRefusedError:
            warnings.append(
                "Could not connect to IBKR. Check TWS/Gateway, API port, and trusted IP settings."
            )
        except Exception as exc:
            warnings.append(f"IBKR live snapshot failed: {exc}")
        finally:
            if getattr(ib, "isConnected", lambda: False)():
                ib.disconnect()

        return BrokerSnapshotEnvelope(
            mode="live",
            status="error",
            profile=self.profile.name,
            display_name=self.profile.display_name,
            account=AccountSnapshot(
                account_id=self.profile.account_id,
                source="live",
                updated_at=now,
            ),
            positions=[],
            quotes={},
            reference_levels={},
            fundamentals={},
            warnings=warnings,
        )

    def test_connection(self) -> tuple[bool, list[str], str]:
        try:
            from ib_async import IB, StartupFetch
        except ImportError:
            return False, [], "ib_async is not installed. Install it before using IBKR mode."

        ib = IB()
        try:
            startup_fetch = StartupFetch.ACCOUNT_UPDATES | StartupFetch.SUB_ACCOUNT_UPDATES
            ib.RequestTimeout = self._request_timeout_seconds()
            ib.connect(
                self.profile.host,
                self.profile.port,
                clientId=self.profile.client_id,
                timeout=self._connect_timeout_seconds(),
                readonly=True,
                account=self.profile.account_id,
                fetchFields=startup_fetch,
            )
            accounts = list(ib.managedAccounts())
            if self.profile.account_id and self.profile.account_id not in accounts:
                return (
                    False,
                    accounts,
                    f"已连接 {self.profile.display_name}，但没有找到指定账户 {self.profile.account_id}。",
                )
            account_hint = f"识别到账户：{', '.join(accounts)}。" if accounts else "未返回账户列表。"
            return True, accounts, f"{self.profile.display_name} 只读连接成功。{account_hint}"
        except ConnectionRefusedError:
            return False, [], self._connection_help("TWS 未监听该端口，或当前连接的是另一个 TWS 会话。")
        except Exception as exc:
            return False, [], self._connection_help(str(exc))
        finally:
            if getattr(ib, "isConnected", lambda: False)():
                ib.disconnect()

    def _connection_help(self, error_detail: str) -> str:
        expected_port = 7497 if self.profile.name == "paper" else 7496
        return (
            f"{self.profile.display_name} 连接失败：{error_detail} "
            f"请确认 TWS 已登录{' Paper Trading' if self.profile.name == 'paper' else '真实账户'}、"
            "已开启 Enable ActiveX and Socket Clients、"
            f"Socket Port 为 {self.profile.port}（默认应为 {expected_port}）、"
            "Trusted IPs 允许 127.0.0.1，且 clientId 没有被其他 API 客户端占用。"
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

    def _build_stock_contracts(
        self,
        ib,
        stock_cls,
        tracked_symbols: Sequence[str],
        warnings: list[str],
    ) -> dict[str, object]:
        contracts: dict[str, object] = {}
        unique_symbols = sorted({symbol.strip().upper() for symbol in tracked_symbols if symbol})

        for symbol in unique_symbols:
            contract = stock_cls(symbol, "SMART", "USD")
            try:
                qualified_contracts = ib.qualifyContracts(contract)
            except Exception as exc:
                warnings.append(f"Failed to qualify stock contract for {symbol}: {exc}")
                continue

            if not qualified_contracts:
                warnings.append(f"Failed to qualify stock contract for {symbol}.")
                continue

            contracts[symbol] = qualified_contracts[0]

        return contracts

    def _build_quotes_and_ratio_payloads(
        self,
        ib,
        contracts_by_symbol: dict[str, object],
        now: datetime,
    ) -> tuple[dict[str, QuoteSnapshot], dict[str, dict[str, float]]]:
        tickers = []
        for symbol, contract in sorted(contracts_by_symbol.items()):
            ticker = ib.reqMktData(contract, "", False, False)
            tickers.append((symbol, ticker))

        self._wait_for_market_data(ib, [ticker for _, ticker in tickers])

        quotes: dict[str, QuoteSnapshot] = {}
        ratio_payloads: dict[str, dict[str, float]] = {}
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
                bid=self._to_positive_price(getattr(ticker, "bid", None)),
                ask=self._to_positive_price(getattr(ticker, "ask", None)),
                as_of=now,
                source="live",
            )

            ratio_payloads[symbol] = self._extract_ratio_payload(
                getattr(ticker, "fundamentalRatios", None)
            )
        return quotes, ratio_payloads

    def _wait_for_market_data(self, ib, tickers: Sequence[object]) -> None:
        if not tickers:
            return

        wait_seconds = max(self.settings.ibkr_market_data_wait_seconds, 1.0)
        interval_seconds = 0.25
        elapsed_seconds = 0.0

        while elapsed_seconds < wait_seconds:
            if all(self._ticker_has_price(ticker) for ticker in tickers):
                return
            sleep_seconds = min(interval_seconds, wait_seconds - elapsed_seconds)
            ib.sleep(sleep_seconds)
            elapsed_seconds += sleep_seconds

    def _ticker_has_price(self, ticker) -> bool:
        if self._resolve_last_price(ticker) is not None:
            return True
        return self._to_positive_price(getattr(ticker, "previousClose", None)) is not None

    def _build_reference_levels(
        self,
        ib,
        contracts_by_symbol: dict[str, object],
        now: datetime,
        warnings: list[str],
    ) -> dict[str, PriceReferenceLevels]:
        reference_levels: dict[str, PriceReferenceLevels] = {}

        for symbol, contract in sorted(contracts_by_symbol.items()):
            try:
                bars = ib.reqHistoricalData(
                    contract,
                    endDateTime="",
                    durationStr="1 Y",
                    barSizeSetting="1 day",
                    whatToShow="TRADES",
                    useRTH=False,
                    timeout=self._request_timeout_seconds(),
                )
                reference_levels[symbol] = self._reference_levels_from_bars(bars, now)
            except Exception as exc:
                warnings.append(f"Failed to load historical highs for {symbol}: {exc}")
                reference_levels[symbol] = PriceReferenceLevels(source="live", as_of=now)

        return reference_levels

    def _build_fundamentals(
        self,
        ib,
        contracts_by_symbol: dict[str, object],
        tracked_symbols: Sequence[str],
        ratio_payloads: dict[str, dict[str, float]],
        now: datetime,
        warnings: list[str],
    ) -> dict[str, FundamentalSnapshot]:
        unique_symbols = sorted({symbol.strip().upper() for symbol in tracked_symbols if symbol})
        snapshots: dict[str, FundamentalSnapshot] = {}

        for symbol in unique_symbols:
            contract = contracts_by_symbol.get(symbol)
            if contract is None:
                snapshots[symbol] = FundamentalSnapshot(source="live", as_of=now)
                continue

            ratio_payload = ratio_payloads.get(symbol, {})
            xml_payloads: list[str] = []

            try:
                report_snapshot = ib.reqFundamentalData(contract, "ReportSnapshot")
                if report_snapshot:
                    xml_payloads.append(report_snapshot)
            except Exception as exc:
                warnings.append(f"Failed to load ReportSnapshot for {symbol}: {exc}")

            try:
                analyst_estimates = ib.reqFundamentalData(contract, "RESC")
                if analyst_estimates:
                    xml_payloads.append(analyst_estimates)
            except Exception as exc:
                warnings.append(f"Failed to load RESC for {symbol}: {exc}")

            snapshots[symbol] = self._fundamentals_from_sources(
                ratio_payload,
                xml_payloads,
                now,
            )

        return snapshots

    def _fundamentals_from_sources(
        self,
        ratio_payload: dict[str, float],
        xml_payloads: list[str],
        now: datetime,
    ) -> FundamentalSnapshot:
        candidates = dict(ratio_payload)
        for xml_payload in xml_payloads:
            candidates.update(self._extract_xml_numeric_candidates(xml_payload))

        pe_ratio = self._pick_candidate(candidates, self.PE_KEYS)
        growth_rate = self._pick_candidate(candidates, self.GROWTH_KEYS)
        peg_ratio = self._pick_candidate(candidates, self.PEG_KEYS)

        if growth_rate is not None and abs(growth_rate) < 1:
            growth_rate = round(growth_rate * 100, 2)

        if peg_ratio is None and pe_ratio is not None and growth_rate not in (None, 0):
            peg_ratio = round(pe_ratio / growth_rate, 2)

        source = "live-ratios" if ratio_payload else "live-fundamentals"
        return FundamentalSnapshot(
            pe_ratio=pe_ratio,
            earnings_growth_rate_percent=growth_rate,
            peg_ratio=peg_ratio,
            source=source,
            as_of=now,
        )

    def _extract_ratio_payload(self, fundamental_ratios) -> dict[str, float]:
        if fundamental_ratios is None:
            return {}

        payload: dict[str, float] = {}
        for key, value in vars(fundamental_ratios).items():
            normalized = self._normalize_key(key)
            numeric_value = self._to_float(value)
            if numeric_value is None:
                continue
            payload[normalized] = numeric_value
        return payload

    def _extract_xml_numeric_candidates(self, xml_payload: str) -> dict[str, float]:
        candidates: dict[str, float] = {}
        try:
            root = ElementTree.fromstring(xml_payload)
        except ElementTree.ParseError:
            return candidates

        for element in root.iter():
            text = (element.text or "").strip()
            numeric_value = self._to_float(text)
            if numeric_value is None:
                continue

            tags = {self._normalize_key(element.tag)}
            for attr_name, attr_value in element.attrib.items():
                tags.add(self._normalize_key(attr_name))
                tags.add(self._normalize_key(str(attr_value)))

            for tag in tags:
                if tag:
                    candidates.setdefault(tag, numeric_value)
        return candidates

    def _pick_candidate(
        self,
        candidates: dict[str, float],
        keys: Sequence[str],
    ) -> float | None:
        preferred = [self._normalize_key(key) for key in keys]

        for key in preferred:
            if key in candidates:
                return candidates[key]

        for candidate_key, value in candidates.items():
            if any(key in candidate_key for key in preferred):
                return value
        return None

    def _reference_levels_from_bars(self, bars, now: datetime) -> PriceReferenceLevels:
        highs: list[float] = []
        lows: list[float] = []
        recent_highs: list[float] = []
        recent_lows: list[float] = []
        cutoff = now - timedelta(days=90)

        for bar in bars:
            high = self._to_float(getattr(bar, "high", None))
            low = self._to_float(getattr(bar, "low", None))

            if high is not None:
                highs.append(high)
            bar_dt = self._normalize_bar_datetime(getattr(bar, "date", None))
            if high is not None and bar_dt is not None and bar_dt >= cutoff:
                recent_highs.append(high)
            if low is not None:
                lows.append(low)
            if low is not None and bar_dt is not None and bar_dt >= cutoff:
                recent_lows.append(low)

        if not recent_highs and highs:
            recent_highs = highs[-65:]
        if not recent_lows and lows:
            recent_lows = lows[-65:]

        return PriceReferenceLevels(
            high_52w=round(max(highs), 2) if highs else None,
            low_52w=round(min(lows), 2) if lows else None,
            high_90d=round(max(recent_highs), 2) if recent_highs else None,
            low_90d=round(min(recent_lows), 2) if recent_lows else None,
            source="live",
            as_of=now,
        )

    def _normalize_bar_datetime(self, value: object) -> datetime | None:
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=UTC)
        if isinstance(value, date):
            return datetime.combine(value, time.min, tzinfo=UTC)
        if isinstance(value, str):
            raw = value.strip()
            for fmt in ("%Y%m%d", "%Y-%m-%d", "%Y%m%d  %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
                try:
                    parsed = datetime.strptime(raw, fmt)
                    return parsed.replace(tzinfo=UTC)
                except ValueError:
                    continue
        return None

    def _resolve_last_price(self, ticker) -> float | None:
        last = self._to_positive_price(getattr(ticker, "last", None))
        if last is not None:
            return last

        close = self._to_positive_price(getattr(ticker, "close", None))
        if close is not None:
            return close

        bid = self._to_positive_price(getattr(ticker, "bid", None))
        ask = self._to_positive_price(getattr(ticker, "ask", None))
        if bid is not None and ask is not None:
            return round((bid + ask) / 2, 2)
        return None

    def _to_positive_price(self, value: object) -> float | None:
        numeric = self._to_float(value)
        if numeric is None or numeric <= 0:
            return None
        return numeric

    def _normalize_key(self, value: str) -> str:
        return "".join(character for character in value.lower() if character.isalnum())

    def _to_float(self, value: object) -> float | None:
        if value in (None, "", "N/A"):
            return None

        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return None

        if isnan(numeric) or numeric <= -99999:
            return None
        return numeric

    def _connect_timeout_seconds(self) -> float:
        return max(float(self.settings.ibkr_connect_timeout_seconds), 1.0)

    def _request_timeout_seconds(self) -> float:
        return max(float(self.settings.ibkr_request_timeout_seconds), 1.0)


@lru_cache(maxsize=1)
def get_ibkr_client() -> IBKRClient:
    settings = get_settings()
    if normalize_ibkr_mode(settings.ibkr_mode) == "ibkr":
        return LiveIBKRClient(settings)
    return MockIBKRClient(settings)
