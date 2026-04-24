import type { AlertRule, AlertRuleMetadata } from "../../shared/api";
import { formatDateTime } from "../../shared/formatters";
import { formatCooldown, formatThreshold, metricText, operatorText, sourceText } from "./alertRuleForm";

export function AlertRulesSummaryBar(props: {
  summary: {
    total: number;
    enabled: number;
    triggeredToday: number;
    failed: number;
  };
  onResetCounters: () => void;
  onCreateRule: () => void;
}) {
  return (
    <div className="monitor-summary-bar alert-rule-summary" aria-label="提醒规则摘要">
      <div className="monitor-summary-metrics">
        <div className="monitor-summary-item">
          <span>规则总数</span>
          <strong>{props.summary.total}</strong>
        </div>
        <div className="monitor-summary-item">
          <span>已启用</span>
          <strong>{props.summary.enabled}</strong>
        </div>
        <div className="monitor-summary-item">
          <span>今日触发</span>
          <strong className={props.summary.triggeredToday > 0 ? "value-warning" : "value-positive"}>
            {props.summary.triggeredToday}
          </strong>
        </div>
        <div className="monitor-summary-item">
          <span>失败规则</span>
          <strong className={props.summary.failed > 0 ? "value-warning" : "value-positive"}>{props.summary.failed}</strong>
        </div>
      </div>

      <div className="alert-rule-toolbar">
        <button type="button" className="button button-secondary" onClick={props.onResetCounters}>
          重置统计
        </button>
        <button type="button" className="button" onClick={props.onCreateRule}>
          新增规则
        </button>
      </div>
    </div>
  );
}

export function AlertRulesTable(props: {
  rules: AlertRule[];
  metadata: AlertRuleMetadata;
  loading: boolean;
  onToggle: (rule: AlertRule) => void;
  onDelete: (ruleId: number) => void;
}) {
  return (
    <section className="section-block">
      <article className="table-shell">
        <div className="table-row table-head table-alert-rules">
          <span>规则</span>
          <span>来源</span>
          <span>条件</span>
          <span>状态</span>
          <span>已发送</span>
          <span>发送失败</span>
          <span>已抑制</span>
          <span>最近触发</span>
          <span>操作</span>
        </div>

        {props.loading ? <div className="table-empty">正在加载提醒规则...</div> : null}

        {!props.loading && props.rules.length === 0 ? (
          <div className="table-empty">还没有提醒规则，先新增一条价格、回撤或资产提醒。</div>
        ) : null}

        {!props.loading &&
          props.rules.map((rule) => (
            <div key={rule.id} className="table-row table-alert-rules">
              <div className="cell-stack">
                <span className="symbol-cell">{rule.name}</span>
                <span className="muted">{rule.symbol || "账户规则"}</span>
              </div>
              <span>{sourceText(props.metadata, rule.source)}</span>
              <div className="cell-stack">
                <span>
                  {metricText(props.metadata, rule.metric)} {operatorText(props.metadata, rule.operator)} {formatThreshold(rule)}
                </span>
                <span className="muted">{rule.edge_only ? "首次命中提醒" : `冷却 ${formatCooldown(rule.cooldown_seconds)}`}</span>
                {rule.last_error ? <span className="value-negative">{rule.last_error}</span> : null}
              </div>
              <span className={rule.enabled ? "status-pill status-pill-ok" : "status-pill"}>{rule.enabled ? "启用" : "暂停"}</span>
              <strong>{rule.sent_count}</strong>
              <strong className={rule.failed_count > 0 ? "value-negative" : undefined}>{rule.failed_count}</strong>
              <strong className={rule.suppressed_count > 0 ? "value-warning" : undefined}>{rule.suppressed_count}</strong>
              <span className="muted">{rule.last_triggered_at ? formatDateTime(rule.last_triggered_at) : "--"}</span>
              <div className="table-actions">
                <button type="button" className="button button-secondary" onClick={() => props.onToggle(rule)}>
                  {rule.enabled ? "停用" : "启用"}
                </button>
                <button type="button" className="button button-danger" onClick={() => props.onDelete(rule.id)}>
                  删除
                </button>
              </div>
            </div>
          ))}
      </article>
    </section>
  );
}
