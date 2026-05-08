import type { FormEvent } from "react";

import type { AlertRuleMetadata, AlertRuleTemplate, WatchlistEntry } from "../../shared/api";
import {
  type AlertRuleFormState,
  cooldownOptions,
  metricText,
  operatorText,
  valuationLabels,
} from "./alertRuleForm";

export function AlertRuleDialog(props: {
  form: AlertRuleFormState;
  metadata: AlertRuleMetadata;
  watchlist: WatchlistEntry[];
  saving: boolean;
  selectedTemplate: AlertRuleTemplate;
  onClose: () => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onTemplateChange: (templateId: string) => void;
  onNameChange: (name: string) => void;
  onSymbolChange: (symbol: string) => void;
  onThresholdChange: (threshold: string) => void;
  onCooldownChange: (cooldownSeconds: number) => void;
  onEdgeOnlyChange: (edgeOnly: boolean) => void;
}) {
  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={props.onClose}>
      <form
        className="modal-card alert-rule-modal"
        onSubmit={props.onSubmit}
        onMouseDown={(event) => event.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="新增提醒规则"
      >
        <div className="modal-header">
          <div>
            <h2>新增提醒规则</h2>
            <p>先选模板，再填少量参数。规则命中后会通过已配置的通知通道推送。</p>
          </div>
          <button type="button" className="button button-tertiary" onClick={props.onClose}>
            关闭
          </button>
        </div>

        <label className="form-field form-field-wide">
          <span>规则模板</span>
          <select value={props.form.template_id} onChange={(event) => props.onTemplateChange(event.target.value)}>
            {props.metadata.templates.map((template) => (
              <option key={template.id} value={template.id}>
                {template.label}
              </option>
            ))}
          </select>
          <small>{props.selectedTemplate.description}</small>
        </label>

        <label className="form-field form-field-wide">
          <span>规则名称</span>
          <input
            value={props.form.name}
            onChange={(event) => props.onNameChange(event.target.value)}
            placeholder="例如 AAPL 价格低于 180"
            maxLength={128}
            required
          />
        </label>

        {props.form.source === "watchlist" ? (
          <label className="form-field">
            <span>标的</span>
            <select value={props.form.symbol ?? ""} onChange={(event) => props.onSymbolChange(event.target.value)}>
              {props.watchlist.length === 0 ? <option value="">先到追踪页添加标的</option> : null}
              {props.watchlist.map((entry) => (
                <option key={entry.id} value={entry.symbol}>
                  {entry.symbol}
                </option>
              ))}
            </select>
          </label>
        ) : null}

        <label className="form-field">
          <span>触发条件</span>
          <input value={`${metricText(props.metadata, props.form.metric)} ${operatorText(props.metadata, props.form.operator)}`} disabled />
        </label>

        <label className="form-field">
          <span>阈值</span>
          {props.form.metric === "valuation_label" ? (
            <select value={props.form.threshold_value} onChange={(event) => props.onThresholdChange(event.target.value)}>
              {Object.entries(valuationLabels).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          ) : (
            <input
              type="number"
              step="0.01"
              value={props.form.threshold_value}
              onChange={(event) => props.onThresholdChange(event.target.value)}
              placeholder="请输入阈值"
              required
            />
          )}
        </label>

        <label className="form-field">
          <span>冷却时间</span>
          <select value={String(props.form.cooldown_seconds ?? 3600)} onChange={(event) => props.onCooldownChange(Number(event.target.value))}>
            {cooldownOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label className="form-check form-field-wide">
          <input type="checkbox" checked={props.form.edge_only ?? true} onChange={(event) => props.onEdgeOnlyChange(event.target.checked)} />
          <span>只在从未命中变成命中时提醒，避免每次刷新都推送。</span>
        </label>

        <div className="modal-actions">
          <button type="button" className="button button-tertiary" onClick={props.onClose}>
            取消
          </button>
          <button type="submit" className="button button-primary" disabled={props.saving}>
            {props.saving ? "保存中..." : "保存规则"}
          </button>
        </div>
      </form>
    </div>
  );
}
