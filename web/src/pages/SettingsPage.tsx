import { FormEvent, useEffect, useState } from "react";

import {
  NotificationSettings,
  getNotificationSettings,
  testNotificationSettings,
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

export function SettingsPage() {
  const [settings, setSettings] = useState<NotificationSettings | null>(null);
  const [telegramBotToken, setTelegramBotToken] = useState("");
  const [telegramChatId, setTelegramChatId] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    void loadSettings();
  }, []);

  async function loadSettings() {
    setLoading(true);
    try {
      const nextSettings = await getNotificationSettings();
      setSettings(nextSettings);
      setTelegramBotToken("");
      setTelegramChatId(nextSettings.telegram_chat_id);
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load notification settings.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setSuccessMessage(null);

    try {
      const payload: { telegram_bot_token?: string; telegram_chat_id?: string } = {
        telegram_chat_id: telegramChatId,
      };

      if (telegramBotToken.trim() !== "") {
        payload.telegram_bot_token = telegramBotToken.trim();
      }

      const nextSettings = await updateNotificationSettings(payload);
      setSettings(nextSettings);
      setTelegramBotToken("");
      setTelegramChatId(nextSettings.telegram_chat_id);
      setError(null);
      setSuccessMessage("Telegram 配置已保存到后端。");
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Failed to save notification settings.");
    } finally {
      setSaving(false);
    }
  }

  async function handleTestSend() {
    setTesting(true);
    setSuccessMessage(null);

    try {
      const result = await testNotificationSettings();
      if (result.success) {
        setSuccessMessage(result.detail);
        setError(null);
      } else {
        setError(result.detail);
      }
    } catch (testError) {
      setError(testError instanceof Error ? testError.message : "Failed to send test message.");
    } finally {
      setTesting(false);
    }
  }

  return (
    <section>
      <header className="page-header">
        <p>配置入口尽量少而清楚，确认当前来源、已保存状态和测试结果即可，不暴露后端真实密钥。</p>
      </header>

      <div className="panel-grid">
        <StatCard
          label="Telegram 状态"
          value={settings?.telegram_enabled ? "已就绪" : "待配置"}
          note={`当前来源：${settings ? sourceLabel(settings.source) : "--"}`}
          tone={settings?.telegram_enabled ? "positive" : "warning"}
        />
        <StatCard
          label="Bot Token"
          value={settings?.telegram_bot_token_configured ? "已保存" : "未保存"}
          note={`掩码：${settings?.telegram_bot_token_masked ?? "--"}`}
        />
        <StatCard
          label="Chat ID"
          value={settings?.telegram_chat_id || "--"}
          note="提醒消息会发送到这个目标。"
        />
      </div>

      <PageSection
        title="Telegram 配置"
        description="Bot token 留空时不会覆盖已保存值；建议每次改完后发一条测试消息验证整条链路。"
        actions={
          <button type="button" className="button button-secondary" onClick={() => void loadSettings()}>
            重新读取
          </button>
        }
      >
        {error ? <div className="banner banner-error">{error}</div> : null}
        {successMessage ? <div className="banner banner-success">{successMessage}</div> : null}
        {loading ? <div className="table-empty">正在加载设置...</div> : null}

        {!loading ? (
          <article className="panel">
            <form className="form-grid form-grid-2" onSubmit={handleSubmit}>
              <label>
                <span>Telegram Bot Token</span>
                <input
                  type="password"
                  value={telegramBotToken}
                  onChange={(event) => setTelegramBotToken(event.target.value)}
                  placeholder={settings?.telegram_bot_token_configured ? "留空则保持当前 token" : "123456:ABCDEF..."}
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
                当前配置来源：{settings ? sourceLabel(settings.source) : "--"}。真实 token 不会回传前端，只显示掩码。
              </div>

              <div className="actions-row form-span-2">
                <button type="submit" className="button" disabled={saving}>
                  {saving ? "保存中..." : "保存设置"}
                </button>
                <button
                  type="button"
                  className="button button-secondary"
                  onClick={() => void handleTestSend()}
                  disabled={testing}
                >
                  {testing ? "测试中..." : "发送测试消息"}
                </button>
              </div>
            </form>
          </article>
        ) : null}
      </PageSection>
    </section>
  );
}
