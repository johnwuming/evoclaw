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
