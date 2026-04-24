import { useSnapshotResource } from "../hooks/useSnapshotResource";
import { formatCurrency, formatDateTime } from "../shared/formatters";
import { formatSnapshotCacheStatus } from "../shared/snapshotStatus";
import { KeyValueList, StatCard } from "../shared/ui";

export function OverviewPage() {
  const { snapshot, snapshotResponse, loading, error } = useSnapshotResource({
    loadErrorMessage: "Failed to load snapshot.",
  });

  const warningCount = snapshot?.meta.warnings.length ?? 0;
  const missingQuotes = snapshot
    ? Math.max(snapshot.summary.enabled_symbols - snapshot.summary.quote_coverage, 0)
    : 0;
  const readinessTone =
    snapshot?.meta.broker_status === "error"
      ? "danger"
      : warningCount > 0 || missingQuotes > 0
        ? "warning"
        : "positive";

  return (
    <section>
      <header className="page-header">
        <p>把开盘前必须确认的几件事压到第一屏，先判断数据能不能信，再决定下一步去监控、提醒还是持仓。</p>
      </header>

      <section className="section-block">
        <p className="panel-note section-intro">先看快照是否可靠，再看今天是否有需要马上处理的异常。</p>
        {error ? <div className="banner banner-error">{error}</div> : null}

        {loading && !snapshot ? <div className="table-empty">首次生成快照中...</div> : null}

        {snapshot ? (
          <>
            <div className="hero-grid">
              <article className={`panel hero-panel hero-panel-${readinessTone}`}>
                <span className="eyebrow">Operational Readiness</span>
                <h3>{warningCount > 0 || missingQuotes > 0 ? "当前快照需要复核" : "当前快照可直接使用"}</h3>
                <p className="metric metric-compact">{snapshot.meta.broker_status}</p>
                <p className="panel-note">
                  来源 {snapshot.meta.broker_display_name}，生成于 {formatDateTime(snapshot.meta.generated_at)}
                </p>
              </article>

              <article className="panel">
                <h3>优先检查项</h3>
                <KeyValueList
                  items={[
                    { label: "Broker 状态", value: snapshot.meta.broker_status },
                    { label: "数据来源", value: snapshot.meta.broker_display_name },
                    { label: "缓存状态", value: formatSnapshotCacheStatus(snapshotResponse) },
                    { label: "Broker 警告", value: `${warningCount} 条`, tone: warningCount > 0 ? "warning" : "positive" },
                    {
                      label: "缺失行情",
                      value: `${missingQuotes} 个`,
                      tone: missingQuotes > 0 ? "warning" : "positive",
                    },
                    {
                      label: "持仓标的",
                      value: `${snapshot.summary.symbols_in_position} / ${snapshot.summary.enabled_symbols}`,
                    },
                  ]}
                />
              </article>
            </div>

            <div className="panel-grid">
              <StatCard
                label="账户净值"
                value={formatCurrency(snapshot.account.net_liquidation, snapshot.account.currency, { compact: true })}
                note={`来源：${snapshot.meta.broker_display_name}`}
              />
              <StatCard
                label="监控标的"
                value={snapshot.summary.tracked_symbols}
                note={`${snapshot.summary.enabled_symbols} 个当前已启用`}
              />
              <StatCard
                label="行情覆盖"
                value={`${snapshot.summary.quote_coverage} / ${snapshot.summary.enabled_symbols}`}
                note={missingQuotes > 0 ? `${missingQuotes} 个启用标的暂无行情` : "启用标的行情齐全"}
                tone={missingQuotes > 0 ? "warning" : "positive"}
              />
              <StatCard
                label="快照持仓"
                value={snapshot.positions.length}
                note={`最近成功 ${formatDateTime(snapshotResponse?.last_success_at ?? snapshot.meta.generated_at)}`}
              />
            </div>

            <div className="panel-grid overview-secondary overview-grid-2">
              <article className="panel">
                <h3>系统警告</h3>
                {snapshot.meta.warnings.length === 0 ? (
                  <p className="empty-copy">当前没有 broker 警告。</p>
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
                <h3>账户摘要</h3>
                <KeyValueList
                  items={[
                    { label: "账户 ID", value: snapshot.account.account_id || "--" },
                    { label: "可用资金", value: formatCurrency(snapshot.account.available_funds, snapshot.account.currency) },
                    { label: "Buying Power", value: formatCurrency(snapshot.account.buying_power, snapshot.account.currency) },
                    { label: "账户更新时间", value: formatDateTime(snapshot.account.updated_at) },
                  ]}
                />
              </article>
            </div>
          </>
        ) : null}
      </section>
    </section>
  );
}
