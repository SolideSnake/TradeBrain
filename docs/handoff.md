# TradeBrain 交接文档

## 文档信息

- 版本：v0.1
- 状态：当前有效
- 更新日期：2026-04-09
- 目的：在更换电脑或中断工作后，帮助快速恢复项目上下文并继续开发

## 1. 当前项目状态

当前项目仍处于“设计完成，准备进入实现”的阶段，尚未开始正式编码。

已经完成的内容：

- 完成需求文档
- 完成模块设计文档
- 完成 MVP 功能清单
- 完成技术方案草案

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
- 生成待办任务
- 通过 Telegram 发送关键预警

AI 在第一版中不是主链路，只负责后续可能的简短说明和摘要。

## 3. 已经明确的技术结论

第一版技术方向已经确定为：

- 后端：Python 3.12 + FastAPI + SQLAlchemy + SQLite + APScheduler + ib_async
- 前端：React + TypeScript + Vite + TanStack Query + Zustand + TanStack Table
- 运行方式：本地单机运行
- 并发模型：单进程 + AsyncIO
- 数据库：SQLite（WAL 模式）
- 通信方式：REST + WebSocket

明确不采用：

- 微服务
- PostgreSQL
- 多线程主架构
- 自动下单
- 桌面壳优先方案

## 4. MVP 范围已经锁定

第一版 MVP 严格只做 8 件事：

1. Watchlist 与分组管理
2. IBKR 只读接入
3. CanonicalSnapshot
4. 核心指标
5. 基础状态引擎
6. 任务中心
7. Telegram 预警
8. Web 看板

第一版禁止扩项到以下方向：

- 自动下单
- 回测
- 多用户
- 云同步
- 复杂策略 DSL
- 高级 AI 决策

## 5. 推荐的下一步开发顺序

下一次继续开发时，建议严格按以下顺序推进：

1. 初始化项目骨架
2. 建立后端基础运行入口
3. 建立 SQLite 与 SQLAlchemy 模型
4. 建立 `adapters/ibkr`
5. 建立 `CanonicalSnapshot`
6. 建立核心指标
7. 建立基础状态引擎
8. 建立任务中心
9. 建立 Telegram 预警
10. 建立 API 与 WebSocket
11. 建立前端 4 个页面
12. 联调与验收测试

## 6. 推荐的第一批编码任务

建议从以下最小任务开始：

- 初始化 `backend/`
- 初始化 `web/`
- 建立 `.env.example`
- 建立后端 `app/main.py`
- 建立后端配置读取
- 建立基础健康检查接口
- 建立 SQLite 初始化逻辑
- 建立 watchlist 最小模型

这批任务完成后，再进入 IBKR 接入。

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
- `freqtrade`：状态、任务、预警流
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

TradeBrain 的设计阶段已经足够完整，下一步不需要再继续发散讨论，应该直接进入项目骨架初始化和第一阶段编码实现。
