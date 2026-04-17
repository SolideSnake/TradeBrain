# TradeBrain 交接文档

## 文档信息

- 版本：v0.5
- 状态：当前有效
- 更新日期：2026-04-17
- 目的：在更换电脑或中断工作后，帮助快速恢复项目上下文并继续开发

## 1. 当前项目状态

当前项目已经完成第一版 MVP，基础骨架和首条完整业务链路已经落地。

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
- 完成 Telegram 预警基础链路（仅针对状态变化）
- 完成 Alerts 前端页面与预警历史展示
- 完成 Settings 前端页面与 Telegram 配置后端持久化
- 完成 Settings 页测试发送按钮与 Telegram 测试消息接口
- 完成根目录一键安装脚本与一键启动脚本
- 完成根目录 README 中文运行说明

当前 `docs/` 目录中的核心文档：

- [product-requirements.md](D:\code\TradeBrain\docs\product-requirements.md)
- [module-design.md](D:\code\TradeBrain\docs\module-design.md)
- [mvp-scope.md](D:\code\TradeBrain\docs\mvp-scope.md)
- [technical-solution.md](D:\code\TradeBrain\docs\technical-solution.md)

## 2. 已经明确的产品结论

TradeBrain 第一版不是自动交易系统，也不是 AI 选股系统，而是一个本地运行的辅助交易工作台。

产品核心目标已经明确为：

- 可视化监控关注标的
- 接入 IBKR 账户与行情
- 计算关键指标
- 输出结构化状态
- 通过 Telegram 发送关键预警

AI 在第一版中不是主链路，只负责后续可能的简短说明和摘要。

当前实现顺序已调整为：

- 先把数据接入、快照、指标和可视化看板做稳
- 再根据实际使用情况决定是否需要补任务中心
- 当前已先落地 PEG 估值标签、状态变化检测和 Telegram 预警基础链路，不做执行待办
- Telegram 配置现在支持通过前端 Settings 页面写入后端本地存储

## 3. 已经明确的技术结论

第一版技术方向已经确定为：

- 后端：Python 3.11+ + FastAPI + SQLAlchemy + SQLite + ib_async
- 前端：React + TypeScript + Vite
- 运行方式：本地单机运行
- 并发模型：单进程 + AsyncIO
- 数据库：SQLite（WAL 模式）
- 通信方式：REST

明确不采用：

- 微服务
- PostgreSQL
- 多线程主架构
- 自动下单
- 桌面壳优先方案
- 当前 MVP 不含 WebSocket 主链路

## 4. MVP 当前结论

第一版 MVP 当前严格只做 7 件事，并且已经全部完成：

1. Watchlist 与分组管理
2. IBKR 只读接入
3. CanonicalSnapshot
4. 核心指标
5. 基础状态引擎
6. Telegram 预警
7. Web 看板

第一版禁止扩项到以下方向：

- 自动下单
- 回测
- 多用户
- 云同步
- 复杂策略 DSL
- 高级 AI 决策

## 5. 推荐的下一步开发顺序

下一次继续开发时，建议进入 `MVP v1 之后的稳定化与扩展阶段`，按以下顺序推进：

1. 验证 live 模式下 PEG 基本面字段的稳定性与覆盖率
2. 配置真实 Telegram Bot Token / Chat ID 并做一次联调
3. 按需要把 PEG/状态变化/预警历史扩展到总览页或账户页
4. 建立 API 与 WebSocket 增量更新
5. 再评估是否进入图表增强、任务中心或更细策略配置

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
- 建立 Telegram 预警发送与 `/api/alerts` 接口
- 建立 Alerts 页并展示预警历史
- 建立 Settings 页并通过 `/api/settings/notifications` 保存 Telegram 配置
- 建立 `/api/settings/notifications/test` 并支持页面直接测试发送

下一批建议任务：

- 验证 IBKR live 模式下 `ReportSnapshot / RESC / ratio 258` 的字段质量
- 评估 PEG 覆盖不足时的降级展示策略
- 配置 Telegram 并验证真实状态变化能否成功触达
- 评估是否需要 WebSocket 推送状态变化
- 根据真实使用反馈决定是否开启下一阶段功能开发

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
- 本地 `C:\Users\ONE\.codex` 目录（如果仍需要本地 Codex 配置）

不要依赖聊天线程本身作为唯一上下文来源，后续继续推进时应优先以仓库文档为准。

## 9. 一句话交接结论

TradeBrain 第一版 MVP 已完成，当前主链路已经跑通为 “IBKR -> Snapshot -> 指标 -> PEG 估值标签 -> 状态变化检测 -> Telegram 预警 -> 看板展示”，下一步重点是做 live 数据质量验证和真实使用联调。
