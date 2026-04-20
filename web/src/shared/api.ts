export type Market = "US" | "HK" | "OTHER";
export type AssetType = "stock" | "etf" | "bond" | "other";
export type ValuationLabel = "undervalued" | "fair" | "overvalued";
export type AlertChannel = "telegram";
export type AlertLevel = "info" | "warning" | "critical";
export type AlertDeliveryStatus = "sent" | "skipped" | "failed";
export type NotificationSettingsSource = "database" | "environment" | "none";
export type IBKRMode = "mock" | "ibkr";
export type IBKRProfileName = "real" | "paper";
export type IBKRSettingsSource = "database" | "environment";
export type SnapshotCacheStatus = "empty" | "idle" | "refreshing" | "success" | "failed";

export interface WatchlistEntry {
  id: number;
  symbol: string;
  name: string;
  market: Market;
  asset_type: AssetType;
  group_name: string;
  enabled: boolean;
  in_position: boolean;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface CreateWatchlistEntryPayload {
  symbol: string;
  name: string;
  market: Market;
  asset_type: AssetType;
  group_name: string;
  enabled: boolean;
  in_position: boolean;
  notes: string;
}

export interface QuoteSnapshot {
  symbol: string;
  last_price: number | null;
  previous_close: number | null;
  change_percent: number | null;
  bid: number | null;
  ask: number | null;
  as_of: string | null;
  source: string;
}

export interface PositionSnapshot {
  symbol: string;
  quantity: number;
  average_cost: number | null;
  market_price: number | null;
  market_value: number | null;
  unrealized_pnl: number | null;
  unrealized_pnl_percent: number | null;
  currency: string;
  account_id: string;
}

export interface PriceReferenceLevels {
  high_52w: number | null;
  high_90d: number | null;
  source: string;
  as_of: string | null;
}

export interface IndicatorSnapshot {
  current_price: number | null;
  previous_close: number | null;
  day_change_percent: number | null;
  average_cost: number | null;
  market_value: number | null;
  unrealized_pnl: number | null;
  unrealized_pnl_percent: number | null;
  high_52w: number | null;
  drawdown_from_52w_high_percent: number | null;
  high_90d: number | null;
  drawdown_from_90d_high_percent: number | null;
  pe_ratio: number | null;
  earnings_growth_rate_percent: number | null;
  peg_ratio: number | null;
  valuation_label: ValuationLabel | null;
}

export interface FundamentalSnapshot {
  pe_ratio: number | null;
  earnings_growth_rate_percent: number | null;
  peg_ratio: number | null;
  source: string;
  as_of: string | null;
}

export interface WatchlistStateSnapshot {
  symbol: string;
  current_label: ValuationLabel | null;
  previous_label: ValuationLabel | null;
  has_changed: boolean;
  changed_at: string | null;
  evaluated_at: string;
}

export interface AlertEvent {
  id: number;
  symbol: string;
  channel: AlertChannel;
  level: AlertLevel;
  delivery_status: AlertDeliveryStatus;
  title: string;
  message: string;
  error_detail: string;
  created_at: string;
}

export interface NotificationSettings {
  telegram_enabled: boolean;
  telegram_bot_token_configured: boolean;
  telegram_bot_token_masked: string | null;
  telegram_chat_id: string;
  source: NotificationSettingsSource;
}

export interface UpdateNotificationSettingsPayload {
  telegram_bot_token?: string;
  telegram_chat_id?: string;
}

export interface NotificationTestResult {
  success: boolean;
  delivery_status: AlertDeliveryStatus;
  detail: string;
}

export interface IBKRConnectionProfile {
  host: string;
  port: number;
  client_id: number;
  account_id: string;
}

export interface IBKRSettings {
  mode: IBKRMode;
  active_profile: IBKRProfileName;
  active_display_name: string;
  real: IBKRConnectionProfile;
  paper: IBKRConnectionProfile;
  source: IBKRSettingsSource;
}

export interface UpdateIBKRSettingsPayload {
  mode?: IBKRMode;
  active_profile?: IBKRProfileName;
  real?: IBKRConnectionProfile;
  paper?: IBKRConnectionProfile;
}

export interface IBKRConnectionTestResult {
  success: boolean;
  profile: IBKRProfileName;
  display_name: string;
  host: string;
  port: number;
  client_id: number;
  account_id: string;
  accounts: string[];
  detail: string;
}

export interface AccountSnapshot {
  account_id: string;
  net_liquidation: number | null;
  available_funds: number | null;
  buying_power: number | null;
  currency: string;
  source: string;
  updated_at: string;
}

export interface SnapshotSummary {
  tracked_symbols: number;
  enabled_symbols: number;
  symbols_in_position: number;
  quote_coverage: number;
  position_count: number;
}

export interface SnapshotMeta {
  generated_at: string;
  broker_mode: "mock" | "live";
  broker_status: "mock" | "connected" | "error";
  broker_profile: "mock" | "real" | "paper";
  broker_display_name: string;
  warnings: string[];
}

export interface SnapshotWatchlistItem extends WatchlistEntry {
  quote: QuoteSnapshot | null;
  position: PositionSnapshot | null;
  reference_levels: PriceReferenceLevels | null;
  fundamentals: FundamentalSnapshot | null;
  indicators: IndicatorSnapshot | null;
  state: WatchlistStateSnapshot | null;
}

export interface CanonicalSnapshot {
  meta: SnapshotMeta;
  summary: SnapshotSummary;
  account: AccountSnapshot;
  watchlist: SnapshotWatchlistItem[];
  positions: PositionSnapshot[];
}

export interface SnapshotResponse {
  snapshot: CanonicalSnapshot | null;
  cache_status: SnapshotCacheStatus;
  from_cache: boolean;
  last_success_at: string | null;
  refresh_started_at: string | null;
  last_error_at: string | null;
  last_error: string;
}

async function request<T>(input: RequestInfo, init?: RequestInit): Promise<T> {
  const response = await fetch(input, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `Request failed with status ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export function listWatchlist(): Promise<WatchlistEntry[]> {
  return request<WatchlistEntry[]>("/api/watchlist");
}

export function getSnapshot(): Promise<SnapshotResponse> {
  return request<SnapshotResponse>("/api/snapshot");
}

export function refreshSnapshot(): Promise<SnapshotResponse> {
  return request<SnapshotResponse>("/api/snapshot/refresh", {
    method: "POST",
  });
}

export function listAlerts(): Promise<AlertEvent[]> {
  return request<AlertEvent[]>("/api/alerts");
}

export function getNotificationSettings(): Promise<NotificationSettings> {
  return request<NotificationSettings>("/api/settings/notifications");
}

export function updateNotificationSettings(
  payload: UpdateNotificationSettingsPayload,
): Promise<NotificationSettings> {
  return request<NotificationSettings>("/api/settings/notifications", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function testNotificationSettings(): Promise<NotificationTestResult> {
  return request<NotificationTestResult>("/api/settings/notifications/test", {
    method: "POST",
  });
}

export function getIBKRSettings(): Promise<IBKRSettings> {
  return request<IBKRSettings>("/api/settings/ibkr");
}

export function updateIBKRSettings(payload: UpdateIBKRSettingsPayload): Promise<IBKRSettings> {
  return request<IBKRSettings>("/api/settings/ibkr", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function testIBKRConnection(profile: IBKRProfileName): Promise<IBKRConnectionTestResult> {
  return request<IBKRConnectionTestResult>("/api/settings/ibkr/test", {
    method: "POST",
    body: JSON.stringify({ profile }),
  });
}

export function createWatchlistEntry(
  payload: CreateWatchlistEntryPayload,
): Promise<WatchlistEntry> {
  return request<WatchlistEntry>("/api/watchlist", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteWatchlistEntry(entryId: number): Promise<void> {
  return request<void>(`/api/watchlist/${entryId}`, {
    method: "DELETE",
  });
}
