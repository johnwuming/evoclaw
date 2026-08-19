# R-242 e1f10dz 死区变体重评与 corr 分量口径复核报告

- 任务号：task-0395（[A14]，用户 2026-08-19 12:27 拍板按建议推进）
- 日期：2026-08-19
- 结论速览：**corr 口径复核判定「双重计价成立」——在役（v5h 与新在役 a9_ranksum_raw 相同）registry 因子表中的 ret120 是 E1 硬护栏登记项而非排序因子（222 期在役目标持仓护栏域占比恒为 0.0），g3 把候选 mom_pen_dz 与该护栏信号的 IC 相关（0.7555）当作「因子-因子冗余」计价，而护栏的行为影响已完整进入在役 locked 指标并被 oos/dd 分量计价过一次。护栏豁免口径下 mom_pen_dz 与在役四个排序因子 max|ρ| 仅 0.2066。按新在役重评：e1f10dz 未修正口径 score 0.7781（<0.867），护栏豁免口径 score 0.8781（>ranksum_raw 0.867，rank1、无 stat_warn、holdout PASS，满足自动激活三条件）。建议：口径修正落地引擎后激活 e1f10dz；口径修正本身列引擎改造建议项（本任务未改引擎）。**

## 一、背景与目标

R-241（task-0390）完成 A13 批引擎级回测：a9_ranksum_raw 以 0.8670 激活为在役（task-0394，决策 D-20260819-002，保留 E1 硬护栏）；E1 因子化最优形态 e1f10dz（λ=1.0 + 死区 0.30）locked 年化 22.02% 全场最高，但 corr 分量归零（mom_pen_dz 与在役 ret120 相关 0.7555 > 0.7 阈值）压制 score 至 0.8337。R-241 建议 #3：优先死区变体并复核 corr 分量口径。用户 12:27 拍板推进。

本任务两个目标：
1. 量化判定「在役 E1 硬护栏（ret120<-30% 排除）与候选排序惩罚因子 mom_pen_dz（λ·|clip(ret120,-1,0)|，死区段外清零）在 corr 分量上是否双重计价」，给出口径修正建议；
2. 以 a9_ranksum_raw 为 incumbent 重评 e1f10dz（oos/corr 分量与总分），对比 0.867，给激活/下线建议。

约束：纯分析 + 独立复核脚本（新文件落盘 HP `scripts/a13_corr_review.py`），未修改 evolution_pipeline.py / a9_common.py / registry / paper_engine / HP crontab。

## 二、方法与数据来源

- **评分口径复刻**：按 `evolution_pipeline.py` SCORE_CONFIG 逐分量复刻算术（oos=0.5+0.5·clamp(rel/0.40)、dd 2-7pp 线性、corr 0.5-0.7 线性、is 封顶、p 分段线性、DSR 线性）。自校验：vs 旧在役 v5h 复算 e1f10dz 的 oos_calmar 0.8026 / oos_sharpe 0.948 / dd 0.65，与 a13_score_summary.json 原评逐位一致。
- **IC 口径（因子-因子）**：ic_df = factor_ic_monthly.csv（247 月）并入 a13_supp_ic_monthly.csv（pb_inv/ret120/mom_pen/mom_pen_dz 月度全市场 Spearman IC）。g3 复现：|Pearson(月IC_f, 月IC_g)|，≥24 月有效。在役因子集三种口径：v5h 全集（原评）、a9_ranksum_raw 全集（未修正）、a9_ranksum_raw 剔除 ret120（护栏豁免）。
- **行为口径（因子-护栏）**：全量池 K 线（截至 2026-08-14）计算每日 ret120（clf/clf.shift(120)）；222 个 locked 调仓日上取四条月度序列——全池护栏域强度（ret120<-30% 个股占比）、候选 e1f10dz 目标持仓护栏域权重占比、候选组合惩罚负载（mean |clip(ret120,-1,-0.3)|）、在役 ranksum_raw 目标持仓护栏域占比；另算两组合持仓 Jaccard/重叠与 locked 月收益相关。
- **在役护栏属性证据**：v5h_xsub registry params `{e1_guard:true, mom_cols:[ret120]}`（ext 排序为 low_amount）；a9_ranksum_raw params `{e1_guard:1, ext_specs:[log_mv⁻,amt20⁻,pb_inv,roe]}`——ret120 在两代在役中都不参与排序打分，仅作硬排除条件。

## 三、核心发现（结论先行）

### 3.1 corr 口径复核：双重计价成立，量化证据四条

1. **0.7555 的构成**：mom_pen_dz 与新在役因子集的 |IC 相关| 逐对为——ret120（护栏）0.7555、roe_ttm 0.2066、circ_mv 0.1236、pb_inv 0.0697、avg_amount_20d 0.0696。惩罚完全来自「候选惩罚因子 × 在役护栏信号」这一对；与在役四个真正排序因子的最高冗余仅 0.2066，远低于 0.5 免罚线。原评 0.9426（非死区 mom_pen）同构。
2. **护栏的「因子」身份不成立**：在役 ranksum_raw 222 个调仓日目标持仓的护栏域占比均值 0.0、最大 0.0——硬护栏在每次调仓都把 ret120<-30% 剔除干净，ret120 从不进入排序分。把护栏信号当「在役因子」参与 g3，是把风险控制规则记作 alpha 信息源。
3. **护栏行为已被 oos/dd 计价一次**：e1f10dz vs ranksum_raw 的全部差异就是「硬排除 vs 软惩罚」：Δcalmar +1.19%、Δsharpe +0.94%（oos 分量 0.5148/0.5117，几乎贴零增量基线 0.5）、MDD 恶化 0.00pp（dd 分量 1.0）。行为口径辅证：两组合 locked 月收益相关 0.9992、持仓 Jaccard 均值 0.954（候选视角重叠 0.9695）——组合行为近乎同一，oos/dd 已完整定价这点残余差异。corr 分量再把同一 ret120 信号以满权重 0.10 计第二次，即双重计价，量级 = 0.10×corr 分量损失。
4. **「因子-护栏行为」相关 0.7223 的正确解读**：候选持仓护栏域权重占比（均值 1.67%，惩罚软排除后残留）与全池护栏域强度（均值 9.95%）月度相关 0.7223（惩罚负载口径 0.711）。这说明候选惩罚与在役护栏响应同一市场状态（深回撤域景气度）——这正是「函数化继承」的语义：候选用连续惩罚替代二值排除继承同一风控意图，而非复制在役的 alpha 来源。IC 口径 0.7555 测的是同一信号的自相关，不是信息冗余。

### 3.2 e1f10dz 按新在役重评（自校验通过后）

| 分量 | 权重 | vs v5h 原评 | vs ranksum_raw 未修正 | vs ranksum_raw 护栏豁免 |
|---|---|---|---|---|
| p | 0.175 | 1.0 | 1.0 | 1.0 |
| dsr | 0.175 | 0.999 | 0.999 | 0.999 |
| oos_calmar | 0.125 | 0.8026 | 0.5148 | 0.5148 |
| oos_sharpe | 0.125 | 0.948 | 0.5117 | 0.5117 |
| is_calmar / is_sharpe | 0.075/0.075 | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 |
| dd | 0.10 | 0.65（3.75pp） | 1.0（0.00pp） | 1.0（0.00pp） |
| corr | 0.10 | 0（0.7555） | 0（0.7555） | **1.0（0.2066）** |
| logic | 0.05 | 1.0 | 1.0 | 1.0 |
| **score** | | **0.8337** | **0.7781** | **0.8781** |

- 未修正口径 0.7781 < 0.867：换在役后 oos 增量红利消失（v5h 太弱），只剩 corr 惩罚 → 低于在役自身评分。
- 护栏豁免口径 0.8781 > 0.867（ranksum_raw）：**rank1、无 stat_warn（p=0.4719、DSR=0.9999）、holdout PASS（复算 25.80%/-16.13%，ann_ok、MDD 恶化 -17.42pp ≤10pp）——满足评分制 v1.1 自动激活三条件**。
- 口径披露：0.8781 vs 0.867 混合两代在役基准（e1f10dz 评 vs ranksum_raw；ranksum_raw 当时评 vs v5h），这是序贯演化的固有口径；同代直接对比应看增量本身（+0.26pp locked 年化、0pp MDD、行为近同一）。
- 旁证：非死区 mom_pen 豁免口径 max|ρ|=0.2943（worst avg_amount_20d），e1f05/10/15 重评也会改善但仍弱于死区变体——「惩罚集中于旧闸门域」的设计在口径修正后依然最优。

### 3.3 过线判定与激活建议

口径修正后 e1f10dz 过线成立（rank1 + 无警示 + holdout PASS）。但两点诚实披露：其一，score 优势 +0.011 全部来自 corr 分量修正（0→1.0），若不修正引擎口径则账面为 0.7781 不过线；其二，与在役行为差异极小（nav 相关 0.9992、持仓重叠 97%、locked +0.26pp 年化 / MDD 持平、holdout 25.80% vs 25.84%），属低边际切换，其价值主要是**消除最后一个硬护栏、与「E1 不做限制性规则」的用户原则对齐**。

## 四、结论 / 建议

1. **corr 口径修正建议（引擎改造项，本任务未实施）**：g3 的在役因子集应区分「排序因子」与「护栏登记项」——当在役 params 含 `e1_guard` 且其 mom_col（ret120）不在排序 specs 中时，该列对候选的因子化替身（mom_pen/mom_pen_dz）豁免 g3 比较；或按 R-241 备选改为持仓权重差异口径（本任务数据显示两组合重叠 97%，该口径下冗余指控同样不成立）。修正影响面：仅 g3 参与集，不动 g1/g2/g4/g5 与评分权重。
2. **e1f10dz 激活建议**：护栏豁免口径下满足自动激活条件，**建议激活**（候选形态与用户「E1 因子化、不做限制性规则」方向一致，且 locked 年化 22.02% 全场最高、MDD 与在役持平）；激活前提是引擎侧同步落地建议 #1 的口径修正以保持评分账面一致。若用户倾向最小变动，可维持 ranksum_raw 在役、e1f10dz 登记 pending 待口径修正后随下次评估自然晋级——两者实盘行为差异预期 <3% 持仓。
3. 后续观察项：e1f10dz 持仓护栏域残留 1.67%（软惩罚不排除干净），若极端月份护栏域强度放大（历史均值 9.95%），惩罚负载随之上升（相关 0.71），建议 shadow 期监控该序列极值。
4. 决策权归属：本任务未写 registry、未改引擎；激活与引擎改造均需用户/主 agent 确认后执行。

## 五、来源清单

- HP 复核脚本与产物（本次新增）：`scripts/a13_corr_review.py`（75.8s 跑通，py_compile OK）；`results/a13_corr_review.json`（4.6KB，P1/P2/P3 全量数字）；`results/a13_corr_review_series.csv`（13.5KB，222 期月度行为序列：guard_binding/cand_zone_w/cand_pen/inc_zone_w/jaccard）；日志 `logs/a13_corr_review.log`。
- HP 既有产物：`results/a13_score_summary.json`（原评 e1f10dz 0.8337 分量明细）；`results/a13_supp_ic_monthly.csv`、`results/factor_ic_monthly.csv`（247 月）；`results/a13_rsraw_e1f10dz_{locked,full}_{metrics,nav,holdings}.*`、`results/a9_ranksum_raw_{locked,full}_{metrics,nav,holdings}.*`；registry `model/registry/{v5h_xsub,a9_ranksum_raw}.json`。
- HP 代码（只读）：`scripts/a13_score.py`（g3 实现 L158-176）、`scripts/evolution_pipeline.py`（SCORE_CONFIG L69-84、score_composite L731+）、`scripts/a9_common.py`（PE2 补丁，mom_pen_dz 公式）。
- 引用报告：R-241（A13 批回测与 e1f10dz 原评）、R-225（评分制 v1.1 口径）、R-222/R-219/R-220（A9、E1 审计背景）。
- 过程笔记：`shared/results/work/task-0395-notes.md`。

*验证命令：HP 上 `/home/noname/miniconda3/envs/quant/bin/python scripts/a13_corr_review.py` 可重跑（幂等，只读既有回测产物，P2 需加载全量池约 75s）；关键相关系数可从 `results/a13_corr_review.json` 的 p1_ic_view/p2_behavior_view 字段复算，月度序列见 a13_corr_review_series.csv。*
