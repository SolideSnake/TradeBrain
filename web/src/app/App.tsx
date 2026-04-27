import { NavLink, Route, Routes } from "react-router-dom";
import { useEffect, useState } from "react";

import { AlertsPage } from "../pages/AlertsPage";
import { MonitorPage } from "../pages/MonitorPage";
import { OverviewPage } from "../pages/OverviewPage";
import { PortfolioPage } from "../pages/PortfolioPage";
import { SettingsPage } from "../pages/SettingsPage";
import { refreshSnapshot } from "../shared/api";
import { dispatchSnapshotRefreshed } from "../shared/snapshotEvents";

const navItems = [
  { to: "/", label: "仪表盘" },
  { to: "/portfolio", label: "资产" },
  { to: "/monitor", label: "追踪" },
  { to: "/alerts", label: "提醒" },
  { to: "/settings", label: "设置" },
];

export function App() {
  const [refreshStatus, setRefreshStatus] = useState<
    "idle" | "loading" | "success" | "pending" | "error"
  >("idle");
  const [refreshMessage, setRefreshMessage] = useState("");

  useEffect(() => {
    if (refreshStatus !== "success" && refreshStatus !== "pending" && refreshStatus !== "error") {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      setRefreshStatus("idle");
      setRefreshMessage("");
    }, 3000);

    return () => window.clearTimeout(timeoutId);
  }, [refreshStatus]);

  async function handleManualRefresh() {
    setRefreshStatus("loading");
    setRefreshMessage("");

    try {
      const response = await refreshSnapshot();
      dispatchSnapshotRefreshed(response);

      if (response.cache_status === "refreshing") {
        setRefreshStatus("pending");
        setRefreshMessage("正在获取，旧数据先保留");
      } else if (response.last_error) {
        setRefreshStatus("error");
        setRefreshMessage("获取失败，已保留旧数据");
      } else {
        setRefreshStatus("success");
        setRefreshMessage("已更新");
      }
    } catch (error) {
      setRefreshStatus("error");
      setRefreshMessage(error instanceof Error ? error.message : "获取失败");
    }
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <h1>TradeBrain</h1>
        </div>

        <nav className="nav">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-refresh">
          <button
            type="button"
            className="sidebar-refresh-button"
            onClick={() => void handleManualRefresh()}
            disabled={refreshStatus === "loading"}
          >
            {refreshStatus === "loading" ? "获取中..." : "手动获取数据"}
          </button>
          {refreshMessage ? (
            <p className={`sidebar-refresh-message sidebar-refresh-message-${refreshStatus}`}>
              {refreshMessage}
            </p>
          ) : null}
        </div>
      </aside>

      <main className="content">
        <Routes>
          <Route path="/" element={<OverviewPage />} />
          <Route path="/monitor" element={<MonitorPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/portfolio" element={<PortfolioPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  );
}
