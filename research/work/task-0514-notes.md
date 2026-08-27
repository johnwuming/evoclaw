# task-0514 过程笔记 — R-336x 破而后立目标架构与迁移方案

## 输入清单（已核验大小）
- source-review-r335-external.md = 5020B（全读，2026-08-27 23:30 用户定调原文在内）
- R-335-组合版本统一迭代架构方案.md = 26761B（全读）
- 背景：R-334 / R-320 / R-322（按需抽读 header，不全读）

## 外部评审逐条提取（回应表素材）

### 定性
- 治理骨架机构级（组合一等对象/版本化不可变/状态机晋升/双层门禁/三方对账=主流思想）
- 工程落地带个人历史包袱（A腿/gold腿术语、GM编号层、零常驻服务、F6/F7打补丁式改造）

### 优点（保留清单）
1. vC-x.y 不可变版本对象（可追溯可回滚可归因）
2. 一切变更统一流水线、无旁路
3. 结构化成绩单+逐条不通过原因
4. 增量重构承诺兼容（对单兵现实）
5. 三方对账+paper一致性徽标防漂移

### 缺点/风险（7条）
1. 术语代号强耦合 → GLOSSARY.md+标准术语(leg/hedge/signal)
2. 状态机隐式、无事件溯源（JSON可变状态，误改无法重放）→ append-only 日志
3. 门禁指标未量化（毕业标准须硬阈值：夏普/IS-OOS/参数扰动高原）
4. 回测引擎基于旧脚本改造，若含前视/缺滑点冲击成本 → 门禁越严越危险 → 单独回测正确性审计
5. 缺退役机制（历史最大回撤倍数、停滞期自动停用）
6. 影子/paper 对账指标偏弱 → 4维漂移（日P&L/Sharpe/成交率/平均滑点），信号对齐率>95%、执行质量>90%才晋升
7. 零常驻服务=无灾备 → 断路器+checkpoint+仓位对账

### P0（上线前必做）
- P0-1 门禁量化：每层毕业硬阈值（夏普、最大回撤、IS/OOS比、参数扰动、成本后收益）
- P0-2 回测引擎正确性审计：无前视、复权口径、退市股、滑点/冲击成本（Almgren-Chriss类）
- P0-3 安全兜底：断路器（单日亏损/回撤/报错率上限）+ 状态checkpoint + 定时仓位对账

### P1（半年内）
- P1-1 状态机显式化+append-only事件日志（重放与审计）
- P1-2 影子阶段业绩漂移监控：shadow vs research、live vs shadow 分层归因，四指标
- P1-3 退役规则：客观自动化淘汰条件
- P1-4 术语表+通用命名

### P2（演进方向）
- P2-1 组合层与回测引擎解耦，考虑 Qlib 对接
- P2-2 容器化+双机冗余（从零常驻走向高可用）

## R-335 关键事实吸收（目标架构的"存量"）
- vC-x.y schema：components{equity:registry_ref, gold:engine_ref} + risk_control{ddc/layer2/weighting/timing} + status + parent_composite + backtest_report_ref + gate_report + paper_since
- 状态机：candidate→组合回测→组合门禁→影子(可选)→用户批准→paper指针→归档
- 六种迭代类型：smallcap_factor_iter / engine_upgrade / new_engine / risk_param_tune / weight_rebalance / unified_model
- 组件级门禁 g1-g6 实测（ICIR_IS≥0.5 / ICIR_OOS p<0.05 / max_corr≤0.7 / DSR≥0.95 / logic非空 / MDD恶化≤2pp一票否决）；任务书"五门禁"是早期口径
- 组合级门禁草案：mdd优于parent / Calmar≥parent / 两腿corr≤0.3（F7a参照：年化13.61% Sharpe1.483 Calmar2.001 mdd-6.80%）
- 迁移 M1建快照→M2回测选择器化→M3前端卡→M4 paper指针(需批准)→M5旧入口降级
- 三方对账：composites.json ↔ registry ↔ engines.json
- 红线：registry active / paper_engine / HP crontab 零擅动；M4=改active语义需批准
- 落点取舍：现阶段 composites.json 并行文件（选A），远期GM15收敛时并入
- 风险表5条：门禁职责重叠/双版本线过渡/口径不一致(易错点:补位吃整体月收益不乘内部仓位、择时闲置现金不补黄金)/用户心智成本/样本n=1 episode

## 在役基线事实（写报告引用，勿凭记忆）
- A腿: paper_engine.py(70504B) + registry a13_rsraw_e1f10dz + timing_internal=true
- gold腿: paper_engine_gold.py(16474B) active_paper(08-25批准)
- 中央风控: ddc 0.20/降0.5/回补0.05 + 层2补位 + 权重口径F6/F7待拍板
- 双轨cron: p3_3_evolution_standalone.py 半月 vs evolution_pipeline.py 周六（R-320 D6）
- R-317: 156月统一口径，F1基线md5=915e446388…，PIT断言(2015-06 FULL/2015-07 REDUCE/2020-06 REDUCE/2020-07 FULL)
- F6成本: 双腿0.13%；ddc语义在 backtest_dividend_quality_iter.py:528-540

## 报告骨架计划（R-336x）
1. 标题+task-0514+2026-08-27
2. 背景与目标（破而后立定调 + 评审来源）
3. 方法与数据来源
4. 核心内容：
   a. 评审总判定吸收（保留什么/推倒什么）——破立边界
   b. 标准术语表（旧→新映射）：A腿→Equity Sleeve/Leg-1；gold腿→Hedge Sleeve/Leg-2(Gold)；vC-x.y→Portfolio Version(PV-x.y)；g1-g6→Component Gate(CG-1..6)；组合门禁→Portfolio Gate(PG)；paper→Paper Trading(Paper Stage)；门禁→Quality Gate；影子→Shadow Trading；registry→Model Registry；engines.json→Runtime Engine State；composites.json→Portfolio Registry；ddc→Drawdown Controller(DDC)；层2补位→Overlay/Backfill Module；F6/F7→Composite Backtest Spec；GM编号→Milestone Ref(仅内部)
   c. 分层架构图（mermaid）：Data Layer → Research/Backtest Layer → Portfolio Construction Layer → Risk/Overlay Layer → Deployment/Paper Layer → Governance Layer（每层职责+接口契约+数据流）
   d. P0审计先行方案：①回测正确性审计清单（前视/复权/退市/成本模型/成交约束），审计=只读验证产出审计报告；②门禁量化（毕业标准硬阈值表，分组件级/组合级/paper晋升级）；③安全兜底（断路器阈值表+checkpoint+仓位对账）——注意：这些设计为纯方案，实施另立项
   e. 迁移路径：Phase 0 审计先行（P0三件套方案+审计执行）→ Phase 1 术语与文档层（GLOSSARY，零风险）→ Phase 2 组合版本对象落地（R-335 M1-M3 并行期）→ Phase 3 治理强化（事件日志/退役规则/漂移监控，P1）→ Phase 4 paper指针切换（需批准）→ Phase 5 演进（Qlib解耦/容器化，P2）。每阶段：进入条件/退出条件/回退方案/是否并行/停机窗口
   f. 评审逐条回应表（P0×3采纳并前置、P1×4采纳/部分缓、P2×2部分采纳缓）
5. 结论建议
6. 来源清单

## 写作纪律
- 只从本笔记+上述已读材料取材，不再扩散读取
- ≥8KB；零代码；交付后更新 README.md 更新日志一行 + completions + PUT pending_review
