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

v2.0 的重点不是重做现有系统，而是增加功能。

当前确定方向：

- 追踪页中的每个标的支持跳转到标的详情页；详情页作为该标的的统一信息入口，可输入的买入卖出计划、新闻、根据估值模型得出的评分、异动归因。
- 仪表盘增加市场热力图，支持 1D / 1W / 1M 切换；支持“板块层级 → 个股层级”切换；颜色表达涨跌幅，面积表达市值或成交额；默认展示美股主要板块
- 仪表盘增加市场情绪指数卡片，展示当前情绪读数、区间标签（极度恐惧/恐惧/中性/贪婪/极度贪婪）、近阶段变化趋势，数据来源CNN。
- 仪表盘增加“市场大事件”和“今日交易主题”和“博主观点”模块；仅展示来源明确、置信度达标的内容。若无显著事件、无法归因或证据不足，则留空。

## 3. 标的详情页

### 3.1 目标

追踪界面中的每一个标的都可以点击进入独立页面，用来承载比列表更详细的信息。

当前追踪页适合横向对比多个标的；详情页适合纵向查看单个标的。

### 3.2 页面入口

预期入口：

- 追踪界面中的标的代码或标的名称可以点击。
- 点击后进入该标的的详情页。
- 从详情页可以返回追踪界面。

具体路由命名待实现时确定。

### 3.3 页面内容

- 标的总览：包括公司名、当前价格、区间位置、PEG、估值标签、持仓/目标持仓、所属行业
- 新闻与异动归因：新闻展示标题、来源、时间，提炼关键。异动归因用于展示个股最近一次显著价格行为的主要公开催化或主题归因；若无明确归因，则留空。详情页展示历史异动归因。
- 交易策略：买入策略和卖出策略2个模块
- 估值评分区：先做个简化的。

### 3.4 异动归因

异动归因用于解释具体标的最近一次显著价格行为的可能原因。

它属于标的详情页能力，不属于仪表盘能力。

追踪页可以只展示一个简短入口或摘要，例如“财报超预期”“板块共振”“未找到明确催化”；详细内容放在详情页。

每次异动归因可以显示：

- 触发时间
- 价格变化
- 成交量变化
- 是否跑赢板块或指数
- 主要公开催化
- 证据来源
- 置信度
- 更新时间

示例：

- `AMD`：财报超预期、数据中心业务强于预期、半导体板块共振。
- `NVDA`：AI 服务器需求和同行财报带动。
- `TSLA`：交付数据、毛利率、监管新闻或博主观点分歧。

如果某个标的没有明确催化、无法归因或证据不足，则异动归因留空。

### 3.5 设计原则

- 详情页不重新计算核心指标，只展示后端给出的结果。
- 详情页第一版可以先轻量实现，后续再逐步接入图表、计划、AI 辅助等能力。
- 如果某些信息还没有稳定数据来源，可以先留出结构，不强行做假数据。

## 4. 仪表盘热力图

### 4.1 目标

仪表盘页面增加热力图，用来快速观察市场或关注范围内的强弱分布。

热力图不替代追踪列表，而是作为更直观的总览入口，让用户先看到哪里在变强、哪里在变弱，再决定是否进入板块、个股或标的详情页继续查看。

### 4.2 时间维度

热力图支持三个时间范围切换：

- 一天
- 一周
- 一个月

时间切换用于改变涨跌幅、强弱排序或颜色映射的统计窗口。

具体数据来源和计算方式待实现时确定，但前端不自行计算核心指标，应优先使用后端提供的聚合结果。

### 4.3 展示层级

热力图支持两个层级：

- 板块热力图：展示不同板块的整体表现。
- 个股热力图：展示具体股票的表现。

板块和个股之间可以通过切换控件切换。

### 4.4 设计原则

- 仪表盘热力图只做总览，不承载所有交易判断。
- 颜色表达涨跌或强弱时，需要保持和系统其它页面的涨跌语义一致。
- 板块、个股、时间范围的含义需要明确，避免用户误解为实时预测。
- 全市场热力图使用独立市场数据源，不依赖用户持仓或追踪列表。

### 4.5 首版实现范围

热力图首版目标是美股全市场覆盖，而不是只覆盖当前持仓或追踪列表。

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

### 4.6 指标定义

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

### 4.7 数据来源

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

### 4.8 数据采集流程

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

### 4.9 数据可用性规则

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

### 4.10 板块与权重数据

板块数据首版不复用 `WatchlistEntry.group_name`。

全市场板块需要来自市场数据源或统一映射：

- 如果 provider 提供 `sector / industry`，直接使用。
- 如果 provider 只提供 SIC，维护一份 `sic_sector_map` 映射到 TradeBrain 板块。
- 如果无法分类，归入“未分类”，但不能阻塞热力图展示。

权重数据：

- 首选 `market_cap`。
- 其次使用 `close * volume`。
- 最后使用等权。

### 4.11 外部数据源策略

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

### 4.12 后端设计

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

### 4.13 API 草案

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

### 4.14 前端设计

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

### 4.15 技术选型

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

### 4.16 GitHub 与文档参考

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

## 5. 仪表盘

### 5.1 目标

v2.0 仪表盘增加“市场大事件 / 今日交易主题 / 博主观点”三类市场主线模块。

这些模块用于展示整个市场今天在交易什么。

这个功能不是预测，也不是买卖建议；它只展示来源明确、证据足够、置信度达标的市场线索。若没有显著事件、无法归因或证据不足，则对应模块留空。

### 5.2 仪表盘模块

仪表盘增加三个模块：

- 市场大事件：展示当天或近期对全市场有影响的事件。
- 今日交易主题：总结当天市场主要在交易的主题。
- 博主观点：展示用户指定 YouTube 频道中与当日市场相关的观点摘要。

如果没有显著事件、无法归因或证据不足，对应模块留空，不用强行填充。

### 5.3 市场大事件

市场大事件用于展示“今天市场发生了什么重要事情”。

候选类型：

- 宏观数据：CPI、PCE、非农、失业率、PMI、GDP。
- 利率与央行：FOMC、点阵图、鲍威尔讲话、美债收益率大幅变化。
- 市场波动：VIX 异动、主要指数大幅跳空、流动性冲击。
- 财报事件：大型科技股、半导体、银行等核心公司财报影响全市场。
- 地缘政治或政策：关税、监管、财政政策、重大国际事件。

展示条件：

- 必须有明确来源。
- 必须能解释影响范围，例如指数、板块、风格或资产类别。
- 置信度达到阈值才展示。
- 如果只是普通新闻或影响范围不清楚，不展示。

### 5.4 今日交易主题

今日交易主题用于回答“今天市场在交易什么”。

示例：

- 市场在交易降息预期升温。
- 市场在交易 AI 半导体财报主线。
- 市场在交易通胀回落和长端利率下行。
- 市场在交易风险偏好修复，成长股强于价值股。

生成规则：

- 主题必须由多个来源或多个市场信号支持。
- 只展示 1-3 个最强主题。
- 每个主题必须能展开查看证据来源。
- 如果没有形成清晰主线，模块留空。

主题证据可以来自：

- 指数表现
- 板块热力图
- 市场大事件
- 新闻来源
- 财报事件
- 宏观数据
- 博主观点

### 5.5 博主观点

博主观点是观点源，不是事实源。

首版固定支持以下用户指定来源：

- Nana 说美股：`https://youtube.com/@nanashuomeigu?si=WGYGu05Y95iIRUdo`
- Yuting Hao Finance：`https://youtube.com/@yutinghaofinance?si=3NaJKJyQim91danb`

这些频道通常每天发布美股相关视频，可以作为市场主线的辅助输入。

采集方式：

- 使用 YouTube Data API 获取频道、视频标题、发布时间、描述、缩略图和链接。
- 通过标题、描述、发布时间和用户配置规则识别宏观主题、板块和标的。
- 如果有合法可用的转录文本或用户手动提供笔记，再用 AI 提炼观点。
- 如果没有可用转录，只基于标题、描述、发布时间和用户手动摘要做弱信号。

限制：

- 不默认抓取 YouTube 页面 HTML。
- 不默认绕过 YouTube 或创作者限制抓字幕。
- 不保存或展示完整视频转录文本。
- 不复制视频内容，只保存观点摘要、时间戳、来源链接和涉及主题。
- 博主观点必须标注频道名、视频标题、发布时间和原始链接。

展示规则：

- 观点源必须和事实源分开展示。
- 单个博主观点不能单独生成“今日交易主题”。
- 多个博主观点一致，但缺少事实源时，显示为“观点线索，待事实验证”。
- 博主观点与事实数据冲突时，显示“来源分歧”。

### 5.6 展示准入规则

市场逻辑默认采用“不确定就留空”的策略。

展示条件：

- 至少 1 个明确来源。
- 置信度达到阈值。
- 来源时间和市场变化时间接近。
- 逻辑能说明影响对象：全市场、板块、风格或资产类别。
- 不是纯猜测、纯情绪或单一无来源观点。

不展示条件：

- 没有显著事件。
- 无法归因。
- 证据不足。
- 只有单条低可信来源。
- 来源之间明显冲突且无法判断。
- AI 只能生成猜测，无法给出来源。

建议置信度：

- `high`：多个事实源一致，且价格 / 板块表现匹配。
- `medium`：至少一个事实源明确，另有新闻或观点源辅助。
- `low`：只有弱关联、单一观点源或时间关系不够清楚。

首版只展示 `high` 和 `medium`，不展示 `low`。

### 5.7 数据来源

事实源：

- 价格和成交量：`market_daily_bars`
- 板块表现：全市场热力图聚合结果
- 新闻：Polygon / Massive News API 或其它结构化新闻 provider
- 财报：FMP、EODHD 或后续确定的 earnings provider
- 宏观：经济日历、利率、VIX、美元、美债等数据源
- 市场情绪：CNN Fear & Greed Index 可作为可选情绪来源

观点源：

- Nana 说美股 YouTube 频道
- Yuting Hao Finance YouTube 频道
- 用户后续新增的其它频道或手动笔记

不要把网页抓取作为默认方案。新闻、财报、宏观和视频元数据应优先来自结构化 API，并保存原始链接和来源。

### 5.8 来源溯源设计

每条仪表盘内容都必须显示来源来自哪里。

来源类型：

- `price_data`：价格、成交量、板块涨跌等市场数据。
- `news`：新闻 API 或财经媒体文章。
- `earnings`：财报日历、财报 surprise、公司业绩数据。
- `filing`：SEC filing 或公司公告。
- `macro`：经济数据、利率、VIX、美元、美债等宏观数据。
- `sentiment`：恐惧贪婪等市场情绪数据。
- `commentary_video`：YouTube 博主视频观点。
- `manual_note`：用户自己补充的笔记。
- `ai_summary`：AI 辅助整理结果。

每个来源至少记录：

- `source_type`
- `provider`
- `source_name`
- `publisher`
- `author`
- `title`
- `url`
- `published_at`
- `retrieved_at`
- `is_opinion`
- `trust_level`
- `raw_record_type`
- `raw_record_id`

UI 展示规则：

- 每条逻辑摘要旁显示来源数量，例如 `3 个事实源 / 2 个观点源`。
- 展开后按来源类型分组：价格、新闻、财报、宏观、情绪、视频观点。
- 观点源必须有明显标识。
- AI 摘要必须显示“由哪些来源整理而来”。
- 如果来源只有观点源，没有事实源，标注“观点线索，待事实验证”。
- 如果来源之间冲突，显示“来源分歧”。

### 5.9 AI 使用边界

AI 可以使用，但只能作为整理层和研究助理。

AI 可做：

- 把多条新闻归并成 1-3 条市场主题。
- 把多个视频观点归并成市场主线。
- 把事件分类为财报、宏观、板块、公司新闻等。
- 生成简短中文解释。
- 标注“可能原因”“证据不足”“来源分歧”。

AI 不可做：

- 给出买入、卖出、加仓、止损建议。
- 把没有证据的新闻硬解释成涨跌原因。
- 把单个博主观点写成市场事实。
- 隐藏来源。
- 覆盖或改写确定性价格、财报、提醒规则数据。
- 作为最终数据源。

如果使用 AI 辅助获取资料，必须保存原始 URL、provider、标题、发布时间、抓取时间、AI 提取时间，以及是否经过人工确认。

推荐流程：

```text
AI Search / AI Research
  -> 候选来源列表
  -> 后端抓取或用户确认
  -> market_logic_sources
  -> market_logic_evidence_links
  -> AI 摘要
  -> UI 展示
```

### 5.10 后端设计

建议新增领域目录：

- `domains/market_logic`：市场大事件、交易主题、观点、来源、置信度定义。

建议新增应用服务：

- `application/market_news_sync_service.py`：同步新闻数据。
- `application/earnings_event_sync_service.py`：同步财报日历、财报 surprise。
- `application/market_commentary_sync_service.py`：同步用户配置的 YouTube 观点来源。
- `application/market_logic_service.py`：聚合价格变化、新闻、财报、板块、情绪和观点。

建议新增持久化：

- `market_news_articles`：结构化新闻。
- `earnings_events`：财报事件。
- `market_commentary_sources`：用户配置的视频观点来源。
- `market_commentary_videos`：视频元数据。
- `market_commentary_claims`：视频观点提炼结果。
- `market_logic_sources`：市场逻辑统一来源。
- `market_logic_evidence_links`：逻辑与来源的关联。
- `market_logic_notes`：已生成并缓存的市场大事件、交易主题和博主观点摘要。

### 5.11 API 草案

仪表盘市场主线：

```text
GET /api/market-logic/dashboard?market=US
```

响应草案：

```json
{
  "market": "US",
  "as_of": "2026-05-07T10:00:00Z",
  "modules": {
    "major_events": [],
    "trading_themes": [],
    "commentary_views": []
  },
  "empty_reason": "no_significant_event"
}
```

当有符合条件的内容时：

```json
{
  "market": "US",
  "as_of": "2026-05-07T10:00:00Z",
  "modules": {
    "major_events": [
      {
        "title": "CPI 低于预期",
        "summary": "通胀数据低于市场预期，利率下行带动成长股反弹。",
        "confidence": "high",
        "sources": []
      }
    ],
    "trading_themes": [
      {
        "title": "市场交易降息预期升温",
        "summary": "利率下行、科技股走强和多条新闻共同指向降息预期升温。",
        "confidence": "medium",
        "sources": []
      }
    ],
    "commentary_views": [
      {
        "source_name": "Nana 说美股",
        "title": "今日美股复盘",
        "summary": "视频观点认为市场主线集中在 AI 和利率预期。",
        "confidence": "medium",
        "is_opinion": true,
        "url": "https://youtube.com/@nanashuomeigu?si=WGYGu05Y95iIRUdo"
      }
    ]
  }
}
```

观点来源管理：

```text
GET /api/market-commentary/sources
POST /api/market-commentary/sources
GET /api/market-commentary/videos?source_id=1&limit=20
```

### 5.12 UI 原则

- 仪表盘只显示 `市场大事件`、`今日交易主题`、`博主观点` 三个模块。
- 三个模块都允许为空。
- 空模块不强行显示占位解释。
- 只展示来源明确、置信度达标的内容。
- 事实源和观点源分开展示。
- 列表摘要显示来源徽标，例如 `新闻`、`财报`、`宏观`、`情绪`、`视频观点`、`AI 整理`。
- 详情面板显示完整来源列表，包括来源名、发布时间、抓取时间和外部链接。
- 不复制新闻全文，只展示标题、摘要、来源和链接。
- 不复制视频转录全文，只展示短摘要、来源和原视频链接。

### 5.13 参考来源

- [YouTube Nana 说美股](https://youtube.com/@nanashuomeigu?si=WGYGu05Y95iIRUdo)：用户指定的美股解读观点来源。
- [YouTube Yuting Hao Finance](https://youtube.com/@yutinghaofinance?si=3NaJKJyQim91danb)：用户指定的美股解读观点来源。
- [YouTube Data API Search: list](https://developers.google.com/youtube/v3/docs/search/list)：按频道、关键词和发布时间发现视频。
- [YouTube Data API Videos: list](https://developers.google.com/youtube/v3/docs/videos/list)：读取视频元数据。
- [YouTube Data API Captions](https://developers.google.com/youtube/v3/docs/captions)：字幕资源能力和权限边界参考。
- [Polygon / Massive News API](https://polygon.io/docs/rest/stocks/news)：ticker news、publisher、summary、sentiment 和相关 tickers 参考。
- [FMP Earnings Calendar](https://site.financialmodelingprep.com/developer/docs/earnings-calendar-confirmed-api)：财报日历和财报事件参考。
- [CNN Fear & Greed Index](https://edition.cnn.com/markets/fear-and-greed)：可选市场情绪来源。

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
