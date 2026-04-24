import { type FormEvent, useCallback, useEffect, useState } from "react";

import {
  type IBKRConnectionProfile,
  type IBKRProfileName,
  type IBKRSettings,
  type NotificationSettings,
  type SnapshotRefreshSettings,
  getIBKRSettings,
  getNotificationSettings,
  getSnapshotRefreshSettings,
  testIBKRConnection,
  testNotificationSettings,
  updateIBKRSettings,
  updateNotificationSettings,
  updateSnapshotRefreshSettings,
} from "../../shared/api";

function defaultIBKRProfile(profile: IBKRProfileName): IBKRConnectionProfile {
  return {
    host: "127.0.0.1",
    port: profile === "real" ? 7496 : 7497,
    client_id: profile === "real" ? 1 : 2,
    account_id: "",
  };
}

export interface NotificationSettingsSectionState {
  notificationSettings: NotificationSettings | null;
  telegramBotToken: string;
  telegramChatId: string;
  loading: boolean;
  saving: boolean;
  testing: boolean;
  error: string | null;
  success: string | null;
  setTelegramBotToken: (value: string) => void;
  setTelegramChatId: (value: string) => void;
  reload: () => Promise<void>;
  handleSubmit: (event: FormEvent<HTMLFormElement>) => Promise<void>;
  handleTestSend: () => Promise<void>;
}

export interface SettingsProfileState {
  profileName: IBKRProfileName;
  profile: IBKRConnectionProfile;
  active: boolean;
  onChange: (nextProfile: IBKRConnectionProfile) => void;
  testing: boolean;
}

export interface IBKRSettingsSectionState {
  ibkrSettings: IBKRSettings | null;
  ibkrMode: IBKRSettings["mode"];
  activeProfile: IBKRProfileName;
  loading: boolean;
  saving: boolean;
  error: string | null;
  success: string | null;
  activeProfileState: SettingsProfileState;
  standbyProfileState: SettingsProfileState;
  setIbkrMode: (mode: IBKRSettings["mode"]) => void;
  setActiveProfile: (profile: IBKRProfileName) => void;
  reload: () => Promise<void>;
  handleSubmit: (event: FormEvent<HTMLFormElement>) => Promise<void>;
  handleTest: (profile: IBKRProfileName) => Promise<void>;
}

export interface SnapshotRefreshSettingsSectionState {
  snapshotRefreshSettings: SnapshotRefreshSettings | null;
  snapshotRefreshEnabled: boolean;
  snapshotRefreshIntervalMinutes: number;
  loading: boolean;
  saving: boolean;
  error: string | null;
  success: string | null;
  setSnapshotRefreshEnabled: (value: boolean) => void;
  setSnapshotRefreshIntervalMinutes: (value: number) => void;
  reload: () => Promise<void>;
  handleSubmit: (event: FormEvent<HTMLFormElement>) => Promise<void>;
}

export function useNotificationSettingsSection(): NotificationSettingsSectionState {
  const [notificationSettings, setNotificationSettings] = useState<NotificationSettings | null>(null);
  const [telegramBotToken, setTelegramBotToken] = useState("");
  const [telegramChatId, setTelegramChatId] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const nextSettings = await getNotificationSettings();
      setNotificationSettings(nextSettings);
      setTelegramBotToken("");
      setTelegramChatId(nextSettings.telegram_chat_id);
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load notification settings.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const handleSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      setSaving(true);
      setSuccess(null);

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
        setError(null);
        setSuccess("Telegram 配置已保存到后端。");
      } catch (saveError) {
        setError(saveError instanceof Error ? saveError.message : "Failed to save notification settings.");
      } finally {
        setSaving(false);
      }
    },
    [telegramBotToken, telegramChatId],
  );

  const handleTestSend = useCallback(async () => {
    setTesting(true);
    setSuccess(null);

    try {
      const result = await testNotificationSettings();
      if (result.success) {
        setSuccess(result.detail);
        setError(null);
      } else {
        setError(result.detail);
      }
    } catch (testError) {
      setError(testError instanceof Error ? testError.message : "Failed to send test message.");
    } finally {
      setTesting(false);
    }
  }, []);

  return {
    notificationSettings,
    telegramBotToken,
    telegramChatId,
    loading,
    saving,
    testing,
    error,
    success,
    setTelegramBotToken,
    setTelegramChatId,
    reload,
    handleSubmit,
    handleTestSend,
  };
}

export function useIBKRSettingsSection(): IBKRSettingsSectionState {
  const [ibkrSettings, setIbkrSettings] = useState<IBKRSettings | null>(null);
  const [ibkrMode, setIbkrMode] = useState<IBKRSettings["mode"]>("mock");
  const [activeProfile, setActiveProfile] = useState<IBKRProfileName>("paper");
  const [realProfile, setRealProfile] = useState<IBKRConnectionProfile>(defaultIBKRProfile("real"));
  const [paperProfile, setPaperProfile] = useState<IBKRConnectionProfile>(defaultIBKRProfile("paper"));
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testingProfile, setTestingProfile] = useState<IBKRProfileName | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const applyIBKRSettings = useCallback((nextSettings: IBKRSettings) => {
    setIbkrSettings(nextSettings);
    setIbkrMode(nextSettings.mode);
    setActiveProfile(nextSettings.active_profile);
    setRealProfile(nextSettings.real);
    setPaperProfile(nextSettings.paper);
  }, []);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const nextSettings = await getIBKRSettings();
      applyIBKRSettings(nextSettings);
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load IBKR settings.");
    } finally {
      setLoading(false);
    }
  }, [applyIBKRSettings]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const handleSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      setSaving(true);
      setSuccess(null);

      try {
        const nextSettings = await updateIBKRSettings({
          mode: ibkrMode,
          active_profile: activeProfile,
          real: realProfile,
          paper: paperProfile,
        });
        applyIBKRSettings(nextSettings);
        setError(null);
        setSuccess("IBKR 连接配置已保存。刷新快照后会使用当前激活环境。");
      } catch (saveError) {
        setError(saveError instanceof Error ? saveError.message : "Failed to save IBKR settings.");
      } finally {
        setSaving(false);
      }
    },
    [activeProfile, applyIBKRSettings, ibkrMode, paperProfile, realProfile],
  );

  const handleTest = useCallback(async (profile: IBKRProfileName) => {
    setTestingProfile(profile);
    setSuccess(null);

    try {
      const result = await testIBKRConnection(profile);
      if (result.success) {
        setSuccess(result.detail);
        setError(null);
      } else {
        setError(result.detail);
      }
    } catch (testError) {
      setError(testError instanceof Error ? testError.message : "Failed to test IBKR connection.");
    } finally {
      setTestingProfile(null);
    }
  }, []);

  const activeProfileState =
    activeProfile === "paper"
      ? {
          profileName: "paper" as const,
          profile: paperProfile,
          active: true,
          onChange: setPaperProfile,
          testing: testingProfile === "paper",
        }
      : {
          profileName: "real" as const,
          profile: realProfile,
          active: true,
          onChange: setRealProfile,
          testing: testingProfile === "real",
        };

  const standbyProfileState =
    activeProfile === "paper"
      ? {
          profileName: "real" as const,
          profile: realProfile,
          active: false,
          onChange: setRealProfile,
          testing: testingProfile === "real",
        }
      : {
          profileName: "paper" as const,
          profile: paperProfile,
          active: false,
          onChange: setPaperProfile,
          testing: testingProfile === "paper",
        };

  return {
    ibkrSettings,
    ibkrMode,
    activeProfile,
    loading,
    saving,
    error,
    success,
    activeProfileState,
    standbyProfileState,
    setIbkrMode,
    setActiveProfile,
    reload,
    handleSubmit,
    handleTest,
  };
}

export function useSnapshotRefreshSettingsSection(): SnapshotRefreshSettingsSectionState {
  const [snapshotRefreshSettings, setSnapshotRefreshSettings] = useState<SnapshotRefreshSettings | null>(null);
  const [snapshotRefreshEnabled, setSnapshotRefreshEnabled] = useState(true);
  const [snapshotRefreshIntervalMinutes, setSnapshotRefreshIntervalMinutes] = useState(5);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const applySnapshotRefreshSettings = useCallback((nextSettings: SnapshotRefreshSettings) => {
    setSnapshotRefreshSettings(nextSettings);
    setSnapshotRefreshEnabled(nextSettings.enabled);
    setSnapshotRefreshIntervalMinutes(Math.max(5, Math.round(nextSettings.interval_seconds / 60)));
  }, []);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const nextSettings = await getSnapshotRefreshSettings();
      applySnapshotRefreshSettings(nextSettings);
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load snapshot refresh settings.");
    } finally {
      setLoading(false);
    }
  }, [applySnapshotRefreshSettings]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const handleSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      setSaving(true);
      setSuccess(null);

      try {
        const nextSettings = await updateSnapshotRefreshSettings({
          enabled: snapshotRefreshEnabled,
          interval_seconds: snapshotRefreshIntervalMinutes * 60,
        });
        applySnapshotRefreshSettings(nextSettings);
        setError(null);
        setSuccess("快照自动刷新设置已保存，后端会在下一轮循环读取新配置。");
      } catch (saveError) {
        setError(saveError instanceof Error ? saveError.message : "Failed to save snapshot refresh settings.");
      } finally {
        setSaving(false);
      }
    },
    [applySnapshotRefreshSettings, snapshotRefreshEnabled, snapshotRefreshIntervalMinutes],
  );

  return {
    snapshotRefreshSettings,
    snapshotRefreshEnabled,
    snapshotRefreshIntervalMinutes,
    loading,
    saving,
    error,
    success,
    setSnapshotRefreshEnabled,
    setSnapshotRefreshIntervalMinutes,
    reload,
    handleSubmit,
  };
}
