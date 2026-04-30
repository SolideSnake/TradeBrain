# TradeBrain 下一版设计草案 v2.0

## 文档信息

- 版本：v2.0 草案
- 状态：下一版设计，未并入主设计文档
- 创建日期：2026-04-28
- 主文档：`docs/design.md`

## 1. 文档目的

本文只记录下一版准备评估或设计的增量内容。

主设计文档 `docs/design.md` 继续代表当前有效设计；本文件中的内容在功能稳定、决策明确后，再合并回主设计文档。

本文件不维护设计变更历史，也不复制主设计文档中的完整结构。

## 2. 下一版方向

v2.0 的重点不是重做现有系统，而是在当前监控、提醒、扫描能力之上，增加更适合深挖单个标的和接入 AI 能力的基础。

当前确定方向：

- 接入 AI 能力，但暂不设计具体 AI 功能。
- 追踪界面中的每一个标的变成可跳转页面。
- 标的详情页展示更详细的信息，具体信息范围待定。
- 仪表盘页面增加市场热力图，可在一天、一周、一个月之间切换，并支持板块和具体股票两个层级。

## 3. AI 接入

### 3.1 目标

v2.0 可以为 AI 接入预留基础能力，但不急于把 AI 做成具体产品功能。

AI 在当前阶段的定位是辅助能力入口，而不是交易主判断链路。

### 3.2 原则

- 不做 AI 自动决策。
- 不做 AI 自动下单。
- 不让 AI 直接改写核心交易规则。
- 不让 AI 取代提醒规则、指标计算、扫描评分等确定性逻辑。
- AI 输出只作为解释、摘要、研究或辅助理解的候选能力。

### 3.3 预留边界

后续如果接入 AI，优先把它放在独立服务或独立应用层能力中，避免侵入现有领域模型。

建议边界：

- 输入来自已有快照、标的资料、提醒记录、扫描结果或用户显式选择的数据。
- 输出默认是文本、摘要、解释或建议线索。
- 输出不直接写入交易计划、提醒规则或账户相关数据，除非用户明确确认。
- 所有 AI 生成内容需要在界面上和确定性指标区分开。

### 3.4 暂不定义

本版暂不定义具体 AI 功能，例如：

- AI 标的分析
- AI 财报摘要
- AI 新闻总结
- AI 策略生成
- AI 聊天助手
- AI 自动生成提醒规则

这些能力可以后续单独拆成更小的设计条目。

## 4. 标的详情页

### 4.1 目标

追踪界面中的每一个标的都可以点击进入独立页面，用来承载比列表更详细的信息。

当前追踪页适合横向对比多个标的；详情页适合纵向查看单个标的。

### 4.2 页面入口

预期入口：

- Monitor / 追踪界面中的标的代码或标的名称可以点击。
- 点击后进入该标的的详情页。
- 从详情页可以返回追踪界面。

具体路由命名待实现时确定。

### 4.3 页面内容

详情页需要展示哪些信息目前未定。

可候选的信息包括：

- 当前快照信息
- 区间位置指标
- 持仓与盈亏信息
- 估值标签和 PEG 相关字段
- 提醒规则命中情况
- 最近状态变化
- 扫描评分或策略线索
- 图表或历史趋势
- 备注、计划、观察记录

最终展示内容应以实际使用频率为准，不在第一版详情页里堆满所有字段。

### 4.4 设计原则

- 详情页不重新计算核心指标，只展示后端给出的结果。
- 列表页继续承担多标的扫描和对比，详情页承担单标的深挖。
- 详情页第一版可以先轻量实现，后续再逐步接入图表、计划、AI 辅助等能力。
- 如果某些信息还没有稳定数据来源，可以先留出结构，不强行做假数据。

## 5. 仪表盘热力图

### 5.1 目标

仪表盘页面增加热力图，用来快速观察市场或关注范围内的强弱分布。

热力图不替代追踪列表，而是作为更直观的总览入口，让用户先看到哪里在变强、哪里在变弱，再决定是否进入板块、个股或标的详情页继续查看。

### 5.2 时间维度

热力图支持三个时间范围切换：

- 一天
- 一周
- 一个月

时间切换用于改变涨跌幅、强弱排序或颜色映射的统计窗口。

具体数据来源和计算方式待实现时确定，但前端不自行计算核心指标，应优先使用后端提供的聚合结果。

### 5.3 展示层级

热力图支持两个层级：

- 板块热力图：展示不同板块的整体表现。
- 个股热力图：展示具体股票的表现。

板块和个股之间可以通过切换控件切换，也可以后续评估从板块点击下钻到对应个股。

### 5.4 设计原则

- 仪表盘热力图只做总览，不承载所有交易判断。
- 颜色表达涨跌或强弱时，需要保持和系统其它页面的涨跌语义一致。
- 板块、个股、时间范围的含义需要明确，避免用户误解为实时预测。
- 全市场热力图使用独立市场数据源，不依赖用户持仓或追踪列表。

### 5.5 首版实现范围

热力图首版目标就是全市场覆盖，而不是只覆盖当前持仓或追踪列表。

原因：

- 用户需要先看到整个市场的强弱分布，再决定要深入哪个板块或标的。
- 持仓和追踪列表只能反映个人已关注范围，容易错过市场整体变化。
- 全市场热力图需要单独的数据源、股票池、板块分类、权重和历史行情缓存。

首版范围：

- `universe = us_market`：美国股票全市场。
- `level = sector`：按板块 / 分组聚合。
- `level = stock`：展示具体股票。
- `range = 1d | 1w | 1m`：一天、一周、一个月。

首版默认不包含 OTC，不把 ETF、基金、权证、优先股、ADR 等混进普通股票热力图。后续可以增加筛选项：

- `include_etf`
- `include_adr`
- `exchange`
- `market_cap_bucket`
- `watchlist_only`
- `portfolio_only`

### 5.6 指标定义

热力图需要区分“面积”和“颜色”两个含义。

面积：

- 首选 `market_cap`，更接近 Finviz 这类全市场热力图的阅读方式。
- 如果暂时缺少 `market_cap`，可以使用 `close * volume` 作为流动性权重。
- 如果两个字段都缺失，才退回等权面积。

颜色：

- 使用所选时间范围内的涨跌幅。
- `1d` 使用最近交易日收盘价相对前一交易日收盘价的涨跌幅。
- `1w` 使用最近交易日收盘价相对约 5 个交易日前收盘价的涨跌幅。
- `1m` 使用最近交易日收盘价相对约 21 个交易日前收盘价的涨跌幅。
- 如果某个标的缺少对应时间范围数据，显示中性颜色，并在 tooltip 中标明“数据不足”。

板块聚合：

- 板块涨跌幅优先使用子股票的市值加权平均。
- 如果缺少市值，则使用流动性权重。
- 如果缺少权重，则使用等权平均。
- 板块面积为子股票面积之和。

### 5.7 数据来源

全市场热力图不能依赖 IBKR TWS 或现有 `CanonicalSnapshot`。

IBKR 适合做账户、持仓、少量关注标的行情，不适合作为全市场热力图主数据源。原因是：

- 全市场需要几千到上万只标的。
- TWS API 历史数据有 pacing 限制。
- IBKR 官方也说明它不是专门的历史市场数据供应商。
- 全市场 UI 需要稳定的批量行情、股票池、板块和权重数据。

因此 v2.0 需要新增市场数据源适配层。

全市场热力图需要四类数据：

- 股票池：当前活跃股票列表、交易所、证券类型、是否退市。
- 日线行情：全市场最近交易日和历史交易日的 OHLCV。
- 板块信息：sector / industry / SIC / 自定义板块映射。
- 权重信息：market cap，缺失时可用成交额或等权兜底。

首版推荐两条可选路线：

路线 A：Polygon / Massive。

- 用 `/v3/reference/tickers` 获取全市场股票池。
- 用 `/v2/aggs/grouped/locale/us/market/stocks/{date}` 获取某个交易日所有美国股票的日线 OHLCV。
- 用 ticker details 获取 `market_cap`、`sic_code`、`sic_description` 等公司参考信息。
- 板块可以先用 SIC 映射到 TradeBrain 自定义板块。

路线 B：EODHD。

- 用交易所股票列表和 EOD / bulk EOD 能力获取全市场日线。
- 用 fundamentals 获取 sector、industry、market capitalization。
- 如果后续要扩展到非美市场，EODHD 的全球交易所覆盖更方便。

首版默认实现建议：

- 默认 provider：Polygon / Massive。
- 默认市场：美国股票全市场。
- 日线数据：使用 Daily Market Summary 批量同步。
- 股票池：使用 All Tickers 同步活跃普通股。
- 板块：优先用 provider 字段；缺失时使用 SIC 映射。
- 权重：优先用 `market_cap`；缺失时用成交额兜底。

如果后续要扩展到香港、美股以外市场，优先评估 EODHD，因为它的全球交易所、历史 EOD 和基础数据覆盖更完整。

### 5.8 数据采集流程

建议流程：

```text
MarketDataProvider
  -> MarketUniverseSyncService
  -> MarketDailyBarSyncService
  -> MarketReferenceSyncService
  -> SQLite market_* tables
  -> HeatmapApplicationService
  -> GET /api/heatmap
  -> Overview / MarketHeatmapCard
```

同步策略：

1. 每天同步或刷新全市场股票池。
2. 每个交易日收盘后同步全市场日线数据。
3. 定期同步板块、行业、市值等参考数据。
4. 热力图 API 只读取本地 SQLite，不在用户打开页面时临时请求外部 API。
5. 前端切换 `1D / 1W / 1M` 时命中本地缓存，保证页面响应快。

### 5.9 数据可用性规则

不同时间范围的数据可用性：

| 时间范围 | 数据来源 | 首次可用性 | 说明 |
| --- | --- | --- | --- |
| `1D` | 最近两个交易日的全市场日线 | 同步最近 2 个交易日后可用 | 不依赖用户持仓或 watchlist |
| `1W` | 最近约 5 个交易日前后的日线 | 同步最近 1-2 周后可用 | 使用最近可用交易日对齐 |
| `1M` | 最近约 21 个交易日前后的日线 | 同步最近 1-2 个月后可用 | 使用最近可用交易日对齐 |

缺失规则：

- 没有最近价格：不显示该股票。
- 没有历史基准价：节点显示中性颜色，并标注数据不足。
- 没有板块：归入“未分类”。
- 没有市值：使用成交额或等权兜底。
- 停牌、退市、低流动性标的默认过滤，后续可在设置中打开。

### 5.10 板块与权重数据

板块数据首版不复用 `WatchlistEntry.group_name`。

全市场板块需要来自市场数据源或统一映射：

- 如果 provider 提供 `sector / industry`，直接使用。
- 如果 provider 只提供 SIC，维护一份 `sic_sector_map` 映射到 TradeBrain 板块。
- 如果无法分类，归入“未分类”，但不能阻塞热力图展示。

权重数据：

- 首选 `market_cap`。
- 其次使用 `close * volume`。
- 最后使用等权。

### 5.11 外部数据源策略

首版允许新增付费或免费额度有限的市场数据源，但必须做成可配置 adapter。

优先级：

1. 全市场批量日线能力。
2. 股票池和退市 / 活跃状态。
3. sector / industry / SIC 分类。
4. market cap 或可替代权重。
5. 价格、复权、交易日历规则清晰。

不建议通过网页抓取 Finviz、Yahoo 页面或其它非正式页面来构建核心数据源。

原因：

- 稳定性不可控。
- 限流和反爬风险高。
- 字段解释、复权规则、授权边界不清晰。
- 后续很难调试数据差异。

IBKR 继续作为账户和关注标的行情来源，不作为全市场热力图主数据源。

### 5.12 后端设计

新增全市场数据同步和热力图聚合能力。

建议新增领域目录：

- `domains/heatmap`：热力图节点、聚合规则、颜色指标定义。
- `domains/market_universe`：全市场股票池、板块分类、权重字段定义。

建议新增应用服务：

- `application/market_data_sync_service.py`：同步股票池、日线、参考数据。
- `application/heatmap_service.py`：读取本地市场数据，聚合 API 响应。

建议新增持久化：

- `market_symbols`：全市场股票池。
- `market_daily_bars`：日线 OHLCV。
- `market_symbol_profile`：板块、行业、市值、SIC 等参考数据。
- `market_data_sync_runs`：记录每次同步的时间、范围、状态和错误。

`market_symbols` 建议字段：

- `symbol`
- `market`
- `exchange`
- `name`
- `asset_type`
- `active`
- `currency`
- `source`
- `updated_at`

`market_daily_bars` 建议字段：

- `symbol`
- `market`
- `trade_date`
- `open`
- `high`
- `low`
- `close`
- `adjusted_close`
- `volume`
- `vwap`
- `currency`
- `source`
- `created_at`

`market_symbol_profile` 建议字段：

- `symbol`
- `market`
- `sector`
- `industry`
- `sic_code`
- `sic_description`
- `market_cap`
- `shares_outstanding`
- `source`
- `updated_at`

首版不强制做分钟级历史，也不需要回测级别的 K 线库；只要能支撑全市场 `1d / 1w / 1m` 热力图即可。

### 5.13 API 草案

新增接口：

```text
GET /api/heatmap?universe=us_market&level=sector&range=1d
```

参数：

- `universe`：`us_market`
- `level`：`sector | stock`
- `range`：`1d | 1w | 1m`
- `exchange`：可选，按交易所过滤
- `sector`：可选，按板块过滤
- `min_market_cap`：可选，过滤过小市值标的
- `include_etf`：可选，默认 false

响应草案：

```json
{
  "generated_at": "2026-04-30T10:00:00Z",
  "universe": "us_market",
  "level": "sector",
  "range": "1d",
  "size_metric": "market_cap",
  "color_metric": "return_percent",
  "source": "market_data_provider",
  "as_of_trade_date": "2026-04-29",
  "nodes": [
    {
      "id": "technology",
      "label": "Technology",
      "value": 12500000000000,
      "return_percent": 1.8,
      "children": [
        {
          "id": "AAPL",
          "symbol": "AAPL",
          "label": "AAPL",
          "value": 2800000000000,
          "return_percent": 0.9,
          "last_price": 180.12,
          "market_cap": 2800000000000,
          "sector": "Technology",
          "data_quality": "ok"
        }
      ]
    }
  ]
}
```

API 返回结构尽量保持前端库无关；前端可以把它转换成 ECharts treemap 需要的 `series.data`。

### 5.14 前端设计

热力图放在 `Overview / 仪表盘` 页面，作为资产走势和事件列表之外的市场强弱总览。

建议组件：

- `MarketHeatmapCard`
- `HeatmapRangeSwitch`
- `HeatmapLevelSwitch`
- `HeatmapChart`

交互：

- 时间切换：`1D / 1W / 1M`
- 层级切换：`板块 / 个股`
- hover 显示 tooltip：名称、涨跌幅、价格、面积指标、数据质量。
- 点击个股：进入标的详情页。
- 点击板块：首版可以切换到该板块下的个股，或后续实现下钻。

加载状态：

- 数据加载中显示骨架或空态。
- 无历史数据时保留热力图结构，但标注 `1W / 1M 数据不足`。
- API 失败时显示错误 banner，不影响仪表盘其它卡片。

### 5.15 技术选型

推荐首选 Apache ECharts 的 `treemap`。

理由：

- 股票热力图本质是 treemap：面积表达权重，颜色表达涨跌幅。
- ECharts 支持 treemap、tooltip、事件、颜色映射、Canvas 渲染和响应式尺寸。
- 当前前端是 React + TypeScript + Vite，可以直接接入 `echarts`，也可以使用 `echarts-for-react` 作为轻量 React 包装。

不建议首版直接手写 D3 treemap。

原因：

- D3 灵活但偏底层，会把布局、颜色、tooltip、resize、交互都压到项目自己维护。
- 当前项目更需要稳定可用的仪表盘组件，不需要从零实现图表引擎。

可选方案对比：

| 方案 | 当前 GitHub 热度 | 优点 | 风险 | 结论 |
| --- | --- | --- | --- | --- |
| Apache ECharts | 约 66k stars | 功能完整、交互强、Canvas 友好、treemap 成熟 | 比 Recharts 重一些 | 首选 |
| Recharts | 约 27k stars | React 风格好、接入简单、有 Treemap | 大量节点和复杂交互不如 ECharts 稳 | 备选 |
| Nivo | 约 14k stars | React + D3，组件化好 | 引入包较多，定制金融热力图仍需适配 | 备选 |
| D3 | 约 113k stars | 最灵活、生态最强 | 维护成本最高 | 不作为首版实现 |
| visx | 约 20k stars | 适合自研可视化组件 | 仍偏底层 | 暂不选 |

GitHub star 数会随时间变化；以上为 `2026-04-30` 调研时的近似值，只作为选型参考，不作为长期事实。

### 5.16 GitHub 与文档参考

高赞参考：

- [apache/echarts](https://github.com/apache/echarts)：Apache ECharts 主仓库。
- [hustcc/echarts-for-react](https://github.com/hustcc/echarts-for-react)：ECharts 的 React 包装组件。
- [recharts/recharts](https://github.com/recharts/recharts)：React 图表库，内置 Treemap。
- [plouc/nivo](https://github.com/plouc/nivo)：React + D3 图表组件库。
- [d3/d3](https://github.com/d3/d3)：底层可视化基础库。
- [airbnb/visx](https://github.com/airbnb/visx)：React 可视化低层组件集合。

官方文档参考：

- [ECharts Visual Map](https://echarts.apache.org/handbook/en/concepts/visual-map/)：颜色映射设计参考。
- [Recharts Treemap](https://recharts.github.io/en-US/api/Treemap/)：React Treemap API 参考。
- [Polygon / Massive All Tickers](https://polygon.io/docs/rest/stocks/tickers/all-tickers)：全市场股票池参考。
- [Polygon / Massive Daily Market Summary](https://polygon.io/docs/rest/stocks/aggregates/daily-market-summary)：单日全美国股票 OHLCV 批量数据参考。
- [EODHD Market Data API](https://eodhd.com/)：全球市场行情、历史数据和基础数据源参考。
- [EODHD Fundamental Data API](https://eodhd.com/lp/fundamental-data-api)：sector、industry、market cap 等参考字段。
- [IBKR Historical Market Data](https://interactivebrokers.github.io/tws-api/historical_data.html)：TWS API 历史行情能力参考。
- [IBKR Historical Data Limitations](https://interactivebrokers.github.io/tws-api/historical_limitations.html)：历史行情请求限制参考。

## 6. 待补充

后续可以在这里继续追加新的 v2.0 方向；当某个方向足够清晰时，再拆成独立章节。

待补充项暂空。

## 7. 并入主设计文档的条件

当 v2.0 内容满足以下条件后，再合并回 `docs/design.md`：

- 功能范围已经确定。
- 已经实现或决定近期必须实现。
- 接口、数据来源和页面职责基本稳定。
- 不再只是想法或占位。

合并后，本文件可以保留为草案归档，也可以删除；不需要额外维护设计变更历史。
