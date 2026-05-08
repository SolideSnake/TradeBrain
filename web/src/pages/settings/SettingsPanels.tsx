import { type ReactNode } from "react";

import type { IBKRProfileName, NotificationSettings } from "../../shared/api";
import type {
  IBKRSettingsSectionState,
  NotificationSettingsSectionState,
  SettingsProfileState,
  SnapshotRefreshSettingsSectionState,
} from "./useSettingsSections";

const refreshIntervalOptions = [5, 15, 30, 60];

function sourceLabel(source: NotificationSettings["source"]) {
  switch (source) {
    case "database":
      return "数据库";
    case "environment":
      return "环境变量";
    case "none":
    default:
      return "未配置";
  }
}

function profileLabel(profile: IBKRProfileName) {
  return profile === "paper" ? "模拟 TWS" : "真实 TWS";
}

function formatRefreshInterval(seconds: number) {
  return `${Math.round(seconds / 60)} 分钟`;
}

export function SettingsBadge(props: {
  children: ReactNode;
  tone?: "default" | "positive" | "warning" | "danger";
}) {
  return <span className={`settings-badge settings-badge-${props.tone ?? "default"}`}>{props.children}</span>;
}

export function SettingsPanel(props: {
  title: string;
  description: ReactNode;
  actions?: ReactNode;
  meta?: ReactNode;
  children: ReactNode;
}) {
  return (
    <article className="settings-panel">
      <div className="settings-panel-header">
        <div>
          <div className="settings-title-row">
            <h3>{props.title}</h3>
            {props.meta}
          </div>
          {props.description ? <p className="panel-note">{props.description}</p> : null}
        </div>
        {props.actions ? <div className="settings-actions settings-actions-top">{props.actions}</div> : null}
      </div>
      {props.children}
    </article>
  );
}

function IBKRProfileSection(props: {
  profileState: SettingsProfileState;
  onTest: (profile: IBKRProfileName) => void;
}) {
  const { profileState } = props;

  function updateField<Key extends keyof SettingsProfileState["profile"]>(key: Key, value: SettingsProfileState["profile"][Key]) {
    profileState.onChange({ ...profileState.profile, [key]: value });
  }

  return (
    <section className={`settings-profile-section${profileState.active ? " settings-profile-section-active" : ""}`}>
      <div className="settings-profile-header">
        <div>
          <div className="settings-title-row">
            <h4>{profileLabel(profileState.profileName)}</h4>
            {profileState.active ? <SettingsBadge tone="positive">当前激活</SettingsBadge> : null}
          </div>
        </div>
      </div>

      <div className="settings-field-grid">
        <label>
          <span>Host</span>
          <input value={profileState.profile.host} onChange={(event) => updateField("host", event.target.value)} />
        </label>

        <label>
          <span>Port</span>
          <input
            type="number"
            min={1}
            max={65535}
            value={profileState.profile.port}
            onChange={(event) => updateField("port", event.currentTarget.valueAsNumber)}
          />
        </label>

        <label>
          <span>Client ID</span>
          <input
            type="number"
            min={0}
            value={profileState.profile.client_id}
            onChange={(event) => updateField("client_id", event.currentTarget.valueAsNumber)}
          />
        </label>

        <label>
          <span>Account ID</span>
          <input
            value={profileState.profile.account_id}
            onChange={(event) => updateField("account_id", event.target.value)}
            placeholder="留空则自动使用 TWS 返回的第一个账户"
          />
        </label>
      </div>

      <div className="settings-profile-actions">
        <button
          type="button"
          className="button button-ghost"
          onClick={() => props.onTest(profileState.profileName)}
          disabled={profileState.testing}
        >
          {profileState.testing ? "测试中..." : `测试${profileLabel(profileState.profileName)}连接`}
        </button>
      </div>
    </section>
  );
}

export function IBKRSettingsSection(props: { state: IBKRSettingsSectionState }) {
  const { state } = props;
  const paperProfileState = state.activeProfile === "paper" ? state.activeProfileState : state.standbyProfileState;
  const realProfileState = state.activeProfile === "real" ? state.activeProfileState : state.standbyProfileState;

  return (
    <form className="settings-flat-page settings-ibkr-flat" onSubmit={state.handleSubmit}>
      <div className="settings-page-controls">
        <div>
          <div className="settings-title-row">
            <h3>IBKR TWS 连接</h3>
            <SettingsBadge tone={state.activeProfile === "paper" ? "positive" : "warning"}>
              当前环境：{profileLabel(state.activeProfile)}
            </SettingsBadge>
          </div>
        </div>

        <div className="settings-actions settings-actions-top">
          <button type="button" className="button button-tertiary" onClick={() => void state.reload()}>
            重新读取
          </button>
        </div>
      </div>

      {state.error ? <div className="banner banner-error">{state.error}</div> : null}
      {state.success ? <div className="banner banner-success">{state.success}</div> : null}
      {state.loading ? <div className="table-empty">正在加载 IBKR 设置...</div> : null}

      {!state.loading ? (
        <>
          <div className="settings-control-meta">
            <label>
              <span>当前激活环境</span>
              <select
                value={state.activeProfile}
                onChange={(event) => state.setActiveProfile(event.target.value as IBKRProfileName)}
              >
                <option value="paper">模拟 TWS Paper，默认 7497</option>
                <option value="real">真实 TWS，默认 7496</option>
              </select>
            </label>
          </div>

          <div className="settings-profile-grid">
            <IBKRProfileSection profileState={paperProfileState} onTest={(profile) => void state.handleTest(profile)} />
            <IBKRProfileSection profileState={realProfileState} onTest={(profile) => void state.handleTest(profile)} />
          </div>

          <div className="settings-save-row">
            <button type="submit" className="button button-primary" disabled={state.saving}>
              {state.saving ? "保存中..." : "保存 IBKR 设置"}
            </button>
          </div>
        </>
      ) : null}
    </form>
  );
}

export function SnapshotRefreshSettingsSection(props: { state: SnapshotRefreshSettingsSectionState }) {
  const { state } = props;

  return (
    <form onSubmit={state.handleSubmit}>
      <SettingsPanel
        title="快照自动刷新"
        description={null}
        actions={
          <button type="button" className="button button-tertiary" onClick={() => void state.reload()}>
            重新读取
          </button>
        }
        meta={
          <SettingsBadge tone={state.snapshotRefreshEnabled ? "positive" : "warning"}>
            {state.snapshotRefreshEnabled ? "自动刷新已开启" : "自动刷新已关闭"}
          </SettingsBadge>
        }
      >
        {state.error ? <div className="banner banner-error">{state.error}</div> : null}
        {state.success ? <div className="banner banner-success">{state.success}</div> : null}
        {state.loading ? <div className="table-empty">正在加载快照刷新设置...</div> : null}

        {!state.loading ? (
          <>
            <div className="settings-meta-row">
              <SettingsBadge>
                当前间隔：
                {state.snapshotRefreshSettings
                  ? formatRefreshInterval(state.snapshotRefreshSettings.interval_seconds)
                  : "--"}
              </SettingsBadge>
            </div>

            <div className="settings-field-grid">
              <label>
                <span>自动刷新</span>
                <select
                  value={state.snapshotRefreshEnabled ? "enabled" : "disabled"}
                  onChange={(event) => state.setSnapshotRefreshEnabled(event.target.value === "enabled")}
                >
                  <option value="enabled">开启</option>
                  <option value="disabled">关闭</option>
                </select>
              </label>

              <label>
                <span>刷新间隔</span>
                <select
                  value={state.snapshotRefreshIntervalMinutes}
                  onChange={(event) => state.setSnapshotRefreshIntervalMinutes(Number(event.target.value))}
                  disabled={!state.snapshotRefreshEnabled}
                >
                  {refreshIntervalOptions.map((minutes) => (
                    <option key={minutes} value={minutes}>
                      {minutes} 分钟
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="settings-actions">
              <button type="submit" className="button button-primary" disabled={state.saving}>
                {state.saving ? "保存中..." : "保存刷新设置"}
              </button>
            </div>
          </>
        ) : null}
      </SettingsPanel>
    </form>
  );
}

export function NotificationSettingsSection(props: { state: NotificationSettingsSectionState }) {
  const { state } = props;

  return (
    <form onSubmit={state.handleSubmit}>
      <SettingsPanel
        title="通知设置"
        description={null}
        actions={
          <button type="button" className="button button-tertiary" onClick={() => void state.reload()}>
            重新读取
          </button>
        }
        meta={
          <SettingsBadge
            tone={
              state.notificationSettings?.telegram_enabled || state.notificationSettings?.feishu_enabled
                ? "positive"
                : "warning"
            }
          >
            {state.notificationSettings?.telegram_enabled || state.notificationSettings?.feishu_enabled
              ? "通知通道已就绪"
              : "通知通道待配置"}
          </SettingsBadge>
        }
      >
        {state.error ? <div className="banner banner-error">{state.error}</div> : null}
        {state.success ? <div className="banner banner-success">{state.success}</div> : null}
        {state.loading ? <div className="table-empty">正在加载通知设置...</div> : null}

        {!state.loading ? (
          <>
            <div className="settings-meta-row">
              <SettingsBadge>
                配置来源：{state.notificationSettings ? sourceLabel(state.notificationSettings.source) : "--"}
              </SettingsBadge>
              <SettingsBadge tone={state.notificationSettings?.telegram_bot_token_configured ? "positive" : "warning"}>
                Telegram：{state.notificationSettings?.telegram_enabled ? "已就绪" : "未就绪"}
              </SettingsBadge>
              <SettingsBadge tone={state.notificationSettings?.feishu_webhook_url_configured ? "positive" : "warning"}>
                飞书：{state.notificationSettings?.feishu_enabled ? "已就绪" : "未就绪"}
              </SettingsBadge>
            </div>

            <h4 className="settings-subtitle">Telegram</h4>
            <div className="settings-field-grid">
              <label>
                <span>Telegram Bot Token</span>
                <input
                  type="password"
                  value={state.telegramBotToken}
                  onChange={(event) => state.setTelegramBotToken(event.target.value)}
                  placeholder={
                    state.notificationSettings?.telegram_bot_token_configured
                      ? "留空则保持当前 token"
                      : "123456:ABCDEF..."
                  }
                />
              </label>

              <label>
                <span>Telegram Chat ID</span>
                <input
                  value={state.telegramChatId}
                  onChange={(event) => state.setTelegramChatId(event.target.value)}
                  placeholder="123456789"
                />
              </label>
            </div>

            <div className="settings-meta-row">
              <SettingsBadge>Token 掩码：{state.notificationSettings?.telegram_bot_token_masked ?? "--"}</SettingsBadge>
            </div>

            <h4 className="settings-subtitle">飞书自定义机器人</h4>
            <div className="settings-field-grid">
              <label>
                <span>飞书 Webhook URL</span>
                <input
                  type="password"
                  value={state.feishuWebhookUrl}
                  onChange={(event) => state.setFeishuWebhookUrl(event.target.value)}
                  placeholder={
                    state.notificationSettings?.feishu_webhook_url_configured
                      ? "留空则保持当前 Webhook"
                      : "https://open.feishu.cn/open-apis/bot/v2/hook/..."
                  }
                />
              </label>

              <label>
                <span>飞书签名 Secret（可选）</span>
                <input
                  type="password"
                  value={state.feishuSecret}
                  onChange={(event) => state.setFeishuSecret(event.target.value)}
                  placeholder={state.notificationSettings?.feishu_secret_configured ? "留空则保持当前 Secret" : "未开启签名可留空"}
                />
              </label>
            </div>

            <div className="settings-meta-row">
              <SettingsBadge>Webhook 掩码：{state.notificationSettings?.feishu_webhook_url_masked ?? "--"}</SettingsBadge>
              <SettingsBadge>
                签名 Secret：{state.notificationSettings?.feishu_secret_configured ? "已保存" : "未保存"}
              </SettingsBadge>
            </div>

            <div className="settings-actions">
              <button type="submit" className="button button-primary" disabled={state.saving}>
                {state.saving ? "保存中..." : "保存通知设置"}
              </button>
              <button
                type="button"
                className="button button-ghost"
                onClick={() => void state.handleTestSend()}
                disabled={state.testing}
              >
                {state.testing ? "测试中..." : "发送测试消息"}
              </button>
            </div>
          </>
        ) : null}
      </SettingsPanel>
    </form>
  );
}
