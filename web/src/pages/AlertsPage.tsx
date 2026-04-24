import { AlertRuleDialog } from "./alerts/AlertRuleDialog";
import { AlertRulesSummaryBar, AlertRulesTable } from "./alerts/AlertRulesTable";
import { useAlertsPageState } from "./alerts/useAlertsPageState";

export function AlertsPage() {
  const state = useAlertsPageState();

  return (
    <section className="alerts-page">
      <AlertRulesSummaryBar
        summary={state.summary}
        onResetCounters={() => void state.handleResetCounters()}
        onCreateRule={state.openCreateModal}
      />

      {state.error ? <div className="banner banner-error">{state.error}</div> : null}

      <AlertRulesTable
        rules={state.rules}
        metadata={state.metadata}
        loading={state.loading}
        onToggle={(rule) => void state.handleToggle(rule)}
        onDelete={(ruleId) => void state.handleDelete(ruleId)}
      />

      {state.showForm ? (
        <AlertRuleDialog
          form={state.form}
          metadata={state.metadata}
          watchlist={state.watchlist}
          saving={state.saving}
          selectedTemplate={state.selectedTemplate}
          onClose={state.closeCreateModal}
          onSubmit={(event) => void state.handleSubmit(event)}
          onTemplateChange={state.updateTemplate}
          onNameChange={(name) => state.updateForm((current) => ({ ...current, name }))}
          onSymbolChange={state.updateSymbol}
          onThresholdChange={(threshold_value) => state.updateForm((current) => ({ ...current, threshold_value }))}
          onCooldownChange={(cooldown_seconds) => state.updateForm((current) => ({ ...current, cooldown_seconds }))}
          onEdgeOnlyChange={(edge_only) => state.updateForm((current) => ({ ...current, edge_only }))}
        />
      ) : null}
    </section>
  );
}
