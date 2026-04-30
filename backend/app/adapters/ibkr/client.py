from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from functools import lru_cache
from math import isnan
from typing import Literal, Sequence
from xml.etree import ElementTree

from app.config.settings import Settings, get_settings
from app.domains.fundamentals.schemas import FundamentalSnapshot
from app.domains.fx.schemas import FxRateSnapshot
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
            cash_balance=82000.0,
            settled_cash=82000.0,
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
            currency=self._currency_for_symbol(symbol),
            as_of=now,
            source="mock",
        )

    def _currency_for_symbol(self, symbol: str) -> str:
        if symbol.isdigit() and len(symbol) == 6:
            return "KRW"
        return "USD"

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
            from ib_async import IB, Forex, StartupFetch, Stock
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
        fx_rates: dict[str, FxRateSnapshot] = {}

        try:
            ib.RequestTimeout = self._request_timeout_seconds()
            ib.connect(
                self.profile.host,
                self.profile.port,
                clientId=self.profile.client_id,
                timeout=self._connect_timeout_seconds(),
                readonly=True,
                account=self.profile.account_id,
                fetchFields=StartupFetch(0),
            )

            if self.settings.ibkr_market_data_type == "delayed":
                ib.reqMarketDataType(3)
            elif self.settings.ibkr_market_data_type == "delayed_frozen":
                ib.reqMarketDataType(4)
            else:
                ib.reqMarketDataType(1)

            accounts = self._safe_managed_accounts(ib, warnings)
            account_id = self.profile.account_id or (accounts[0] if accounts else "")

            account = self._safe_build_account_snapshot(ib, account_id, now, warnings)
            positions = self._safe_build_positions(ib, account_id, warnings)
            fx_rates = self._build_fx_rates(
                ib,
                Forex,
                {position.currency for position in positions},
                account.currency,
                now,
                warnings,
            )
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
                fx_rates=fx_rates,
                warnings=warnings,
            )
        except ConnectionRefusedError:
            warnings.append(
                "Could not connect to IBKR. Check TWS/Gateway, API port, and trusted IP settings."
            )
        except Exception as exc:
            warnings.append(f"IBKR live snapshot failed: {self._describe_exception(exc)}")
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
            ib.RequestTimeout = self._request_timeout_seconds()
            ib.connect(
                self.profile.host,
                self.profile.port,
                clientId=self.profile.client_id,
                timeout=self._connect_timeout_seconds(),
                readonly=True,
                account=self.profile.account_id,
                fetchFields=StartupFetch(0),
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
            return False, [], self._connection_help(self._describe_exception(exc))
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

    def _safe_managed_accounts(self, ib, warnings: list[str]) -> list[str]:
        try:
            return list(ib.managedAccounts())
        except Exception as exc:
            warnings.append(f"Failed to load IBKR managed accounts: {self._describe_exception(exc)}")
            return []

    def _safe_build_account_snapshot(
        self,
        ib,
        account_id: str,
        now: datetime,
        warnings: list[str],
    ) -> AccountSnapshot:
        try:
            return self._build_account_snapshot(ib, account_id, now)
        except Exception as exc:
            warnings.append(f"Failed to load IBKR account summary: {self._describe_exception(exc)}")
            return AccountSnapshot(
                account_id=account_id,
                source="live",
                updated_at=now,
            )

    def _safe_build_positions(
        self,
        ib,
        account_id: str,
        warnings: list[str],
    ) -> list[PositionSnapshot]:
        try:
            return self._build_positions(ib, account_id)
        except Exception as exc:
            warnings.append(f"Failed to load IBKR positions: {self._describe_exception(exc)}")
            return []

    def _build_account_snapshot(self, ib, account_id: str, now: datetime) -> AccountSnapshot:
        summary_items = ib.accountSummary(account_id) if account_id else []
        currency = next(
            (
                item.currency
                for item in summary_items
                if getattr(item, "tag", "") == "NetLiquidation" and getattr(item, "currency", "")
            ),
            "USD",
        )
        total_cash_value = self._account_summary_float(summary_items, "TotalCashValue", currency)
        cash_balance = (
            total_cash_value
            if total_cash_value is not None
            else self._account_summary_float(summary_items, "CashBalance", currency)
        )

        return AccountSnapshot(
            account_id=account_id,
            net_liquidation=self._account_summary_float(summary_items, "NetLiquidation", currency),
            cash_balance=cash_balance,
            settled_cash=self._account_summary_float(summary_items, "SettledCash", currency),
            available_funds=self._account_summary_float(summary_items, "AvailableFunds", currency),
            buying_power=self._account_summary_float(summary_items, "BuyingPower", currency),
            currency=currency,
            source="live",
            updated_at=now,
        )

    def _account_summary_float(
        self,
        summary_items: Sequence[object],
        tag: str,
        currency: str,
    ) -> float | None:
        preferred_currency = currency.strip().upper()
        matching_items = [
            item for item in summary_items if getattr(item, "tag", "") == tag
        ]

        for item in matching_items:
            item_currency = str(getattr(item, "currency", "")).strip().upper()
            if item_currency == preferred_currency:
                return self._to_float(getattr(item, "value", None))

        if matching_items:
            return self._to_float(getattr(matching_items[0], "value", None))
        return None

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
            symbol = symbol.strip().upper()

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

    def _build_fx_rates(
        self,
        ib,
        forex_cls,
        currencies: set[str],
        base_currency: str,
        now: datetime,
        warnings: list[str],
    ) -> dict[str, FxRateSnapshot]:
        normalized_base = base_currency.strip().upper() or "USD"
        rates: dict[str, FxRateSnapshot] = {}

        for currency in sorted({currency.strip().upper() for currency in currencies if currency}):
            if currency == normalized_base:
                rates[currency] = FxRateSnapshot(
                    from_currency=currency,
                    to_currency=normalized_base,
                    rate=1.0,
                    source="identity",
                    as_of=now,
                )
                continue

            rate = self._fetch_fx_rate_to_base(ib, forex_cls, currency, normalized_base)
            if rate is None:
                warnings.append(
                    f"Failed to load FX rate for {currency}->{normalized_base}; "
                    "base-currency portfolio totals may exclude this position."
                )
                continue

            rates[currency] = FxRateSnapshot(
                from_currency=currency,
                to_currency=normalized_base,
                rate=rate,
                source="ibkr-fx",
                as_of=now,
            )

        return rates

    def _fetch_fx_rate_to_base(
        self,
        ib,
        forex_cls,
        from_currency: str,
        base_currency: str,
    ) -> float | None:
        direct_price = self._fetch_fx_pair_price(ib, forex_cls, f"{from_currency}{base_currency}")
        if direct_price is not None:
            return direct_price

        inverse_price = self._fetch_fx_pair_price(ib, forex_cls, f"{base_currency}{from_currency}")
        if inverse_price not in (None, 0):
            return round(1 / inverse_price, 10)
        return None

    def _fetch_fx_pair_price(self, ib, forex_cls, pair: str) -> float | None:
        try:
            qualified_contracts = ib.qualifyContracts(forex_cls(pair))
        except Exception:
            return None

        contract = self._first_valid_contract(qualified_contracts)
        if contract is None:
            return None

        ticker = None
        try:
            ticker = ib.reqMktData(contract, "", False, False)
            self._wait_for_market_data(ib, [ticker])
            return self._resolve_last_price(ticker)
        except Exception:
            return None
        finally:
            if ticker is not None:
                try:
                    ib.cancelMktData(contract)
                except Exception:
                    pass

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
            ibkr_symbol, exchange, currency = self._stock_contract_spec(symbol)
            contract = stock_cls(ibkr_symbol, exchange, currency)
            try:
                qualified_contracts = ib.qualifyContracts(contract)
            except Exception as exc:
                warnings.append(
                    f"Failed to qualify stock contract for {symbol}: {self._describe_exception(exc)}"
                )
                continue

            qualified_contract = self._first_valid_contract(qualified_contracts)
            if qualified_contract is None:
                warnings.append(f"Failed to qualify stock contract for {symbol}.")
                continue

            contracts[symbol] = qualified_contract

        return contracts

    def _stock_contract_spec(self, symbol: str) -> tuple[str, str, str]:
        normalized_symbol = symbol.strip().upper()
        if normalized_symbol.isdigit() and len(normalized_symbol) == 6:
            return normalized_symbol, "KRX", "KRW"
        return self._to_ibkr_stock_symbol(normalized_symbol), "SMART", "USD"

    def _to_ibkr_stock_symbol(self, symbol: str) -> str:
        # IBKR commonly represents class shares such as BRK.B as BRK B.
        return symbol.strip().upper().replace(".", " ")

    def _first_valid_contract(self, contracts: Sequence[object]) -> object | None:
        for contract in contracts:
            if contract is None:
                continue
            if getattr(contract, "secType", None):
                return contract
        return None

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
            previous_close = self._resolve_previous_close(ticker)
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
                currency=self._quote_currency(symbol, contract),
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
        return self._resolve_last_price(ticker) is not None

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

        market_price = self._resolve_market_price(ticker)
        if market_price is not None:
            return market_price

        close = self._to_positive_price(getattr(ticker, "close", None))
        if close is not None:
            return close

        previous_close = self._to_positive_price(getattr(ticker, "previousClose", None))
        if previous_close is not None:
            return previous_close

        bid = self._to_positive_price(getattr(ticker, "bid", None))
        ask = self._to_positive_price(getattr(ticker, "ask", None))
        if bid is not None and ask is not None:
            return round((bid + ask) / 2, 2)
        return None

    def _resolve_previous_close(self, ticker) -> float | None:
        close = self._to_positive_price(getattr(ticker, "close", None))
        if close is not None:
            return close
        return self._to_positive_price(getattr(ticker, "previousClose", None))

    def _resolve_market_price(self, ticker) -> float | None:
        market_price = getattr(ticker, "marketPrice", None)
        if not callable(market_price):
            return None
        try:
            return self._to_positive_price(market_price())
        except Exception:
            return None

    def _quote_currency(self, symbol: str, contract: object) -> str:
        # KRX six-digit tickers can come back with incomplete contract metadata.
        if symbol.isdigit() and len(symbol) == 6:
            return "KRW"
        return getattr(contract, "currency", "USD") or "USD"

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

    def _describe_exception(self, exc: Exception) -> str:
        detail = str(exc).strip()
        if detail:
            return detail

        name = type(exc).__name__
        if name == "TimeoutError":
            return (
                "请求超时。TWS 可能刚启动尚未完成同步，或当前 clientId 被占用，"
                "也可能是账户/行情权限响应过慢。"
            )
        return name

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
