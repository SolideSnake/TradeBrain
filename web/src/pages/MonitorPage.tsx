import { type FormEvent, useEffect, useMemo, useRef, useState } from "react";

import { useSnapshotResource } from "../hooks/useSnapshotResource";
import {
  type CanonicalSnapshot,
  type ScannerCandidate,
  type SnapshotWatchlistItem,
  type ValuationLabel,
  createWatchlistEntry,
  deleteWatchlistEntry,
  getScannerResult,
  refreshSnapshot,
} from "../shared/api";
import { formatCurrency, formatPercent } from "../shared/formatters";

const columns = ["代码", "行情", "区间位置", "估值状态", "变化", "操作"];

export function MonitorPage() {
  const { snapshot, loading, error, setError, applySnapshotResponse } = useSnapshotResource({
    loadErrorMessage: "Failed to load monitor snapshot.",
  });
  const [symbolInput, setSymbolInput] = useState("");
  const symbolInputRef = useRef<HTMLInputElement>(null);
  const [submitting, setSubmitting] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [scannerCandidates, setScannerCandidates] = useState<ScannerCandidate[]>([]);
  const [scannerLoading, setScannerLoading] = useState(true);
  const [scannerError, setScannerError] = useState<string | null>(null);

  useEffect(() => {
    if (!toastMessage) {
      return;
    }

    const timerId = window.setTimeout(() => setToastMessage(null), 2400);
    return () => window.clearTimeout(timerId);
  }, [toastMessage]);

  useEffect(() => {
    void loadScannerResult();
  }, [snapshot?.meta.generated_at]);

  const summary = useMemo(
    () => ({
      total: snapshot?.summary.tracked_symbols ?? 0,
      enabled: snapshot?.summary.enabled_symbols ?? 0,
      changed: snapshot?.watchlist.filter((entry) => entry.state?.has_changed).length ?? 0,
      missingQuote:
        snapshot?.watchlist.filter((entry) => entry.enabled && entry.indicators?.current_price === null).length ?? 0,
    }),
    [snapshot],
  );

  const sortedEntries = useMemo(() => {
    if (!snapshot) {
      return [];
    }

    return [...snapshot.watchlist].sort((left, right) => rowPriority(right) - rowPriority(left));
  }, [snapshot]);

  async function handleRefreshSnapshot() {
    try {
      const data = await refreshSnapshot();
      applySnapshotResponse(data);
    } catch (refreshError) {
      setError(refreshError instanceof Error ? refreshError.message : "Failed to refresh monitor snapshot.");
    }
  }

  async function loadScannerResult() {
    setScannerLoading(true);
    try {
      const data = await getScannerResult();
      setScannerCandidates(data.candidates);
      setScannerError(null);
    } catch (scanError) {
      setScannerError(scanError instanceof Error ? scanError.message : "策略线索加载失败。");
    } finally {
      setScannerLoading(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const symbol = symbolInput.trim().toUpperCase();

    if (!symbol) {
      setAddError("请输入代码");
      window.requestAnimationFrame(() => symbolInputRef.current?.focus());
      return;
    }

    setSubmitting(true);
    setAddError(null);

    try {
      await createWatchlistEntry({ symbol });
      setSymbolInput("");
      setError(null);
      await handleRefreshSnapshot();
      setToastMessage("已加入 Watchlist");
      window.requestAnimationFrame(() => symbolInputRef.current?.focus());
    } catch (submitError) {
      const detail = submitError instanceof Error ? submitError.message : "添加失败";
      setAddError(detail.length > 32 ? "添加失败，请检查代码" : detail);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(entryId: number) {
    try {
      await deleteWatchlistEntry(entryId);
      setError(null);
      await handleRefreshSnapshot();
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Failed to delete symbol.");
    }
  }

  function formatPeg(value: number | null) {
    return value === null ? "--" : value.toFixed(2);
  }

  function formatValuationLabel(value: ValuationLabel | null) {
    switch (value) {
      case "undervalued":
        return "低估";
      case "fair":
        return "合理";
      case "overvalued":
        return "高估";
      default:
        return "--";
    }
  }

  function valuationClass(value: ValuationLabel | null) {
    switch (value) {
      case "undervalued":
        return "status-pill status-pill-ok";
      case "fair":
        return "status-pill";
      case "overvalued":
        return "status-pill status-pill-danger";
      default:
        return "muted";
    }
  }

  function formatStateChange(current: ValuationLabel | null, previous: ValuationLabel | null, changed: boolean) {
    if (!changed || current === null || previous === null) {
      return "--";
    }
    return `${formatValuationLabel(previous)} -> ${formatValuationLabel(current)}`;
  }

  function marketToneClass(value: number | null) {
    if (value === null) {
      return "muted";
    }
    if (value === 0) {
      return "value-neutral";
    }
    return value > 0 ? "market-value-positive" : "market-value-negative";
  }

  function rowPriority(entry: CanonicalSnapshot["watchlist"][number]) {
    let score = 0;

    if (entry.state?.has_changed) {
      score += 6;
    }
    if (entry.enabled && entry.indicators?.current_price === null) {
      score += 4;
    }
    if (!entry.enabled) {
      score -= 2;
    }

    return score;
  }

  function rowClassName(entry: CanonicalSnapshot["watchlist"][number]) {
    if (entry.state?.has_changed) {
      return "table-row table-monitor row-emphasis";
    }
    if (entry.enabled && entry.indicators?.current_price === null) {
      return "table-row table-monitor row-warning";
    }
    return "table-row table-monitor";
  }

  return (
    <section className="monitor-page">
      {toastMessage ? <div className="toast toast-success">{toastMessage}</div> : null}

      <div className="monitor-summary-bar" aria-label="监控摘要">
        <div className="monitor-summary-metrics">
          <div className="monitor-summary-item">
            <span>监控总数</span>
            <strong>{summary.total}</strong>
          </div>
          <div className="monitor-summary-item">
            <span>已启用</span>
            <strong>{summary.enabled}</strong>
          </div>
          <div className="monitor-summary-item">
            <span>状态变化</span>
            <strong className={summary.changed > 0 ? "value-warning" : "value-positive"}>{summary.changed}</strong>
          </div>
          <div className="monitor-summary-item">
            <span>缺失行情</span>
            <strong className={summary.missingQuote > 0 ? "value-warning" : "value-positive"}>{summary.missingQuote}</strong>
          </div>
        </div>

        <form className="monitor-inline-add" onSubmit={handleSubmit} noValidate>
          <div className={`monitor-inline-add-field${addError ? " has-error" : ""}`}>
            <input
              ref={symbolInputRef}
              value={symbolInput}
              onChange={(event) => {
                setSymbolInput(event.target.value.toUpperCase());
                setAddError(null);
              }}
              placeholder="输入代码，如 AAPL"
              maxLength={32}
              aria-label="新增标的代码"
              aria-invalid={addError ? true : undefined}
              aria-describedby={addError ? "monitor-add-error" : undefined}
            />
            {addError ? (
              <span id="monitor-add-error" className="monitor-inline-error">
                {addError}
              </span>
            ) : null}
          </div>
          <button type="submit" className="button button-primary" disabled={submitting}>
            {submitting ? "添加中" : "添加"}
          </button>
        </form>
      </div>

      <section className="section-block">
        <div className="table-header">
          <div>
            <h3>策略线索</h3>
          </div>
          <button type="button" className="button button-ghost" onClick={() => void loadScannerResult()}>
            重新扫描
          </button>
        </div>

        <div className="scanner-strip">
          {scannerLoading ? <div className="scanner-empty">正在扫描...</div> : null}
          {!scannerLoading && scannerError ? <div className="banner banner-error">{scannerError}</div> : null}
          {!scannerLoading && !scannerError && scannerCandidates.length === 0 ? (
            <div className="scanner-empty">当前没有明显策略线索。</div>
          ) : null}
          {!scannerLoading &&
            !scannerError &&
            scannerCandidates.slice(0, 4).map((candidate) => (
              <article key={candidate.symbol} className="scanner-card">
                <div className="scanner-card-top">
                  <div className="cell-stack">
                    <span className="symbol-cell">{candidate.symbol}</span>
                    <span className="muted">{candidate.name}</span>
                  </div>
                  <strong>{candidate.score.score.toFixed(0)}</strong>
                </div>
                <div className="scanner-reason">{scannerReasonText(candidate.reason)}</div>
                <div className="scanner-breakdown">
                  {candidate.score.breakdown.map((part) => (
                    <span key={part.name}>
                      {part.name} {part.score.toFixed(0)}
                    </span>
                  ))}
                </div>
              </article>
            ))}
        </div>
      </section>

      <section className="section-block">
        {error ? <div className="banner banner-error">{error}</div> : null}

        <article className="table-shell">
          <div className="table-row table-head table-monitor">
            {columns.map((column) => (
              <span key={column}>{column}</span>
            ))}
          </div>

          {loading ? <div className="table-empty">首次生成快照中...</div> : null}

          {!loading && sortedEntries.length === 0 ? (
            <div className="table-empty">还没有监控标的，先加入第一只股票或 ETF。</div>
          ) : null}

          {!loading &&
            sortedEntries.map((entry) => (
              <div key={entry.id} className={rowClassName(entry)}>
                <div className="cell-stack">
                  <span className="symbol-cell">{entry.symbol}</span>
                  <span className="muted">{entry.name}</span>
                </div>

                <div className="cell-stack">
                  <span>
                    {formatCurrency(entry.indicators?.current_price ?? null, entryCurrency(entry), {
                      digits: 2,
                    })}
                  </span>
                  <span className={marketToneClass(entry.indicators?.day_change_percent ?? null)}>
                    日内 {formatPercent(entry.indicators?.day_change_percent ?? null)}
                  </span>
                </div>

                <RangePositionCell entry={entry} />

                <div className="cell-stack">
                  <span>
                    {entry.state?.current_label ? (
                      <span className={valuationClass(entry.state.current_label)}>
                        {formatValuationLabel(entry.state.current_label)}
                      </span>
                    ) : (
                      <span className="muted">--</span>
                    )}
                  </span>
                  <span className="muted">PEG {formatPeg(entry.indicators?.peg_ratio ?? null)}</span>
                </div>

                <div className="cell-stack">
                  <span className={entry.state?.has_changed ? "value-warning" : "muted"}>
                    {formatStateChange(
                      entry.state?.current_label ?? null,
                      entry.state?.previous_label ?? null,
                      entry.state?.has_changed ?? false,
                    )}
                  </span>
                </div>

                <div className="table-actions">
                  <button
                    type="button"
                    className="button button-danger-ghost button-compact"
                    onClick={() => void handleDelete(entry.id)}
                  >
                    删除
                  </button>
                </div>
              </div>
            ))}
        </article>
      </section>
    </section>
  );
}

function RangePositionCell({ entry }: { entry: SnapshotWatchlistItem }) {
  const indicators = entry.indicators;
  const currency = entryCurrency(entry);

  return (
    <div className="range-position-cell">
      <RangePositionGroup
        period="52W"
        currency={currency}
        currentPrice={indicators?.current_price ?? null}
        high={indicators?.high_52w ?? null}
        low={indicators?.low_52w ?? null}
        highDistancePercent={indicators?.drawdown_from_52w_high_percent ?? null}
        lowDistancePercent={indicators?.gain_from_52w_low_percent ?? null}
      />
      <RangePositionGroup
        period="90D"
        currency={currency}
        currentPrice={indicators?.current_price ?? null}
        high={indicators?.high_90d ?? null}
        low={indicators?.low_90d ?? null}
        highDistancePercent={indicators?.drawdown_from_90d_high_percent ?? null}
        lowDistancePercent={indicators?.gain_from_90d_low_percent ?? null}
      />
    </div>
  );
}

function RangePositionGroup({
  period,
  currency,
  currentPrice,
  high,
  low,
  highDistancePercent,
  lowDistancePercent,
}: {
  period: string;
  currency: string;
  currentPrice: number | null;
  high: number | null;
  low: number | null;
  highDistancePercent: number | null;
  lowDistancePercent: number | null;
}) {
  const progress = rangePositionPercent(currentPrice, low, high);

  return (
    <div className="range-position-group">
      <div className="range-position-topline">
        <span className="range-period">{period}</span>
        <div className="range-chip-row">
          <span className="range-chip range-chip-low">
            <span className="range-chip-main">
              <span>L</span>
              <span className="range-chip-price">{formatRangePrice(low, currency)}</span>
              <strong>{formatSignedPercent(lowDistancePercent)}</strong>
            </span>
          </span>
          <span className="range-chip range-chip-high">
            <span className="range-chip-main">
              <span>H</span>
              <span className="range-chip-price">{formatRangePrice(high, currency)}</span>
              <strong>{formatHighDistance(highDistancePercent)}</strong>
            </span>
          </span>
        </div>
      </div>
      {progress !== null ? (
        <div className="range-progress-row">
          <div className="range-progress" aria-label={`${period} 区间位置 ${progress.toFixed(0)}%`}>
            <span style={{ width: `${progress}%` }} />
          </div>
        </div>
      ) : null}
    </div>
  );
}

function formatHighDistance(value: number | null) {
  if (value === null) {
    return "--";
  }
  return formatSignedPercent(value > 0 ? -value : Math.abs(value));
}

function formatSignedPercent(value: number | null) {
  if (value === null) {
    return "--";
  }
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${value.toFixed(2)}%`;
}

function formatRangePrice(value: number | null, currency: string) {
  return formatCurrency(value, currency, { digits: 2 });
}

function entryCurrency(entry: SnapshotWatchlistItem) {
  if (entry.market === "KR") {
    return "KRW";
  }
  return entry.quote?.currency ?? "USD";
}

function rangePositionPercent(
  currentPrice: number | null,
  low: number | null,
  high: number | null,
) {
  if (currentPrice === null || low === null || high === null || high <= low) {
    return null;
  }
  return Math.min(Math.max(((currentPrice - low) / (high - low)) * 100, 0), 100);
}

function scannerReasonText(reason: ScannerCandidate["reason"]) {
  switch (reason) {
    case "large_drop":
      return "大跌幅";
    case "undervalued":
      return "低估";
    case "pullback_52w":
      return "52W 回撤";
    default:
      return reason;
  }
}
