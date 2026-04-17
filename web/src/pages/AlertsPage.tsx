import { useEffect, useMemo, useState } from "react";

import { AlertDeliveryStatus, AlertEvent, listAlerts } from "../shared/api";
import { formatDateTime } from "../shared/formatters";
import { PageSection, StatCard } from "../shared/ui";

function deliveryClass(status: AlertDeliveryStatus) {
  switch (status) {
    case "sent":
      return "status-pill status-pill-ok";
    case "failed":
      return "status-pill status-pill-danger";
    case "skipped":
    default:
      return "status-pill";
  }
}

function deliveryLabel(status: AlertDeliveryStatus) {
  switch (status) {
    case "sent":
      return "已发送";
    case "failed":
      return "发送失败";
    case "skipped":
    default:
      return "已跳过";
  }
}

export function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | AlertDeliveryStatus>("all");

  useEffect(() => {
    void loadAlerts();
  }, []);

  async function loadAlerts() {
    setLoading(true);
    try {
      const nextAlerts = await listAlerts();
      setAlerts(nextAlerts);
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load alerts.");
    } finally {
      setLoading(false);
    }
  }

  const sentCount = alerts.filter((alert) => alert.delivery_status === "sent").length;
  const failedCount = alerts.filter((alert) => alert.delivery_status === "failed").length;
  const skippedCount = alerts.filter((alert) => alert.delivery_status === "skipped").length;
  const filteredAlerts = useMemo(
    () => alerts.filter((alert) => (filter === "all" ? true : alert.delivery_status === filter)),
    [alerts, filter],
  );
  const latestFailure = alerts.find((alert) => alert.delivery_status === "failed");

  return (
    <section>
      <header className="page-header">
        <span className="eyebrow">Notifications</span>
        <h1>提醒</h1>
        <p>先看失败提醒，再按状态筛选历史，把“触发了什么”和“有没有送达”分开读。</p>
      </header>

      <div className="panel-grid">
        <StatCard label="提醒总数" value={alerts.length} note="当前后端已存储的提醒记录" />
        <StatCard label="发送成功" value={sentCount} note="Telegram 已接受或发送成功" tone={sentCount > 0 ? "positive" : "default"} />
        <StatCard label="发送失败" value={failedCount} note="优先排查 token、chat id 或网络" tone={failedCount > 0 ? "danger" : "positive"} />
        <StatCard label="已跳过" value={skippedCount} note="触发后未实际投递" />
      </div>

      <div className="panel-grid overview-secondary overview-grid-2">
        <article className="panel">
          <h3>最新失败提醒</h3>
          {latestFailure ? (
            <div className="cell-stack">
              <span className="symbol-cell">{latestFailure.symbol}</span>
              <span>{latestFailure.title}</span>
              <span className="muted">{formatDateTime(latestFailure.created_at)}</span>
              <span className="value-negative">{latestFailure.error_detail || "未返回错误详情"}</span>
            </div>
          ) : (
            <p className="empty-copy">当前没有失败提醒。</p>
          )}
        </article>

        <article className="panel">
          <h3>阅读建议</h3>
          <p className="panel-note">
            如果失败数大于 0，先修投递链路；如果全成功，再按 symbol 和消息正文回看最近状态变化。
          </p>
        </article>
      </div>

      <PageSection
        title="提醒历史"
        description="当前 MVP 只记录估值状态变化提醒。"
        actions={
          <div className="actions-row">
            <div className="filter-group">
              {[
                { value: "all", label: "全部" },
                { value: "failed", label: "失败" },
                { value: "sent", label: "成功" },
                { value: "skipped", label: "跳过" },
              ].map((item) => (
                <button
                  key={item.value}
                  type="button"
                  className={filter === item.value ? "button filter-button active" : "button button-secondary filter-button"}
                  onClick={() => setFilter(item.value as typeof filter)}
                >
                  {item.label}
                </button>
              ))}
            </div>
            <button type="button" className="button button-secondary" onClick={() => void loadAlerts()}>
              刷新提醒
            </button>
          </div>
        }
      >
        {error ? <div className="banner banner-error">{error}</div> : null}

        {loading ? <div className="table-empty">正在加载提醒...</div> : null}

        {!loading && filteredAlerts.length === 0 ? (
          <div className="table-empty">当前筛选条件下没有提醒记录。</div>
        ) : null}

        {!loading && filteredAlerts.length > 0 ? (
          <div className="alert-feed">
            {filteredAlerts.map((alert) => (
              <article key={alert.id} className="panel alert-card">
                <div className="alert-card-header">
                  <div className="cell-stack">
                    <div className="status-stack">
                      <span className="symbol-cell">{alert.symbol}</span>
                      <span className={deliveryClass(alert.delivery_status)}>{deliveryLabel(alert.delivery_status)}</span>
                    </div>
                    <strong>{alert.title}</strong>
                    <span className="muted">{formatDateTime(alert.created_at)}</span>
                  </div>
                </div>
                <div className="alert-message">
                  <pre>{alert.message}</pre>
                  {alert.error_detail ? <small className="value-negative">{alert.error_detail}</small> : null}
                </div>
              </article>
            ))}
          </div>
        ) : null}
      </PageSection>
    </section>
  );
}
