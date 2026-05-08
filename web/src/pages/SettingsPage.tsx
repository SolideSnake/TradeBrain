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
      <div className="settings-stack">
        <IBKRSettingsSection state={ibkrSection} />
        <SnapshotRefreshSettingsSection state={snapshotRefreshSection} />
        <NotificationSettingsSection state={notificationSection} />
      </div>
    </section>
  );
}
