# task-0395 notes (e1f10dz 重评 + corr 口径复核)
开始: 2026-08-19 13:10:13

## 1. 原评数据核对（a13_score_summary.json，落盘于 HP results/）
- e1f10dz 原评（incumbent=v5h_xsub）：score 0.8337
  - components: p=1.0, dsr=0.999, oos_calmar=0.8026, oos_sharpe=0.948, is_calmar=1, is_sharpe=1, dd=0.65, **corr=0**, logic=1.0
  - g3_max_corr: FAIL, max_abs_corr=0.7555, worst_pair=[mom_pen_dz, ret120], new_factors=[avg_amount_20d, pb_inv, mom_pen_dz], method=月度IC序列Pearson(补充IC列并入factor_ic_monthly)
  - 非死区变体 e1f05/10/15 的 corr=0.9426（mom_pen vs ret120）
  - e1f10dz locked: 22.02%/-33.55%/sharpe 1.3561/calmar 0.6562; holdout 25.80%/-16.13% PASS
- 旧在役 v5h_xsub active_metrics: 15.74%/-29.80%/sharpe 0.9983/calmar 0.5283
- 结论：corr 分量归零直接把 score 从 ~0.93 压到 0.8337，是唯一归零分量
## 2. 评分口径事实（代码级）
- SCORE_CONFIG（evolution_pipeline.py L69）：weights p .175/dsr .175/oos_calmar .125/oos_sharpe .125/is_calmar .075/is_sharpe .075/dd .10/corr .10/logic .05
  - oos: 0.5+0.5·clamp(rel/0.40,±1)，rel=(cand-active)/|active|（active 取 registry backtest_refs.metrics，locked 窗）
  - dd: ≤2pp→1.0，2-7pp 线性→0；corr: ≤0.5→1.0，0.5-0.7 线性→0（0.7555→0 ✓）
  - GATE_CONFIG max_corr_max=0.7（g3 硬阈值）
- g3 实现（a13_score.py L158-176）：new_factors=候选因子−在役 registry selection.factors；对每个 new f × 在役 g2f：|Pearson(月度IC_f, 月度IC_g2f)|（ic_df=base 108列+补充列）
- **关键**：v5h_xsub registry factors=[div_yield_ttm,roe_ttm,roa_ttm,circ_mv,ret120]；a9_ranksum_raw factors=[circ_mv,avg_amount_20d,pb_inv,roe_ttm,ret120]
  - 两个在役的 ret120 都是 E1 硬护栏（ret120<-30% 排除）的登记项，非排序因子（ranksum 排序=log_mv⁻/amt20⁻/pb_inv/roe，无 ret120）
  - → 对 e1f10dz 重评时，new_factors=[mom_pen_dz]，其 vs 在役 ret120 的 IC 相关（0.7555）仍会入 g3 → 这是「护栏被当排序因子计价」的口径问题本体
- 新在役 a9_ranksum_raw registry locked: ann 21.76%/mdd -33.55%/sharpe 1.3435/calmar 0.6485
- e1f10dz locked: 22.02%/-33.55%/1.3561/0.6562 → 新 oos_rel: calmar +1.19%、sharpe +0.94% → oos 分 ≈0.515/0.512（近零增量=0.5 基线）；新 dd=0.00pp→1.0（原 3.75pp→0.65）
- mom_pen_dz 精确公式（a9_common.py PE2）：penalty=λ·|clip(ret120,-1,0)|，dz>0 时 (-dz,0] 段清零 → 仅 ret120<-30% 计罚=旧闸门域
- holdings CSV：date,num_target,target(|分隔代码)，222 期，等权约 20 只
## 3. P1 IC 口径复核结果（a13_corr_review.py，日志 logs/a13_corr_review.log）
- 复现原评：mom_pen_dz vs v5h 因子集 max|ρ|=0.7555 ✓（worst pair mom_pen_dz×ret120）
- vs 新在役 a9_ranksum_raw（未修正，护栏 ret120 计入因子集）：max|ρ|=0.7555 —— 与预期一致，
  ranksum_raw 的 registry factors 同样含 ret120（护栏登记项），g3 逻辑不变则惩罚不变
- **护栏豁免口径（在役仅排序因子 circ_mv/avg_amount_20d/pb_inv/roe_ttm）：max|ρ|=0.2066** → corr 分量 1.0
- 结论（口径层）：0.7555 全部来自「mom_pen_dz × 在役护栏信号 ret120」这一对；候选动量惩罚因子与
  在役四个排序因子的 IC 冗余度仅 0.2066，远低于 0.5 免罚线
- mom_pen（非死区）双口径数值待日志确认（预期 uncorr≈0.9426 复现）
## 4. P2 行为口径结果（222 期 locked，2006-02~2026）
- corr(候选持仓护栏域权重占比, 全池护栏域强度) = 0.7223（n=221）——「因子-护栏行为」口径
- corr(候选组合惩罚负载, 全池护栏域强度) = 0.711；corr(zone_w, pen)=0.9951（自洽）
- 在役 ranksum_raw 目标持仓护栏域占比：均值 0.0、最大 0.0 —— 222 期零泄漏，硬护栏在每个调仓日严格执行（数据+语义双重验证）
- 候选 e1f10dz 持仓护栏域占比均值 1.67%（惩罚软排除，非零但很小）；全池护栏域强度均值 9.95%
- 持仓 Jaccard 均值 0.954 / 候选视角重叠 0.9695；locked 月收益相关 0.9992 —— 两组合行为近乎同一
- **双重计价判定**：护栏对在役行为的全部影响已在 locked 指标（→oos/dd 分量：oos 0.5148/0.5117≈零增量基线、dd 0.00pp→1.0）中计价一次；corr 分量再把同一信号（ret120 深回撤域）以满权重 0.10 计价第二次（0.7555>0.7→0 分）。两组合 nav 相关 0.9992、重叠 97%，corr 的「信息冗余」指控实际测的是「风险控制的函数化继承」而非 alpha 冗余
## 5. P3 重评分结果（vs 新在役 a9_ranksum_raw）
- 自校验：vs v5h 复算 oos_calmar 0.8026/oos_sharpe 0.948/dd 0.65 与原评 summary 完全一致（算术复刻可靠）
- 新分量：oos_calmar 0.5148（Δcalmar +1.19%）、oos_sharpe 0.5117（Δsharpe +0.94%）、dd 0.00pp→1.0
- corr 双口径：
  - 未修正（护栏计入在役因子集）：max|ρ|=0.7555（mom_pen_dz×ret120）→ corr 分量 0 → score 0.7781 < 0.867
  - 护栏豁免：max|ρ|=0.2066（worst=roe_ttm；avg_amount_20d 0.0696/circ_mv 0.1236/pb_inv 0.0697）→ corr 分量 1.0 → **score 0.8781 > ranksum_raw 0.867**
  - 非死区 mom_pen 豁免口径 max|ρ|=0.2943（avg_amount_20d）——e1f05/10/15 若重评也会显著改善但弱于 dz
- holdout 复算：25.80%/-16.13%，ann_ok ✓，mdd_det -17.42pp ≤10pp → PASS（与原评一致）
- 过线判定（豁免口径）：rank1（0.8781>0.867）、无 stat_warn（p 0.4719、DSR 0.9999）、holdout PASS → 满足自动激活三条件
- 注意：0.8781 vs 0.867 的对比混合了两代在役基准（e1f10dz 评 vs ranksum_raw；ranksum_raw 当时评 vs v5h），序贯演化固有口径，报告需披露
- 中间产物：HP results/a13_corr_review.json（4.6KB）/ a13_corr_review_series.csv（13.5KB，222 期月度序列）
- 复核脚本：HP scripts/a13_corr_review.py（新文件，未动任何现有代码/registry）
## 6. 交付与验证
- 报告：shared/results/05-量化投资/R-242-e1f10dz重评与corr口径复核.md（6.2KB）
- README.md 变更记录（顶部明细表+正式表）已加 R-242 行
- 复核脚本 HP scripts/a13_corr_review.py 已跑通（75.8s，退出码 0），可重跑（幂等只读）
- 约束遵守：未改 evolution_pipeline.py / a9_common.py / registry / paper_engine / HP crontab；HP 无进程被杀（nohup 自然结束）
- 关键数字一览：corr 0.7555=全部来自护栏对；豁免口径 0.2066(roe_ttm)；score 0.7781/0.8781；ranksum_raw 0.867；
  行为口径 r=0.7223；nav 相关 0.9992；Jaccard 0.954；在役护栏泄漏 0.0
