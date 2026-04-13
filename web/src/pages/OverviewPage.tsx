import { useEffect, useState } from "react";

import { CanonicalSnapshot, getSnapshot } from "../shared/api";

function formatCurrency(value: number | null, currency: string) {
  if (value === null) {
    return "--";
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(value);
}

export function OverviewPage() {
  const [snapshot, setSnapshot] = useState<CanonicalSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void loadSnapshot();
  }, []);

  async function loadSnapshot() {
    setLoading(true);
    try {
      const nextSnapshot = await getSnapshot();
      setSnapshot(nextSnapshot);
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load snapshot.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section>
      <header className="page-header">
        <span className="eyebrow">MVP</span>
        <h2>Overview</h2>
        <p>Start here each day: system status, broker mode, tracked symbols, and the latest snapshot health.</p>
      </header>

      <div className="table-header page-toolbar">
        <div>
          <h3>Current Snapshot</h3>
          <p className="panel-note">This page now reads the backend snapshot API, which is the same shape we will keep when real IBKR data is connected.</p>
        </div>
        <button type="button" className="button button-secondary" onClick={() => void loadSnapshot()}>
          Refresh Snapshot
        </button>
      </div>

      {error ? <div className="banner banner-error">{error}</div> : null}

      {loading && !snapshot ? <div className="table-empty">Loading snapshot...</div> : null}

      {snapshot ? (
        <>
          <div className="panel-grid">
            <article className="panel">
              <h3>Broker Status</h3>
              <p className="metric metric-compact">{snapshot.meta.broker_status}</p>
              <p className="panel-note">Mode: {snapshot.meta.broker_mode}</p>
            </article>
            <article className="panel">
              <h3>Tracked Symbols</h3>
              <p className="metric metric-compact">{snapshot.summary.tracked_symbols}</p>
              <p className="panel-note">{snapshot.summary.enabled_symbols} enabled for monitoring</p>
            </article>
            <article className="panel">
              <h3>Quote Coverage</h3>
              <p className="metric metric-compact">{snapshot.summary.quote_coverage}</p>
              <p className="panel-note">Rows currently enriched with market data</p>
            </article>
            <article className="panel">
              <h3>Account Value</h3>
              <p className="metric metric-compact">
                {formatCurrency(snapshot.account.net_liquidation, snapshot.account.currency)}
              </p>
              <p className="panel-note">Source: {snapshot.account.source}</p>
            </article>
          </div>

          <div className="panel-grid overview-secondary">
            <article className="panel">
              <h3>Warnings</h3>
              {snapshot.meta.warnings.length === 0 ? (
                <p>No broker warnings right now.</p>
              ) : (
                <div className="stack-list">
                  {snapshot.meta.warnings.map((warning) => (
                    <div key={warning} className="status-pill status-pill-warn status-pill-block">
                      {warning}
                    </div>
                  ))}
                </div>
              )}
            </article>
            <article className="panel">
              <h3>Open Positions In Snapshot</h3>
              <p className="metric metric-compact">{snapshot.positions.length}</p>
              <p className="panel-note">
                Watchlist rows marked in position: {snapshot.summary.symbols_in_position}
              </p>
            </article>
          </div>
        </>
      ) : null}
    </section>
  );
}
