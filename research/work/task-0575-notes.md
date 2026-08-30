# task-0575 过程笔记（组合视角完整性修复：版本/持仓页补齐黄金腿）

## 任务要点
- 方案 B（用户 08-30 10:14 拍板）：纯前端 sleeve 卡，零在役改动、零新端点、零新依赖。
- 改版对象：src/pages/Version.jsx + src/styles.css 增量样式。
- 原则：组合模型（vC-0 双腿）是主语；黄金腿=hedge_sleeve_gold（引擎级独立记账），如实呈现状态+权重，不伪造明细。

## 数据源核对（契约 #7 GET /portfolios/:id，既有字段）
- sleeves.hedge_sleeve_gold.component_ref = {type:engine_ref, engine_id:gold_trend_sma200, status:active_paper}
- sleeves.hedge_sleeve_gold.code_hash（sha256:…）
- weight_solution.weights = {equity_sleeve:0.5803, hedge_sleeve_gold:0.4197}
- detail.data_cut（版本级数据截止）

## 改动计划
1. PaperViews 增加 detail prop（Detail 内已持有 detail，零新请求）。
2. 持仓区改双区块：
   - 标题改「组合持仓（vC-0 · 双腿视角）」主语；
   - 股票腿卡：equity_sleeve + 动态权重（fmtPct），保留 8 股明细表/费用卡/交易清单；
   - 黄金腿卡：hedge_sleeve_gold + 引擎 ID（fmtID 截断）+ 状态 active_paper→「模拟运行中」+ 权重 + data_cut + 「引擎级跟踪，仓位明细由黄金引擎独立记账」注脚。
3. 降级：weights 字段缺失→显示 —；sleeve 缺失→卡内逐字段 —（或无权重且无 sleeve 时整块不渲染，兼容单腿旧版本）。

（待续：实施结果、验证输出）

## 实施结果（2026-08-30）
### 修改文件清单
1. src/pages/Version.jsx —— PaperViews 改造：
   - 签名 `PaperViews({ id })` → `PaperViews({ id, detail })`（Detail 已持有契约 #7 detail，零新请求）；
   - 区块标题「模拟盘持仓（账本投影）」→「组合持仓（{id} · 双腿视角）」；
   - ① 股票腿卡 `.sleeve-pos-card`：头部「股票腿（equity_sleeve）+ 权重（weight_solution.weights.equity_sleeve 动态）」，内含原 8 股持仓明细表/合计市值/费用卡/交易清单（交易清单标题改「交易清单（股票腿账本投影）」标明归属）；
   - ② 黄金腿卡 `.sleeve-pos-card.sleeve-gold`：头部「黄金腿（hedge_sleeve_gold）+ 权重（weights.hedge_sleeve_gold 动态）」，行：引擎（fmtID 截断 18）、运行状态（SLEEVE_STATUS_LABEL：active_paper→「模拟运行中」，未知状态回退原文）、数据截止（detail.data_cut）；注脚「引擎级跟踪，仓位明细由黄金引擎独立记账（黄金引擎不落组合账本逐笔成交）」；
   - 降级：权重/引擎/状态/截止任一缺失→「—」；sleeve 与权重均缺失时整卡不渲染（兼容单腿旧版本）；新增 SLEEVE_STATUS_LABEL 常量。
2. src/styles.css —— 追加 4 条规则（.sleeve-pos-card / .sleeve-pos-head / .sleeve-w / .sleeve-gold 琥珀色左边条 / .sleeve-note），只用既有 CSS 变量，无新依赖。
3. scripts/t0575-headless-check.cjs —— 新增 390x844 无头验收脚本（复用 t0565-serve.cjs 伺服方式）。

### 字段映射（契约 #7，全部既有字段，未造数）
| UI | 字段 |
|---|---|
| 股票腿权重 | weight_solution.weights.equity_sleeve（0.5803→58.03%） |
| 黄金腿权重 | weight_solution.weights.hedge_sleeve_gold（0.4197→41.97%） |
| 黄金腿引擎 | sleeves.hedge_sleeve_gold.component_ref.engine_id（gold_trend_sma200） |
| 运行状态 | sleeves.hedge_sleeve_gold.component_ref.status（active_paper→模拟运行中） |
| 数据截止 | detail.data_cut（2026-08-26） |

### 验证输出摘录
- `VITE_API_BASE=/quantv6 npm run build` → ✓ built in 2.02s，零报错；dist/assets/index-onZeBZWG.js
- `npm test` → engine-copy assertions: 39 passed
- `grep -rl quantv6 dist/assets/` → dist/assets/index-onZeBZWG.js（命中）
- 无头 390x844（#/version 展开 vC-0）：bodyScrollW=390，docScrollW=390（无横滚）；
  title=「组合持仓（vC-0 · 双腿视角）」；股票腿卡=「股票腿（equity_sleeve）权重 58.03%」+ 8 行持仓 + 8 行成交；
  黄金腿卡=「黄金腿（hedge_sleeve_gold）权重 41.97%」+ 引擎 gold_trend_sma200 + 运行状态模拟运行中 + 数据截止 2026-08-26 + 注脚齐全。
- 零改动确认：api.js / App.jsx / hooks.js / BFF / nginx 均未触碰；git 侧仅 Version.jsx、styles.css、新增验收脚本三处。
