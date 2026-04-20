import { FormEvent, useEffect, useState } from "react";

import {
  IBKRConnectionProfile,
  IBKRProfileName,
  IBKRSettings,
  NotificationSettings,
  getIBKRSettings,
  getNotificationSettings,
  testIBKRConnection,
  testNotificationSettings,
  updateIBKRSettings,
  updateNotificationSettings,
} from "../shared/api";
import { PageSection, StatCard } from "../shared/ui";

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

function defaultIBKRProfile(profile: IBKRProfileName): IBKRConnectionProfile {
  return {
    host: "127.0.0.1",
    port: profile === "real" ? 7496 : 7497,
    client_id: profile === "real" ? 1 : 2,
    account_id: "",
  };
}

function ProfileFields(props: {
  title: string;
  warning?: string;
  profile: IBKRConnectionProfile;
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
    <article className="panel">
      <div className="section-header section-header-compact">
        <div>
          <h3>{props.title}</h3>
          {props.warning ? <p className="panel-note">{props.warning}</p> : null}
        </div>
        <button type="button" className="button button-secondary" onClick={props.onTest} disabled={props.testing}>
          {props.testing ? "测试中..." : "测试连接"}
        </button>
      </div>

      <div className="form-grid form-grid-2">
        <label>
          <span>Host</span>
          <input value={props.profile.host} onChange={(event) => updateField("host", event.target.value)} />
        </label>

        <label>
          <span>Port</span>
          <input
            type="number"
            min={1}
            max={65535}
            value={props.profile.port}
            onChange={(event) => updateField("port", event.currentTarget.valueAsNumber)}
          />
        </label>

        <label>
          <span>Client ID</span>
          <input
            type="number"
            min={0}
            value={props.profile.client_id}
            onChange={(event) => updateField("client_id", event.currentTarget.valueAsNumber)}
          />
        </label>

        <label>
          <span>Account ID</span>
          <input
            value={props.profile.account_id}
            onChange={(event) => updateField("account_id", event.target.value)}
            placeholder="留空则自动使用 TWS 返回的第一个账户"
          />
        </label>
      </div>
    </article>
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

  return (
    <section>
      <header className="page-header">
        <p>配置入口尽量少而清楚，优先区分数据来源、当前激活环境和测试结果，避免真实账户与模拟账户混在一起。</p>
      </header>

      <PageSection
        title="IBKR 连接设置"
        description="同一时间只激活一个 TWS 环境；真实和模拟共用同一个只读 IBKR 接入模块。"
        actions={
          <button type="button" className="button button-secondary" onClick={() => void loadIBKRSettings()}>
            重新读取
          </button>
        }
      >
        {ibkrError ? <div className="banner banner-error">{ibkrError}</div> : null}
        {ibkrSuccess ? <div className="banner banner-success">{ibkrSuccess}</div> : null}
        {ibkrLoading ? <div className="table-empty">正在加载 IBKR 设置...</div> : null}

        {!ibkrLoading ? (
          <>
            <div className="panel-grid">
              <StatCard
                label="当前模式"
                value={ibkrMode === "mock" ? "Mock 数据" : "IBKR TWS"}
                note={`配置来源：${ibkrSettings ? ibkrSourceLabel(ibkrSettings.source) : "--"}`}
                tone={ibkrMode === "mock" ? "warning" : "positive"}
              />
              <StatCard
                label="激活环境"
                value={activeProfile === "paper" ? "模拟 TWS" : "真实 TWS"}
                note={activeProfile === "paper" ? "默认端口 7497" : "默认端口 7496，只读连接"}
                tone={activeProfile === "paper" ? "positive" : "warning"}
              />
              <StatCard label="真实账户端口" value={realProfile.port} note={`clientId ${realProfile.client_id}`} />
              <StatCard label="模拟账户端口" value={paperProfile.port} note={`clientId ${paperProfile.client_id}`} />
            </div>

            <form className="form-grid" onSubmit={handleIBKRSubmit}>
              <article className="panel">
                <div className="form-grid form-grid-2">
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

                <div className="subtle-callout overview-secondary">
                  真实账户 profile 也只会使用只读 API；但它读取的是你的真实账户数据。切换环境后，请刷新总览或账户页确认数据来源。
                </div>
              </article>

              <div className="panel-grid overview-secondary overview-grid-2">
                <ProfileFields
                  title="模拟 TWS Paper"
                  warning="建议先在这里验收；TWS Paper 默认 socket port 是 7497。"
                  profile={paperProfile}
                  onChange={setPaperProfile}
                  onTest={() => void handleIBKRTest("paper")}
                  testing={testingProfile === "paper"}
                />
                <ProfileFields
                  title="真实 TWS"
                  warning="只读读取真实账户数据；TWS 真实账户默认 socket port 是 7496。"
                  profile={realProfile}
                  onChange={setRealProfile}
                  onTest={() => void handleIBKRTest("real")}
                  testing={testingProfile === "real"}
                />
              </div>

              <div className="actions-row">
                <button type="submit" className="button" disabled={ibkrSaving}>
                  {ibkrSaving ? "保存中..." : "保存 IBKR 设置"}
                </button>
              </div>
            </form>
          </>
        ) : null}
      </PageSection>

      <PageSection
        title="Telegram 配置"
        description="Bot token 留空时不会覆盖已保存值；建议每次改完后发一条测试消息验证整条链路。"
        actions={
          <button type="button" className="button button-secondary" onClick={() => void loadNotificationSettings()}>
            重新读取
          </button>
        }
      >
        <div className="panel-grid">
          <StatCard
            label="Telegram 状态"
            value={notificationSettings?.telegram_enabled ? "已就绪" : "待配置"}
            note={`当前来源：${notificationSettings ? sourceLabel(notificationSettings.source) : "--"}`}
            tone={notificationSettings?.telegram_enabled ? "positive" : "warning"}
          />
          <StatCard
            label="Bot Token"
            value={notificationSettings?.telegram_bot_token_configured ? "已保存" : "未保存"}
            note={`掩码：${notificationSettings?.telegram_bot_token_masked ?? "--"}`}
          />
          <StatCard
            label="Chat ID"
            value={notificationSettings?.telegram_chat_id || "--"}
            note="提醒消息会发送到这个目标。"
          />
        </div>

        {notificationError ? <div className="banner banner-error">{notificationError}</div> : null}
        {notificationSuccess ? <div className="banner banner-success">{notificationSuccess}</div> : null}
        {notificationLoading ? <div className="table-empty">正在加载设置...</div> : null}

        {!notificationLoading ? (
          <article className="panel">
            <form className="form-grid form-grid-2" onSubmit={handleNotificationSubmit}>
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

              <div className="form-span-2 subtle-callout">
                当前配置来源：{notificationSettings ? sourceLabel(notificationSettings.source) : "--"}。
                真实 token 不会回传前端，只显示掩码。
              </div>

              <div className="actions-row form-span-2">
                <button type="submit" className="button" disabled={notificationSaving}>
                  {notificationSaving ? "保存中..." : "保存设置"}
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
            </form>
          </article>
        ) : null}
      </PageSection>
    </section>
  );
}
