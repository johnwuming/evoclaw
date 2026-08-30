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

## 实现方案（定稿）
- Version.jsx：新增 PortfolioConstructionSection（组合构建）/ GateReportSection（门禁成绩单），增强 RiskControlSection（四带动态兼容 + per_sleeve_risk_cap 语义行）；Detail 顺序=…ModelCard、PaperViews(不动) → 组合构建 → 风控配置 → 门禁成绩单 → Sleeve 明细 → 状态历史
- 移除旧内联「门禁成绩单」行与底部「权重解」块（内容并入新卡，无信息丢失）
- 四带回撤门：lt5/5_10/10_15/gt15 键存在则逐带渲染（vC-0 无 → 走 in_service_charter 分支）
- gate_report 非空但无结构化条目 → 截断 JSON 如实显示，绝不误标「未评级」
- styles.css 增量：.ver-wblock/.gate-none/.gate-row/.gate-chip(.gp/.gf)
- npm test 只测 engine-copy（39 断言），与本次改动无耦合

## 验证结果（2026-08-30）
- build：`VITE_API_BASE=/quantv6 npm run build` 零报错（✓ built in 1.99s）；npm test：engine-copy assertions: 39 passed；grep -rl quantv6 dist/assets/ → dist/assets/index-BuytD1hm.js 命中
- 390 无头（scripts/t0578-headless-check.cjs，本地 dist+8180 代理静态服务器 t0578-static-server.cjs:8981）：
  - bodyScrollW=390 / docScrollW=390，无页面级横滚
  - 详情标题「组合 vC-0 · 版本详情」；区块顺序：模型组成 → 组合构建（solver）→ 风控配置（risk_control）→ 门禁成绩单（gate_report）；持仓双腿卡未动
  - 组合构建：等波动率 / 窗口 60 天·年化 252·最小样本 40 / sample_diagonal_vol / closed_form / fallback未触发 / 权重 58.0%+42.0%（解 2026-08-28）/ 演进行含「MVO 仅对比留档，未启用」
  - 风控配置：在役宪章分支（减半 25%·清仓 35%，宪章 v1.0，源 config/risk-charter.json）+ note；波动目标未设定；单腿风险上限 — + 语义行「只封顶、不下指令」；回填规则如实
  - 门禁成绩单：gate_report=null → 整卡「未评级（本版本未过门禁流程）」（PRD 裁决口径）
  - overflowEls 全部为持仓表既有 `<td>2026-08-14</td>`（task-0575 pos-table 内部 5px 裁剪，非本次引入，页面级无横滚）

## 修改文件清单
- src/pages/Version.jsx（新增 PortfolioConstructionSection/GateReportSection，增强 RiskControlSection 四带兼容+cap，Detail 重排三区块，移除被取代的内联门禁行/权重解块）
- src/styles.css（+8 行：.ver-wblock/.gate-none/.gate-row/.gate-chip）
- scripts/t0578-headless-check.cjs、scripts/t0578-static-server.cjs（新增，过程验收工具，仿 t0575 先例）
- 纯前端：api.js/App.jsx/hooks.js/零 BFF/nginx 零改动；零新依赖
