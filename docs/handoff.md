# TradeBrain 交接文档

## 文档信息

- 版本：v0.11
- 状态：当前有效
- 更新日期：2026-04-30
- 目的：在更换电脑或中断工作后，帮助快速恢复项目上下文并继续开发

## 1. 当前项目状态

当前项目已经完成第一版 MVP，并进入 MVP 后的稳定化与下一阶段扩展。当前重点已从“跑通主链路”转为“保持低耦合、补策略线索、完善可配置提醒”。

已经完成的内容：

- 完成需求文档
- 完成模块设计文档
- 完成 MVP 功能清单
- 完成技术方案草案
- 完成后端 FastAPI + SQLite 基础骨架
- 完成前端 React + Vite 基础骨架
- 完成 watchlist 的数据库、API 和前端页面闭环
- 完成 `CanonicalSnapshot` 第一版
- 完成 IBKR 只读接入骨架
- 已验证可以读取真实 TWS 账户与持仓
- 完成核心指标第一版（价格、涨跌、回撤、持仓盈亏）
- 完成账户页真实数据展示
- 完成 PEG 驱动的估值标签第一版（`低估 / 合理 / 高估`）
- 完成状态引擎第一版（状态持久化、前后状态对比、变化检测）
- 完成 Telegram 通知基础链路
- 完成飞书自定义机器人通知通道：Webhook、可选签名 Secret、测试发送、规则提醒投递
- 完成 Alerts 前端规则管理页面
- 完成提醒规则 v1：规则 CRUD、指标字典、边界触发、冷却抑制、发送/失败/抑制统计
- 完成旧 `domains/alerts` 删除，切换到全局 `domains/events` 事件时间线
- 完成 `/api/events`，快照刷新、通知发送成功/失败/跳过都会进入事件记录
- 完成 Settings 前端页面与 Telegram 配置后端持久化
- 完成 Settings 页测试发送按钮与 Telegram 测试消息接口
- 完成预警模块分层重构：`domains/alerting` 负责判定规则，`application/notifications` 负责发送与历史记录
- 完成快照主链路拆分：`SnapshotBuilder` 只构建快照，`SnapshotPipelineService` 负责状态和通知编排
- 完成 `useSnapshotResource` 前端复用 hook，`Overview / Portfolio / Monitor` 共用快照读取流
- 完成 `SettingsPage`、`AlertsPage` 拆分，降低前端大页面复杂度
- 完成 `domains/strategy`、`domains/scoring`、`domains/scanner` 最小脚手架
- 完成 `/api/scanner`，并在 `Monitor` 页展示“策略线索”
- 完成追踪页 `区间位置` UI：52W / 90D 小分组、High/Low chip、区间进度条
- 完成 52W / 90D 低点指标：`low_52w`、`low_90d`、`gain_from_52w_low_percent`、`gain_from_90d_low_percent`
- 完成韩国股票最小支持：6 位数字代码默认按 KRX / KRW 处理，`000660` 可显示名称和韩元行情
- 完成账户现金字段修正：`TotalCashValue` 才显示为现金，`AvailableFunds` 单独显示为可用资金
- 完成多币种持仓换算：新增 `domains/fx`，IBKR 拉汇率并缓存到 SQLite，资产页用账户基准货币计算环图和未实现盈亏汇总
- 完成资产页多币种展示：汇总用 USD 基准金额，单行保留原币副行，例如 KRW 持仓同时显示 USD / KRW
- 完成资产走势后端：每次快照成功刷新后写入 `portfolio_history`，总览页通过 `/api/portfolio/history` 绘制本地历史走势
- 完成 IBKR 请求超时配置和手动刷新防卡住保护
- 完成根目录一键安装脚本与一键启动脚本
- 完成根目录 README 中文运行说明
- 完成 Windows Terminal 标签页启动体验优化
- 修复重复启动前端时错误拉起第二个 Vite 实例的问题

最近一次完整验证：

- 后端：`pytest`，`70 passed`
- 前端：`npm run build`，通过

当前 `docs/` 目录只保留两份核心文档：

- [design.md](D:\code\TradeBrain\docs\design.md)：产品、MVP、架构、技术方案合并版
- [handoff.md](D:\code\TradeBrain\docs\handoff.md)：换电脑、换线程、恢复上下文

## 2. 已经明确的产品结论

TradeBrain 第一版不是自动交易系统，也不是 AI 选股系统，而是一个本地运行的辅助交易工作台。

产品核心目标已经明确为：

- 可视化监控关注标的
- 接入 IBKR 账户与行情
- 计算关键指标
- 输出结构化状态
- 通过 Telegram / 飞书发送关键预警

AI 在第一版中不是主链路，只负责后续可能的简短说明和摘要。

当前实现顺序已调整为：

- 先把数据接入、快照、指标和可视化看板做稳
- 再根据实际使用情况决定是否需要补任务中心
- 当前已先落地 PEG 估值标签、状态变化检测和 Telegram / 飞书预警基础链路，不做执行待办
- Telegram 和飞书配置现在支持通过前端 Settings 页面写入后端本地存储
- 预警判断和通知发送已经拆开，后续新增回撤、买入区间、止损等规则时应优先放到 `domains/alerting`
- 策略线索和评分已经作为独立 `strategy / scoring / scanner` 域存在，不应塞回 `SnapshotBuilder`
- 买卖计划后续应从 `watchlist` 边界外提出来，单独进入 `domains/strategy` 或专门的计划模块
- `Monitor` 页的 `区间位置` 只做展示：核心高低点和百分比指标由后端 `domains/indicators` 生成
- 快照刷新失败或 IBKR 未就绪时应保留旧快照，不应让页面空白或按钮无限转圈
- 多币种原则已经明确：账户级汇总、环图占比和未实现盈亏汇总必须使用账户基准货币；单个标的行情和表格副行可以保留原币
- 现金和可用资金不能混用：现金来自 IBKR `TotalCashValue`，可用资金来自 `AvailableFunds`

## 3. 已经明确的技术结论

第一版技术方向已经确定为：

- 后端：Python 3.11+ + FastAPI + SQLAlchemy + SQLite + ib_async
- 前端：React + TypeScript + Vite
- 运行方式：本地单机运行
- 并发模型：单进程 + AsyncIO
- 数据库：SQLite（WAL 模式）
- 通信方式：REST
- 当前架构：单体分层架构，核心为 `adapters -> application -> domains -> api -> web`
- 汇率换算：`adapters/ibkr` 负责拉 FX 行情，`domains/fx` 负责换算，`snapshot_builder` 负责把基准币字段放进快照
- 本地缓存：快照缓存、设置、提醒规则、事件记录、FX 汇率缓存都在 SQLite

明确不采用：

- 微服务
- PostgreSQL
- 多线程主架构
- 自动下单
- 桌面壳优先方案
- 当前 MVP 不含 WebSocket 主链路

## 4. MVP 当前结论

第一版 MVP 已完成，当前实际能力已经超过最初 7 件事：

1. Watchlist 与分组管理
2. IBKR 只读接入
3. CanonicalSnapshot
4. 核心指标
5. 基础状态引擎
6. Telegram / 飞书预警
7. Web 看板

MVP 后已新增：

- IBKR 真实/模拟 profile 单切换
- 快照缓存与后端自动刷新
- 侧边栏手动获取数据
- 可配置提醒规则页
- 策略线索扫描与基础评分
- 追踪页区间位置可视化
- 刷新超时和并发刷新保护
- 全局事件时间线，替代旧提醒历史
- 飞书通知通道
- 韩国股票与多币种资产页换算

第一版禁止扩项到以下方向：

- 自动下单
- 回测
- 多用户
- 云同步
- 复杂策略 DSL
- 高级 AI 决策

## 5. 推荐的下一步开发顺序

下一次继续开发时，建议进入 `MVP v1 之后的稳定化与扩展阶段`，按以下顺序推进：

1. 在真实/模拟 TWS 下继续验证行情、PEG、账户字段和 FX 汇率稳定性
2. 检查含 KRW 持仓时资产页环图、未实现盈亏、表格副行是否符合预期
3. 观察 `区间位置` UI 在真实数据下是否过密，必要时拆出标的详情页
4. 完善策略计划模型，把买入区间、卖出区间、止损止盈从 watchlist 外提出来
5. 把 `/api/scanner` 的策略线索扩展成可配置扫描条件
6. 根据真实使用反馈决定是否加图表、标的详情页或 WebSocket
7. 再评估任务中心是否恢复

## 5.1 当前最适合的新线程方向

如果下一条线程要继续开发，当前推荐方向有两个：

- “策略计划线程”：只做 `domains/strategy`、买卖计划、止盈止损、策略提醒。
- “前端追踪页线程”：只做 `Monitor` 页策略线索、筛选、排序、详情交互。

如果只开一个线程，优先开“策略计划线程”。

建议边界如下：

- 策略计划线程：优先改 `backend/app/domains/strategy`、`backend/app/application`、相关测试。
- 前端追踪页线程：优先改 `web/src/pages/MonitorPage.tsx` 和追踪页相关组件。
- 不要把策略计划字段继续塞进 `watchlist_entries`。
- 不要把扫描逻辑塞进 `SnapshotBuilder`。

建议优先事项：

1. 建立策略计划模型：买入区间、卖出区间、止损、止盈、计划状态
2. 让提醒规则可以引用策略计划字段
3. 扩展 scanner：支持计划命中、低估、回撤、日跌幅等多条件
4. 追踪页增加策略线索详情，不在前端自行计算核心评分

说明：

- 当前后端主链路已经较稳定，适合把前端作为独立迭代线程处理
- 共享文件如前端 API 类型层仍应谨慎修改，尽量避免大改

## 6. 推荐的第一批编码任务

当前已经完成的编码任务：

- 初始化 `backend/`
- 初始化 `web/`
- 建立 `.env.example`
- 建立根目录 `.env` 本地运行配置
- 建立后端 `app/main.py`
- 建立后端配置读取
- 建立基础健康检查接口
- 建立 SQLite 初始化逻辑
- 建立 watchlist 最小模型
- 建立 snapshot API
- 建立 overview/monitor 页面基础联通
- 验证真实 TWS 端口 `7496` 可读账户与持仓
- 建立核心指标计算与监控页真实指标展示
- 建立账户页真实持仓与盈亏展示
- 建立 PEG 基本面字段与估值标签展示
- 建立状态引擎第一版和 `/api/states` 接口
- 建立 Telegram / 飞书预警发送，并把投递结果写入全局事件时间线
- 建立 Alerts 页用于提醒规则管理和发送统计
- 建立 `/api/events` 全局事件接口，承接通知投递和快照刷新记录
- 建立 Settings 页并通过 `/api/settings/notifications` 保存 Telegram / 飞书配置
- 建立 `/api/settings/notifications/test` 并支持页面直接测试发送
- 建立 `/api/alert-rules` 规则管理接口
- 建立 `/api/scanner` 策略线索扫描接口
- 建立 `domains/strategy`、`domains/scoring`、`domains/scanner`

下一批建议任务：

- 抽出策略计划模型和数据库表
- 让规则提醒支持策略计划字段
- 继续验证 IBKR live/paper 行情、账户和 PEG 字段质量
- 继续验证 52W / 90D high/low 在真实行情下是否稳定
- 继续验证 KRW/USD FX 汇率在 TWS 启动较慢或行情权限不足时的降级表现
- 评估 PEG 覆盖不足时的降级展示策略
- 根据真实使用反馈决定是否开启图表、详情页或 WebSocket

## 7. 已参考的高星项目

当前方案主要参考了以下项目的结构思路：

- [ib-api-reloaded/ib_async](https://github.com/ib-api-reloaded/ib_async)
- [freqtrade/freqtrade](https://github.com/freqtrade/freqtrade)
- [ghostfolio/ghostfolio](https://github.com/ghostfolio/ghostfolio)
- [afadil/wealthfolio](https://github.com/afadil/wealthfolio)
- [nautechsystems/nautilus_trader](https://github.com/nautechsystems/nautilus_trader)
- [QuantConnect/Lean](https://github.com/QuantConnect/Lean)

参考方式已经明确：

- `ib_async`：IBKR 接入
- `freqtrade`：状态、预警流
- `ghostfolio`：看板结构与读模型思路
- `wealthfolio`：本地优先产品形态
- `nautilus_trader / Lean`：事件驱动和边界设计

## 8. 换电脑时需要保留什么

如果换电脑继续开发，至少保留以下内容：

- 整个项目仓库
- `docs/` 目录
- `.env` 或后续的本地配置文件
- IBKR 连接参数
- Telegram Bot 配置
- 飞书自定义机器人 Webhook / Secret
- 本地 `C:\Users\ONE\.codex` 目录（如果仍需要本地 Codex 配置）

特别说明：

- 真正后端源码在 `backend/app`。
- `backend/backend` 是空目录，目前没有用，可以删除或忽略。
- `backend/tradebrain.db`、`backend/tradebrain.db-shm`、`backend/tradebrain.db-wal` 是本地运行数据，不是源码。
- 换电脑如果不复制数据库，项目仍能运行，只是本地 watchlist、Settings 配置、提醒规则、事件时间线和 FX 汇率缓存需要重新生成或重新配置。
- 如果复制数据库，注意里面会包含本地 watchlist、提醒规则、事件记录、通知配置和 FX 汇率缓存；不建议把数据库提交到 Git。
- 旧快照缓存里可能没有新增的 low 字段，换电脑或刷新代码后点一次“手动获取数据”即可生成新字段。
- 旧快照缓存里也可能没有新增的 `cash_balance`、`market_value_base`、`unrealized_pnl_base` 字段，换电脑或更新代码后点一次“手动获取数据”即可生成新字段。

不要依赖聊天线程本身作为唯一上下文来源，后续继续推进时应优先以仓库文档为准。

## 8.1 新电脑快速恢复步骤

换到新电脑后，建议按下面顺序恢复：

1. 拉取整个仓库，确认在 `main` 分支最新提交
2. 先看 [README.md](D:\code\TradeBrain\README.md)
3. 再看本文件，确认当前阶段和下一步
4. 运行一键安装：
   - [install.cmd](D:\code\TradeBrain\install.cmd)
5. 运行一键启动：
   - [start.cmd](D:\code\TradeBrain\start.cmd)
6. 确认前端页面可打开：
   - `Overview`
   - `Monitor`
   - `Alerts`
   - `Portfolio`
   - `Settings`
7. 在 `Monitor` 页确认“策略线索”区域可以展示或显示空状态
8. 在 `Monitor` 页确认 `区间位置` 列能显示 52W / 90D 的 High/Low chip
9. 如果要做 live 联调，再确认 TWS / IB Gateway 与 `.env` 配置
10. 如果账户里有非 USD 持仓，点“手动获取数据”后确认资产页环图不再被 KRW / HKD 裸数字放大
11. 如果 FX 获取失败，优先检查 TWS 是否完全启动、行情权限是否可用、事件卡片是否有 FX 相关 warning

关于启动脚本的当前行为：

- 启动器完成后会自动关闭
- 正常情况下会在一个 Windows Terminal 窗口中打开两个标签页：
  - `TradeBrain Backend`
  - `TradeBrain Frontend`
- 如果前后端都已运行，再次点启动只会打开网页，不会重复拉起前端
- 前端固定使用 `5173`，不会再自动跳到 `5174`

## 9. 一句话交接结论

TradeBrain 第一版 MVP 已完成，当前主链路已经演进为 “IBKR TWS real/paper -> SnapshotBuilder -> FX 换算 -> SnapshotPipeline -> 指标/状态/提醒 -> 快照缓存 -> Web 看板”。后端运行链路已移除 Mock 数据模式，日常测试建议使用 TWS Paper 账户；自动化测试保留测试专用 IBKR 客户端。项目已新增 “CanonicalSnapshot -> StrategyEvaluator -> ScoringService -> ScannerService -> /api/scanner -> 追踪页策略线索”。追踪页已具备 52W/90D 区间位置展示，资产页已支持现金/可用资金区分和多币种基准货币汇总。下一步重点是把买卖计划从 watchlist 外提出来，进入独立策略计划模型。
