import { type ReactNode, useEffect, useMemo, useState } from "react";

import {
  type CanonicalSnapshot,
  type PositionSnapshot,
  type SnapshotResponse,
  getSnapshot,
  refreshSnapshot,
} from "../shared/api";
import { formatCurrency, formatDateTime, formatPercent } from "../shared/formatters";
import { PageSection } from "../shared/ui";

const PIE_COLORS = ["#4f7eff", "#4fd46b", "#f0b35f", "#f06f82", "#8f7dff", "#42cbd4"];

interface PieSlice {
  label: string;
  value: number;
  detail: string;
  color: string;
}

function toneClass(value: number | null) {
  if (value === null || value === 0) {
    return "value-neutral";
  }

  return value > 0 ? "value-positive" : "value-negative";
}

function cashRatioLabel(availableFunds: number | null, netLiquidation: number | null) {
  if (availableFunds === null || netLiquidation === null || netLiquidation <= 0) {
    return "--";
  }

  return formatPlainPercent((availableFunds / netLiquidation) * 100, 1);
}

function formatPlainPercent(value: number | null, digits = 1) {
  if (value === null || !Number.isFinite(value)) {
    return "--";
  }

  return `${value.toFixed(digits)}%`;
}

function brokerStatusLabel(status: CanonicalSnapshot["meta"]["broker_status"]) {
  if (status === "connected") {
    return "已连接";
  }
  if (status === "error") {
    return "异常";
  }
  return "模拟";
}

function buildPositionSlices(positions: PositionSnapshot[], currency: string): PieSlice[] {
  const rankedPositions = positions
    .map((position) => ({
      label: position.symbol,
      value: Math.abs(position.market_value ?? 0),
      marketValue: position.market_value,
    }))
    .filter((position) => position.value > 0)
    .sort((left, right) => right.value - left.value);

  const topPositions = rankedPositions.slice(0, 5);
  const otherPositions = rankedPositions.slice(5);
  const slices = topPositions.map((position, index) => ({
    label: position.label,
    value: position.value,
    detail: formatCurrency(position.marketValue, currency, { digits: 2 }),
    color: PIE_COLORS[index % PIE_COLORS.length],
  }));

  if (otherPositions.length > 0) {
    const otherValue = otherPositions.reduce((sum, position) => sum + position.value, 0);
    slices.push({
      label: `其他 ${otherPositions.length} 项`,
      value: otherValue,
      detail: formatCurrency(otherValue, currency, { digits: 2 }),
      color: PIE_COLORS[5],
    });
  }

  return slices;
}

function PortfolioKpiCard(props: {
  label: string;
  value: ReactNode;
  note: ReactNode;
  tone?: "default" | "positive" | "danger";
  sideLabel?: string;
  sideValue?: ReactNode;
}) {
  const toneClassName =
    props.tone === "positive" ? " value-positive" : props.tone === "danger" ? " value-negative" : "";

  return (
    <article className="panel portfolio-kpi-card">
      <div className="portfolio-kpi-top">
        <p className="stat-label">{props.label}</p>
        {props.sideLabel ? (
          <div className="portfolio-kpi-side">
            <span>{props.sideLabel}</span>
            <strong>{props.sideValue}</strong>
          </div>
        ) : null}
      </div>
      <p className={`metric metric-compact${toneClassName}`}>{props.value}</p>
      <p className="panel-note">{props.note}</p>
    </article>
  );
}

function AccountSummaryBadge(props: {
  accountId: string;
  positionCount: number;
  investedValue: number;
  currency: string;
  source: string;
  cacheStatus: string;
  updatedAt: string | null;
}) {
  return (
    <div className="account-badge-wrap">
      <button type="button" className="account-badge" aria-label="查看账户概览">
        <span>账户</span>
        <strong>{props.accountId || "--"}</strong>
      </button>
      <div className="account-badge-popover" role="tooltip">
        <div className="kv-row">
          <span className="kv-label">持仓数量</span>
          <span className="kv-value">{props.positionCount}</span>
        </div>
        <div className="kv-row">
          <span className="kv-label">总市值</span>
          <span className="kv-value">{formatCurrency(props.investedValue, props.currency, { digits: 2 })}</span>
        </div>
        <div className="kv-row">
          <span className="kv-label">数据来源</span>
          <span className="kv-value">{props.source}</span>
        </div>
        <div className="kv-row">
          <span className="kv-label">缓存状态</span>
          <span className="kv-value">{props.cacheStatus}</span>
        </div>
        <div className="kv-row">
          <span className="kv-label">账户更新时间</span>
          <span className="kv-value">{formatDateTime(props.updatedAt)}</span>
        </div>
      </div>
    </div>
  );
}

function PortfolioPieChart(props: {
  title: string;
  description: string;
  slices: PieSlice[];
  emptyMessage: string;
  centerValue?: ReactNode;
  centerLabel?: string;
}) {
  const total = props.slices.reduce((sum, slice) => sum + slice.value, 0);
  const radius = 42;
  const circumference = 2 * Math.PI * radius;
  let offset = 0;

  return (
    <article className="panel portfolio-chart-card">
      <div>
        <h3>{props.title}</h3>
        <p className="panel-note">{props.description}</p>
      </div>

      {props.slices.length === 0 || total <= 0 ? (
        <div className="portfolio-empty-chart">{props.emptyMessage}</div>
      ) : (
        <div className="portfolio-pie-layout">
          <div className="portfolio-pie">
            <svg viewBox="0 0 120 120" aria-hidden="true">
              <circle className="portfolio-pie-track" cx="60" cy="60" r={radius} />
              {props.slices.map((slice) => {
                const dashLength = (slice.value / total) * circumference;
                const currentOffset = offset;
                offset += dashLength;

                return (
                  <circle
                    key={slice.label}
                    className="portfolio-pie-slice"
                    cx="60"
                    cy="60"
                    r={radius}
                    stroke={slice.color}
                    strokeDasharray={`${dashLength} ${circumference - dashLength}`}
                    strokeDashoffset={-currentOffset}
                  />
                );
              })}
            </svg>
            <div className="portfolio-pie-center">
              <strong>{props.centerValue}</strong>
              <span>{props.centerLabel}</span>
            </div>
          </div>

          <div className="portfolio-legend">
            {props.slices.map((slice) => (
              <div key={slice.label} className="portfolio-legend-row">
                <span className="legend-dot" style={{ background: slice.color, color: slice.color }} />
                <span className="portfolio-legend-name">{slice.label}</span>
                <span className="portfolio-legend-percent">{formatPlainPercent((slice.value / total) * 100)}</span>
                <span className="portfolio-legend-detail">{slice.detail}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </article>
  );
}

export function PortfolioPage() {
  const [snapshot, setSnapshot] = useState<CanonicalSnapshot | null>(null);
  const [snapshotResponse, setSnapshotResponse] = useState<SnapshotResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void loadSnapshot();
  }, []);

  const totals = useMemo(() => {
    const positions = snapshot?.positions ?? [];
    const investedValue = positions.reduce((sum, position) => sum + (position.market_value ?? 0), 0);
    const unrealizedPnl = positions.reduce((sum, position) => sum + (position.unrealized_pnl ?? 0), 0);

    return {
      count: positions.length,
      investedValue,
      unrealizedPnl,
    };
  }, [snapshot]);

  async function loadSnapshot() {
    setLoading(true);
    try {
      const nextSnapshot = await getSnapshot();
      applySnapshotResponse(nextSnapshot);
      setError(nextSnapshot.last_error || null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load portfolio snapshot.");
    } finally {
      setLoading(false);
    }
  }

  async function handleRefreshSnapshot() {
    setRefreshing(true);
    try {
      const nextSnapshot = await refreshSnapshot();
      applySnapshotResponse(nextSnapshot);
      setError(nextSnapshot.last_error || null);
    } catch (refreshError) {
      setError(refreshError instanceof Error ? refreshError.message : "Failed to refresh portfolio snapshot.");
    } finally {
      setRefreshing(false);
    }
  }

  function applySnapshotResponse(response: SnapshotResponse) {
    setSnapshotResponse(response);
    if (response.snapshot) {
      setSnapshot(response.snapshot);
    }
  }

  function cacheStatusLabel(response: SnapshotResponse | null) {
    if (!response) {
      return "--";
    }
    if (response.cache_status === "failed") {
      return "刷新失败，显示旧快照";
    }
    if (response.cache_status === "success") {
      return response.from_cache ? "缓存快照" : "刚刚刷新";
    }
    if (response.cache_status === "empty") {
      return "暂无快照";
    }
    return "刷新中";
  }

  const currency = snapshot?.account.currency ?? "USD";
  const positionSlices = useMemo(() => buildPositionSlices(snapshot?.positions ?? [], currency), [currency, snapshot?.positions]);

  return (
    <section>
      <header className="page-header">
        <p>先看账户资金，再看当前持仓分布与每只持仓的盈亏表现。</p>
      </header>

      <PageSection
        title="账户快照"
        description="和追踪页共用同一个快照，这里更强调资金与仓位结构。"
        actions={
          <div className="actions-row">
            {snapshot ? (
              <AccountSummaryBadge
                accountId={snapshot.account.account_id}
                positionCount={totals.count}
                investedValue={totals.investedValue}
                currency={currency}
                source={snapshot.meta.broker_display_name}
                cacheStatus={cacheStatusLabel(snapshotResponse)}
                updatedAt={snapshot.account.updated_at}
              />
            ) : null}
            <button type="button" className="button button-secondary" onClick={() => void loadSnapshot()}>
              读取缓存
            </button>
            <button type="button" className="button" onClick={() => void handleRefreshSnapshot()} disabled={refreshing}>
              {refreshing ? "刷新中..." : "刷新快照"}
            </button>
          </div>
        }
      >
        {error ? <div className="banner banner-error">{error}</div> : null}
        {loading && !snapshot ? <div className="table-empty">首次生成快照中...</div> : null}

        {snapshot ? (
          <>
            <div className="portfolio-kpi-grid">
              <PortfolioKpiCard
                label="净值"
                value={formatCurrency(snapshot.account.net_liquidation, currency)}
                sideLabel="当日盈亏"
                sideValue="--"
                note={`${snapshot.meta.broker_display_name} / ${brokerStatusLabel(snapshot.meta.broker_status)}`}
              />
              <PortfolioKpiCard
                label="现金"
                value={formatCurrency(snapshot.account.available_funds, currency)}
                note={`现金占资产 ${cashRatioLabel(snapshot.account.available_funds, snapshot.account.net_liquidation)}`}
              />
              <PortfolioKpiCard
                label="未实现盈亏"
                value={formatCurrency(totals.unrealizedPnl, currency)}
                note={`快照时间 ${formatDateTime(snapshot.account.updated_at)}`}
                tone={totals.unrealizedPnl > 0 ? "positive" : totals.unrealizedPnl < 0 ? "danger" : "default"}
              />
              <PortfolioKpiCard label="本周盈亏" value="--" note="等待后端提供真实周盈亏字段" />
            </div>

            <div className="portfolio-chart-grid overview-secondary">
              <PortfolioPieChart
                title="当前持仓"
                description="按持仓市值占比展示，便于快速判断仓位集中度。"
                slices={positionSlices}
                emptyMessage="当前快照里没有可用于绘图的持仓。"
                centerValue={totals.count}
                centerLabel="持仓"
              />
              <PortfolioPieChart
                title="目标持仓"
                description="目标持仓暂未配置。"
                slices={[]}
                emptyMessage="目标持仓暂未配置"
                centerValue="--"
                centerLabel="目标"
              />
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
