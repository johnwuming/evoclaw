# task-0393 过程笔记：MFX（v4d_mfu_raw 裸选股）回撤归因

数据：/root/.openclaw/workspace/shared/results/04-投资研究/mfx_equiv_*（equiv==ref 已验，直接引用）
对照：a2c_v2b_trr_locked_*（父本系，q3z×EW-MA200 择时）

## 基础事实（来自 metrics json）

- mfx_equiv_locked（2006-01-04 ~ 2024-06-28，18.48y）：年化 26.46%，MDD -69.49%，Sharpe 0.8894，Calmar 0.3807，222 次调仓，avg_holdings 19.69，月换手估计 0.2718，月胜率 0.5882
- mfx_equiv_full（~2026-08-14，20.61y）：年化 26.52%，MDD -69.49%，Sharpe 0.9066，Calmar 0.3817
- 注意：父报告表格 v4d_mfu_raw locked 写 20.59%/-69.27%/0.7774/0.2972，与 equiv metrics json（26.46%/-69.49%/0.8894/0.3807）不同——父表可能用了不同年化/成本口径的原始 mf_* 5件套；本报告以 equiv 文件复算数字为准（任务书口径）
- 父报告关键结论（引用）：
  - EV/EBIT 与 pe_ttm 排名相关 0.881、与 pb 0.821 → 同一负 alpha 便宜度维度（质量宇宙 ICIR -1.25）
  - ROC 独立维度但 IC≈0（宇宙内 -0.15 ICIR）
  - mf_score 复合 IC -0.047 / ICIR -1.24（质量宇宙）
  - 同批对照：v4b_mfu_trr（本地化+择时）locked 年化 12.42% / MDD -28.95% / Sharpe 0.8322 / Calmar 0.429；v4c_mfu_e1_trr（+E1）11.99% / -28.95% / 0.8116 / 0.4143
  - 五门禁 v4d：FAIL,FAIL,PASS,FAIL,PASS,FAIL（g6 MDD 违约 39.41）
- yearly returns（locked）：2008 -46.2%、2011 -30.6%、2017 -17.0%、2018 -11.8%、2024H1 -2.4%；2007 +156%、2009 +175%、2015 +160%

## 待办
- [ ] 回撤分期表（Top8）
- [ ] 最大段逐月路径
- [ ] 每段 trades/holdings 行为归因
- [ ] v2b_trr 同期对照
- [ ] 报告 R-240
