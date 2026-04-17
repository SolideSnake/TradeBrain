# TradeBrain 技术方案草案

## 文档信息

- 版本：v0.2
- 状态：当前有效（MVP v1 落地版）
- 更新日期：2026-04-17
- 适用范围：TradeBrain 第一版 MVP
- 文档目的：明确第一版的技术选型、运行方式、代码落地结构、数据流、存储方式、接口方案和实现原则，并反映 MVP v1 的已落地技术现实

## 0. 当前落地说明

截至 `2026-04-17`，TradeBrain 第一版 MVP 已完成。当前真正落地的主链路为：

`IBKR / mock -> CanonicalSnapshot -> 指标 -> PEG 估值标签 -> 状态变化检测 -> Telegram 预警 -> Web 看板`

当前已实现范围：

- FastAPI + SQLite 本地后端
- React + Vite 本地前端
- watchlist / snapshot / states / alerts / notification settings API
- PEG 驱动状态引擎
- Telegram 配置页与测试发送
- Windows 一键安装与一键启动脚本

当前未落地、仍属于后续阶段的内容：

- 任务中心
- WebSocket 增量推送
- 图表增强
- 更复杂的策略 DSL

## 1. 技术方案目标

TradeBrain 第一版技术方案必须满足以下目标：

- 能在本地稳定运行，适合个人长期使用。
- 能优先完成 IBKR 只读接入、状态、预警和看板闭环。
- 能快速进入开发，而不是陷入过重的基础设施建设。
- 能为后续扩展保留空间，但不为了未来扩展牺牲 MVP 交付速度。

本方案的核心取舍是：

- 后端优先使用 Python，原因是 IBKR 与指标处理生态更成熟。
- 前端使用本地 Web 看板，而不是原生桌面应用。
- 整体采用单体应用架构，而不是微服务。
- 默认单进程 + AsyncIO 运行，不以多线程为基础设计。

## 2. 参考项目与借鉴点

本方案不是凭空决定，而是结合高星开源项目的成熟做法进行取舍。

### 2.1 `ib-api-reloaded/ib_async`

用途：

- 作为 IBKR 接入首选参考

借鉴点：

- Python 下现代化 IBKR API 适配方式
- 账户、持仓、行情、历史数据读取方式
- AsyncIO 友好的运行模型

采用结论：

- 第一版直接基于 `ib_async` 做 `adapters/ibkr`

### 2.2 `freqtrade/freqtrade`

用途：

- 作为长时运行交易系统结构参考

借鉴点：

- 状态驱动工作流
- Telegram 集成方式
- SQLite 持久化与任务调度思路
- 后台任务与 Web 管理界面的组合方式

采用结论：

- 借它的“状态 -> 任务 -> 通知”链路，不借自动下单部分

### 2.3 `ghostfolio/ghostfolio`

用途：

- 作为投资类 Web 产品结构参考

借鉴点：

- 前后台分离
- 读模型导向的数据展示
- 投资产品页面的信息组织

采用结论：

- 借其 API + 前端分离、看板查询优先的思路

### 2.4 `afadil/wealthfolio`

用途：

- 作为本地优先产品形态参考

借鉴点：

- 本地优先
- Web 与本地运行结合
- 产品形态强调个人使用体验

采用结论：

- 借其本地优先理念，不采用 Rust/Tauri 方案，以降低 MVP 技术门槛

### 2.5 `nautechsystems/nautilus_trader` / `QuantConnect/Lean`

用途：

- 作为事件驱动与领域边界参考

借鉴点：

- 事件驱动思想
- 核心对象边界清晰
- 数据流、状态流和执行流分层

采用结论：

- 借其边界设计，不采用其重量级引擎实现

## 3. 总体技术选型

### 3.1 后端

后端选择：

- Python `3.12`
- FastAPI
- Uvicorn
- Pydantic v2
- SQLAlchemy 2.0
- SQLite
- APScheduler
- `ib_async`

选择理由：

- Python 对 IBKR 接入最友好。
- FastAPI 适合本地 REST + WebSocket 服务。
- Pydantic v2 适合配置、接口和对象校验。
- SQLAlchemy 2.0 足够支撑 MVP，又保留后续扩展能力。
- SQLite 适合本地优先和单用户场景。
- APScheduler 适合分钟级、小时级扫描任务。

### 3.2 前端

前端选择：

- React
- TypeScript
- Vite
- TanStack Query
- Zustand
- TanStack Table
- ECharts

选择理由：

- React + TypeScript 生态成熟，开发效率高。
- Vite 启动快，适合 MVP。
- TanStack Query 适合 API 拉取和缓存。
- Zustand 足够轻，适合本地看板状态管理。
- TanStack Table 很适合监控列表型页面。
- ECharts 适合后续扩展图表，但 MVP 仅少量使用。

### 3.3 包管理与工程工具

建议使用：

- Python：`uv`
- Node：`pnpm`
- Lint：`ruff`、`mypy`、`eslint`
- Test：`pytest`、`vitest`、`playwright`

选择理由：

- `uv` 在 Python 项目中足够快，适合新项目。
- `pnpm` 对前端依赖管理更快更稳。
- 工具链足够主流，不增加额外学习成本。

## 4. 实际项目落地结构

模块设计文档定义的是逻辑结构，实际工程结构建议如下：

```text
TradeBrain/
  backend/
    pyproject.toml
    app/
      config/
      core/
      domains/
      application/
      adapters/
      projections/
      jobs/
      observability/
      api/
    tests/
  web/
    package.json
    src/
      app/
      pages/
      widgets/
      features/
      entities/
      shared/
    tests/
  docs/
```

说明：

- `backend/app/` 对应 [arch.md](D:\code\TradeBrain\docs\arch.md) 的核心后端模块。
- `web/src/` 单独管理前端页面与组件。
- `docs/` 持续保存需求、模块设计、MVP、技术方案等文档。

## 5. 运行模型

### 5.1 总体运行方式

第一版采用：

- 单机本地运行
- 单后端进程
- 单前端开发服务器或后端托管静态资源

开发模式：

- 后端独立运行在本地端口
- 前端通过 Vite 代理调用后端 API

生产模式：

- 前端打包后由后端静态托管
- 用户只启动一个本地服务

### 5.2 并发模型

第一版并发策略为：

- 基础采用 `AsyncIO`
- 不以多线程为主
- 不拆多进程

具体做法：

- IBKR 连接和行情订阅跑在 AsyncIO 循环中
- WebSocket 推送跑在同一事件循环中
- 定时扫描任务由 APScheduler 触发
- SQLite 写入保持单写者原则，避免锁冲突

选择理由：

- 你的 MVP 需求是 I/O 型，不是 CPU 型。
- IBKR、WebSocket、Telegram 都适合异步模型。
- 多线程会增加共享状态和落库复杂度，不利于 MVP。

## 6. 数据与存储方案

### 6.1 数据库选择

第一版数据库选择：

- SQLite
- 开启 WAL 模式

理由：

- 本地优先
- 单用户
- 部署简单
- 备份简单

### 6.2 存储策略

第一版采用：

- 配置与历史状态落库
- 最新快照以内存缓存 + 落库并存
- 看板数据通过投影表读取

### 6.3 第一版核心表

第一版至少需要以下表：

- `assets`
- `watchlist_entries`
- `account_snapshots`
- `position_snapshots`
- `price_snapshots`
- `canonical_snapshots`
- `indicator_snapshots`
- `strategy_states`
- `tasks`
- `task_events`
- `alerts`
- `dashboard_rows`
- `system_status`

### 6.4 落库原则

- 所有历史类数据带时间戳
- 任务和预警必须可追溯
- 看板页面优先查 `dashboard_rows`
- 原始快照和投影分离

## 7. 统一数据流实现

### 7.1 主流程

后端主流程固定为：

1. 从 `config` 读取 watchlist 和系统配置
2. `adapters/ibkr` 拉取账户、持仓和行情
3. `application/build_snapshot.py` 构建 `CanonicalSnapshot`
4. `domains/indicators` 计算核心指标
5. `application/evaluate_state.py` 生成 `StrategyState`
6. `application/plan_tasks.py` 生成任务变化
7. `application/route_alerts.py` 生成或发送预警
8. `application/project_dashboard.py` 更新读模型
9. `apps/api` 提供 REST 和 WebSocket
10. `apps/web` 读取数据并展示

### 7.2 异常流程

若 IBKR 连接失败：

- 不清空上一次成功快照
- 更新 `system_status`
- 生成异常预警记录
- Telegram 发送系统异常提醒
- 页面显示“数据可能过期”

## 8. API 方案

### 8.1 REST API

第一版建议提供以下 REST API：

- `GET /api/health`
- `GET /api/system/status`
- `GET /api/dashboard/overview`
- `GET /api/dashboard/assets`
- `GET /api/dashboard/assets/{asset_id}`
- `GET /api/tasks`
- `PATCH /api/tasks/{task_id}`
- `GET /api/portfolio/account`
- `GET /api/portfolio/positions`
- `GET /api/watchlist`
- `POST /api/watchlist`
- `PATCH /api/watchlist/{asset_id}`
- `DELETE /api/watchlist/{asset_id}`
- `POST /api/actions/reload`
- `POST /api/actions/test-telegram`

### 8.2 WebSocket

第一版建议提供：

- `GET /ws`

推送内容包括：

- 系统状态变化
- 任务变化
- 预警变化
- 看板行更新

### 8.3 API 原则

- 前端只读读模型和必要的配置接口
- 不暴露复杂内部对象
- 所有返回统一带时间戳
- 所有写操作都要可追溯

## 9. 前端方案

### 9.1 页面结构

MVP 前端只做 4 页：

- 首页总览
- 监控列表页
- 任务中心页
- 账户持仓页

### 9.2 前端数据策略

前端采用以下原则：

- 列表类页面优先用 REST 拉取
- 实时刷新通过 WebSocket 增量更新
- 页面不自行计算核心业务指标
- 页面不直接理解 IBKR 原始字段

### 9.3 前端状态管理

建议如下：

- 服务端数据：TanStack Query
- 本地 UI 状态：Zustand

说明：

- API 数据缓存交给 TanStack Query
- 过滤条件、表格列顺序等 UI 状态交给 Zustand

## 10. 定时任务与后台任务

### 10.1 任务类型

第一版需要以下后台任务：

- `live_monitor`
- `scheduled_scan`
- `rebuild_readmodels`

### 10.2 执行建议

- `live_monitor`：监听实时或准实时行情更新，标记脏标的并触发增量更新
- `scheduled_scan`：每分钟扫描一次状态，每小时做一次全量校验
- `rebuild_readmodels`：手动触发或启动时执行，用于重建看板

### 10.3 单写者原则

为降低 SQLite 冲突：

- 所有数据库写入统一走应用层
- 避免多个线程同时写库
- 后台任务通过队列或统一编排入口落库

## 11. 配置方案

### 11.1 环境变量

第一版建议使用 `.env`，至少包括：

- `APP_ENV`
- `APP_PORT`
- `DB_PATH`
- `IBKR_HOST`
- `IBKR_PORT`
- `IBKR_CLIENT_ID`
- `IBKR_ACCOUNT_ID`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

### 11.2 本地配置文件

第一版建议使用本地配置文件保存：

- watchlist
- 分组
- 风险参数
- 状态引擎参数
- 任务和预警参数

建议格式：

- `YAML`

理由：

- 适合人工维护
- 比 `.env` 更适合结构化配置

## 12. 测试方案

### 12.1 后端测试

第一版必须覆盖：

- 指标纯函数测试
- 状态判断测试
- 任务状态流转测试
- 预警去重与节流测试
- 快照构建测试

### 12.2 集成测试

第一版必须覆盖：

- 假 IBKR 数据输入 -> 快照 -> 状态 -> 任务 -> 预警链路
- API 查询测试
- SQLite 持久化测试

### 12.3 前端测试

第一版最低要求：

- 核心页面渲染测试
- 任务操作交互测试
- 监控列表展示测试

### 12.4 端到端测试

建议至少覆盖：

- 看板启动
- 任务生成
- Telegram 测试发送
- 系统异常展示

## 13. 实现顺序

技术实现顺序建议如下：

1. 初始化工程结构
2. 建立后端基础配置与运行入口
3. 建立 SQLite 和 SQLAlchemy 模型
4. 建立 `adapters/ibkr`
5. 建立 `CanonicalSnapshot`
6. 建立指标计算
7. 建立基础状态引擎
8. 建立任务与预警链路
9. 建立 API 和 WebSocket
10. 建立前端 4 个页面
11. 建立系统状态与日志
12. 做联调与验收测试

## 14. 本方案的明确决策

为防止实现阶段反复摇摆，第一版技术方案明确做出以下决定：

- 使用 Python 后端，不使用 Node.js 后端
- 使用 React + TypeScript 前端，不使用 Angular
- 使用 FastAPI，不使用 Django
- 使用 SQLite，不使用 PostgreSQL
- 使用 `ib_async`，不直接裸接 IB API
- 使用本地 Web 看板，不做 Tauri / Electron 桌面包装
- 使用 AsyncIO 单进程模型，不使用多线程作为主架构
- 使用 REST + WebSocket，不只做轮询
- AI 不进入主判断链路

## 15. 下一步建议

基于本技术方案，下一步应继续补齐：

1. live 基本面字段质量验证
2. 真实 Telegram 联调
3. WebSocket 增量更新评估
4. 下一阶段功能范围定义
