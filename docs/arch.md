# TradeBrain 模块设计文档

## 文档信息

- 版本：v0.3
- 状态：当前有效（长期模块蓝图）
- 更新日期：2026-04-24
- 适用范围：TradeBrain 第一版
- 文档目的：明确系统主链路、模块边界、模块依赖、第一版实现优先级与参考项目，作为后续 MVP、技术方案和编码实现的上游文档

## 0. 当前阶段说明

截至 `2026-04-24`，TradeBrain 第一版 MVP 已完成，并已完成提醒规则 v1、快照 pipeline 重构、策略/评分/扫描最小脚手架。

当前已落地的 MVP 子链路为：

`数据接入 -> 标准化快照 -> 指标计算 -> PEG 估值状态 -> 预警判定 -> 通知发送 -> 看板展示`

当前额外落地的后续链路为：

`CanonicalSnapshot -> StrategyEvaluator -> ScoringService -> ScannerService -> /api/scanner -> Monitor 策略线索`

本文件保留的是更长期的模块蓝图，因此仍保留 `tasks/`、更复杂策略和更完整投影层等扩展模块，不代表它们都已在当前 MVP 中实现。

## 1. 文档定位

本文件回答的问题不是“策略怎么写”，而是“系统应该怎么拆”。

在 TradeBrain 第一版中，必须先把系统框架稳定下来，再去细化策略细节。原因如下：

- 本项目的核心不是纯分析，而是长期运行的辅助交易工作台。
- 系统需要持续接收行情、账户、持仓与任务状态变化，必须先有稳定骨架。
- 可视化、任务、预警、盈透接入之间依赖很强，若不先定边界，后续容易反复返工。

本文件是以下工作的上游依据：

- MVP 功能清单
- 技术方案草案
- 数据表设计
- API 设计
- 页面信息架构

## 2. 设计目标

TradeBrain 第一版的框架设计要满足以下目标：

- 支持本地长期运行，持续监控多个股票、ETF、债券标的。
- 以“数据 -> 指标 -> 状态 -> 任务 -> 预警 -> 看板”的主链路驱动系统。
- 让规则逻辑、外部接入、页面展示、历史存储彼此解耦。
- 即使关闭 AI，系统也能正常完成监控、任务和预警。
- 第一版默认只读，不自动下单。

## 3. 系统主链路

TradeBrain 长期主链路规划为：

`数据接入 -> 标准化快照 -> 指标计算 -> 状态判断 -> 任务生成 -> 预警判定 -> 通知发送 -> 看板投影 -> 页面展示`

当前 MVP 已实际落地的链路为：

`数据接入 -> 标准化快照 -> 指标计算 -> PEG 状态判断 -> 预警判定 -> 通知发送 -> 页面展示`

说明如下：

- 数据接入负责从盈透和配置文件获取原始输入。
- 标准化快照负责把不同来源的数据合成统一上下文。
- 指标计算负责生成“距高点回撤”“距买点”“距止损位”等关键字段。
- 状态判断负责给出结构化状态，例如观察、接近触发、待执行、风险处理。
- 任务生成负责把状态变化落成可操作的待办。
- 预警路由负责控制 Telegram 推送和去重节流。
- 看板投影负责生成适合前端读取的读模型。
- 页面展示只负责读取结果，不直接承载业务判断。

AI 是旁路模块，不在主链路上。

## 4. 总体模块结构

建议采用如下目录结构：

```text
tradebrain/
  config/                   # env, profiles, watchlists, strategy params
  core/
    types/                  # 通用类型、枚举、时间/价格/百分比模型
    events/                 # MarketDataUpdated, SnapshotBuilt, StateChanged...
    ports/                  # repository / broker / notifier 抽象接口
  domains/
    market/                 # 行情标准化、K线与快照领域模型
    portfolio/              # 账户、持仓、风险敞口领域模型
    indicators/             # 纯函数指标计算
    strategy/               # 策略计划与策略判断
    scoring/                # 标的评分
    scanner/                # 扫描候选与策略线索
    tasks/                  # 交易任务模型、任务状态
    alerting/               # 预警判定规则、候选消息生成
    alerts/                 # 预警历史模型、发送结果记录
  application/             # 用例层与编排层
    build_snapshot.py
    evaluate_state.py
    plan_tasks.py
    notifications/          # 通知发送、预警历史保存、通道选择
    project_dashboard.py
  adapters/
    ibkr/                   # ib_async / IBKR 接入
    telegram/               # Telegram 推送
    persistence/
      sqlite/               # 本地存储实现
  projections/             # 看板读模型
  jobs/                    # 实时监控、定时扫描、重建读模型
  apps/
    api/                    # FastAPI / WebSocket
    web/                    # 看板前端
  observability/           # 日志、健康检查、同步状态、运行告警
  tests/
```

这版结构相较于早期草图的优化点：

- 使用 `application/` 替代笼统的 `services/`，专门负责编排。
- 使用 `core/ports/` 声明抽象接口，避免 `repositories/` 和实现耦合。
- 使用 `adapters/persistence/sqlite/` 放存储实现，便于未来替换。
- 使用 `projections/` 单独承接看板读模型，避免页面直接查原始表。
- 使用 `jobs/` 明确长期运行任务，而不是混用在业务服务中。
- 增加 `observability/`，专门处理运行状态、连接异常和日志。

## 5. 模块职责与边界

### 5.1 `config/`

职责：

- 管理环境变量、运行模式、watchlist、分组配置、策略参数、预警参数。

输入：

- `.env`
- 本地配置文件
- 用户在配置页修改后的配置

输出：

- 系统统一运行配置

不负责：

- 业务判断
- 数据拉取

### 5.2 `core/types/`

职责：

- 定义跨模块共用的基础类型和枚举。

示例：

- `AssetId`
- `Money`
- `Percent`
- `Price`
- `Market`
- `AssetType`
- `TaskStatus`
- `AlertLevel`

原则：

- 不依赖外部系统
- 不包含业务流程代码

### 5.3 `core/events/`

职责：

- 定义系统内部事件类型。

第一版建议事件：

- `MarketDataUpdated`
- `PortfolioSynced`
- `SnapshotBuilt`
- `IndicatorsCalculated`
- `StateEvaluated`
- `TaskChanged`
- `AlertRaised`
- `ProjectionUpdated`

原则：

- 事件只表达“发生了什么”
- 不在事件对象内塞业务逻辑

### 5.4 `core/ports/`

职责：

- 声明对外部系统和存储的抽象接口。

示例：

- `BrokerPort`
- `MarketDataPort`
- `NotifierPort`
- `SnapshotRepository`
- `StateRepository`
- `TaskRepository`
- `AlertRepository`
- `ProjectionRepository`

原则：

- 领域层只依赖接口，不依赖具体实现

### 5.5 `domains/market/`

职责：

- 统一定义行情、K 线、快照相关领域模型。
- 负责把 IBKR 数据映射为系统内部标准格式。

输出对象示例：

- `Quote`
- `Bar`
- `MarketSnapshot`

### 5.6 `domains/portfolio/`

职责：

- 管理账户、持仓、盈亏、风险敞口的领域模型。

输出对象示例：

- `AccountSnapshot`
- `PositionSnapshot`
- `ExposureSummary`

### 5.7 `domains/indicators/`

职责：

- 提供纯函数指标计算，不依赖数据库和外部 API。

第一版重点指标：

- 距 52 周高点回撤
- 距阶段高点回撤
- 距买入区距离
- 距止盈位距离
- 距止损位距离
- 持仓盈亏
- 均线
- 波动率或 ATR

原则：

- 相同输入必须得到相同输出
- 不做副作用操作

### 5.8 `domains/strategy/`

职责：

- 基于标准化快照、指标结果和用户计划，输出结构化策略判断。
- 后续买入区间、卖出区间、止盈、止损应放在这里或专门的策略计划子模块中，不继续塞进 watchlist。

长期统一状态：

- `观察`
- `接近触发`
- `待执行`
- `风险处理`

输出字段至少包括：

- 当前状态
- 触发原因
- 建议动作
- 风险等级
- 建议价格区间

### 5.9 `domains/tasks/`

职责：

- 定义交易任务模型和任务状态机。

建议任务状态：

- `待观察`
- `接近触发`
- `待执行`
- `已完成`
- `已忽略`
- `已失效`

任务必须回答：

- 这个标的现在该不该做事
- 该做什么
- 为什么
- 多紧急

### 5.9.1 `domains/scoring/`

职责：

- 对标的做轻量评分，输出总分和评分拆解。
- 第一版评分基于估值标签、52W 回撤和日内跌幅。

原则：

- 输入来自 `CanonicalSnapshot` 中的标准化字段。
- 不直接访问 IBKR、数据库或前端状态。
- 不替代交易策略，只提供排序和提示信号。

### 5.9.2 `domains/scanner/`

职责：

- 组合 `strategy` 和 `scoring`，输出候选标的。
- 为 `/api/scanner` 和前端 `Monitor` 策略线索区提供数据。

原则：

- 不修改 watchlist。
- 不写入快照。
- 不进入 `SnapshotBuilder`。
- 优先作为独立查询入口，而不是扩展 `CanonicalSnapshot` 主契约。

### 5.10 `domains/alerting/` 与 `domains/alerts/`

职责：

- `domains/alerting/` 定义预警判定规则、消息生成和提醒候选。
- `domains/alerts/` 定义已生成预警事件、发送状态和历史记录。
- 告警判断不直接依赖 Telegram、数据库或前端页面。

第一版重要事件：

- 状态从观察升级到接近触发
- 状态从接近触发升级到待执行
- 跌破止损或风险位
- 达到止盈区
- 盈透同步失败
- Telegram 发送失败

### 5.11 `application/`

职责：

- 作为系统编排层，连接领域逻辑、外部适配器和存储接口。

第一版关键用例：

- `build_snapshot.py`
- `evaluate_state.py`
- `plan_tasks.py`
- `notifications/service.py`
- `project_dashboard.py`

原则：

- 编排调用顺序
- 不承载复杂领域规则
- 不直接耦合 UI

### 5.12 `adapters/ibkr/`

职责：

- 接入 `ib_async`
- 连接 TWS 或 IB Gateway
- 获取账户、持仓、订单、行情

第一版原则：

- 默认只读
- 连接异常要有明确状态
- 支持自动重连或至少明确失败状态

### 5.13 `adapters/telegram/`

职责：

- 接收已经生成好的通知文本
- 调用 Telegram API 发送消息

不负责：

- 决定是否提醒
- 决定消息优先级
- 保存预警历史

### 5.14 `adapters/persistence/sqlite/`

职责：

- 提供本地 SQLite 存储实现。

第一版建议落库对象：

- 快照
- 状态
- 任务
- 预警
- 看板读模型
- 配置

### 5.15 `projections/`

职责：

- 生成看板专用查询模型。

第一版建议投影：

- 监控列表读模型
- 持仓页读模型
- 任务中心读模型
- 首页总览读模型
- 系统状态读模型

原则：

- 页面优先读投影，不直接拼原始表

### 5.16 `jobs/`

职责：

- 管理长期运行或周期运行任务。

第一版任务：

- `live_monitor`
- `scheduled_scan`
- `rebuild_readmodels`

说明：

- `live_monitor` 负责实时或准实时行情驱动
- `scheduled_scan` 负责分钟级、小时级补扫
- `rebuild_readmodels` 负责异常恢复和投影重建

### 5.17 `apps/api/`

职责：

- 提供 REST API 与 WebSocket。

第一版建议：

- REST 提供历史查询、配置修改、任务操作
- WebSocket 提供看板实时刷新

### 5.18 `apps/web/`

职责：

- 提供本地 Web 看板界面。

当前已落地页面：

- 首页总览
- 监控列表页
- 账户持仓页
- 配置页
- 提醒规则页

长期可补页面：

- 标的详情页
- 任务中心页

### 5.19 `observability/`

职责：

- 统一管理日志、健康检查、同步状态、最近成功时间和错误告警。

第一版必须能看见：

- IBKR 是否连接成功
- 最近一次行情刷新时间
- 最近一次任务扫描时间
- 最近一次 Telegram 发送时间
- 当前是否存在异常

## 6. 模块依赖规则

为避免系统越做越乱，模块依赖必须遵守以下规则：

- `domains/` 不能依赖 `adapters/`
- `domains/` 不能依赖 `apps/`
- `domains/scanner` 可以组合其他 domain service，但不应依赖数据库。
- `application/` 可以依赖 `domains/` 和 `core/ports/`
- `adapters/` 实现 `core/ports/` 中定义的接口
- `apps/` 只能依赖 `application/`、`projections/` 和读接口
- `jobs/` 只能通过 `application/` 触发业务流程
- `observability/` 可被所有运行时模块调用，但不反向驱动业务逻辑

## 7. 第一版关键对象

第一版建议围绕以下对象建立统一模型：

- `Asset`
- `CanonicalSnapshot`
- `IndicatorSet`
- `StrategyState`
- `Task`
- `Alert`
- `DashboardRow`

其中：

- `CanonicalSnapshot` 是系统判断的统一输入
- `StrategyState` 是规则引擎的统一输出
- `ScannerCandidate` 是策略线索的统一输出
- `Task` 是给用户执行的统一动作单元
- `Alert` 是对外推送和站内提示的统一消息单元
- `DashboardRow` 是前端列表的统一展示单元

## 8. 第一版实现优先级

### P0：必须落地

- `config/`
- `core/types/`
- `core/events/`
- `core/ports/`
- `domains/market/`
- `domains/portfolio/`
- `domains/indicators/`
- `domains/strategy/`
- `domains/tasks/`
- `domains/alerts/`
- `application/`
- `adapters/ibkr/`
- `adapters/telegram/`
- `adapters/persistence/sqlite/`
- `projections/`
- `jobs/`
- `apps/api/`
- `apps/web/`
- `observability/`

### P1：可以后补

- 更复杂的自定义指标 DSL
- 多数据源扩展
- 更多券商适配器
- 更复杂的任务协同与批量操作

### P2：暂不做

- 自动下单执行层
- 多用户权限系统
- 云端同步
- 完整回测平台

## 9. 参考项目与借鉴点

本项目不直接照搬单一高星项目，而是按模块借鉴成熟项目的优点。

### 9.1 IBKR 接入

- `ib-api-reloaded/ib_async`
- `erdewit/ib_insync`（接口设计可参考，仓库已归档）
- `IbcAlpha/IBC`

借鉴点：

- Python 下对 IBKR 的现代化接入
- TWS / Gateway 的连接模式
- 账户、持仓、行情获取接口

### 9.2 状态、任务、预警流

- `freqtrade/freqtrade`

借鉴点：

- 状态驱动流程
- Telegram 消息组织
- 长时间运行任务的结构
- SQLite 持久化路线

### 9.3 本地优先产品形态

- `afadil/wealthfolio`

借鉴点：

- 本地优先
- Web 与本地运行结合
- 前端、后端、存储分层清晰

### 9.4 投资看板信息架构

- `ghostfolio/ghostfolio`

借鉴点：

- 投资类产品的信息组织
- 前后台分离
- 读模型导向的展示方式

### 9.5 事件驱动和领域边界

- `nautechsystems/nautilus_trader`
- `QuantConnect/Lean`

借鉴点：

- 事件驱动思想
- 强边界领域模型
- 数据流和状态流分离

### 9.6 指标和研究能力

- `polakowo/vectorbt`
- `mementum/backtrader`

借鉴点：

- 指标计算层组织
- 时间序列处理方式
- 研究工具与生产系统的边界意识

## 10. 第一版设计结论

TradeBrain 第一版应按以下原则推进：

- 先做系统骨架，再做策略细化。
- 先保证监控、任务、预警、持仓联动跑通，再补 AI。
- 所有判断必须围绕统一快照展开。
- 所有页面优先读取投影结果，而不是直接查原始数据。
- 所有外部系统必须通过适配器接入。
- 所有核心业务判断必须留在领域层与应用层。

## 11. 下一步建议

这份模块设计文档对应的第一阶段工作已完成。下一步应按如下顺序继续：

1. 抽出策略计划模型：买入区间、卖出区间、止损、止盈、计划状态
2. 让提醒规则可以引用策略计划字段
3. 继续扩展 scanner 的候选逻辑和前端展示
4. 在当前 MVP 基础上做 live/paper 联调和稳定化
