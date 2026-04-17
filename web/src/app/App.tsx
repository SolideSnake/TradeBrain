import { NavLink, Route, Routes, useLocation } from "react-router-dom";

import { AlertsPage } from "../pages/AlertsPage";
import { MonitorPage } from "../pages/MonitorPage";
import { OverviewPage } from "../pages/OverviewPage";
import { PortfolioPage } from "../pages/PortfolioPage";
import { SettingsPage } from "../pages/SettingsPage";

const navItems = [
  { to: "/", label: "仪表盘" },
  { to: "/portfolio", label: "资产" },
  { to: "/monitor", label: "追踪" },
  { to: "/alerts", label: "提醒" },
  { to: "/settings", label: "设置" },
];

export function App() {
  const location = useLocation();
  const activeNav = navItems.find((item) => item.to === location.pathname) ?? navItems[0];

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
      </aside>

      <main className="content">
        <div className="content-topbar">
          <div>
            <h2>{activeNav.label}</h2>
          </div>
          <div className="topbar-chip">TradeBrain 本地工作台</div>
        </div>

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
