# task-0581 核验笔记（vC-0 指标基底）

报告编号：实查最大 R-376（预期 376 已被占用）→ 用 R-377。

## 1. 供给链（本地实查）

- Dashboard vC-0 performance 供给：`tools/quant-bff/live/data/performance.json`
  - `curve_source = {file: nav_curves.csv, column: F1_quarterly, md5: 9704a300…}`，metrics ann 0.135702 / vol 0.094679 / sharpe 1.4333 / mdd -0.090794（与看板 13.6%/1.43/-9.1% 一致）
  - generator: hp_export_metrics.py (task-0549/0553)，generated_at_basis=source_csv_mtime_utc
- `perf_history_index.json`：6 条历史线（F0/F1_equal/F3/F4/F5/F7a），**vC-0 不在其中**，cross_check_match=true 的有 F0/F1_equal/F3/F4/F7a，F5=null；vC-0 的核验信息只在 performance.json 的 curve_source.provenance 文本里，无布尔字段 → 「核✓倒挂」的表面成因：vC-0 走 performance.json 单文件通道，无 cross_check_match 字段
- nav_curves.csv 列：month,A,gold,F0_buyhold50,F1_equal,F1_quarterly,F3_volparity,F4_erc,F5_b50_tilt65_80

## 2. F1_quarterly 口径（代码级实锤）

生成引擎：`work/task-0541/combo_selector/engine/backtest_f1_drift_engine.py`（task-0492/scripts/backtest.py 字节级副本，md5 ed95aa76…）
- 输入：a13_full_nav.csv（A 引擎日频 nav）+ gold_shadow_nav.csv（gold 影子链月频），月频对齐 2013-08..2026-07
- `f1q_mask = [d.month % 3 == 1]`；`f1q = run_engine(static_w(0.5), f1q_mask)`
- **F1_quarterly = A+gold 双腿、静态 0.5/0.5、季初再平衡（1/4/7/10月）、月间权重漂移、成本 0.13%×(|Δw_A|+|Δw_gold|)**
- 即：它是双腿组合曲线，但权重=50/50，非 58.03/41.97；也不含 DDC（run_engine 无状态机，F7a 才有 DDC）
- 在役原脚本在案指标 F1: vol 0.0923/mdd -0.0825（含 DDC REDUCE 月现金段）；nav_curves.csv 为满仓复现（vol 0.0947/mdd -0.0908），performance.json caliber.notes 已如实注明该口径差

## 3. 疑点升级

- task-0541 run_vc0_repro.py G3 前置断言写明「vC-0 → 0.5/0.5 等权 + ddc 0.20/0.5/0.05 + cost 0.0013」，源 ~/quant-evolve/portfolio_v1/portfolio/versions/vC-0.json
- 任务书称 R-355/R-368 快照口径为 equity 58.03% / gold 41.97%（等波动率求解 2026-08-28）
- 两个「vC-0 权重」矛盾 → 待查 R-355/R-368 与 HP vC-0.json 原文

## 4. HP 权威 vC-0.json 实查（只读）

- `~/quant-evolve/portfolio_v1/portfolio/versions/vC-0.json`（3976B, created 2026-08-28T15:50Z）：equity_sleeve=registry_ref a13_rsraw_e1f10dz+DDC(0.2/0.5/0.05,t+1)；hedge_sleeve_gold=engine_ref gold_trend_sma200，frozen_form{sma200,vol60,vol_target 0.1,mmf 000198,月首个交易日}；solver_ref=solver_equal_vol_v1{60d窗,252年化,min_obs40,band 0.02,fallback equal_weight}；**文件本身不存权重**
- `portfolio/samples/weight-solution-2026-08-28-dryrun.json`：solve 2026-08-28，weights equity=0.5802970 / gold=0.4197030（vol 11.11%/15.37%，风险贡献各 0.0645，closed_form，无 fallback）→ 任务书 58.03/41.97 出处实锤

## 5. 重算偏差（本地 python，源=live/data/nav_curves.csv A/gold 列）

- 复现校验：50/50 季度再平衡重跑 vs F1_quarterly 列 max|diff|=0.0（逐位一致，口径判定铁证）
- 正确口径重算（58.03/41.97 双腿月收益加权，同引擎同成本 0.13%）：
  - 月度再平衡：ann 14.44% / vol 10.32% / sharpe(几何) 1.399 / mdd −9.69% / final 5.774
  - 季度再平衡：ann 14.47% / vol 10.56% / sharpe 1.370 / mdd −10.44%
  - 期初配平漂移：ann 15.64% / vol 13.38% / sharpe 1.169 / mdd −13.85%
- 展示值（F1_quarterly 50/50季）：ann 13.57% / vol 9.47% / sharpe 1.433 / mdd −9.08% / final 5.229
- 偏差（展示 vs 58/42月度）：ann −0.87pp（低报收益）、vol −0.85pp（低报波动）、sharpe +0.034（高报）、mdd +0.61pp（高报抗回撤）
- 方向解释：50/50 黄金仓位更高（42%→50%），gold 波动低收益低 → 曲线更平更稳；看板把「更稳」错误归因给 58/42 等波动率解
- 注意：更严格口径还应含 equity DDC + gold vol_target/mmf（vC-0.json 定义），nav_curves.csv 无此数据，重算只能到「58/42 裸双腿」这一层；真实 vC-0 回测曲线与展示差异只会更大（在案在役曲线 vol 0.0923/mdd −0.0825 为 50/50+DDC，可证 DDC 显著改变曲线形状）
