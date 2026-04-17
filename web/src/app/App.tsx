import { NavLink, Route, Routes, useLocation } from "react-router-dom";

import { AlertsPage } from "../pages/AlertsPage";
import { MonitorPage } from "../pages/MonitorPage";
import { OverviewPage } from "../pages/OverviewPage";
import { PortfolioPage } from "../pages/PortfolioPage";
import { SettingsPage } from "../pages/SettingsPage";

const navItems = [
  { to: "/", label: "总览", hint: "先确认系统是否可用" },
  { to: "/monitor", label: "监控", hint: "优先看状态变化与缺失行情" },
  { to: "/alerts", label: "提醒", hint: "区分触发与投递结果" },
  { to: "/portfolio", label: "持仓", hint: "看账户、仓位与盈亏" },
  { to: "/settings", label: "设置", hint: "管理通知配置" },
];

export function App() {
  const location = useLocation();
  const activeNav = navItems.find((item) => item.to === location.pathname) ?? navItems[0];

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-kicker">TradeBrain</span>
          <h1>交易监控台</h1>
          <p>不扩业务边界，只把现有监控链路做得更清楚、更快扫、更容易判断。</p>
        </div>

        <nav className="nav">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
            >
              <span>{item.label}</span>
              <small>{item.hint}</small>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <p className="sidebar-footnote">当前线程仅改 `web/`，不改后端接口契约。</p>
        </div>
      </aside>

      <main className="content">
        <div className="content-topbar">
          <div>
            <span className="eyebrow">Frontend Optimization</span>
            <h2>{activeNav.label}</h2>
          </div>
          <div className="topbar-chip">TradeBrain MVP 前端体验优化中</div>
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
