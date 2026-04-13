import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from "react";

import {
  AssetType,
  CreateWatchlistEntryPayload,
  Market,
  WatchlistEntry,
  createWatchlistEntry,
  deleteWatchlistEntry,
  listWatchlist,
} from "../shared/api";

const columns = ["Symbol", "Name", "Group", "Market", "Asset", "Flags", "Actions"];
const marketOptions: Market[] = ["US", "HK", "OTHER"];
const assetTypeOptions: AssetType[] = ["stock", "etf", "bond", "other"];

const defaultForm: CreateWatchlistEntryPayload = {
  symbol: "",
  name: "",
  market: "US",
  asset_type: "stock",
  group_name: "core",
  enabled: true,
  in_position: false,
  notes: "",
};

export function MonitorPage() {
  const [entries, setEntries] = useState<WatchlistEntry[]>([]);
  const [form, setForm] = useState<CreateWatchlistEntryPayload>(defaultForm);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void loadWatchlist();
  }, []);

  const summary = useMemo(
    () => ({
      total: entries.length,
      enabled: entries.filter((entry) => entry.enabled).length,
      inPosition: entries.filter((entry) => entry.in_position).length,
    }),
    [entries],
  );

  async function loadWatchlist() {
    setLoading(true);
    try {
      const data = await listWatchlist();
      setEntries(data);
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load watchlist.");
    } finally {
      setLoading(false);
    }
  }

  function handleInputChange(
    event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>,
  ) {
    const { name, value, type } = event.target;
    const nextValue =
      type === "checkbox" ? (event.target as HTMLInputElement).checked : value;

    setForm((current) => ({
      ...current,
      [name]:
        typeof nextValue === "string" && name === "symbol" ? nextValue.toUpperCase() : nextValue,
    }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);

    try {
      const created = await createWatchlistEntry(form);
      setEntries((current) => [...current, created].sort((left, right) => left.symbol.localeCompare(right.symbol)));
      setForm(defaultForm);
      setError(null);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Failed to add symbol.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(entryId: number) {
    try {
      await deleteWatchlistEntry(entryId);
      setEntries((current) => current.filter((entry) => entry.id !== entryId));
      setError(null);
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Failed to delete symbol.");
    }
  }

  return (
    <section>
      <header className="page-header">
        <span className="eyebrow">Watchlist</span>
        <h2>Monitor</h2>
        <p>The first live MVP surface: curate tracked symbols before we layer on prices, states, and tasks.</p>
      </header>

      <div className="panel-grid">
        <article className="panel">
          <h3>Tracked Symbols</h3>
          <p className="metric">{summary.total}</p>
          <p className="panel-note">All active and parked symbols currently under watch.</p>
        </article>
        <article className="panel">
          <h3>Enabled</h3>
          <p className="metric">{summary.enabled}</p>
          <p className="panel-note">Entries included in the next monitoring pass.</p>
        </article>
        <article className="panel">
          <h3>In Position</h3>
          <p className="metric">{summary.inPosition}</p>
          <p className="panel-note">Symbols already tied to an open portfolio position.</p>
        </article>
      </div>

      <div className="monitor-layout">
        <article className="panel">
          <h3>Add Watchlist Entry</h3>
          <p className="panel-note">Keep the first version simple: symbol, grouping, and whether you already hold it.</p>

          <form className="form-grid" onSubmit={handleSubmit}>
            <label>
              <span>Symbol</span>
              <input
                name="symbol"
                value={form.symbol}
                onChange={handleInputChange}
                placeholder="AAPL"
                maxLength={32}
                required
              />
            </label>

            <label>
              <span>Name</span>
              <input
                name="name"
                value={form.name}
                onChange={handleInputChange}
                placeholder="Apple Inc."
                maxLength={128}
                required
              />
            </label>

            <label>
              <span>Group</span>
              <input
                name="group_name"
                value={form.group_name}
                onChange={handleInputChange}
                placeholder="core"
                maxLength={64}
                required
              />
            </label>

            <label>
              <span>Market</span>
              <select name="market" value={form.market} onChange={handleInputChange}>
                {marketOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>

            <label>
              <span>Asset Type</span>
              <select name="asset_type" value={form.asset_type} onChange={handleInputChange}>
                {assetTypeOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>

            <label className="form-span-2">
              <span>Notes</span>
              <textarea
                name="notes"
                value={form.notes}
                onChange={handleInputChange}
                placeholder="Why this belongs in the list, risk notes, or target setup."
                rows={3}
              />
            </label>

            <label className="checkbox">
              <input
                type="checkbox"
                name="enabled"
                checked={form.enabled}
                onChange={handleInputChange}
              />
              <span>Enabled for monitoring</span>
            </label>

            <label className="checkbox">
              <input
                type="checkbox"
                name="in_position"
                checked={form.in_position}
                onChange={handleInputChange}
              />
              <span>Already in position</span>
            </label>

            <div className="actions-row form-span-2">
              <button type="submit" className="button" disabled={submitting}>
                {submitting ? "Saving..." : "Add to Watchlist"}
              </button>
              <button type="button" className="button button-secondary" onClick={() => setForm(defaultForm)}>
                Reset
              </button>
            </div>
          </form>
        </article>

        <article className="table-shell">
          <div className="table-header">
            <div>
              <h3>Tracked Entries</h3>
              <p className="panel-note">This table is now live data from the backend watchlist API.</p>
            </div>
            <button type="button" className="button button-secondary" onClick={() => void loadWatchlist()}>
              Refresh
            </button>
          </div>

          {error ? <div className="banner banner-error">{error}</div> : null}

          <div className="table-row table-head">
            {columns.map((column) => (
              <span key={column}>{column}</span>
            ))}
          </div>

          {loading ? <div className="table-empty">Loading watchlist...</div> : null}

          {!loading && entries.length === 0 ? (
            <div className="table-empty">No watchlist entries yet. Add your first symbol from the form.</div>
          ) : null}

          {!loading &&
            entries.map((entry) => (
              <div key={entry.id} className="table-row">
                <span className="symbol-cell">{entry.symbol}</span>
                <span>{entry.name}</span>
                <span>{entry.group_name}</span>
                <span>{entry.market}</span>
                <span>{entry.asset_type}</span>
                <span className="status-stack">
                  <span className={entry.enabled ? "status-pill status-pill-ok" : "status-pill"}>
                    {entry.enabled ? "Enabled" : "Paused"}
                  </span>
                  <span className={entry.in_position ? "status-pill status-pill-warn" : "status-pill"}>
                    {entry.in_position ? "In position" : "Watching"}
                  </span>
                </span>
                <span className="table-actions">
                  <button
                    type="button"
                    className="button button-danger"
                    onClick={() => void handleDelete(entry.id)}
                  >
                    Remove
                  </button>
                </span>
              </div>
            ))}
        </article>
      </div>
    </section>
  );
}
