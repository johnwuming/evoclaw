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

## 6. 连带检查：runtime NAV 镜像（契约 #10）

- `live/data/governance/runtime.json`：portfolio_version_ref=vC-0，nav_daily=11 个日频点（2026-08-14..08-28），source_file=results/baseline-paper-nav.csv，§3.6 镜像语义
- HP `results/baseline-paper-summary.json` 实查：mode=paper，start 2026-08-17，8 只持仓 equity_w=0.6、cash 40393（40%），**无任何黄金/货基持仓**，model_version=a13_rsraw_e1f10dz，timing_layer=timing_v4_i4_q3z（timing_ratio 0.6174）
- 判定：runtime 镜像与 perf-history **不同源不同病**（不经 nav_curves.csv），但它是第三个口径——60% equity(a13+择时)+40% 现金的单腿纸面链，被 R-354 治理切换挂到 vC-0 ref 下（有意决策、有记录）；严格讲 runtime NAV 也不是 58/42 双腿组合

## 7. 核✓倒挂成因（代码级闭环）

- 写入方：task-0555 一次性计算（perf_history_index.json generator="task-0555 one-off compute (HP read-only)"）
- 语义：对 nav_curves.csv 各历史列用 0549 口径重算指标 vs HP all_results.json 在案锚逐项比对；true=F0/F1_equal/F3/F4/F7a；null=F5（all_results 无锚）
- vC-0 为何缺失：①performance.json 根本没有 cross_check_match 布尔字段（只有 cross_check_ref 数值 + provenance 文本）；②`src/perf-history.js:84` activeEntry() 硬编码 `cross_check_match: null`，label 同样硬编码'vC-0 现役（F1·vc0 口径）'
- 即：vC-0 的 null 是「代码硬编码+字段缺失」，不是核验失败；而历史条目的 true 是「同文件列 vs 同引擎锚」的弱核验（自洽性核验）——信号倒挂成立：核验最厚的 vC-0（G1-G5 复现门）反而无布尔标记
- 另：G3 断言「vC-0→0.5/0.5 等权+ddc」是 task-0541 时代口径；08-28 task-0540 快照把 vC-0 权威定义改为 solver_equal_vol_v1（58.03/41.97），但曲线列未随定义更新——展示基底滞后于定义变更

## 8. 最终判定

**基底错误（展示≠权威 vC-0 双腿组合）**。F1_quarterly 虽是双腿（A+gold）曲线，但权重 50/50 季度再平衡、满仓、无 DDC、无 vol_target，与 vC-0.json 权威定义（等波动率 58.03/41.97 + equity DDC + gold sma200/vol_target/mmf）是两个策略。重算偏差（58/42 固定权重月度再平衡 vs 展示）：ann −0.87pp、vol −0.85pp、sharpe +0.034、mdd +0.61pp。
数据缺口：滚动等波动率权重的全历史 vC-0 组合回测曲线在任何地方都不存在；本报告重算为「58/42 固定权重」近似（任务书指定口径），真实组合历史曲线只会偏离更远。
