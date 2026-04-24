import type {
  AlertRule,
  AlertRuleMetadata,
  AlertRuleMetric,
  AlertRuleOperator,
  AlertRuleSource,
  AlertRuleTemplate,
  CreateAlertRulePayload,
  WatchlistEntry,
} from "../../shared/api";

export const fallbackMetadata: AlertRuleMetadata = {
  sources: [
    { value: "watchlist", label: "追踪数据" },
    { value: "portfolio", label: "资产数据" },
  ],
  operators: [
    { value: "above", label: "高于" },
    { value: "below", label: "低于" },
    { value: "gte", label: "大于等于" },
    { value: "lte", label: "小于等于" },
    { value: "equals", label: "等于" },
    { value: "not_equals", label: "不等于" },
    { value: "cross_above", label: "上穿" },
    { value: "cross_below", label: "下穿" },
    { value: "change_to", label: "变为" },
  ],
  metrics: [],
  templates: [
    {
      id: "price_below",
      label: "价格低于",
      description: "标的当前价低于指定价格时提醒。",
      source: "watchlist",
      metric: "current_price",
      operator: "below",
      threshold_value: "",
      cooldown_seconds: 3600,
      edge_only: true,
    },
  ],
};

export const valuationLabels: Record<string, string> = {
  undervalued: "低估",
  fair: "合理",
  overvalued: "高估",
};

export const cooldownOptions = [
  { value: 900, label: "15 分钟" },
  { value: 1800, label: "30 分钟" },
  { value: 3600, label: "1 小时" },
  { value: 10800, label: "3 小时" },
  { value: 86400, label: "1 天" },
];

export type AlertRuleFormState = CreateAlertRulePayload & {
  template_id: string;
};

export const initialForm: AlertRuleFormState = {
  template_id: "price_below",
  name: "",
  enabled: true,
  category: "threshold",
  source: "watchlist",
  symbol: "",
  metric: "current_price",
  operator: "below",
  threshold_value: "",
  cooldown_seconds: 3600,
  edge_only: true,
  message_template: "",
};

export function buildTemplateForm(template: AlertRuleTemplate, watchlist: WatchlistEntry[]): AlertRuleFormState {
  const symbol = template.source === "watchlist" ? watchlist[0]?.symbol ?? "" : "";
  return {
    ...initialForm,
    template_id: template.id,
    name: buildRuleName(template, symbol),
    category: isEventOperator(template.operator) ? "event" : "threshold",
    source: template.source,
    symbol,
    metric: template.metric,
    operator: template.operator,
    threshold_value: template.threshold_value,
    cooldown_seconds: template.cooldown_seconds,
    edge_only: template.edge_only,
  };
}

export function buildRuleName(template: AlertRuleTemplate, symbol: string) {
  if (template.source === "portfolio") {
    return template.label;
  }
  return symbol ? `${symbol} ${template.label}` : template.label;
}

export function normalizeAlertRulePayload(payload: AlertRuleFormState): CreateAlertRulePayload {
  return {
    name: payload.name.trim(),
    enabled: true,
    category: isEventOperator(payload.operator) ? "event" : "threshold",
    source: payload.source,
    symbol: payload.source === "watchlist" ? (payload.symbol ?? "").trim().toUpperCase() : "",
    metric: payload.metric,
    operator: payload.operator,
    threshold_value: payload.threshold_value.trim(),
    cooldown_seconds: payload.cooldown_seconds ?? 3600,
    edge_only: payload.edge_only ?? true,
    message_template: payload.message_template ?? "",
  };
}

export function sourceText(metadata: AlertRuleMetadata, source: AlertRuleSource) {
  return metadata.sources.find((option) => option.value === source)?.label ?? source;
}

export function metricText(metadata: AlertRuleMetadata, metric: AlertRuleMetric) {
  return metadata.metrics.find((option) => option.value === metric)?.label ?? metric;
}

export function operatorText(metadata: AlertRuleMetadata, operator: AlertRuleOperator) {
  return metadata.operators.find((option) => option.value === operator)?.label ?? operator;
}

export function formatThreshold(rule: AlertRule) {
  return valuationLabels[rule.threshold_value] ?? rule.threshold_value;
}

export function formatCooldown(seconds: number) {
  if (seconds >= 86400) {
    return `${Math.round(seconds / 86400)} 天`;
  }
  if (seconds >= 3600) {
    return `${Math.round(seconds / 3600)} 小时`;
  }
  return `${Math.round(seconds / 60)} 分钟`;
}

export function isEventOperator(operator: AlertRuleOperator) {
  return operator === "cross_above" || operator === "cross_below" || operator === "change_to" || operator === "becomes";
}

export function isToday(value: string | null) {
  if (!value) {
    return false;
  }
  return new Date(value).toDateString() === new Date().toDateString();
}
