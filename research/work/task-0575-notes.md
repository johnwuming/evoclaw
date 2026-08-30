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
