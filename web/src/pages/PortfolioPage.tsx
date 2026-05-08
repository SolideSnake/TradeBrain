import { type CSSProperties, type FormEvent, type ReactNode, useEffect, useMemo, useState } from "react";

import { useSnapshotResource } from "../hooks/useSnapshotResource";
import {
  createTargetPosition,
  deleteTargetPosition,
  listTargetPositions,
  type CanonicalSnapshot,
  type PositionSnapshot,
  type TargetPosition,
} from "../shared/api";
import { formatCurrency, formatDateTime, formatPercent } from "../shared/formatters";

const PIE_COLORS = ["#4f7eff", "#4fd46b", "#f0b35f", "#f06f82", "#8f7dff", "#42cbd4"];

interface PieSlice {
  label: string;
  value: number;
  detail: string;
  color: string;
  action?: ReactNode;
}

type FundsTone = "positive" | "negative" | "neutral";

function toneClass(value: number | null) {
  if (value === null || value === 0) {
    return "value-neutral";
  }

  return value > 0 ? "market-value-positive" : "market-value-negative";
}

function ratioLabel(value: number | null | undefined, base: number | null | undefined) {
  if (value === null || value === undefined || base === null || base === undefined || base <= 0) {
    return "--";
  }

  return formatPlainPercent((value / base) * 100, 1);
}

function fundsTone(value: number | null | undefined): FundsTone {
  if (value === null || value === undefined || value === 0) {
    return "neutral";
  }

  return value > 0 ? "positive" : "negative";
}

function fundsLevelPercent(value: number | null | undefined, base: number | null | undefined) {
  if (value === null || value === undefined || value === 0 || base === null || base === undefined || base <= 0) {
    return "0%";
  }

  return `${Math.min(Math.abs(value / base) * 100, 100).toFixed(1)}%`;
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
  return "异常";
}

function baseAmount(
  baseValue: number | null | undefined,
  nativeValue: number | null | undefined,
  nativeCurrency: string,
  baseCurrency: string,
) {
  if (baseValue !== null && baseValue !== undefined) {
    return baseValue;
  }
  return nativeCurrency === baseCurrency ? (nativeValue ?? null) : null;
}

function formatBaseAndNative(
  baseValue: number | null | undefined,
  nativeValue: number | null | undefined,
  nativeCurrency: string,
  baseCurrency: string,
  options: { digits?: number } = { digits: 2 },
) {
  const normalizedNative = nativeCurrency || baseCurrency;
  const resolvedBase = baseAmount(baseValue, nativeValue, normalizedNative, baseCurrency);
  const baseLabel = formatCurrency(resolvedBase, baseCurrency, options);

  if (normalizedNative === baseCurrency || nativeValue === null || nativeValue === undefined) {
    return baseLabel;
  }

  return `${baseLabel} / ${formatCurrency(nativeValue, normalizedNative, options)}`;
}

function NativeSubline(props: {
  baseValue: number | null | undefined;
  nativeValue: number | null | undefined;
  nativeCurrency: string;
  baseCurrency: string;
}) {
  if (
    props.nativeCurrency === props.baseCurrency ||
    props.nativeValue === null ||
    props.nativeValue === undefined
  ) {
    return null;
  }

  return <span className="muted">{formatCurrency(props.nativeValue, props.nativeCurrency, { digits: 2 })}</span>;
}

function buildPositionSlices(positions: PositionSnapshot[], baseCurrency: string): PieSlice[] {
  const rankedPositions = positions
    .map((position) => {
      const value = baseAmount(
        position.market_value_base,
        position.market_value,
        position.currency,
        baseCurrency,
      );

      return {
        label: position.symbol,
        value: Math.abs(value ?? 0),
        marketValue: position.market_value,
        marketValueBase: value,
        currency: position.currency,
      };
    })
    .filter((position) => position.value > 0)
    .sort((left, right) => right.value - left.value);

  const topPositions = rankedPositions.slice(0, 5);
  const otherPositions = rankedPositions.slice(5);
  const slices = topPositions.map((position, index) => ({
    label: position.label,
    value: position.value,
    detail: formatBaseAndNative(
      position.marketValueBase,
      position.marketValue,
      position.currency,
      baseCurrency,
    ),
    color: PIE_COLORS[index % PIE_COLORS.length],
  }));

  if (otherPositions.length > 0) {
    const otherValue = otherPositions.reduce((sum, position) => sum + position.value, 0);
    slices.push({
      label: `其他 ${otherPositions.length} 项`,
      value: otherValue,
      detail: formatCurrency(otherValue, baseCurrency, { digits: 2 }),
      color: PIE_COLORS[5],
    });
  }

  return slices;
}

function buildTargetSlices(
  targetPositions: TargetPosition[],
  onDelete: (position: TargetPosition) => void,
  deletingId: number | null,
): PieSlice[] {
  return targetPositions
    .filter((position) => position.target_value_usd > 0)
    .sort((left, right) => right.target_value_usd - left.target_value_usd || left.symbol.localeCompare(right.symbol))
    .map((position, index) => ({
      label: position.symbol,
      value: position.target_value_usd,
      detail: formatCurrency(position.target_value_usd, "USD", { digits: 2 }),
      color: PIE_COLORS[index % PIE_COLORS.length],
      action: (
        <button
          type="button"
          className="button button-danger-ghost button-compact"
          onClick={() => onDelete(position)}
          disabled={deletingId === position.id}
        >
          {deletingId === position.id ? "删除中" : "删除"}
        </button>
      ),
    }));
}

function PortfolioKpiCard(props: {
  label: string;
  value: ReactNode;
  note: ReactNode;
  tone?: "default" | "positive" | "danger";
}) {
  const toneClassName =
    props.tone === "positive"
      ? " market-value-positive"
      : props.tone === "danger"
        ? " market-value-negative"
        : "";

  return (
    <article className="panel portfolio-kpi-card">
      <div className="portfolio-kpi-top">
        <p className="stat-label">{props.label}</p>
      </div>
      <p className={`metric metric-compact${toneClassName}`}>{props.value}</p>
      <p className="panel-note">{props.note}</p>
    </article>
  );
}

function PortfolioFundsItem(props: {
  label: string;
  value: number | null | undefined;
  netLiquidation: number | null | undefined;
  currency: string;
}) {
  const tone = fundsTone(props.value);
  const direction = tone === "negative" ? "down" : "up";
  const style = { "--funds-level": fundsLevelPercent(props.value, props.netLiquidation) } as CSSProperties;

  return (
    <div className={`portfolio-funds-item portfolio-funds-item-${tone} portfolio-funds-item-${direction}`} style={style}>
      <span className="portfolio-funds-level" aria-hidden="true" />
      <div className="portfolio-funds-content">
        <span>{props.label}</span>
        <strong>{formatCurrency(props.value, props.currency)}</strong>
        <small>
          {props.label}/净值 {ratioLabel(props.value, props.netLiquidation)}
        </small>
      </div>
    </div>
  );
}

function PortfolioFundsCard(props: {
  cashBalance: number | null | undefined;
  availableFunds: number | null | undefined;
  netLiquidation: number | null | undefined;
  currency: string;
}) {
  return (
    <article className="panel portfolio-kpi-card portfolio-funds-card">
      <div className="portfolio-funds-stack">
        <PortfolioFundsItem
          label="现金"
          value={props.cashBalance}
          netLiquidation={props.netLiquidation}
          currency={props.currency}
        />
        <PortfolioFundsItem
          label="可用资金"
          value={props.availableFunds}
          netLiquidation={props.netLiquidation}
          currency={props.currency}
        />
      </div>
    </article>
  );
}

function PortfolioPieChart(props: {
  title: string;
  description?: string;
  slices: PieSlice[];
  emptyMessage: string;
  centerValue?: ReactNode;
  centerLabel?: string;
  variant?: "default" | "featured";
  actions?: ReactNode;
}) {
  const total = props.slices.reduce((sum, slice) => sum + slice.value, 0);
  const radius = 42;
  const circumference = 2 * Math.PI * radius;
  let offset = 0;
  const variantClassName = props.variant === "featured" ? " portfolio-chart-card-featured" : "";

  return (
    <article className={`panel portfolio-chart-card${variantClassName}`}>
      <div className="portfolio-chart-header">
        <div>
          <h3>{props.title}</h3>
          {props.description ? <p className="panel-note">{props.description}</p> : null}
        </div>
        {props.actions ? <div className="portfolio-chart-actions">{props.actions}</div> : null}
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
                {slice.action ? <span className="portfolio-legend-action">{slice.action}</span> : null}
              </div>
            ))}
          </div>
        </div>
      )}
    </article>
  );
}

export function PortfolioPage() {
  const { snapshot, loading, error } = useSnapshotResource({
    loadErrorMessage: "Failed to load portfolio snapshot.",
  });
  const [targetPositions, setTargetPositions] = useState<TargetPosition[]>([]);
  const [targetSymbol, setTargetSymbol] = useState("");
  const [targetValue, setTargetValue] = useState("");
  const [targetLoading, setTargetLoading] = useState(true);
  const [targetSubmitting, setTargetSubmitting] = useState(false);
  const [targetDeletingId, setTargetDeletingId] = useState<number | null>(null);
  const [targetError, setTargetError] = useState<string | null>(null);

  async function loadTargetPositions() {
    setTargetLoading(true);
    setTargetError(null);
    try {
      setTargetPositions(await listTargetPositions());
    } catch (nextError) {
      setTargetError(nextError instanceof Error ? nextError.message : "目标持仓加载失败");
    } finally {
      setTargetLoading(false);
    }
  }

  useEffect(() => {
    void loadTargetPositions();
  }, []);

  async function handleCreateTargetPosition(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const symbol = targetSymbol.trim().toUpperCase();
    const parsedValue = Number(targetValue);

    if (!symbol) {
      setTargetError("请输入代码");
      return;
    }
    if (!Number.isFinite(parsedValue) || parsedValue <= 0) {
      setTargetError("请输入大于 0 的美元金额");
      return;
    }

    setTargetSubmitting(true);
    setTargetError(null);
    try {
      const created = await createTargetPosition({
        symbol,
        target_value_usd: parsedValue,
      });
      setTargetPositions((current) =>
        [...current, created].sort(
          (left, right) => right.target_value_usd - left.target_value_usd || left.symbol.localeCompare(right.symbol),
        ),
      );
      setTargetSymbol("");
      setTargetValue("");
    } catch (nextError) {
      setTargetError(nextError instanceof Error ? nextError.message : "目标持仓保存失败");
    } finally {
      setTargetSubmitting(false);
    }
  }

  async function handleDeleteTargetPosition(position: TargetPosition) {
    setTargetDeletingId(position.id);
    setTargetError(null);
    try {
      await deleteTargetPosition(position.id);
      setTargetPositions((current) => current.filter((item) => item.id !== position.id));
    } catch (nextError) {
      setTargetError(nextError instanceof Error ? nextError.message : "目标持仓删除失败");
    } finally {
      setTargetDeletingId(null);
    }
  }

  const totals = useMemo(() => {
    const positions = snapshot?.positions ?? [];
    const accountCurrency = snapshot?.account.currency ?? "USD";
    const unrealizedPnl = positions.reduce(
      (sum, position) =>
        sum +
        (baseAmount(
          position.unrealized_pnl_base,
          position.unrealized_pnl,
          position.currency,
          accountCurrency,
        ) ?? 0),
      0,
    );

    return {
      count: positions.length,
      unrealizedPnl,
    };
  }, [snapshot]);

  const currency = snapshot?.account.currency ?? "USD";
  const positionSlices = useMemo(
    () => buildPositionSlices(snapshot?.positions ?? [], currency),
    [currency, snapshot?.positions],
  );
  const targetSlices = useMemo(
    () => buildTargetSlices(targetPositions, handleDeleteTargetPosition, targetDeletingId),
    [targetDeletingId, targetPositions],
  );
  const targetTotal = targetPositions.reduce((sum, position) => sum + position.target_value_usd, 0);

  return (
    <section>
      <section className="section-block">
        {error ? <div className="banner banner-error">{error}</div> : null}
        {loading && !snapshot ? <div className="table-empty">首次生成快照中...</div> : null}

        {snapshot ? (
          <>
            <div className="portfolio-kpi-grid">
              <PortfolioKpiCard
                label="净值"
                value={formatCurrency(snapshot.account.net_liquidation, currency)}
                note={`${snapshot.meta.broker_display_name} / ${brokerStatusLabel(snapshot.meta.broker_status)}`}
              />
              <PortfolioFundsCard
                cashBalance={snapshot.account.cash_balance}
                availableFunds={snapshot.account.available_funds}
                netLiquidation={snapshot.account.net_liquidation}
                currency={currency}
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
                slices={positionSlices}
                emptyMessage="当前快照里没有可用于绘图的持仓。"
                centerValue={totals.count}
                centerLabel="持仓"
                variant="featured"
              />
              <PortfolioPieChart
                title="目标持仓"
                description={targetError ?? (targetLoading ? "目标持仓加载中..." : undefined)}
                slices={targetSlices}
                emptyMessage={targetLoading ? "目标持仓加载中..." : "目标持仓暂未配置"}
                centerValue={targetPositions.length || "--"}
                centerLabel={targetTotal > 0 ? formatCurrency(targetTotal, "USD", { digits: 0 }) : "目标"}
                actions={
                  <form className="target-position-form" onSubmit={handleCreateTargetPosition} noValidate>
                    <input
                      value={targetSymbol}
                      onChange={(event) => {
                        setTargetSymbol(event.target.value.toUpperCase());
                        setTargetError(null);
                      }}
                      placeholder="代码"
                      maxLength={32}
                      aria-label="目标持仓代码"
                    />
                    <input
                      value={targetValue}
                      onChange={(event) => {
                        setTargetValue(event.target.value);
                        setTargetError(null);
                      }}
                      placeholder="USD 金额"
                      inputMode="decimal"
                      aria-label="目标持仓美元金额"
                    />
                    <button type="submit" className="button button-toolbar" disabled={targetSubmitting}>
                      {targetSubmitting ? "添加中" : "添加"}
                    </button>
                  </form>
                }
              />
            </div>

            <article className="table-shell overview-secondary">
              <div className="table-row table-head table-positions">
                <span>代码</span>
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
                    <span>{formatCurrency(position.average_cost, position.currency, { digits: 2 })}</span>
                    <span>{formatCurrency(position.market_price, position.currency, { digits: 2 })}</span>
                    <span className="cell-stack">
                      <span>
                        {formatCurrency(
                          baseAmount(position.market_value_base, position.market_value, position.currency, currency),
                          currency,
                          { digits: 2 },
                        )}
                      </span>
                      <NativeSubline
                        baseValue={position.market_value_base}
                        nativeValue={position.market_value}
                        nativeCurrency={position.currency}
                        baseCurrency={currency}
                      />
                    </span>
                    <span
                      className={`cell-stack ${toneClass(
                        baseAmount(position.unrealized_pnl_base, position.unrealized_pnl, position.currency, currency),
                      )}`}
                    >
                      <span>
                        {formatCurrency(
                          baseAmount(
                            position.unrealized_pnl_base,
                            position.unrealized_pnl,
                            position.currency,
                            currency,
                          ),
                          currency,
                          { digits: 2 },
                        )}
                      </span>
                      <NativeSubline
                        baseValue={position.unrealized_pnl_base}
                        nativeValue={position.unrealized_pnl}
                        nativeCurrency={position.currency}
                        baseCurrency={currency}
                      />
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
      </section>
    </section>
  );
}
