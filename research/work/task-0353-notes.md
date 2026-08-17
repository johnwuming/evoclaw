# task-0353 评分制 v1.1 影子观察期+holdout 晋升门槛 — 工作笔记

## 目标
1. 影子观察期：auto-activate 遇 stat_warn → shadow 标记 + shadow_watch 日志，连续 N=3 评估周期无升级才可上岗
2. holdout 晋升门槛：activate 前算 2024-07~数据末 holdout 指标；年化 ≥ locked 60%，MDD 恶化 ≤ +10pp
3. evaluate/decision-log 双段指标口径
4. 三版回归试算（v5h_xsub/v6a_def/v5i_comb）
5. D-20260817-P04 日志 + 笔记 + completions

## 进度

## 发现（代码/数据勘察）
- pipeline=64KB；关键段：SCORE_CONFIG L68-83；score_composite L713-796；cmd_evaluate L816-948（auto-activate L910-928）；_do_activate L989+；decision_log(dtype,version,trigger,metrics_summary,...,**extra) L247
- registry=model/registry/（49文件）；REGISTRY_DIR/RESULTS 常量 L38-47
- 三版现状：v5h_xsub active score=None(legacy) nav=results/a7_v5h_xsub_formal_locked_nav.csv(止2024-06-28)；v6a_def candidate score=0.6446 flags=partial，endtoend=None 但 backtest_refs.nav=results/a9_timing_MA15_on_f0_nav.csv(2006→2026-08-14)；v5i_comb candidate score=None nav=a7_v5i_comb_formal_locked(止2024-06-28)
- 关键：v5h/v5i locked nav 无 holdout 段，但 results/ 有同名 _full_ nav（a7_v5h_xsub_formal_full_nav.csv / a7_v5i_comb_formal_full_nav.csv，均 2006-01→2026-08-14）→ 计算函数用 "_locked_→_full_" 换名约定兜底
- v6a_def locked 指标源自 a9_timing_grid_table.csv（locked 口径）；a9 nav 全窗口
