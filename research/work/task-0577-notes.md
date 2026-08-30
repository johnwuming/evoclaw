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

## 3. 前端逐页核对（源码 grep，10:38）
- **Overview.jsx**：activePv 从 /portfolios 兜底取（代码注释自认"投影 active 指针依赖 promotion.executed，账本尚无"）→ vC-0 卡+PvWeights 权重堆叠条（58/42）能渲染，组合主语在场。引擎卡（区块②）只显 sleeve_id/status/engine_id/IC/信号日/paper 天数/data_cut，**无权重、无 pv_ref**。健康卡硬编码文案「NAV 序列待 HP 产物接入」与下方运行态 NAV 曲线（navseries 已有 11 点，末值 1.00993）**文案打架**。
- **Risk.jsx**：两腿相关性（equity × gold）+ recon per_sleeve 视角 ✓ 组合视角在场；correlation/vol insufficient 态如实。
- **Version.jsx**：组合版本页，sleeve×2 组成卡 + weight_solution 各腿权重 + task-0575 双腿持仓视角（L137-183 动态读契约 #7 字段）——修复代码已入源码，dist 10:32 重建含双腿资产。
- **Events.jsx**：通用账本视图；trade.fill target 自带 `#equity` 腿后缀可辨识；无 sleeve 过滤（小）。
- **Migration.jsx**：迁移工程主语（Phase A-D 含 C1/D1），与组合/引擎主语无关，合规。
- **Candidates.jsx**：迭代候选库=单引擎历史回测对照（合法成分视角）；active 项 label=「vC-0 现役（F1·vc0 口径）」已带归属语义；KIND_LABEL 现役/迭代/跳过。
- **App.jsx**：站名「量化看板」无组合主语字样（小，可不改）。

## 4. 契约/文档对照
- R-342 v2.0 契约总表（L404+）：#4 overview 契约含 active_pv/sleeves[{id,weight,nav,mdd}]——实现结构合规、数据断供；#8 holdings **契约 schema 本身无 sleeve 字段**（items 仅 code/shares/cost/last/mv/weight）→ 单腿盲区是契约层根因；#9 trades 同样无 sleeve，filter 前缀 `paper/<id>#` 两腿通吃（黄金成交后会混排）；#10 navseries 仅组合口径（config equityNavPath/goldShadowNavPath 两腿镜像位已留，task-0565 D-1=c 未点亮）；#11 risk/gates per_sleeve+correlation pair+组合 dd_gate 合规。
- R-344 PRD 43 模块对照表（L308+，快照 2026-08-29）：≥5 行已过时——净值曲线❌（实际 navseries 已通）、回撤闸门❌"risk/gates 无 portfolio_dd_gate"（实测已有）、波动率带❌/两腿相关性❌（字段已落 insufficient 态）、迁移 C/D 缺（实测 C1/D1 在表）。

## 5. 结论分级（定稿）
- P0-1 持仓页单腿（task-0575 修复中，dist 已建）；根因链含契约 #8 无 sleeve 字段。
- P1-1 /overview active_pv+sleeves 空断供（账本无 executed + overview.json 无 stub）；P1-2 overview NAV 全 null 而镜像 CSV 已有数据（两源不同步）；P1-3 每腿 NAV/回撤无 API 呈现（配置位已留）；P1-4 引擎卡缺权重/pv_ref 标注；P1-5 trades 契约无 sleeve（黄金成交后混排隐患）；P1-6 R-344 对照表快照过时。
- P2：engines.json 数据层合规；Candidates 页合规；Events 合规；Risk 页合规；Migration 合规。附：overview note 文案指向裸 API、健康卡 NAV 文案打架（并入 P1-2 副作用）。
- 范围外提示：sync_lag 20.8h 接近陈旧心智阈值，建议交易日感知口径。
