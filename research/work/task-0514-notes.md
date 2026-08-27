# task-0514 破而后立目标架构与迁移方案 — 工作笔记

- 编号核对：05-量化投资/ 下最大 R 号 = R-335 → 本报告 = **R-336**
- 产出路径：/root/.openclaw/workspace/shared/results/05-量化投资/R-336-破而后立目标架构与迁移方案.md
- 输入：source-review-r335-external.md (5.0KB)；R-335 (26.8KB)；R-333 (paper真实成本对账审计，直接引用)；R-334 (既有结论复用)；task-0501-notes.md (22.3KB)

## 外部评审核心问题（已读完，要点）
- 判定：治理骨架（版本对象+状态机+对账）= 机构级主流，保留；工程落地 = 个人历史包袱（术语/隐式状态/未审计回测/主观门禁/无退役/弱对账/零兜底）
- P0：门禁量化硬阈值；回测引擎正确性审计（前视/复权/退市/滑点冲击成本 Almgren-Chriss 类）；安全兜底三件套（断路器/checkpoint/仓位对账）
- P1：append-only 事件日志；影子 4 维漂移监控（日P&L、Sharpe、成交率、滑点，信号对齐率>95%、执行质量>90%）；客观退役规则；GLOSSARY 术语表
- P2：Qlib 解耦对接；容器化双机冗余
- 金句：严格门禁建立在错误回测上，越严格越危险

## R-335 骨架（保留思想、重述术语）
- vC-x.y 组合版本对象（components: equity registry_ref + gold engine_ref；risk_control: ddc 0.20/0.5/0.05 + layer2 补位 + weighting F7a + timing）
- 状态机 candidate→组合回测→组合门禁→影子(可选)→用户批准→paper 指针→归档
- 六种迭代类型：smallcap_factor_iter / engine_upgrade / new_engine / risk_param_tune / weight_rebalance / unified_model
- 组合门禁 = 组件级 g1-g6（ICIR_IS≥0.5 / ICIR_OOS p<0.05 / max_corr≤0.7 / DSR≥0.95 / logic 非空 / MDD 恶化≤2pp 一票否决）+ 组合级（mdd 优于 parent、Calmar≥parent、两腿 corr≤0.3）
- F6/F7 选择器化 = 现成组合回测；R-317 156 月统一口径 + F1 基线 md5 复现 + PIT assert（2015-06/07、2020-06/07）
- M1-M5 迁移步；M4 paper 指针切换需用户批准；红线：registry active / paper_engine / HP crontab 零擅动
- 在役基线数字：F7a 年化13.61% / Sharpe1.483 / Calmar2.001 / mdd−6.80% / 月胜率69.2%；两腿 corr≈0.03

## 现状画像（task-0501-notes 摘取，待补）
（待填）
