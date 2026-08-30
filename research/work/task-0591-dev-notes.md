2026-08-30 20:42:50 task-0591-dev 启动：④lint⑥重算血缘 ②滚动四指标 ③PRD演进目标化。已确认 B8 引擎语义：首月建仓成本 0.0013 在场、月度漂移Δw成本、pct_change 首行相对基期1.0、产物 round(10)。

## ④ lint检查⑥ 重算血缘断言（已完成）
- 关键对齐发现（任务书「首期建仓免成本」表述与 B8 实际引擎不符，按任务书要求以 B8 引擎为准）：task-0585-compute_vc0_authoritative.py run_engine 首月 cost=0.0013×(|wA|+|wG|)=0.0013 在场（产物首点 1.0333423802 = 无成本值 1.0346423802 - 0.0013，逐位验证）；此后每月 cost=0.0013×(|目标-上月漂移权重|)，月度再平衡月月有漂移；首行收益相对基期 1.0（pct_change.fillna(A-1)）；产物列 round(10)。
- Python 原型复现：156 点 max_rel_err=4.075e-11 < 1e-10 ✓（残差=round(10) 噪声+浮点序差）。
- policy.json 新增 caliber.static_recalc{source_file:nav_curves.csv, w_a:0.580297, w_gold:0.419703, cost_rate:0.0013, rel_tol:1e-10, anchor:...}——参数锚 policy，lint 零硬编码。
- policy-lint.mjs：新增 checkRecalcLineage()（月轴逐行比对/非正数值拒绝/行数比对/建仓成本在场/漂移Δw成本/逐点相对误差≤1e-10，违规文案「重算与产物失配（基底错或产物损坏）」）；⑤c 顺带升级为 rolling_compare 四指标（ann/vol/sharpe/mdd）全部声明+实算比照（TOL 1e-4）；PASS 输出增⑥行。
- 实跑：真实数据 PASS exit0（156点）；破坏性自测 /tmp/t0591-bff（全拷 live/data+src，2020-03-31 VC0 值×1.01）→ FAIL exit1，命中「⑤md5失配 + ⑥重算与产物失配 max_rel_err 9.901e-3 @2020-03-31」✓。
