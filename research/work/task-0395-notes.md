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
