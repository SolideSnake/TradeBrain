export type Market = "US" | "HK" | "OTHER";
export type AssetType = "stock" | "etf" | "bond" | "other";

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
  currency: string;
  account_id: string;
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
  warnings: string[];
}

export interface SnapshotWatchlistItem extends WatchlistEntry {
  quote: QuoteSnapshot | null;
  position: PositionSnapshot | null;
}

export interface CanonicalSnapshot {
  meta: SnapshotMeta;
  summary: SnapshotSummary;
  account: AccountSnapshot;
  watchlist: SnapshotWatchlistItem[];
  positions: PositionSnapshot[];
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

export function getSnapshot(): Promise<CanonicalSnapshot> {
  return request<CanonicalSnapshot>("/api/snapshot");
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
