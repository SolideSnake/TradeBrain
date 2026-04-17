import { useEffect, useMemo, useState } from "react";

import { CanonicalSnapshot, getSnapshot } from "../shared/api";
import { formatCurrency, formatDateTime, formatPercent } from "../shared/formatters";
import { PageSection, StatCard } from "../shared/ui";

function toneClass(value: number | null) {
  if (value === null || value === 0) {
    return "value-neutral";
  }

  return value > 0 ? "value-positive" : "value-negative";
}

export function PortfolioPage() {
  const [snapshot, setSnapshot] = useState<CanonicalSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void loadSnapshot();
  }, []);

  const totals = useMemo(() => {
    const positions = snapshot?.positions ?? [];
    const investedValue = positions.reduce((sum, position) => sum + (position.market_value ?? 0), 0);
    const unrealizedPnl = positions.reduce((sum, position) => sum + (position.unrealized_pnl ?? 0), 0);
    const largestPosition = [...positions].sort((left, right) => (right.market_value ?? 0) - (left.market_value ?? 0))[0] ?? null;

    return {
      count: positions.length,
      investedValue,
      unrealizedPnl,
      largestPosition,
    };
  }, [snapshot]);

  async function loadSnapshot() {
    setLoading(true);
    try {
      const nextSnapshot = await getSnapshot();
      setSnapshot(nextSnapshot);
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load portfolio snapshot.");
    } finally {
      setLoading(false);
    }
  }

  const currency = snapshot?.account.currency ?? "USD";

  return (
    <section>
      <header className="page-header">
        <span className="eyebrow">IBKR</span>
        <h1>持仓</h1>
        <p>把账户层和持仓层拆开，先判断资金与仓位暴露，再看每只持仓的盈亏表现。</p>
      </header>

      <PageSection
        title="账户快照"
        description="和 Monitor 共用同一个 snapshot，但这里更强调账户与仓位结构。"
        actions={
          <button type="button" className="button button-secondary" onClick={() => void loadSnapshot()}>
            刷新持仓
          </button>
        }
      >
        {error ? <div className="banner banner-error">{error}</div> : null}
        {loading && !snapshot ? <div className="table-empty">正在加载持仓快照...</div> : null}

        {snapshot ? (
          <>
            <div className="panel-grid">
              <StatCard label="账户净值" value={formatCurrency(snapshot.account.net_liquidation, currency)} note={`Broker ${snapshot.meta.broker_status}`} />
              <StatCard label="可用资金" value={formatCurrency(snapshot.account.available_funds, currency)} note="可用于新开仓位" />
              <StatCard label="Buying Power" value={formatCurrency(snapshot.account.buying_power, currency)} note="券商返回值" />
              <StatCard
                label="未实现盈亏"
                value={formatCurrency(totals.unrealizedPnl, currency)}
                note={`快照时间 ${formatDateTime(snapshot.account.updated_at)}`}
                tone={totals.unrealizedPnl > 0 ? "positive" : totals.unrealizedPnl < 0 ? "danger" : "default"}
              />
            </div>

            <div className="panel-grid overview-secondary overview-grid-2">
              <article className="panel">
                <h3>仓位概览</h3>
                <div className="kv-list">
                  <div className="kv-row">
                    <span className="kv-label">持仓数量</span>
                    <span className="kv-value">{totals.count}</span>
                  </div>
                  <div className="kv-row">
                    <span className="kv-label">总市值</span>
                    <span className="kv-value">{formatCurrency(totals.investedValue, currency)}</span>
                  </div>
                  <div className="kv-row">
                    <span className="kv-label">账户 ID</span>
                    <span className="kv-value">{snapshot.account.account_id || "--"}</span>
                  </div>
                </div>
              </article>

              <article className="panel">
                <h3>最大仓位</h3>
                {totals.largestPosition ? (
                  <div className="cell-stack">
                    <span className="symbol-cell">{totals.largestPosition.symbol}</span>
                    <span>{formatCurrency(totals.largestPosition.market_value, currency, { digits: 2 })}</span>
                    <span className={toneClass(totals.largestPosition.unrealized_pnl_percent)}>
                      {formatPercent(totals.largestPosition.unrealized_pnl_percent)}
                    </span>
                  </div>
                ) : (
                  <p className="empty-copy">当前没有仓位。</p>
                )}
              </article>
            </div>

            <article className="table-shell overview-secondary">
              <div className="table-row table-head table-positions">
                <span>标的</span>
                <span>数量</span>
                <span>成本价</span>
                <span>现价</span>
                <span>市值</span>
                <span>未实现盈亏</span>
                <span>盈亏比例</span>
              </div>

              {snapshot.positions.length === 0 ? (
                <div className="table-empty">当前快照里没有持仓。</div>
              ) : (
                snapshot.positions.map((position) => (
                  <div key={`${position.account_id}-${position.symbol}`} className="table-row table-positions">
                    <span className="symbol-cell">{position.symbol}</span>
                    <span>{position.quantity}</span>
                    <span>{formatCurrency(position.average_cost, currency, { digits: 2 })}</span>
                    <span>{formatCurrency(position.market_price, currency, { digits: 2 })}</span>
                    <span>{formatCurrency(position.market_value, currency, { digits: 2 })}</span>
                    <span className={toneClass(position.unrealized_pnl)}>
                      {formatCurrency(position.unrealized_pnl, currency, { digits: 2 })}
                    </span>
                    <span className={toneClass(position.unrealized_pnl_percent)}>
                      {formatPercent(position.unrealized_pnl_percent)}
                    </span>
                  </div>
                ))
              )}
            </article>
          </>
        ) : null}
      </PageSection>
    </section>
  );
}
