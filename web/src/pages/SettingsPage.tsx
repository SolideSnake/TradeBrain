import {
  IBKRSettingsSection,
  NotificationSettingsSection,
  SnapshotRefreshSettingsSection,
} from "./settings/SettingsPanels";
import {
  useIBKRSettingsSection,
  useNotificationSettingsSection,
  useSnapshotRefreshSettingsSection,
} from "./settings/useSettingsSections";

export function SettingsPage() {
  const ibkrSection = useIBKRSettingsSection();
  const snapshotRefreshSection = useSnapshotRefreshSettingsSection();
  const notificationSection = useNotificationSettingsSection();

  return (
    <section>
      <header className="page-header">
        <p>设置页用于查看当前配置、修改字段、测试链路和保存应用；状态只做辅助提示，不再做大面积摘要卡。</p>
      </header>

      <div className="settings-stack">
        <IBKRSettingsSection state={ibkrSection} />
        <SnapshotRefreshSettingsSection state={snapshotRefreshSection} />
        <NotificationSettingsSection state={notificationSection} />
      </div>
    </section>
  );
}
