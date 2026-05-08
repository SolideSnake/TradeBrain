import { useEffect, useMemo, useState } from "react";

import { useSnapshotResource } from "../hooks/useSnapshotResource";
import {
  type CanonicalSnapshot,
  type EventRecord,
  type PortfolioHistoryPoint,
  type PortfolioHistoryRange,
  listEvents,
  listPortfolioHistory,
} from "../shared/api";
import { formatCurrency, formatPercent } from "../shared/formatters";

interface AssetTrendPoint {
  timestamp: string;
  value: number;
}

const TREND_RANGES: PortfolioHistoryRange[] = ["1D", "1W", "1M", "YTD"];
const EVENT_LIMIT = 50;
const TREND_VIEWBOX = {
  width: 720,
  height: 260,
  paddingTop: 26,
  paddingRight: 96,
  paddingBottom: 38,
  paddingLeft: 26,
};

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

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "--";
  }

  const now = new Date();
  const isSameDay = date.toDateString() === now.toDateString();
  const time = new Intl.DateTimeFormat("zh-HK", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);

  if (isSameDay) {
    return `今天 ${time}`;
  }

  return new Intl.DateTimeFormat("zh-HK", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);
}

function formatAxisCurrency(value: number, domainRange: number) {
  const absValue = Math.abs(value);
  if (absValue >= 1_000_000 && domainRange >= 100_000) {
    return `$${(value / 1_000_000).toFixed(1)}M`;
  }
  if (absValue >= 1_000 && domainRange >= 10_000) {
    return `$${Math.round(value / 1_000).toLocaleString("en-US")}k`;
  }
  return formatCurrency(value, "USD", { digits: 0 });
}

function formatTrendDate(value: string, range: PortfolioHistoryRange) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "--";
  }

  if (range === "1D") {
    return new Intl.DateTimeFormat("zh-HK", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).format(date);
  }

  return new Intl.DateTimeFormat("zh-HK", {
    month: "2-digit",
    day: "2-digit",
  }).format(date);
}

function buildTrendModel(points: AssetTrendPoint[]) {
  const { width, height, paddingTop, paddingRight, paddingBottom, paddingLeft } = TREND_VIEWBOX;
  const chartWidth = width - paddingLeft - paddingRight;
  const chartHeight = height - paddingTop - paddingBottom;
  const values = points.map((point) => point.value);
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const valuePadding = Math.max((maxValue - minValue) * 0.08, Math.max(maxValue, 1) * 0.002);
  const domainMin = minValue === maxValue ? minValue - valuePadding : minValue - valuePadding;
  const domainMax = minValue === maxValue ? maxValue + valuePadding : maxValue + valuePadding;
  const valueRange = domainMax - domainMin || 1;

  const coordinates = points.map((point, index) => {
    const x = paddingLeft + (index / Math.max(points.length - 1, 1)) * chartWidth;
    const y = paddingTop + (1 - (point.value - domainMin) / valueRange) * chartHeight;
    return { ...point, x, y };
  });
  const path = coordinates
    .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`)
    .join(" ");
  const axisTicks = [
    { value: domainMax, y: paddingTop },
    { value: (domainMax + domainMin) / 2, y: paddingTop + chartHeight / 2 },
    { value: domainMin, y: paddingTop + chartHeight },
  ];

  return {
    path,
    coordinates,
    axisTicks,
    valueRange,
    chartStartX: paddingLeft,
    chartEndX: paddingLeft + chartWidth,
    chartBottomY: paddingTop + chartHeight,
  };
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

function AssetTrendChart(props: { points: AssetTrendPoint[]; range: PortfolioHistoryRange }) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  if (props.points.length < 2) {
    return <div className="dashboard-trend-empty">暂无资产走势数据</div>;
  }

  const model = buildTrendModel(props.points);
  const hoverPoint = hoverIndex === null ? null : model.coordinates[hoverIndex];
  const xLabels = [
    props.points[0],
    props.points[Math.floor((props.points.length - 1) / 2)],
    props.points[props.points.length - 1],
  ];

  return (
    <div className="dashboard-trend-chart-shell">
      <svg className="dashboard-trend-chart" viewBox={`0 0 ${TREND_VIEWBOX.width} ${TREND_VIEWBOX.height}`} role="img" aria-label="资产走势折线图">
        <defs>
          <linearGradient id="assetTrendArea" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#7aa2ff" stopOpacity="0.22" />
            <stop offset="100%" stopColor="#7aa2ff" stopOpacity="0" />
          </linearGradient>
        </defs>

        {model.axisTicks.map((tick) => (
          <g key={`${tick.value}-${tick.y}`} className="dashboard-trend-grid">
            <line x1={model.chartStartX} y1={tick.y} x2={model.chartEndX} y2={tick.y} />
            <text x={model.chartEndX + 10} y={tick.y + 4}>{formatAxisCurrency(tick.value, model.valueRange)}</text>
          </g>
        ))}

        <path
          className="dashboard-trend-area"
          d={`${model.path} L ${model.chartEndX} ${model.chartBottomY} L ${model.chartStartX} ${model.chartBottomY} Z`}
        />
        <path className="dashboard-trend-line" d={model.path} />

        {model.coordinates.map((point, index) => (
          <circle
            key={`${point.timestamp}-${index}`}
            className={index === hoverIndex ? "dashboard-trend-point is-active" : "dashboard-trend-point"}
            cx={point.x}
            cy={point.y}
            r={index === hoverIndex ? 4.5 : 2.5}
          />
        ))}

        {xLabels.map((point, index) => {
          const coordinate = model.coordinates[index === 0 ? 0 : index === 1 ? Math.floor((model.coordinates.length - 1) / 2) : model.coordinates.length - 1];
          return (
            <text
              key={`${point.timestamp}-${index}`}
              className="dashboard-trend-x-label"
              x={coordinate.x}
              y={TREND_VIEWBOX.height - 8}
              textAnchor={index === 0 ? "start" : index === 1 ? "middle" : "end"}
            >
              {formatTrendDate(point.timestamp, props.range)}
            </text>
          );
        })}

        {model.coordinates.map((point, index) => (
          <rect
            key={`hit-${point.timestamp}-${index}`}
            className="dashboard-trend-hit-area"
            x={point.x - Math.max(8, (model.chartEndX - model.chartStartX) / props.points.length / 2)}
            y={TREND_VIEWBOX.paddingTop}
            width={Math.max(16, (model.chartEndX - model.chartStartX) / props.points.length)}
            height={model.chartBottomY - TREND_VIEWBOX.paddingTop}
            onMouseEnter={() => setHoverIndex(index)}
            onMouseLeave={() => setHoverIndex(null)}
          />
        ))}
      </svg>

      {hoverPoint ? (
        <div
          className="dashboard-trend-tooltip"
          style={{
            left: `${(hoverPoint.x / TREND_VIEWBOX.width) * 100}%`,
            top: `${(hoverPoint.y / TREND_VIEWBOX.height) * 100}%`,
          }}
        >
          <strong>{formatCurrency(hoverPoint.value, "USD")}</strong>
          <span>{formatShortTime(hoverPoint.timestamp)}</span>
        </div>
      ) : null}
    </div>
  );
}

function mapHistoryToTrendPoints(history: PortfolioHistoryPoint[]): AssetTrendPoint[] {
  return history
    .filter((point) => point.net_liquidation !== null)
    .map((point) => ({
      timestamp: point.recorded_at,
      value: point.net_liquidation as number,
    }));
}

function AssetTrendCard() {
  const [activeRange, setActiveRange] = useState<PortfolioHistoryRange>("1D");
  const [history, setHistory] = useState<PortfolioHistoryPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const trendPoints = useMemo<AssetTrendPoint[]>(() => mapHistoryToTrendPoints(history), [history]);
  const latestPoint = trendPoints.length > 0 ? trendPoints[trendPoints.length - 1] : null;
  const firstPoint = trendPoints[0] ?? null;
  const valueChange = latestPoint && firstPoint ? latestPoint.value - firstPoint.value : null;
  const percentChange = valueChange !== null && firstPoint && firstPoint.value !== 0
    ? (valueChange / firstPoint.value) * 100
    : null;

  useEffect(() => {
    let ignore = false;

    async function loadHistory() {
      setLoading(true);
      try {
        const nextHistory = await listPortfolioHistory(activeRange);
        if (!ignore) {
          setHistory(nextHistory);
          setError(null);
        }
      } catch (nextError) {
        if (!ignore) {
          setError(nextError instanceof Error ? nextError.message : "资产走势加载失败");
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }

    void loadHistory();

    function handleSnapshotRefreshed() {
      void loadHistory();
    }

    window.addEventListener("tradebrain:snapshot-refreshed", handleSnapshotRefreshed);
    return () => {
      ignore = true;
      window.removeEventListener("tradebrain:snapshot-refreshed", handleSnapshotRefreshed);
    };
  }, [activeRange]);

  return (
    <article className="panel dashboard-trend-card">
      <div className="dashboard-card-header">
        <div>
          <h3>资产走势</h3>
          <div className="dashboard-trend-summary">
            <strong>{latestPoint ? formatCurrency(latestPoint.value, "USD") : "--"}</strong>
            <span className={(valueChange ?? 0) >= 0 ? "trend-positive" : "trend-negative"}>
              {valueChange !== null ? formatCurrency(valueChange, "USD") : "--"}
              {percentChange !== null ? ` / ${formatPercent(percentChange)}` : ""}
            </span>
          </div>
        </div>
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
      {error ? <div className="dashboard-events-error">{error}</div> : null}
      {loading ? <div className="dashboard-trend-empty">加载资产走势中...</div> : <AssetTrendChart points={trendPoints} range={activeRange} />}
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
