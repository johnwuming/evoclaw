# R-342 R-336 实施级架构设计（含 Dashboard 全新可视化设计）

> 任务 task-0529 ｜ 2026-08-28 ｜ 状态：设计报告（纯设计零代码）
> 设计依据（唯一口径）：R-336 v1.2《破而后立量化系统目标架构与迁移方案》。本文所有「§N」引用除特别注明外均指 R-336 原文章节。新增设计不与 v1.2 冻结条款冲突；凡与冻结条款相关的字段名/阈值/事件类型一律原文引用。

## 架构一图流

```mermaid
flowchart LR
  subgraph HP["HP 量化主机 ~/quant-evolve（唯一写点）"]
    D1["① Data Layer<br/>四口径·tradable_mask"] --> D2["② Alpha Layer<br/>evolution_pipeline"]
    D2 --> D3["③ Backtest Layer<br/>composite_backtest"]
    D3 --> D4["④ 组合构建层<br/>等波动率求解器"]
    D4 --> D5["⑤ Portfolio Layer<br/>portfolio_version"]
    D5 --> D6["⑥ Execution Layer<br/>paper/canary/live"]
    D7["⑦ Risk Layer 横切⑤⑥<br/>熔断>组合级>单腿级"]
    EL["Iteration Ledger<br/>append-only JSONL"]
    D4 -. weight.solved .-> EL
    D5 -. promotion.* .-> EL
    D7 -. risk.action .-> EL
    EL --> PROJ["投影缓存 registry/engines/composites JSON"]
  end
  HP -->|"sync cron（只读镜像）"| subgraph VPS["VPS shared/results/04-投资研究/"]
    SYNC["同步目录：ledger/registry/产物 csv+json"]
  end
  VPS --> READ["新 Dashboard BFF（只读 API，重放投影消费）"]
  READ --> UI["新前端 SPA：六区块，390px 移动端优先"]
  USER["用户"] -->|读| UI
  USER -->|人工门操作（G-L4 批准等）| TC["任务中心/HP 流程"]
```

## 关键决策摘要（≤10 条）

1. **三落点分工**：计算与写入全部在 HP（事件账本、投影、求解器），VPS 只持只读镜像（sync cron 产物），新 Dashboard 是纯只读消费者——写操作（用户批准类，G-L4 唯一人工门，§4.3）一律走任务中心/HP 流程，前端不提供任何写入口。
2. **事件账本照抄冻结条款**：`events/iteration-ledger-YYYY-MM.jsonl`，格式 `{ts, actor, event_type, target, payload}`，flock+fsync+月滚动，投影 sha256 校验（§3.3）。不引入消息队列/数据库（§3.3 明文冻结），本设计不新增任何账本存储引擎。
3. **投影缓存=JSON，读侧加速可选 SQLite 物化**：source of truth 只有账本+JSON 投影；Dashboard 可选一层只读 SQLite 物化（沿用现有 agent-dashboard 的 node:sqlite 基建），语义=「可随时删了重建的投影缓存」（§3.1 表：JSON 降级为投影缓存），不承载任何唯一状态。
4. **七层映射**：现有 HP 管线（evolution_pipeline / registry / paper 引擎 / ddc）分别归 Alpha / Portfolio / Execution / Risk 层载体；**新建**=组合构建层求解器与 Iteration Ledger（§1.2④、§3）；Data 层四口径校验器从现有散点收敛为唯一出口。
5. **portfolio_version schema 一次到位按 v1.2 A1**：sleeves 附 `code_hash + data_cut`、`capital_policy{gross_limit, net_limit}`、solver_ref 扩 `tolerances + fallback`；`data_cut ≤ min(所有输入数据源最大时间戳)` 硬断言，违反即 `config.invalid` 绝对阻塞（§1.2⑤）。
6. **状态机含反向降级**：正向 `candidate → backtested → gated → shadow → approved → paper → canary → live`，反向 `live → shadow`（4 维漂移超标）/ `live → gated`（reconciliation.failed / 断路器 / 审计不合格），全部走 `promotion.downgraded` 事件，禁人工直改 JSON（§1.2⑤）。
7. **Dashboard 技术栈推荐：Vite + React SPA + Express BFF**（备选 SvelteKit 放弃理由见 §4.1）；部署=现有 nginx 反代 + systemd 单元，单机 VPS 零新增常驻依赖之外的基础设施。
8. **实时性=HTTP 轮询**（总览 60s / 其余 300s），不启用 SSE/WebSocket：月频调仓系统的状态变化天然低频（事件级：日/调仓日/门禁评估时），推送通道的连接管理成本 > 收益；预留 Phase C 后按需升级 SSE 的接口形态（同一路径可演进）。
9. **390px 移动端优先为硬约束**：全局 `overflow-x: hidden` + 容器断点组件规范（见 §4.4），任何区块禁横向滚动；表格降级为卡片列表，状态机图降级为状态胶囊。
10. **过渡三步走**：并行新建（Phase B，读旧+新双源）→ 验收（双看板对照 ≥1 个调仓周期）→ 切换（Phase C 指针切换获批准后，nginx 路由级切换，秒级回退）；旧 agent-dashboard 保留至 Phase D 才退役，观测能力不断档。

---
