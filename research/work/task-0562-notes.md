# task-0562 看板小修包 P1 笔记

## 0. 任务范围
- 前端4项: a)TabBar风险角标(pending_risks.count) b)HealthStrip投影校验位 c)Version详情risk_control块 d)Events actor/target过滤
- migration.json: B2/B3→done(据R-349), 补Phase B动作1-5(R-346/347/348), 补Phase C行(R-354已完成)与Phase D行(规划中), 备份.bak
- R-342增补「契约与现实对齐(2026-08-29)」节: /risk/drift与/portfolios/:id/timeline列为后续版本项(引R-359 B1/B2)
- 构建 VITE_API_BASE=/quantv6 + npm test + 无头390x844验证
- 不改BFF代码

## 1. R-359 审计要点摘录
- G3: TabBar.jsx(20行)无角标; health.pending_risks.count 可用
- G2: /health 已返回 projection_sha256_ok=true; HealthStrip 未显示
- V5: BFF detail 返回 risk_control.drawdown_gates(宪章25%/35%); Version.jsx 未渲染
- E3: Events.jsx 类型过滤✓; actor/target 无UI, 数据在 items 内
- M5/M1: migration.json 静态5行; B2(MVO对照)/B3(协方差对比)已由R-349完成; Phase B动作1-5=R-346(动作12 vC0快照+等波动率求解器)/R-347(动作3 选择器化+vC0复现门)/R-348(动作45 影子对账+漂移监控基建); Phase C=R-354 治理切换已完成(2026-08-29)
