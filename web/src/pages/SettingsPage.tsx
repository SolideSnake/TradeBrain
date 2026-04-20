import { type FormEvent, type ReactNode, useEffect, useState } from "react";

import {
  type IBKRConnectionProfile,
  type IBKRProfileName,
  type IBKRSettings,
  type NotificationSettings,
  getIBKRSettings,
  getNotificationSettings,
  testIBKRConnection,
  testNotificationSettings,
  updateIBKRSettings,
  updateNotificationSettings,
} from "../shared/api";

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

function defaultIBKRProfile(profile: IBKRProfileName): IBKRConnectionProfile {
  return {
    host: "127.0.0.1",
    port: profile === "real" ? 7496 : 7497,
    client_id: profile === "real" ? 1 : 2,
    account_id: "",
  };
}

function SettingsBadge(props: { children: ReactNode; tone?: "default" | "positive" | "warning" | "danger" }) {
  return <span className={`settings-badge settings-badge-${props.tone ?? "default"}`}>{props.children}</span>;
}

function SettingsPanel(props: {
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
  profileName: IBKRProfileName;
  profile: IBKRConnectionProfile;
  active: boolean;
  onChange: (nextProfile: IBKRConnectionProfile) => void;
  onTest: () => void;
  testing: boolean;
}) {
  function updateField<Key extends keyof IBKRConnectionProfile>(
    key: Key,
    value: IBKRConnectionProfile[Key],
  ) {
    props.onChange({ ...props.profile, [key]: value });
  }

  return (
    <details className={`settings-details${props.active ? " settings-details-active" : ""}`} open={props.active}>
      <summary>
        <span>
          <strong>{profileLabel(props.profileName)}</strong>
          <span>{profileDescription(props.profileName)}</span>
        </span>
        <SettingsBadge tone={props.active ? "positive" : "default"}>
          {props.active ? "当前激活" : "备用配置"}
        </SettingsBadge>
      </summary>

      <div className="settings-details-body">
        <div className="settings-field-grid">
          <label>
            <span>主机</span>
            <input value={props.profile.host} onChange={(event) => updateField("host", event.target.value)} />
          </label>

          <label>
            <span>端口</span>
            <input
              type="number"
              min={1}
              max={65535}
              value={props.profile.port}
              onChange={(event) => updateField("port", event.currentTarget.valueAsNumber)}
            />
          </label>

          <label>
            <span>客户端 ID</span>
            <input
              type="number"
              min={0}
              value={props.profile.client_id}
              onChange={(event) => updateField("client_id", event.currentTarget.valueAsNumber)}
            />
          </label>

          <label>
            <span>账户 ID</span>
            <input
              value={props.profile.account_id}
              onChange={(event) => updateField("account_id", event.target.value)}
              placeholder="留空则自动使用 TWS 返回的第一个账户"
            />
          </label>
        </div>

        <div className="settings-actions">
          <button type="button" className="button button-secondary" onClick={props.onTest} disabled={props.testing}>
            {props.testing ? "测试中..." : `测试${profileLabel(props.profileName)}连接`}
          </button>
        </div>
      </div>
    </details>
  );
}

export function SettingsPage() {
  const [notificationSettings, setNotificationSettings] = useState<NotificationSettings | null>(null);
  const [telegramBotToken, setTelegramBotToken] = useState("");
  const [telegramChatId, setTelegramChatId] = useState("");
  const [notificationLoading, setNotificationLoading] = useState(true);
  const [notificationSaving, setNotificationSaving] = useState(false);
  const [notificationTesting, setNotificationTesting] = useState(false);
  const [notificationError, setNotificationError] = useState<string | null>(null);
  const [notificationSuccess, setNotificationSuccess] = useState<string | null>(null);

  const [ibkrSettings, setIbkrSettings] = useState<IBKRSettings | null>(null);
  const [ibkrMode, setIbkrMode] = useState<IBKRSettings["mode"]>("mock");
  const [activeProfile, setActiveProfile] = useState<IBKRProfileName>("paper");
  const [realProfile, setRealProfile] = useState<IBKRConnectionProfile>(defaultIBKRProfile("real"));
  const [paperProfile, setPaperProfile] = useState<IBKRConnectionProfile>(defaultIBKRProfile("paper"));
  const [ibkrLoading, setIbkrLoading] = useState(true);
  const [ibkrSaving, setIbkrSaving] = useState(false);
  const [testingProfile, setTestingProfile] = useState<IBKRProfileName | null>(null);
  const [ibkrError, setIbkrError] = useState<string | null>(null);
  const [ibkrSuccess, setIbkrSuccess] = useState<string | null>(null);

  useEffect(() => {
    void loadNotificationSettings();
    void loadIBKRSettings();
  }, []);

  async function loadNotificationSettings() {
    setNotificationLoading(true);
    try {
      const nextSettings = await getNotificationSettings();
      setNotificationSettings(nextSettings);
      setTelegramBotToken("");
      setTelegramChatId(nextSettings.telegram_chat_id);
      setNotificationError(null);
    } catch (loadError) {
      setNotificationError(loadError instanceof Error ? loadError.message : "Failed to load notification settings.");
    } finally {
      setNotificationLoading(false);
    }
  }

  async function loadIBKRSettings() {
    setIbkrLoading(true);
    try {
      const nextSettings = await getIBKRSettings();
      applyIBKRSettings(nextSettings);
      setIbkrError(null);
    } catch (loadError) {
      setIbkrError(loadError instanceof Error ? loadError.message : "Failed to load IBKR settings.");
    } finally {
      setIbkrLoading(false);
    }
  }

  function applyIBKRSettings(nextSettings: IBKRSettings) {
    setIbkrSettings(nextSettings);
    setIbkrMode(nextSettings.mode);
    setActiveProfile(nextSettings.active_profile);
    setRealProfile(nextSettings.real);
    setPaperProfile(nextSettings.paper);
  }

  async function handleNotificationSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setNotificationSaving(true);
    setNotificationSuccess(null);

    try {
      const payload: { telegram_bot_token?: string; telegram_chat_id?: string } = {
        telegram_chat_id: telegramChatId,
      };

      if (telegramBotToken.trim() !== "") {
        payload.telegram_bot_token = telegramBotToken.trim();
      }

      const nextSettings = await updateNotificationSettings(payload);
      setNotificationSettings(nextSettings);
      setTelegramBotToken("");
      setTelegramChatId(nextSettings.telegram_chat_id);
      setNotificationError(null);
      setNotificationSuccess("Telegram 配置已保存到后端。");
    } catch (saveError) {
      setNotificationError(saveError instanceof Error ? saveError.message : "Failed to save notification settings.");
    } finally {
      setNotificationSaving(false);
    }
  }

  async function handleIBKRSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIbkrSaving(true);
    setIbkrSuccess(null);

    try {
      const nextSettings = await updateIBKRSettings({
        mode: ibkrMode,
        active_profile: activeProfile,
        real: realProfile,
        paper: paperProfile,
      });
      applyIBKRSettings(nextSettings);
      setIbkrError(null);
      setIbkrSuccess("IBKR 连接配置已保存。刷新快照后会使用当前激活环境。");
    } catch (saveError) {
      setIbkrError(saveError instanceof Error ? saveError.message : "Failed to save IBKR settings.");
    } finally {
      setIbkrSaving(false);
    }
  }

  async function handleNotificationTestSend() {
    setNotificationTesting(true);
    setNotificationSuccess(null);

    try {
      const result = await testNotificationSettings();
      if (result.success) {
        setNotificationSuccess(result.detail);
        setNotificationError(null);
      } else {
        setNotificationError(result.detail);
      }
    } catch (testError) {
      setNotificationError(testError instanceof Error ? testError.message : "Failed to send test message.");
    } finally {
      setNotificationTesting(false);
    }
  }

  async function handleIBKRTest(profile: IBKRProfileName) {
    setTestingProfile(profile);
    setIbkrSuccess(null);

    try {
      const result = await testIBKRConnection(profile);
      if (result.success) {
        setIbkrSuccess(result.detail);
        setIbkrError(null);
      } else {
        setIbkrError(result.detail);
      }
    } catch (testError) {
      setIbkrError(testError instanceof Error ? testError.message : "Failed to test IBKR connection.");
    } finally {
      setTestingProfile(null);
    }
  }

  const activeProfileProps =
    activeProfile === "paper"
      ? {
          active: {
            profileName: "paper" as const,
            profile: paperProfile,
            onChange: setPaperProfile,
            testing: testingProfile === "paper",
          },
          standby: {
            profileName: "real" as const,
            profile: realProfile,
            onChange: setRealProfile,
            testing: testingProfile === "real",
          },
        }
      : {
          active: {
            profileName: "real" as const,
            profile: realProfile,
            onChange: setRealProfile,
            testing: testingProfile === "real",
          },
          standby: {
            profileName: "paper" as const,
            profile: paperProfile,
            onChange: setPaperProfile,
            testing: testingProfile === "paper",
          },
        };

  return (
    <section>
      <header className="page-header">
        <p>设置页用于查看当前配置、修改字段、测试链路和保存应用；状态只做辅助提示，不再做大面积摘要卡。</p>
      </header>

      <div className="settings-stack">
        <form className="settings-stack" onSubmit={handleIBKRSubmit}>
          <SettingsPanel
            title="交易数据源"
            description="选择快照读取方式和当前激活的 TWS 环境。保存后刷新快照，前台数据会使用新的连接配置。"
            actions={
              <button type="button" className="button button-secondary" onClick={() => void loadIBKRSettings()}>
                重新读取
              </button>
            }
            meta={
              <SettingsBadge tone={ibkrMode === "mock" ? "warning" : "positive"}>
                {modeLabel(ibkrMode)}
              </SettingsBadge>
            }
          >
            {ibkrError ? <div className="banner banner-error">{ibkrError}</div> : null}
            {ibkrSuccess ? <div className="banner banner-success">{ibkrSuccess}</div> : null}
            {ibkrLoading ? <div className="table-empty">正在加载 IBKR 设置...</div> : null}

            {!ibkrLoading ? (
              <>
                <div className="settings-meta-row">
                  <SettingsBadge>配置来源：{ibkrSettings ? ibkrSourceLabel(ibkrSettings.source) : "--"}</SettingsBadge>
                  <SettingsBadge tone={activeProfile === "paper" ? "positive" : "warning"}>
                    激活环境：{profileLabel(activeProfile)}
                  </SettingsBadge>
                </div>

                <div className="settings-field-grid">
                  <label>
                    <span>数据模式</span>
                    <select value={ibkrMode} onChange={(event) => setIbkrMode(event.target.value as IBKRSettings["mode"])}>
                      <option value="mock">Mock 数据，不连接 TWS</option>
                      <option value="ibkr">IBKR TWS，只读连接</option>
                    </select>
                  </label>

                  <label>
                    <span>当前激活环境</span>
                    <select value={activeProfile} onChange={(event) => setActiveProfile(event.target.value as IBKRProfileName)}>
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

          {!ibkrLoading ? (
            <SettingsPanel
              title="连接配置"
              description="当前激活的环境默认展开，备用环境可按需展开编辑。每个环境都可以单独测试连接。"
              meta={<SettingsBadge>当前激活：{profileLabel(activeProfile)}</SettingsBadge>}
            >
              <div className="settings-details-stack">
                <ProfileDetails
                  profileName={activeProfileProps.active.profileName}
                  profile={activeProfileProps.active.profile}
                  active
                  onChange={activeProfileProps.active.onChange}
                  onTest={() => void handleIBKRTest(activeProfileProps.active.profileName)}
                  testing={activeProfileProps.active.testing}
                />
                <ProfileDetails
                  profileName={activeProfileProps.standby.profileName}
                  profile={activeProfileProps.standby.profile}
                  active={false}
                  onChange={activeProfileProps.standby.onChange}
                  onTest={() => void handleIBKRTest(activeProfileProps.standby.profileName)}
                  testing={activeProfileProps.standby.testing}
                />
              </div>

              <div className="settings-actions">
                <button type="submit" className="button" disabled={ibkrSaving}>
                  {ibkrSaving ? "保存中..." : "保存 IBKR 设置"}
                </button>
              </div>
            </SettingsPanel>
          ) : null}
        </form>

        <form onSubmit={handleNotificationSubmit}>
          <SettingsPanel
            title="通知设置"
            description="Bot token 留空时不会覆盖已保存值；保存后建议发送测试消息验证整条提醒链路。"
            actions={
              <button type="button" className="button button-secondary" onClick={() => void loadNotificationSettings()}>
                重新读取
              </button>
            }
            meta={
              <SettingsBadge tone={notificationSettings?.telegram_enabled ? "positive" : "warning"}>
                {notificationSettings?.telegram_enabled ? "Telegram 已就绪" : "Telegram 待配置"}
              </SettingsBadge>
            }
          >
            {notificationError ? <div className="banner banner-error">{notificationError}</div> : null}
            {notificationSuccess ? <div className="banner banner-success">{notificationSuccess}</div> : null}
            {notificationLoading ? <div className="table-empty">正在加载通知设置...</div> : null}

            {!notificationLoading ? (
              <>
                <div className="settings-meta-row">
                  <SettingsBadge>
                    配置来源：{notificationSettings ? sourceLabel(notificationSettings.source) : "--"}
                  </SettingsBadge>
                  <SettingsBadge tone={notificationSettings?.telegram_bot_token_configured ? "positive" : "warning"}>
                    Bot Token：{notificationSettings?.telegram_bot_token_configured ? "已保存" : "未保存"}
                  </SettingsBadge>
                  <SettingsBadge>掩码：{notificationSettings?.telegram_bot_token_masked ?? "--"}</SettingsBadge>
                </div>

                <div className="settings-field-grid">
                  <label>
                    <span>Telegram Bot Token</span>
                    <input
                      type="password"
                      value={telegramBotToken}
                      onChange={(event) => setTelegramBotToken(event.target.value)}
                      placeholder={notificationSettings?.telegram_bot_token_configured ? "留空则保持当前 token" : "123456:ABCDEF..."}
                    />
                  </label>

                  <label>
                    <span>Telegram Chat ID</span>
                    <input
                      value={telegramChatId}
                      onChange={(event) => setTelegramChatId(event.target.value)}
                      placeholder="123456789"
                    />
                  </label>
                </div>

                <div className="subtle-callout">真实 token 不会回传前端，只显示掩码。提醒消息会发送到当前 Chat ID。</div>

                <div className="settings-actions">
                  <button type="submit" className="button" disabled={notificationSaving}>
                    {notificationSaving ? "保存中..." : "保存通知设置"}
                  </button>
                  <button
                    type="button"
                    className="button button-secondary"
                    onClick={() => void handleNotificationTestSend()}
                    disabled={notificationTesting}
                  >
                    {notificationTesting ? "测试中..." : "发送测试消息"}
                  </button>
                </div>
              </>
            ) : null}
          </SettingsPanel>
        </form>
      </div>
    </section>
  );
}
