export type Market = "US" | "HK" | "KR" | "OTHER";
export type AssetType = "stock" | "etf" | "bond" | "other";
export type ValuationLabel = "undervalued" | "fair" | "overvalued";
export type AlertChannel = "telegram" | "feishu";
export type AlertLevel = "info" | "warning" | "critical";
export type AlertDeliveryStatus = "sent" | "skipped" | "failed";
export type EventSeverity = "info" | "warning" | "critical";
export type EventStatus = "success" | "failed" | "skipped" | "sent" | string;
export type AlertRuleSource = "watchlist" | "portfolio" | "custom";
export type AlertRuleCategory = "threshold" | "event" | "schedule" | "composite";
export type AlertRuleMetric =
  | "current_price"
  | "day_change_percent"
  | "drawdown_52w"
  | "drawdown_90d"
  | "valuation_label"
  | "net_liquidation"
  | "available_funds"
  | "buying_power"
  | "custom_value";
export type AlertRuleOperator =
  | "above"
  | "below"
  | "equals"
  | "becomes"
  | "gte"
  | "lte"
  | "not_equals"
  | "cross_above"
  | "cross_below"
  | "change_to";
export type NotificationSettingsSource = "database" | "environment" | "none";
export type IBKRMode = "mock" | "ibkr";
export type IBKRProfileName = "real" | "paper";
export type IBKRSettingsSource = "database" | "environment";
export type SnapshotCacheStatus = "empty" | "idle" | "refreshing" | "success" | "failed";
export type ScannerCandidateReason = "large_drop" | "pullback_52w" | "undervalued";

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
  name?: string;
  market?: Market;
  asset_type?: AssetType;
  group_name?: string;
  enabled?: boolean;
  in_position?: boolean;
  notes?: string;
}

export interface QuoteSnapshot {
  symbol: string;
  last_price: number | null;
  previous_close: number | null;
  change_percent: number | null;
  bid: number | null;
  ask: number | null;
  currency: string;
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
  base_currency: string;
  fx_rate_to_base: number | null;
  average_cost_base: number | null;
  market_price_base: number | null;
  market_value_base: number | null;
  unrealized_pnl_base: number | null;
  account_id: string;
}

export interface PriceReferenceLevels {
  high_52w: number | null;
  low_52w: number | null;
  high_90d: number | null;
  low_90d: number | null;
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
  low_52w: number | null;
  drawdown_from_52w_high_percent: number | null;
  gain_from_52w_low_percent: number | null;
  high_90d: number | null;
  low_90d: number | null;
  drawdown_from_90d_high_percent: number | null;
  gain_from_90d_low_percent: number | null;
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

export interface EventRecord {
  id: number;
  event_type: string;
  source: string;
  severity: EventSeverity | string;
  title: string;
  message: string;
  symbol: string;
  status: EventStatus;
  entity_type: string;
  entity_id: string;
  payload: Record<string, unknown>;
  occurred_at: string;
  created_at: string;
}

export interface NotificationSettings {
  telegram_enabled: boolean;
  telegram_bot_token_configured: boolean;
  telegram_bot_token_masked: string | null;
  telegram_chat_id: string;
  feishu_enabled: boolean;
  feishu_webhook_url_configured: boolean;
  feishu_webhook_url_masked: string | null;
  feishu_secret_configured: boolean;
  feishu_secret_masked: string | null;
  source: NotificationSettingsSource;
}

export interface UpdateNotificationSettingsPayload {
  telegram_bot_token?: string;
  telegram_chat_id?: string;
  feishu_webhook_url?: string;
  feishu_secret?: string;
}

export interface NotificationTestResult {
  success: boolean;
  delivery_status: AlertDeliveryStatus;
  detail: string;
}

export interface AlertRule {
  id: number;
  schema_version: number;
  name: string;
  enabled: boolean;
  category: AlertRuleCategory;
  source: AlertRuleSource;
  symbol: string;
  metric: AlertRuleMetric;
  operator: AlertRuleOperator;
  threshold_value: string;
  cooldown_seconds: number;
  edge_only: boolean;
  message_template: string;
  last_observed_value: string;
  last_evaluated_at: string | null;
  last_matched: boolean;
  last_suppressed_at: string | null;
  suppressed_count: number;
  sent_count: number;
  failed_count: number;
  last_triggered_at: string | null;
  last_sent_at: string | null;
  last_failed_at: string | null;
  last_error: string;
  created_at: string;
  updated_at: string;
}

export interface CreateAlertRulePayload {
  name: string;
  enabled?: boolean;
  category?: AlertRuleCategory;
  source: AlertRuleSource;
  symbol?: string;
  metric: AlertRuleMetric;
  operator: AlertRuleOperator;
  threshold_value: string;
  cooldown_seconds?: number;
  edge_only?: boolean;
  message_template?: string;
}

export interface UpdateAlertRulePayload {
  name?: string;
  enabled?: boolean;
  category?: AlertRuleCategory;
  source?: AlertRuleSource;
  symbol?: string;
  metric?: AlertRuleMetric;
  operator?: AlertRuleOperator;
  threshold_value?: string;
  cooldown_seconds?: number;
  edge_only?: boolean;
  message_template?: string;
}

export interface AlertRuleOption {
  value: string;
  label: string;
}

export interface AlertRuleMetricOption extends AlertRuleOption {
  source: AlertRuleSource;
  value_type: "number" | "text" | string;
  default_operator: AlertRuleOperator;
  default_threshold: string;
  unit: string;
}

export interface AlertRuleTemplate {
  id: string;
  label: string;
  description: string;
  source: AlertRuleSource;
  metric: AlertRuleMetric;
  operator: AlertRuleOperator;
  threshold_value: string;
  cooldown_seconds: number;
  edge_only: boolean;
}

export interface AlertRuleMetadata {
  sources: AlertRuleOption[];
  operators: AlertRuleOption[];
  metrics: AlertRuleMetricOption[];
  templates: AlertRuleTemplate[];
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
  cash_balance: number | null;
  settled_cash: number | null;
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

export interface SnapshotRefreshSettings {
  enabled: boolean;
  interval_seconds: number;
}

export interface UpdateSnapshotRefreshSettingsPayload {
  enabled?: boolean;
  interval_seconds?: number;
}

export interface ScoreBreakdown {
  name: string;
  score: number;
  reason: string;
}

export interface ScoreResult {
  symbol: string;
  score: number;
  breakdown: ScoreBreakdown[];
}

export interface StrategyEvaluation {
  rule_id: string;
  rule_name: string;
  matched: boolean;
  reasons: string[];
}

export interface ScannerCandidate {
  symbol: string;
  name: string;
  reason: ScannerCandidateReason;
  score: ScoreResult;
  strategy: StrategyEvaluation;
}

export interface ScannerResult {
  generated_at: string;
  candidates: ScannerCandidate[];
}

interface RequestOptions extends RequestInit {
  timeoutMs?: number;
}

async function request<T>(input: RequestInfo, init?: RequestOptions): Promise<T> {
  const { timeoutMs, signal, ...requestInit } = init ?? {};
  const controller = timeoutMs ? new AbortController() : null;
  const timeoutId = controller
    ? window.setTimeout(() => controller.abort(), timeoutMs)
    : null;

  try {
    const response = await fetch(input, {
      headers: {
        "Content-Type": "application/json",
        ...(requestInit.headers ?? {}),
      },
      ...requestInit,
      signal: signal ?? controller?.signal,
    });

    if (!response.ok) {
      const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
      throw new Error(payload?.detail ?? `Request failed with status ${response.status}`);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error("刷新等待超时，旧数据已保留。请确认 TWS 已完全启动后再试。");
    }
    throw error;
  } finally {
    if (timeoutId !== null) {
      window.clearTimeout(timeoutId);
    }
  }
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
    timeoutMs: 30000,
  });
}

export function getScannerResult(): Promise<ScannerResult> {
  return request<ScannerResult>("/api/scanner");
}

export function listEvents(limit = 50): Promise<EventRecord[]> {
  return request<EventRecord[]>(`/api/events?limit=${limit}`);
}

export function listAlertRules(): Promise<AlertRule[]> {
  return request<AlertRule[]>("/api/alert-rules");
}

export function getAlertRuleMetadata(): Promise<AlertRuleMetadata> {
  return request<AlertRuleMetadata>("/api/alert-rules/metadata");
}

export function createAlertRule(payload: CreateAlertRulePayload): Promise<AlertRule> {
  return request<AlertRule>("/api/alert-rules", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateAlertRule(ruleId: number, payload: UpdateAlertRulePayload): Promise<AlertRule> {
  return request<AlertRule>(`/api/alert-rules/${ruleId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteAlertRule(ruleId: number): Promise<void> {
  return request<void>(`/api/alert-rules/${ruleId}`, {
    method: "DELETE",
  });
}

export function resetAlertRuleCounters(): Promise<AlertRule[]> {
  return request<AlertRule[]>("/api/alert-rules/reset-counters", {
    method: "POST",
  });
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

export function getSnapshotRefreshSettings(): Promise<SnapshotRefreshSettings> {
  return request<SnapshotRefreshSettings>("/api/settings/snapshot-refresh");
}

export function updateSnapshotRefreshSettings(
  payload: UpdateSnapshotRefreshSettingsPayload,
): Promise<SnapshotRefreshSettings> {
  return request<SnapshotRefreshSettings>("/api/settings/snapshot-refresh", {
    method: "PUT",
    body: JSON.stringify(payload),
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
