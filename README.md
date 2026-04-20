# TradeBrain

TradeBrain 是一个本地优先的辅助交易工作台，用来监控自选标的、读取 IBKR 账户数据、计算一小组高信号指标、基于 PEG 打估值标签，并在状态变化时发送 Telegram 预警。

第一版 MVP 已于 `2026-04-17` 完成，当前仓库已进入 `MVP v1 完成后的稳定化与下一阶段规划`。

当前 MVP 聚焦这 7 件事：

- Watchlist 管理
- IBKR 只读接入
- CanonicalSnapshot 统一快照
- 核心指标计算
- PEG 估值标签：`低估 / 合理 / 高估`
- 状态变化检测
- Telegram 预警
- Web 看板

## 技术栈

- 后端：Python 3.11+、FastAPI、SQLAlchemy、SQLite、`ib_async`
- 前端：React、TypeScript、Vite
- 运行方式：本地单机
- 数据库：SQLite + WAL

## 项目结构

```text
TradeBrain/
  backend/        FastAPI 后端与 SQLite 模型
  web/            React + Vite 看板前端
  docs/           需求、MVP、技术方案、交接文档
  install.ps1     Windows 一键安装 / 检测脚本
  install.cmd     给双击或 cmd 用的包装脚本
  .env.example    本地环境变量模板
```

## 运行前准备

- Windows + PowerShell
- Python `3.11+`
- Node.js `18+`
- npm

如需做真实联调，还需要：

- IBKR TWS 或 IB Gateway
- Telegram Bot Token 和 Chat ID

## 一键安装

在仓库根目录执行：

```powershell
cd D:\code\TradeBrain
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

或者直接运行：

```powershell
cd D:\code\TradeBrain
.\install.cmd
```

脚本会自动完成：

- 检查 Python、Node.js、npm 版本
- 创建 `.venv`
- 安装后端依赖，来源见 [pyproject.toml](D:\code\TradeBrain\backend\pyproject.toml)
- 安装前端依赖，来源见 [package.json](D:\code\TradeBrain\web\package.json)
- 检查后端关键包是否可导入，包括 `ib_async`
- 如果缺少 [\.env](D:\code\TradeBrain\.env)，自动根据 [\.env.example](D:\code\TradeBrain\.env.example) 生成
- 提示 IBKR 常见端口是否监听
- 默认顺手跑后端测试和前端构建

常用模式：

```powershell
# 只检查环境，不安装
powershell -ExecutionPolicy Bypass -File .\install.ps1 -CheckOnly

# 安装依赖，但跳过测试和构建
powershell -ExecutionPolicy Bypass -File .\install.ps1 -SkipValidation
```

## 一键启动

在仓库根目录执行：

```powershell
cd D:\code\TradeBrain
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

或者直接运行：

```powershell
cd D:\code\TradeBrain
.\start.cmd
```

启动脚本会：

- 先调用安装脚本做轻量环境检查
- 如果缺依赖，会自动补装
- 拉起后端标签页
- 拉起前端标签页
- 如果前后端都已启动，则直接打开浏览器，不重复启动服务
- 前端固定使用 `5173` 端口，不会自动跳到 `5174`
- 如果只缺后端或前端其中一个，只补启动缺失的一边

常用模式：

```powershell
# 启动但不自动打开浏览器
powershell -ExecutionPolicy Bypass -File .\start.ps1 -NoBrowser

# 只演练启动流程，不真正启动服务
powershell -ExecutionPolicy Bypass -File .\start.ps1 -DryRun
```

说明：

- 启动器完成后会自动关闭。
- 正常情况下会在一个 Windows Terminal 窗口里打开两个标签页：
  - `TradeBrain Backend`
  - `TradeBrain Frontend`
- 如果系统不可用 `Windows Terminal`，会自动回退到两个独立窗口。

## 本地启动

### 1. 启动后端

```powershell
cd D:\code\TradeBrain\backend
..\.venv\Scripts\python -m uvicorn app.main:app --reload
```

健康检查：

- [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

### 2. 启动前端

```powershell
cd D:\code\TradeBrain\web
npm run dev
```

前端地址：

- [http://127.0.0.1:5173](http://127.0.0.1:5173)

前端开发服务器会把 `/api` 自动代理到后端 `127.0.0.1:8000`。

## 环境变量

基础模板在 [\.env.example](D:\code\TradeBrain\.env.example)。

当前常用字段：

```env
APP_ENV=development
APP_PORT=8000
DB_PATH=backend/tradebrain.db

IBKR_MODE=mock
IBKR_ACTIVE_PROFILE=paper
IBKR_HOST=127.0.0.1
IBKR_PORT=7497
IBKR_CLIENT_ID=1
IBKR_ACCOUNT_ID=
IBKR_REAL_HOST=127.0.0.1
IBKR_REAL_PORT=7496
IBKR_REAL_CLIENT_ID=1
IBKR_REAL_ACCOUNT_ID=
IBKR_PAPER_HOST=127.0.0.1
IBKR_PAPER_PORT=7497
IBKR_PAPER_CLIENT_ID=2
IBKR_PAPER_ACCOUNT_ID=
IBKR_MARKET_DATA_TYPE=delayed
IBKR_MARKET_DATA_WAIT_SECONDS=1.0

TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

说明：

- `IBKR_MODE=mock` 适合本地先看 UI，不依赖 TWS。
- 如果要连接 TWS，请改成 `IBKR_MODE=ibkr`；旧写法 `IBKR_MODE=live` 仍兼容。
- `IBKR_ACTIVE_PROFILE=paper` 使用模拟 TWS，默认端口 `7497`；`real` 使用真实 TWS，默认端口 `7496`。
- 更推荐在前端 `Settings` 页面保存和切换 IBKR 配置；同一时间只会激活真实或模拟中的一个。
- Telegram 配置更推荐在前端 `Settings` 页面里填写，由后端本地保存，不建议长期直接写在 `.env`。

## 当前页面

- `Overview`：券商连接状态和快照摘要
- `Monitor`：watchlist、行情指标、PEG、估值标签、状态变化
- `Alerts`：预警历史和 Telegram 发送记录
- `Portfolio`：账户余额、持仓、浮盈亏
- `Settings`：IBKR 真实/模拟 TWS 配置、Telegram 配置与测试发送

## 当前后端 API

- `GET /api/health`
- `GET /api/watchlist`
- `POST /api/watchlist`
- `PATCH /api/watchlist/{entry_id}`
- `DELETE /api/watchlist/{entry_id}`
- `GET /api/snapshot`：读取最近一次成功快照；没有缓存时会首次生成
- `POST /api/snapshot/refresh`：手动刷新快照，失败时保留旧快照
- `GET /api/states`
- `GET /api/alerts`
- `GET /api/settings/notifications`
- `PUT /api/settings/notifications`
- `POST /api/settings/notifications/test`
- `GET /api/settings/ibkr`
- `PUT /api/settings/ibkr`
- `POST /api/settings/ibkr/test`

## 怎么验收 MVP

### 基础本地验收

1. 跑一键安装脚本
2. 启动后端和前端
3. 打开看板
4. 确认 `Overview / Monitor / Alerts / Portfolio / Settings` 都能正常打开

### IBKR 联调验收

1. 打开 TWS 或 IB Gateway
2. 在 TWS 里开启 API socket
3. 打开 `Settings`，把 `IBKR` 数据模式改成 `IBKR TWS`
4. 模拟账户选择 `模拟 TWS Paper`，确认端口是 `7497`
5. 真实账户选择 `真实 TWS`，确认端口是 `7496`
6. 点击对应 profile 的 `测试连接`
7. 保存设置后刷新页面，确认 broker 状态变成 `connected`

### Telegram 联调验收

1. 打开 `Settings`
2. 保存 Telegram Bot Token 和 Chat ID
3. 点击 `Send Test Message`
4. 确认 Telegram 收到消息
5. 确认 `Alerts` 页面出现对应测试记录

## 测试命令

后端：

```powershell
cd D:\code\TradeBrain\backend
..\.venv\Scripts\python -m pytest
```

前端：

```powershell
cd D:\code\TradeBrain\web
npm run build
```

## 重要说明

- 当前 TradeBrain 是监控和提醒工具，不是自动下单系统。
- 当前状态引擎是 PEG 驱动的轻量版。
- 正确数据库位置应为 [tradebrain.db](D:\code\TradeBrain\backend\tradebrain.db)。
- 不要把 Telegram Bot Token 发到聊天记录里，也不要提交进仓库。

## 相关文档

- [prd.md](D:\code\TradeBrain\docs\prd.md)
- [arch.md](D:\code\TradeBrain\docs\arch.md)
- [mvp.md](D:\code\TradeBrain\docs\mvp.md)
- [tech.md](D:\code\TradeBrain\docs\tech.md)
- [handoff.md](D:\code\TradeBrain\docs\handoff.md)
