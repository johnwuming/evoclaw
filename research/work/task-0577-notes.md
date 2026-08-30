# task-0577 审计笔记（看板+BFF 单引擎残留检查）
开始时间: 2026-08-30 10:21

## 0. 基础探测

## 1. BFF 实测（8180，/api/v1，2026-08-30 10:25）
- 端点清单 13 个：health/events/migration/overview/engines/portfolios/portfolios:id(+holdings/trades/navseries)/risk/gates/perf-history(+id)
- **overview 实测**：`{"nav":null,"nav_chg_1d":null,"mdd":null,"drawdown_pct":null,"active_pv":null,"sleeves":[],...}` 全空。
  - 根因链（app.js overviewHandler L146-180）：nav/mdd ← overview.json nav_series（文件里 nav_series=[]，note 说 HP 产物未输出）；active_pv ← ledger projection.composites.active_pv_id（账本无 executed/promotion 事件→null）；sleeves ← active.weight_solution 派生（active=null→[]）。
  - overview.json 全文仅 `{"nav_series":[],"note":"HP NAV 序列产物尚未输出...active 权重见 /api/v1/portfolios"}`，无 active_pv/sleeve_stub 字段。
- **holdings 实测（P0 已知，task-0575 修复中）**：8 只微盘股，items 字段仅 [code,shares,cost_price,last_price,market_value,weight]，**无 sleeve/leg 字段**；weight 8 只合计=1.0（腿内归一），黄金腿（active_paper）完全不可见；total_market_value=59567。source=ledger:trade.fill projection。
- **engines.json**：2 引擎（equity_sleeve/engine A active；hedge_sleeve_gold/gold_trend_sma200 active_paper），均有 pv_ref=vC-0、sleeve_id、description；IC/ICIR/信号日全 null（HP 指标未接入）。组合归属靠 pv_ref 字段，但需查前端是否渲染。
- **portfolios.json**：仅 vC-0，status=paper，无权重/sleeve 摘要字段（权重要进详情才有）。
- versions/vC-0.json：sleeves 含 equity_sleeve+hedge_sleeve_gold、weight_solution、risk_control 等（组合级结构完整）。

## 2. 待查
- trades/navseries 是否含黄金腿
- 前端 6 页逐一核对
- risk/gates、perf-history、events、migration 组合视角
