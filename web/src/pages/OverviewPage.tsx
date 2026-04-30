import { useEffect, useMemo, useState } from "react";

import { useSnapshotResource } from "../hooks/useSnapshotResource";
import { type CanonicalSnapshot, type EventRecord, listEvents } from "../shared/api";

type TrendRange = "1D" | "1W" | "1M" | "YTD";

interface AssetTrendPoint {
  timestamp: string;
  value: number;
}

const TREND_RANGES: TrendRange[] = ["1D", "1W", "1M", "YTD"];
const EVENT_LIMIT = 50;

function environmentLabel(snapshot: CanonicalSnapshot | null) {
  if (!snapshot) {
    return "--";
  }

  return snapshot.meta.broker_profile === "real" ? "真实" : "模拟";
}

function formatShortTime(value: string | null) {
  if (!value) {
    return "--";
  }

  return new Intl.DateTimeFormat("zh-HK", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date(value));
}

function buildLinePath(points: AssetTrendPoint[]) {
  const width = 640;
  const height = 220;
  const paddingX = 20;
  const paddingY = 24;
  const values = points.map((point) => point.value);
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const valueRange = maxValue - minValue || 1;

  return points
    .map((point, index) => {
      const x = paddingX + (index / Math.max(points.length - 1, 1)) * (width - paddingX * 2);
      const y = height - paddingY - ((point.value - minValue) / valueRange) * (height - paddingY * 2);
      return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(" ");
}

function DashboardStatusCard(props: {
  snapshot: CanonicalSnapshot | null;
  lastSuccessAt: string | null;
}) {
  const accountLabel = props.snapshot
    ? `${environmentLabel(props.snapshot)} · ${props.snapshot.account.account_id || "--"}`
    : "--";
  const trackedLabel = props.snapshot
    ? `${props.snapshot.summary.quote_coverage} / ${props.snapshot.summary.tracked_symbols}`
    : "-- / --";

  return (
    <article className="panel dashboard-status-card">
      <div className="dashboard-status-row">
        <span>账户</span>
        <strong>{accountLabel}</strong>
      </div>
      <div className="dashboard-status-row">
        <span>追踪</span>
        <strong>{trackedLabel}</strong>
      </div>
      <div className="dashboard-status-row">
        <span>刷新</span>
        <strong>{formatShortTime(props.lastSuccessAt)}</strong>
      </div>
    </article>
  );
}

function AssetTrendChart(props: { points: AssetTrendPoint[] }) {
  if (props.points.length < 2) {
    return <div className="dashboard-trend-empty">暂无资产走势数据</div>;
  }

  const path = buildLinePath(props.points);

  return (
    <svg className="dashboard-trend-chart" viewBox="0 0 640 220" role="img" aria-label="资产走势折线图">
      <line x1="20" y1="196" x2="620" y2="196" />
      <path d={path} />
    </svg>
  );
}

function AssetTrendCard() {
  const [activeRange, setActiveRange] = useState<TrendRange>("1D");
  const trendPoints = useMemo<AssetTrendPoint[]>(() => [], []);

  return (
    <article className="panel dashboard-trend-card">
      <div className="dashboard-card-header">
        <h3>资产走势</h3>
        <div className="dashboard-range-tabs" aria-label="资产走势时间范围">
          {TREND_RANGES.map((range) => (
            <button
              key={range}
              type="button"
              className={range === activeRange ? "is-active" : undefined}
              aria-pressed={range === activeRange}
              onClick={() => setActiveRange(range)}
            >
              {range}
            </button>
          ))}
        </div>
      </div>
      <AssetTrendChart points={trendPoints} />
    </article>
  );
}

function eventSeverityLabel(severity: EventRecord["severity"]) {
  if (severity === "critical") {
    return "严重";
  }
  if (severity === "warning") {
    return "警告";
  }
  return "信息";
}

function eventStatusLabel(status: EventRecord["status"]) {
  if (status === "success") {
    return "成功";
  }
  if (status === "sent") {
    return "已发送";
  }
  if (status === "failed") {
    return "失败";
  }
  return "跳过";
}

function DashboardEventsCard(props: {
  events: EventRecord[];
  loading: boolean;
  error: string | null;
}) {
  return (
    <article className="panel dashboard-events-card">
      <div className="dashboard-events-header">
        <h3>事件</h3>
        <span>最近 {EVENT_LIMIT} 条</span>
      </div>

      {props.error ? <div className="dashboard-events-error">{props.error}</div> : null}
      {props.loading ? <div className="dashboard-events-empty">加载事件中...</div> : null}

      {!props.loading && !props.error && props.events.length === 0 ? (
        <div className="dashboard-events-empty">暂无事件记录</div>
      ) : null}

      {!props.loading && !props.error && props.events.length > 0 ? (
        <div className="dashboard-events-list">
          {props.events.map((event) => (
            <div key={event.id} className="dashboard-event-row">
              <time>{formatShortTime(event.occurred_at)}</time>
              <span className={`dashboard-event-level dashboard-event-level-${event.severity}`}>
                {eventSeverityLabel(event.severity)}
              </span>
              <span className="dashboard-event-source">{event.source}</span>
              <span className="dashboard-event-symbol">{event.symbol || "系统"}</span>
              <div className="dashboard-event-copy">
                <strong>{event.title}</strong>
                <span>{event.message || "--"}</span>
              </div>
              <span className={`dashboard-event-delivery dashboard-event-delivery-${event.status}`}>
                {eventStatusLabel(event.status)}
              </span>
            </div>
          ))}
        </div>
      ) : null}
    </article>
  );
}

export function OverviewPage() {
  const { snapshot, snapshotResponse, error } = useSnapshotResource({
    loadErrorMessage: "Failed to load snapshot.",
  });
  const [events, setEvents] = useState<EventRecord[]>([]);
  const [eventsLoading, setEventsLoading] = useState(true);
  const [eventsError, setEventsError] = useState<string | null>(null);
  const lastSuccessAt = snapshotResponse?.last_success_at ?? snapshot?.meta.generated_at ?? null;
  const visibleEvents = useMemo(
    () =>
      [...events]
        .sort((left, right) => {
          const createdAtDiff = new Date(right.occurred_at).getTime() - new Date(left.occurred_at).getTime();
          return createdAtDiff || right.id - left.id;
        })
        .slice(0, EVENT_LIMIT),
    [events],
  );

  useEffect(() => {
    let ignore = false;

    async function loadEvents() {
      setEventsLoading(true);
      try {
        const nextEvents = await listEvents(EVENT_LIMIT);
        if (!ignore) {
          setEvents(nextEvents);
          setEventsError(null);
        }
      } catch (loadError) {
        if (!ignore) {
          setEventsError(loadError instanceof Error ? loadError.message : "事件加载失败。");
        }
      } finally {
        if (!ignore) {
          setEventsLoading(false);
        }
      }
    }

    void loadEvents();

    return () => {
      ignore = true;
    };
  }, []);

  return (
    <section className="dashboard-page">
      <div className="dashboard-primary-row">
        <DashboardStatusCard snapshot={snapshot} lastSuccessAt={lastSuccessAt} />
        <AssetTrendCard />
      </div>
      <DashboardEventsCard events={visibleEvents} loading={eventsLoading} error={eventsError} />
      {error ? <div className="banner banner-error dashboard-error">{error}</div> : null}
    </section>
  );
}
