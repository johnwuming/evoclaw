# task-0609 P1 规格设计过程笔记（风控层监控先行：DDC/vol_target 日频监控可实现性）

## 事实基线（读 task-0607-notes.md + task-0602-compute.py 头部确认，2026-08-31）
- 最大 R 号实查 = **R-390**，R-391 可用 ✓
- a13 腿日频 NAV：`shared/results/04-投资研究/a13_rsraw_e1f10dz_full_nav.csv`（date,nav）
- 金腿日频：本地可能已有重建产物（task-0607 腾讯 sh518880 qfq 日线 3184 行 2013-07-29→2026-08-31）；接口 GET https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh518880,day,{start},{end},640,qfq
- DDC 权威定义（task-0607/R-390 核实）：ddc_th20_rd50_rc5；sleeve NAV 对自身 running_max，≤−20% ×0.5 减半，回撤≥−5% 收复回补；执行语义=日频 T 收盘判定 T+1 生效（R-336 §4.4/R-318 F6）
- runtime 历史模拟日频 MDD −21.31%（a13+现金 60/40 组合路径）；a13 腿日频 MDD −33.55%（DDC 真正观测对象，深度击穿 −20%）
- 8%±2pp vol_target 带宽无文档出处（0602/R-388 发现）→ 规格标注「待用户确认」
- 硬约束：阶段二实现不在本任务；不改引擎/生产/policy/registry；监控零在役触碰、只告警不拦截；禁 SSH HP

## 待查
- [ ] task-0607 金腿日频重建产物是否落盘（避免重新 fetch）
- [ ] R-388 vol_target 相关段落
- [ ] R-390 DDC 权威段落
- [ ] 看板（quant-bff）结构，确认告警通道挂点
