import { type FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import {
  type AlertRule,
  type AlertRuleMetadata,
  type AlertRuleTemplate,
  type WatchlistEntry,
  createAlertRule,
  deleteAlertRule,
  getAlertRuleMetadata,
  listAlertRules,
  listWatchlist,
  resetAlertRuleCounters,
  updateAlertRule,
} from "../../shared/api";
import {
  type AlertRuleFormState,
  buildRuleName,
  buildTemplateForm,
  fallbackMetadata,
  initialForm,
  isToday,
  normalizeAlertRulePayload,
} from "./alertRuleForm";

export function useAlertsPageState() {
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [watchlist, setWatchlist] = useState<WatchlistEntry[]>([]);
  const [metadata, setMetadata] = useState<AlertRuleMetadata>(fallbackMetadata);
  const [form, setForm] = useState<AlertRuleFormState>(initialForm);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedTemplate = useMemo(
    () => metadata.templates.find((template) => template.id === form.template_id) ?? metadata.templates[0] ?? fallbackMetadata.templates[0],
    [form.template_id, metadata.templates],
  );

  const summary = useMemo(
    () => ({
      total: rules.length,
      enabled: rules.filter((rule) => rule.enabled).length,
      triggeredToday: rules.filter((rule) => isToday(rule.last_triggered_at)).length,
      failed: rules.filter((rule) => rule.failed_count > 0).length,
    }),
    [rules],
  );

  const sortedRules = useMemo(
    () => [...rules].sort((left, right) => Number(right.enabled) - Number(left.enabled)),
    [rules],
  );

  const loadPage = useCallback(async () => {
    setLoading(true);
    try {
      const [nextRules, nextWatchlist, nextMetadata] = await Promise.all([
        listAlertRules(),
        listWatchlist(),
        getAlertRuleMetadata(),
      ]);
      setRules(nextRules);
      setWatchlist(nextWatchlist);
      setMetadata(nextMetadata);
      setError(null);
      setForm(buildTemplateForm(nextMetadata.templates[0] ?? fallbackMetadata.templates[0], nextWatchlist));
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "加载提醒规则失败。");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadPage();
  }, [loadPage]);

  const updateTemplate = useCallback(
    (templateId: string) => {
      const template = metadata.templates.find((option) => option.id === templateId) ?? metadata.templates[0] ?? fallbackMetadata.templates[0];
      setForm(buildTemplateForm(template, watchlist));
    },
    [metadata.templates, watchlist],
  );

  const openCreateModal = useCallback(() => {
    setForm(buildTemplateForm(selectedTemplate, watchlist));
    setShowForm(true);
    setError(null);
  }, [selectedTemplate, watchlist]);

  const closeCreateModal = useCallback(() => {
    setShowForm(false);
    setError(null);
  }, []);

  const handleSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      const payload = normalizeAlertRulePayload(form);
      if (!payload.name || !payload.threshold_value) {
        setError("请填写规则名称和阈值。");
        return;
      }
      if (payload.source === "watchlist" && !payload.symbol) {
        setError("追踪数据规则需要选择标的。");
        return;
      }

      setSaving(true);
      try {
        const created = await createAlertRule(payload);
        setRules((current) => [created, ...current]);
        setForm(buildTemplateForm(selectedTemplate, watchlist));
        setShowForm(false);
        setError(null);
      } catch (saveError) {
        setError(saveError instanceof Error ? saveError.message : "新增提醒规则失败。");
      } finally {
        setSaving(false);
      }
    },
    [form, selectedTemplate, watchlist],
  );

  const handleToggle = useCallback(async (rule: AlertRule) => {
    try {
      const updated = await updateAlertRule(rule.id, { enabled: !rule.enabled });
      setRules((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      setError(null);
    } catch (updateError) {
      setError(updateError instanceof Error ? updateError.message : "更新规则失败。");
    }
  }, []);

  const handleDelete = useCallback(async (ruleId: number) => {
    try {
      await deleteAlertRule(ruleId);
      setRules((current) => current.filter((rule) => rule.id !== ruleId));
      setError(null);
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "删除规则失败。");
    }
  }, []);

  const handleResetCounters = useCallback(async () => {
    try {
      const nextRules = await resetAlertRuleCounters();
      setRules(nextRules);
      setError(null);
    } catch (resetError) {
      setError(resetError instanceof Error ? resetError.message : "重置统计失败。");
    }
  }, []);

  const updateForm = useCallback((updater: (current: AlertRuleFormState) => AlertRuleFormState) => {
    setForm((current) => updater(current));
  }, []);

  const updateSymbol = useCallback(
    (symbol: string) => {
      setForm((current) => ({
        ...current,
        symbol,
        name: buildRuleName(selectedTemplate, symbol),
      }));
    },
    [selectedTemplate],
  );

  return {
    rules: sortedRules,
    watchlist,
    metadata,
    form,
    showForm,
    loading,
    saving,
    error,
    summary,
    selectedTemplate,
    loadPage,
    openCreateModal,
    closeCreateModal,
    updateTemplate,
    updateForm,
    updateSymbol,
    handleSubmit,
    handleToggle,
    handleDelete,
    handleResetCounters,
  };
}
