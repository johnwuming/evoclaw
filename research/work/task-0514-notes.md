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

## 现状画像（已摘取）
- D6 双cron：p3_3_evolution_standalone(939行旧)半月 vs evolution_pipeline(1605行)周六；HP 182脚本中 107 孤儿
- GATE_CONFIG：icir_is≥0.5 / oos_p<0.05(split 2021-01) / max_corr≤0.7 / DSR≥0.95 / logic非空 / MDD恶化≤2pp一票否决 = g1-g6；STATUS_ENUM candidate→pending→active→sota→retired
- 6种留痕载体散装：decision-log/ledger/history/switch_log/n_trials_ledger/cycle-report + engines.audit → 事件化改造的起点
- engines.json 快照缺 gold 引擎 = 状态滞后风险

## R-333 审计结论（直接引用）
- 成本 v2 = 佣金0.10%+价差0.03% = 13bp/边（R-304 冻结）；实记账滑点≡0（收盘回填），v2建仓实付4.00bp（¥5最小佣金），无卖出侧样本
- 三情景年化偏差：A记账延续 −0.9pp 低于带；B可实现中间态(万2.5佣金+tick半价差+印花税摊≈11.5bp/边) −0.21pp 落在 ±0.1~0.3pp 预期带；C小微资金 +1.0pp 超上界
- 一字板不可成交实证：v1 组 300862 四连一字板；当前规模参与率≈0.002~0.007%，冲击成本可忽略，603551 低成交额票最先触线
- 判定：±0.1~0.3pp 预期带仅在「比例佣金可得+收盘竞价可成交」下成立

## R-334 复用结论（不重查）
- qlib qrun 第二裁判双轨（先验 cn_data bin 就绪性）；PIT：R-328 NOTICE_DATE 细则、000001 滞后371天反例；复权：R-330 F4 唯一 qfq、513100 假 MDD −85% 反例；Mask-First：R-333 一字板实证支撑
- GM→标准名映射素材：GM4(进化单轨)/GM6(门禁schema)/GM7(影子合一)/GM9(quant_common)/GM13(同步总线)/GM15(engines.json单落点)
- 辩论代理→Alpha Layer 候选供给；ICIR+HMM→择时模块

## 报告决策
- 编号 R-336；文件名 R-336-破而后立目标架构与迁移方案.md
- 标准术语：portfolio_version / sleeve / signal / gate / promotion(shadow→paper→canary→live) / retirement / event_log
- GLOSSARY.md 全文放报告附录；门禁阈值全部带数字并标「初版建议值」
- paper 指针语义切换（Phase C）标红需用户批准

## 增补建议（23:39 用户转外部，source-advice-portfolio-construction.md，2.0KB 已读全文）
- 六层改七层：Alpha 与 Portfolio 之间新增 Portfolio Construction Layer（组合构建层）；职责=给定风险预算求 sleeve 权重；求解器可插拔分阶段：①等波动率 ②风险预算/ERC（协方差 Ledoit-Wolf 收缩）；明确不用 MVO（收益预测误差敏感）
- 解耦铁律：portfolio_version 存配置（sleeve 指针/风控参数/求解器选型+参数），构建层输出权重求解结果；禁止在 vC 上直接加 model_weights
- 门禁追加组合级回撤分级闸门：<5% 正常 / 5-10% 提级审查 / 10-15% 降仓×0.5 / >15% 熔断；波动率目标化参数位；层级关系：分级闸门=组合级、ddc=sleeve 级，两层独立触发，组合级>策略级裁决
- 再平衡协调协议：sleeve 内重大调仓后组合层冷却期 1 个完整调仓周期，期间不因 RC 变化反向加仓；防减仓→RC骤降→反向加仓横跳
- 相关性用持仓相关性 holding-based（非仅净值），同源信号>0.75 告警，危机期趋近1=分散失效
- P2/P3 降级为演进方向不现在做：约束体系、分层风险预算、HRP、体制切换
- 外部优先级：P0=组合构建器+波动率目标化+回撤分级闸门；P1=相关性筛查+ERC+Ledoit-Wolf；P2=约束+分层预算+退役；P3=HRP/体制切换

## 撰写状态
- [x] 证据全部落笔记；[ ] R-336 报告主体；[ ] README 顶部日志；[ ] 完成回报
