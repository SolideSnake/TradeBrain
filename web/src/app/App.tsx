import { NavLink, Route, Routes } from "react-router-dom";

import { MonitorPage } from "../pages/MonitorPage";
import { OverviewPage } from "../pages/OverviewPage";
import { PortfolioPage } from "../pages/PortfolioPage";
import { TasksPage } from "../pages/TasksPage";

const navItems = [
  { to: "/", label: "Overview" },
  { to: "/monitor", label: "Monitor" },
  { to: "/tasks", label: "Tasks" },
  { to: "/portfolio", label: "Portfolio" },
];

export function App() {
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-kicker">TradeBrain</span>
          <h1>Local Trading Console</h1>
          <p>MVP dashboard skeleton for watchlists, states, tasks, and alerts.</p>
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
        <Routes>
          <Route path="/" element={<OverviewPage />} />
          <Route path="/monitor" element={<MonitorPage />} />
          <Route path="/tasks" element={<TasksPage />} />
          <Route path="/portfolio" element={<PortfolioPage />} />
        </Routes>
      </main>
    </div>
  );
}

