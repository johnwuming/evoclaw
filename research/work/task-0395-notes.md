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
