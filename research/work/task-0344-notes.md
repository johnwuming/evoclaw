# task-0344 量化流水线人为约束全量盘点 — 过程笔记

任务：审计量化流水线所有人为约束，分类 A/B/C/D，产出 R-219 报告（只盘点不改代码）。
分类口径：
- A类·评估流程约束：门禁/activate/locked窗口/战役目标
- B类·策略内硬约束：闸门/护栏/剔除/地板（可权重化）
- C类·市场现实约束：一字板/T+1/成本/停牌（物理现实）
- D类·数据正确性约束：PIT对齐/审计锁/防作弊基建

## 阶段0：环境确认
- [2026-08-17 13:12] VPS 侧确认 R-218 为现有最大编号，本任务用 R-219。
- HP 访问：ssh -i /root/.ssh/id_hp -p 2222 noname@10.12.192.174

## 阶段1：代码级盘点（HP: ~/quant-evolve）

### 1.1 evolution_pipeline.py（55KB）— 五门禁 g1-g6
- GATE_CONFIG（L56-64）：
  - g1 icir_is_min=0.5：IS全样本复合ICIR年化下限
  - g2 oos_p_min=0.05：OOS相对IS劣化单侧t检验 p>0.05（不显著劣于才过）；oos_split_ym=2021-01（OOS起始月）
  - g3 max_corr_max=0.7：与在役因子最高|ρ|上限
  - g4 dsr_min=0.95：Deflated Sharpe Ratio 下限；n_trials=HISTORICAL_TRIAL_OFFSET=34+台账backtest计数（多重检验校正）
  - g5_logic：logic 字段非空（文档性门禁）
  - g6 mdd_vs_parent_max_pp=2.0：MDD较父版本恶化≤2pp，一票否决（E3修复task-0292）
- 判定逻辑（L751-753）：decisive=状态为PASS/FAIL的门禁集合；任一FAIL→REJECT；全PASS→PASS；无decisive→N/A
- FAIL后果（L846-848 _do_activate）：verdict∉(PASS, legacy-grandfathered) 且无 --force → 拒绝激活。activate 需人工确认（Step7 注释 L1136：activate 为人工确认操作，不自动激活）
- HISTORICAL_TRIAL_OFFSET=34（registry化前历史试验数，L54）

### 1.2 audit_lock.py（1.5KB）— 审计锁
- AUDIT_LOCK_END="2024-06-30"：2024-06-30之后为锁定审计段，所有OOS/评估窗口不得穿透（R-213评审确认，task-0292/E6修复）
- clamp_date/clamp_ym/breaches_lock 统一工具；gate_icir 中 oos_mask 强制 ym<=2024-06
- 历史：v1.4及之前 gate-report OOS穿透是历史事实，不回改
