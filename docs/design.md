# TradeBrain 设计文档

## 文档信息

- 版本：v1.0
- 状态：当前有效
- 更新日期：2026-04-27
- 目的：合并原 `prd.md`、`mvp.md`、`arch.md`、`tech.md`，作为单人项目的长期设计依据

## 1. 产品定位

TradeBrain 是一个本地优先的个人辅助交易工作台。

它的核心目标不是预测市场，也不是自动交易，而是把用户平时靠肉眼盯盘、靠记忆维护关注名单、靠经验执行策略的过程，变成一个可视化、可提醒、可复盘的系统。

当前定位：

- 个人交易监控中枢
- IBKR 账户和行情只读看板
- 关注标的指标监控工具
- 可配置提醒规则系统
- 策略线索扫描和评分辅助工具

明确不是：

- 自动下单系统
- 高频或超短线交易系统
- 多用户协作系统
- AI 自动决策系统
- 完整回测平台

AI 后续可以用于说明、摘要和研究辅助，但不进入第一主判断链路。

## 2. 当前状态

第一版 MVP 已完成，当前进入 MVP 后的稳定化与扩展阶段。

截至 `2026-04-27`，已落地能力：

- Watchlist 管理
- IBKR TWS 只读接入
- 真实/模拟 TWS profile 单切换
- `CanonicalSnapshot` 统一快照
- 快照缓存和后端自动刷新
- 核心指标计算：当前价、日涨跌、52W/90D 高点回撤、52W/90D 低点涨幅、持仓盈亏、PE、增长率、PEG
- PEG 驱动估值标签：`低估 / 合理 / 高估`
- 状态引擎：当前状态、上一次状态、是否变化
- Telegram 通知发送和测试
- 可配置提醒规则 v1
- 提醒规则冷却、边界触发、发送/失败/抑制统计
- 策略/评分/扫描最小脚手架
- `/api/scanner` 策略线索扫描
- Web 看板：`Overview / Monitor / Alerts / Portfolio / Settings`
- 追踪页 `区间位置` 列：52W / 90D 分组、High/Low chip、区间进度条
- IBKR 请求超时与手动刷新防卡住保护
- 根目录一键安装和一键启动脚本

当前还没有落地：

- 独立策略计划表
- 买入区间、卖出区间、止盈、止损的完整计划模型
- 标的详情页
- 图表工作台
- WebSocket 增量推送
- 自动下单
- 回测系统

## 3. 核心原则

项目按以下原则继续开发：

- 本地优先：默认运行在个人电脑上。
- 只读优先：IBKR 默认只读，不自动下单。
- 规则优先：核心判断来自数据、指标和规则，不依赖 AI。
- 页面只展示：前端不自行计算核心业务指标。
- 快照统一：核心判断围绕 `CanonicalSnapshot` 展开。
- 低耦合：外部接入、领域判断、通知投递、页面展示彼此分离。
- 单人维护：文档和架构不做过度团队化设计。

## 4. 当前主链路

快照主链路：

```text
IBKR / Mock
  -> SnapshotBuilder
  -> CanonicalSnapshot
  -> SnapshotPipelineService
  -> StateEngine
  -> NotificationService
  -> SnapshotCacheService
  -> Web
```

策略线索链路：

```text
CanonicalSnapshot
  -> StrategyEvaluator
  -> ScoringService
  -> ScannerService
  -> /api/scanner
  -> Monitor 策略线索
```

提醒链路：

```text
CanonicalSnapshot
  -> MetricRegistry
  -> AlertRuleEngine
  -> NotificationService
  -> Telegram
  -> Alert history / rule counters
```

关键边界：

- `SnapshotBuilder` 只负责构建标准化快照。
- `SnapshotPipelineService` 负责编排状态和通知。
- `ScannerService` 不写入快照，不修改 watchlist。
- `AlertRuleEngine` 只判断规则，不直接发 Telegram。
- `Telegram adapter` 只发送消息，不决定是否提醒。

## 5. 目录结构

当前工程结构：

```text
TradeBrain/
  README.md
  .gitignore
  install.ps1
  start.ps1
  backend/
    pyproject.toml
    app/
      adapters/
      api/
      application/
      config/
      core/
      domains/
      jobs/
      observability/
    tests/
  web/
    package.json
    src/
      app/
      hooks/
      pages/
      shared/
  docs/
    design.md
    handoff.md
```

说明：

- 真正后端源码在 `backend/app`。
- `backend/backend` 是空目录，可以忽略或删除。
- `backend/tradebrain.db*` 是本地运行数据，不是源码。
- `.env` 是本地配置，不应提交。

## 6. 后端分层

后端采用单体分层架构：

```text
api -> application -> domains -> adapters
```

### `api/`

FastAPI 路由入口，只负责 HTTP 请求和响应。

不负责：

- 复杂业务判断
- 直接拼装 IBKR 原始数据
- 直接发送 Telegram

### `application/`

应用编排层，负责把领域逻辑、存储和外部适配器串起来。

当前重要 service：

- `SnapshotBuilder`：构建 `CanonicalSnapshot`
- `SnapshotPipelineService`：快照后处理，附加状态并触发通知
- `SnapshotCacheService`：快照缓存、刷新状态、失败兜底
- `StateEngine`：估值状态持久化和变化检测
- `AlertRuleService`：提醒规则 CRUD 和元数据
- `NotificationService`：通知发送、历史记录、规则统计
- `ScannerApplicationService`：读取最近快照并调用扫描域服务
- `WatchlistService`：watchlist CRUD 和名称补全

### `domains/`

领域层，放业务对象、规则和纯计算。

当前主要 domain：

- `market`：行情快照
- `portfolio`：账户和持仓
- `indicators`：核心指标计算
- `valuation`：PEG 估值标签
- `state`：状态对象和状态判断
- `metrics`：提醒规则可引用的指标字典
- `alerting`：提醒规则判断和消息候选
- `alerts`：提醒历史对象
- `strategy`：策略规则和计划方向
- `scoring`：标的评分
- `scanner`：策略线索候选
- `watchlist`：关注标的基础信息
- `preferences`：IBKR / Telegram / 快照刷新设置

领域层原则：

- 不直接依赖数据库 session
- 不直接依赖 IBKR、Telegram、FastAPI
- 尽量保持同输入同输出

### `adapters/`

适配外部系统和基础设施。

当前 adapter：

- `ibkr`：TWS / IBKR 接入
- `telegram`：Telegram Bot API
- `persistence/sqlite`：SQLite repository

## 7. 前端结构

前端使用 React + TypeScript + Vite。

当前页面：

- `Overview`：快照摘要和 broker 状态
- `Monitor`：watchlist、行情指标、区间位置、估值状态、策略线索
- `Alerts`：提醒规则管理和发送统计
- `Portfolio`：账户和持仓
- `Settings`：IBKR、Telegram、快照刷新配置

当前复用点：

- `useSnapshotResource`：统一读取和接收快照刷新事件
- `snapshotEvents`：侧边栏手动刷新后广播快照
- `alerts/` 子组件：提醒页拆分
- `settings/` 子组件：设置页拆分

前端原则：

- 不自行计算核心策略评分
- 不自行计算核心指标，只做展示格式化和可视化映射
- 不直接理解 IBKR 原始字段
- 优先消费后端 API
- 页面组件只做展示和交互

## 8. 当前 API

核心 API：

- `GET /api/health`
- `GET /api/watchlist`
- `POST /api/watchlist`
- `PATCH /api/watchlist/{entry_id}`
- `DELETE /api/watchlist/{entry_id}`
- `GET /api/snapshot`
- `POST /api/snapshot/refresh`
- `GET /api/states`
- `GET /api/scanner`
- `GET /api/alerts`

提醒规则 API：

- `GET /api/alert-rules`
- `POST /api/alert-rules`
- `PATCH /api/alert-rules/{rule_id}`
- `DELETE /api/alert-rules/{rule_id}`
- `GET /api/alert-rules/metadata`
- `POST /api/alert-rules/reset-counters`

设置 API：

- `GET /api/settings/notifications`
- `PUT /api/settings/notifications`
- `POST /api/settings/notifications/test`
- `GET /api/settings/ibkr`
- `PUT /api/settings/ibkr`
- `POST /api/settings/ibkr/test`
- `GET /api/settings/snapshot-refresh`
- `PUT /api/settings/snapshot-refresh`

## 9. 数据与存储

当前数据库：

- SQLite
- WAL 模式
- 默认位置：`backend/tradebrain.db`

当前已落库内容：

- watchlist
- 状态
- 快照缓存
- IBKR 设置
- Telegram 设置
- 快照刷新设置
- 提醒规则
- 提醒历史

## 9.1 快照刷新与防卡住

当前快照刷新采用“最近成功快照 + 手动/自动刷新”的模式。

规则：

- `GET /api/snapshot` 优先读取最近一次成功快照。
- `POST /api/snapshot/refresh` 触发完整刷新。
- 刷新失败时保留旧快照，并记录错误。
- 后端同一时间只允许一轮快照刷新，避免自动刷新和手动刷新互相叠加。
- 前端手动刷新有超时提示，不会一直转圈。

IBKR 相关超时配置：

- `IBKR_CONNECT_TIMEOUT_SECONDS=5.0`
- `IBKR_REQUEST_TIMEOUT_SECONDS=12.0`
- `IBKR_MARKET_DATA_WAIT_SECONDS=8.0`

这些配置只控制等待上限，不改变行情或账户数据计算逻辑。

## 9.2 区间位置指标

`Monitor` 页的 `区间位置` 列展示后端已经计算好的指标：

- `High -x%`：当前价距离区间高点的百分比。
- `Low +x%`：当前价相对区间低点上涨的百分比。
- `52W`：过去一年区间。
- `90D`：过去 90 天区间。
- 细进度条：当前价在 low/high 区间中的相对位置。

涉及字段：

- `high_52w`
- `low_52w`
- `drawdown_from_52w_high_percent`
- `gain_from_52w_low_percent`
- `high_90d`
- `low_90d`
- `drawdown_from_90d_high_percent`
- `gain_from_90d_low_percent`

边界：

- 高低点来自 IBKR 历史 K 线或 mock 生成。
- 指标计算在 `domains/indicators`。
- 前端只做 chip、颜色和进度条展示。

换电脑说明：

- 不复制数据库也能运行。
- 不复制数据库会丢失本地 watchlist、提醒规则、IBKR/Telegram 页面配置、提醒历史。
- 如果要完整迁移使用状态，需要复制 `backend/tradebrain.db` 以及同目录 WAL/SHM 文件，最好先关闭后端再复制。

## 10. 提醒规则 v1

当前提醒规则采用统一模型，不为每种提醒单独建一套表。

核心字段：

- `source`：数据来源，例如 watchlist / portfolio
- `metric`：指标，例如当前价、52W 回撤、账户净值
- `operator`：高于、低于、等于、上穿、下穿、变为
- `threshold_value`：阈值
- `cooldown_seconds`：冷却时间
- `edge_only`：是否只在首次命中时提醒
- `sent_count / failed_count / suppressed_count`：发送统计

当前支持：

- 价格高于 / 低于
- 日涨跌幅阈值
- 52W / 90D 回撤阈值
- 估值状态变化
- 账户净值 / 可用资金 / Buying Power 阈值

后续提醒规则应继续基于 `MetricRegistry` 扩展，不要在规则引擎里硬写一堆零散字段。

## 11. 策略、评分、扫描

当前为最小版本。

`domains/strategy`：

- 当前有 `StrategyRule`
- 当前有 `StrategyEvaluator`
- 后续买入区间、卖出区间、止损、止盈、计划状态应在这里扩展

`domains/scoring`：

- 当前评分基于估值标签、52W 回撤、日内跌幅
- 输出总分和评分拆解
- 不代表买卖建议，只是排序和线索

`domains/scanner`：

- 当前组合 strategy + scoring
- 输出 `ScannerCandidate`
- 通过 `/api/scanner` 给追踪页展示

下一步最重要：

- 建立独立策略计划模型
- 不把买卖计划字段继续塞进 watchlist
- 让提醒规则可以引用策略计划字段

## 12. 当前不做

短期不做：

- 自动下单
- 回测系统
- 多用户
- 云同步
- 复杂策略 DSL
- AI 主决策
- 高频实时交易
- 多券商接入

可以后续评估：

- 标的详情页
- 图表增强
- WebSocket 增量刷新
- 任务中心
- 策略计划复盘

## 13. 下一步

建议下一阶段顺序：

1. 抽出策略计划模型和数据库表
2. 支持买入区间、卖出区间、止损、止盈
3. 让提醒规则引用策略计划字段
4. 扩展 `/api/scanner`，让策略线索更接近实际交易计划
5. 继续验证真实 / 模拟 TWS 下行情、账户、PEG 字段质量
6. 根据使用反馈决定是否补标的详情页和图表

## 14. 文档维护规则

单人项目只保留三类文档入口：

- `README.md`：安装、启动、当前能力、常用命令
- `docs/handoff.md`：换电脑、换线程、恢复上下文
- `docs/design.md`：产品、架构、技术和长期设计

旧文档合并关系：

- `prd.md` -> `design.md`
- `mvp.md` -> `design.md`
- `arch.md` -> `design.md`
- `tech.md` -> `design.md`
