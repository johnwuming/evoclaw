# task-0578 过程笔记

## 数据源核验（/tmp/vc0.json，curl 127.0.0.1:8180/api/v1/portfolios/vC-0，12283B）

- gate_report = **null** → 门禁卡整卡如实显「未评级（本版本未过门禁流程）」
- per_sleeve_risk_cap = **null** → 风控卡显「—」+ 语义标注「单腿风险上限：只封顶、不下指令」
- risk_control.drawdown_gates 实际结构 = `in_service_charter`（**不是** lt5/5_10/10_15/gt15 四带）：
  - cut_half_at=0.25, stop_at=0.35, charter_version="1.0", source="config/risk-charter.json"
  - note=「在役宪章实况；目标架构 5/10/15 分级带属 Phase C 治理切换范围」
  - vol_target=null；backfill_rule=「禁止回填含未来信息的统计量」
  - → 渲染策略：兼容两种形态，四带键(lt5/5_10/10_15/gt15)存在则逐带渲染；否则渲染 in_service_charter 实况行 + note（vC-0 走此分支）
- solver_ref：solver_id=solver_equal_vol_v1，params{window_days:60, annualization:252, min_obs:40}
- weight_solution.solver_meta：type=equal_volatility；cov_estimator=sample_diagonal_vol；convergence_status=closed_form；fallback_triggered=false, fallback_reason=null；dry_run=true；solve_date=2026-08-28
- weights：equity_sleeve=0.58030 (58.0%)，hedge_sleeve_gold=0.41970 (42.0%)

## 字段映射（组合构建卡）
| UI 项 | 契约路径 |
|---|---|
| 求解器 | solver_meta.type（equal_volatility→等波动率）/ 无则 solver_ref.solver_id |
| 窗口/年化/最小样本 | solver_meta.params 或 solver_ref.params |
| 协方差估计 | solver_meta.cov_estimator |
| 权重 | weight_solution.weights 逐腿 % |
| fallback | solver_meta.fallback_triggered/reason |
| 演进行 | 静态文案（R-336 §8 口径：MVO 仅对比留档未启用） |

## 待办
- [ ] 读 Version.jsx 现有结构（22KB < 30KB 可全读，但先 grep 分段）
- [ ] 实现③区块
- [ ] build + test + grep dist
- [ ] 390 无头自查
