import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from "react";

import {
  AssetType,
  CanonicalSnapshot,
  CreateWatchlistEntryPayload,
  Market,
  ValuationLabel,
  createWatchlistEntry,
  deleteWatchlistEntry,
  getSnapshot,
} from "../shared/api";
import { formatCurrency, formatPercent } from "../shared/formatters";
import { KeyValueList, PageSection, StatCard } from "../shared/ui";

const columns = ["标的", "行情", "回撤", "估值状态", "变化", "持仓 / P&L", "标记", "操作"];
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
  const [snapshot, setSnapshot] = useState<CanonicalSnapshot | null>(null);
  const [form, setForm] = useState<CreateWatchlistEntryPayload>(defaultForm);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    void loadSnapshot();
  }, []);

  const summary = useMemo(
    () => ({
      total: snapshot?.summary.tracked_symbols ?? 0,
      enabled: snapshot?.summary.enabled_symbols ?? 0,
      inPosition: snapshot?.summary.symbols_in_position ?? 0,
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

  async function loadSnapshot() {
    setLoading(true);
    try {
      const data = await getSnapshot();
      setSnapshot(data);
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load monitor snapshot.");
    } finally {
      setLoading(false);
    }
  }

  function handleInputChange(
    event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>,
  ) {
    const { name, value, type } = event.target;
    const nextValue = type === "checkbox" ? (event.target as HTMLInputElement).checked : value;

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
      await createWatchlistEntry(form);
      setForm(defaultForm);
      setError(null);
      await loadSnapshot();
      setShowForm(false);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Failed to add symbol.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(entryId: number) {
    try {
      await deleteWatchlistEntry(entryId);
      setError(null);
      await loadSnapshot();
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Failed to delete symbol.");
    }
  }

  function formatPeg(value: number | null) {
    return value === null ? "--" : value.toFixed(2);
  }

  function formatMarketLabel(value: Market) {
    switch (value) {
      case "US":
        return "美股";
      case "HK":
        return "港股";
      case "OTHER":
      default:
        return "其他";
    }
  }

  function formatAssetTypeLabel(value: AssetType) {
    switch (value) {
      case "stock":
        return "股票";
      case "etf":
        return "ETF";
      case "bond":
        return "债券";
      case "other":
      default:
        return "其他";
    }
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

  function indicatorTone(value: number | null, preferLower = false) {
    if (value === null) {
      return "muted";
    }
    if (value === 0) {
      return "neutral";
    }
    if (preferLower) {
      return value <= 5 ? "positive" : "warning";
    }
    return value > 0 ? "positive" : "negative";
  }

  function rowPriority(entry: CanonicalSnapshot["watchlist"][number]) {
    let score = 0;

    if (entry.state?.has_changed) {
      score += 6;
    }
    if (entry.enabled && entry.indicators?.current_price === null) {
      score += 4;
    }
    if (entry.in_position) {
      score += 3;
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
    <section>
      <header className="page-header">
        <p>监控页优先服务日常扫描，不让录入表单抢主视觉，把最值得先处理的标的排在前面。</p>
      </header>

      <div className="panel-grid">
        <StatCard label="监控总数" value={summary.total} note="全部 watchlist 标的" />
        <StatCard label="已启用" value={summary.enabled} note="会进入下一轮监控" />
        <StatCard
          label="状态变化"
          value={summary.changed}
          note="今天先看这一批"
          tone={summary.changed > 0 ? "warning" : "positive"}
        />
        <StatCard
          label="缺失行情"
          value={summary.missingQuote}
          note="启用但暂未拿到价格"
          tone={summary.missingQuote > 0 ? "warning" : "positive"}
        />
      </div>

      <PageSection
        title="监控列表"
        description="默认按优先级排序：状态变化、缺失行情、持仓标的会排在前面。"
        actions={
          <div className="actions-row">
            <button type="button" className="button button-secondary" onClick={() => void loadSnapshot()}>
              刷新
            </button>
            <button type="button" className="button" onClick={() => setShowForm((current) => !current)}>
              {showForm ? "收起新增表单" : "新增标的"}
            </button>
          </div>
        }
      >
        {error ? <div className="banner banner-error">{error}</div> : null}

        {snapshot ? (
          <article className="panel overview-secondary">
            <h3>当前关注点</h3>
            <KeyValueList
              items={[
                { label: "状态变化", value: `${summary.changed} 个`, tone: summary.changed > 0 ? "warning" : "positive" },
                { label: "持仓标的", value: `${summary.inPosition} 个` },
                { label: "缺失行情", value: `${summary.missingQuote} 个`, tone: summary.missingQuote > 0 ? "warning" : "positive" },
              ]}
            />
          </article>
        ) : null}

        {showForm ? (
          <article className="panel overview-secondary">
            <h3>新增 Watchlist 标的</h3>
            <p className="panel-note">录入动作保留在本页，但默认收起，避免干扰扫描路径。</p>

            <form className="form-grid form-grid-2" onSubmit={handleSubmit}>
              <label>
                <span>代码</span>
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
                <span>名称</span>
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
                <span>分组</span>
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
                <span>市场</span>
                <select name="market" value={form.market} onChange={handleInputChange}>
                  {marketOptions.map((option) => (
                    <option key={option} value={option}>
                      {formatMarketLabel(option)}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                <span>资产类型</span>
                <select name="asset_type" value={form.asset_type} onChange={handleInputChange}>
                  {assetTypeOptions.map((option) => (
                    <option key={option} value={option}>
                      {formatAssetTypeLabel(option)}
                    </option>
                  ))}
                </select>
              </label>

              <label className="form-span-2">
                <span>备注</span>
                <textarea
                  name="notes"
                  value={form.notes}
                  onChange={handleInputChange}
                  placeholder="记录为什么要继续跟踪这只标的。"
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
                <span>纳入监控</span>
              </label>

              <label className="checkbox">
                <input
                  type="checkbox"
                  name="in_position"
                  checked={form.in_position}
                  onChange={handleInputChange}
                />
                <span>当前已持仓</span>
              </label>

              <div className="actions-row form-span-2">
                <button type="submit" className="button" disabled={submitting}>
                  {submitting ? "保存中..." : "加入 Watchlist"}
                </button>
                <button
                  type="button"
                  className="button button-secondary"
                  onClick={() => setForm(defaultForm)}
                >
                  重置
                </button>
              </div>
            </form>
          </article>
        ) : null}

        <article className="table-shell overview-secondary">
          <div className="table-row table-head table-monitor">
            {columns.map((column) => (
              <span key={column}>{column}</span>
            ))}
          </div>

          {loading ? <div className="table-empty">正在加载监控快照...</div> : null}

          {!loading && sortedEntries.length === 0 ? (
            <div className="table-empty">还没有监控标的，先加入第一只股票或 ETF。</div>
          ) : null}

          {!loading &&
            sortedEntries.map((entry) => (
              <div key={entry.id} className={rowClassName(entry)}>
                <div className="cell-stack">
                  <span className="symbol-cell">{entry.symbol}</span>
                  <span className="muted">{entry.name}</span>
                  <div className="status-stack">
                    <span className="table-chip">{formatMarketLabel(entry.market)}</span>
                    <span className="table-chip">{formatAssetTypeLabel(entry.asset_type)}</span>
                    <span className="table-chip">{entry.group_name}</span>
                  </div>
                </div>

                <div className="cell-stack">
                  <span>{formatCurrency(entry.indicators?.current_price ?? null, "USD", { digits: 2 })}</span>
                  <span className={`value-${indicatorTone(entry.indicators?.day_change_percent ?? null)}`}>
                    日内 {formatPercent(entry.indicators?.day_change_percent ?? null)}
                  </span>
                </div>

                <div className="cell-stack">
                  <span
                    className={`value-${indicatorTone(
                      entry.indicators?.drawdown_from_52w_high_percent ?? null,
                      true,
                    )}`}
                  >
                    52W {formatPercent(entry.indicators?.drawdown_from_52w_high_percent ?? null)}
                  </span>
                  <span
                    className={`value-${indicatorTone(
                      entry.indicators?.drawdown_from_90d_high_percent ?? null,
                      true,
                    )}`}
                  >
                    90D {formatPercent(entry.indicators?.drawdown_from_90d_high_percent ?? null)}
                  </span>
                </div>

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

                <div className="cell-stack">
                  <span>{entry.position ? `${entry.position.quantity} 股` : "--"}</span>
                  <span className={`value-${indicatorTone(entry.indicators?.unrealized_pnl_percent ?? null)}`}>
                    {formatPercent(entry.indicators?.unrealized_pnl_percent ?? null)}
                  </span>
                </div>

                <div className="status-stack">
                  <span className={entry.enabled ? "status-pill status-pill-ok" : "status-pill"}>
                    {entry.enabled ? "启用" : "暂停"}
                  </span>
                  <span className={entry.in_position ? "status-pill status-pill-warn" : "status-pill"}>
                    {entry.in_position ? "已持仓" : "观察中"}
                  </span>
                  {entry.enabled && entry.indicators?.current_price === null ? (
                    <span className="status-pill status-pill-danger">无行情</span>
                  ) : null}
                </div>

                <div className="table-actions">
                  <button
                    type="button"
                    className="button button-danger"
                    onClick={() => void handleDelete(entry.id)}
                  >
                    删除
                  </button>
                </div>
              </div>
            ))}
        </article>
      </PageSection>
    </section>
  );
}
