import { type ReactNode } from "react";

import type { IBKRProfileName, IBKRSettings, NotificationSettings } from "../../shared/api";
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

function ibkrSourceLabel(source: IBKRSettings["source"]) {
  return source === "database" ? "数据库" : "环境变量";
}

function modeLabel(mode: IBKRSettings["mode"]) {
  return mode === "mock" ? "Mock 数据" : "IBKR TWS";
}

function profileLabel(profile: IBKRProfileName) {
  return profile === "paper" ? "模拟 TWS" : "真实 TWS";
}

function profileDescription(profile: IBKRProfileName) {
  return profile === "paper"
    ? "建议先用 Paper 环境验收；TWS Paper 默认 socket 端口是 7497。"
    : "只读读取真实账户数据；TWS 真实账户默认 socket 端口是 7496。";
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
          <p className="panel-note">{props.description}</p>
        </div>
        {props.actions ? <div className="settings-actions settings-actions-top">{props.actions}</div> : null}
      </div>
      {props.children}
    </article>
  );
}

function ProfileDetails(props: {
  profileState: SettingsProfileState;
  onTest: (profile: IBKRProfileName) => void;
}) {
  const { profileState } = props;

  function updateField<Key extends keyof SettingsProfileState["profile"]>(key: Key, value: SettingsProfileState["profile"][Key]) {
    profileState.onChange({ ...profileState.profile, [key]: value });
  }

  return (
    <details
      className={`settings-details${profileState.active ? " settings-details-active" : ""}`}
      open={profileState.active}
    >
      <summary>
        <span>
          <strong>{profileLabel(profileState.profileName)}</strong>
          <span>{profileDescription(profileState.profileName)}</span>
        </span>
        <SettingsBadge tone={profileState.active ? "positive" : "default"}>
          {profileState.active ? "当前激活" : "备用配置"}
        </SettingsBadge>
      </summary>

      <div className="settings-details-body">
        <div className="settings-field-grid">
          <label>
            <span>主机</span>
            <input value={profileState.profile.host} onChange={(event) => updateField("host", event.target.value)} />
          </label>

          <label>
            <span>端口</span>
            <input
              type="number"
              min={1}
              max={65535}
              value={profileState.profile.port}
              onChange={(event) => updateField("port", event.currentTarget.valueAsNumber)}
            />
          </label>

          <label>
            <span>客户端 ID</span>
            <input
              type="number"
              min={0}
              value={profileState.profile.client_id}
              onChange={(event) => updateField("client_id", event.currentTarget.valueAsNumber)}
            />
          </label>

          <label>
            <span>账户 ID</span>
            <input
              value={profileState.profile.account_id}
              onChange={(event) => updateField("account_id", event.target.value)}
              placeholder="留空则自动使用 TWS 返回的第一个账户"
            />
          </label>
        </div>

        <div className="settings-actions">
          <button
            type="button"
            className="button button-secondary"
            onClick={() => props.onTest(profileState.profileName)}
            disabled={profileState.testing}
          >
            {profileState.testing ? "测试中..." : `测试${profileLabel(profileState.profileName)}连接`}
          </button>
        </div>
      </div>
    </details>
  );
}

export function IBKRSettingsSection(props: { state: IBKRSettingsSectionState }) {
  const { state } = props;

  return (
    <form className="settings-stack" onSubmit={state.handleSubmit}>
      <SettingsPanel
        title="交易数据源"
        description="选择快照读取方式和当前激活的 TWS 环境。保存后刷新快照，前台数据会使用新的连接配置。"
        actions={
          <button type="button" className="button button-secondary" onClick={() => void state.reload()}>
            重新读取
          </button>
        }
        meta={<SettingsBadge tone={state.ibkrMode === "mock" ? "warning" : "positive"}>{modeLabel(state.ibkrMode)}</SettingsBadge>}
      >
        {state.error ? <div className="banner banner-error">{state.error}</div> : null}
        {state.success ? <div className="banner banner-success">{state.success}</div> : null}
        {state.loading ? <div className="table-empty">正在加载 IBKR 设置...</div> : null}

        {!state.loading ? (
          <>
            <div className="settings-meta-row">
              <SettingsBadge>配置来源：{state.ibkrSettings ? ibkrSourceLabel(state.ibkrSettings.source) : "--"}</SettingsBadge>
              <SettingsBadge tone={state.activeProfile === "paper" ? "positive" : "warning"}>
                激活环境：{profileLabel(state.activeProfile)}
              </SettingsBadge>
            </div>

            <div className="settings-field-grid">
              <label>
                <span>数据模式</span>
                <select
                  value={state.ibkrMode}
                  onChange={(event) => state.setIbkrMode(event.target.value as IBKRSettings["mode"])}
                >
                  <option value="mock">Mock 数据，不连接 TWS</option>
                  <option value="ibkr">IBKR TWS，只读连接</option>
                </select>
              </label>

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

            <div className="subtle-callout">
              真实账户 profile 也只会使用只读 API；但它读取的是你的真实账户数据。切换环境后，请刷新总览或资产页确认数据来源。
            </div>
          </>
        ) : null}
      </SettingsPanel>

      {!state.loading ? (
        <SettingsPanel
          title="连接配置"
          description="当前激活的环境默认展开，备用环境可按需展开编辑。每个环境都可以单独测试连接。"
          meta={<SettingsBadge>当前激活：{profileLabel(state.activeProfile)}</SettingsBadge>}
        >
          <div className="settings-details-stack">
            <ProfileDetails profileState={state.activeProfileState} onTest={(profile) => void state.handleTest(profile)} />
            <ProfileDetails profileState={state.standbyProfileState} onTest={(profile) => void state.handleTest(profile)} />
          </div>

          <div className="settings-actions">
            <button type="submit" className="button" disabled={state.saving}>
              {state.saving ? "保存中..." : "保存 IBKR 设置"}
            </button>
          </div>
        </SettingsPanel>
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
        description="后端按这个间隔自动刷新最近快照；页面只读取最近成功结果，失败时不会清空旧数据。"
        actions={
          <button type="button" className="button button-secondary" onClick={() => void state.reload()}>
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
              <SettingsBadge>执行位置：后端后台任务</SettingsBadge>
              <SettingsBadge tone="warning">完整快照刷新会请求 IBKR</SettingsBadge>
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

            <div className="subtle-callout">
              默认 5 分钟更稳，不会频繁请求 IBKR；如果以后拆出轻量行情刷新，再考虑更短间隔。
            </div>

            <div className="settings-actions">
              <button type="submit" className="button" disabled={state.saving}>
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
        description="Bot token 留空时不会覆盖已保存值；保存后建议发送测试消息验证整条提醒链路。"
        actions={
          <button type="button" className="button button-secondary" onClick={() => void state.reload()}>
            重新读取
          </button>
        }
        meta={
          <SettingsBadge tone={state.notificationSettings?.telegram_enabled ? "positive" : "warning"}>
            {state.notificationSettings?.telegram_enabled ? "Telegram 已就绪" : "Telegram 待配置"}
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
                Bot Token：{state.notificationSettings?.telegram_bot_token_configured ? "已保存" : "未保存"}
              </SettingsBadge>
              <SettingsBadge>掩码：{state.notificationSettings?.telegram_bot_token_masked ?? "--"}</SettingsBadge>
            </div>

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

            <div className="subtle-callout">真实 token 不会回传前端，只显示掩码。提醒消息会发送到当前 Chat ID。</div>

            <div className="settings-actions">
              <button type="submit" className="button" disabled={state.saving}>
                {state.saving ? "保存中..." : "保存通知设置"}
              </button>
              <button
                type="button"
                className="button button-secondary"
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
