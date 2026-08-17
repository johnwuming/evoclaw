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

## P04 实施开始 (23:53)
- HP 现场: pipeline 64079B=完整态 mtime 15:04(UTC); shadow/holdout 命中=0; py_compile OK(一次 transient segfault 重试即过)
- 备份已建: scripts/evolution_pipeline.py.bak-p04-155305
- 路径: HP ~/quant-evolve/scripts/evolution_pipeline.py; PY=/home/noname/miniconda3/envs/quant/bin/python
- 代码勘察: nav csv 格式=date,nav[,num_held]; 三份 nav 均 5009 行 2006-01-04→2026-08-14
- v5h/v5i backtest_refs: endtoend=_locked_nav, baseline=_full_nav(全窗口!), metrics=locked口径(v5h ann .1574/mdd -.298; v5i .1523/-.293)
- v6a_def: metrics=locked口径(ann .1463/mdd -.2467 源 a9 grid 表), nav=a9_timing_MA15_on_f0_nav.csv 全窗口
- save_version=save_json 直接写 registry/<vid>.json 无备份 → demo 写前手动 cp .bak
- 设计: SHADOW_CONFIG 常量(N=3, holdout 2024-07, ann≥60%locked, mdd≤+10pp); _seg_nav_metrics+compute_holdout_metrics(nav→baseline→locked换full 兜底); _shadow_update 状态机(gate.shadow_watch); cmd_evaluate 晋升链 rank1→影子→holdout→activate(shadow_watch/holdout_hold decision-log); _do_activate 晋升前双检查(--force 越过); score_holdout 写入 gate; 11 个小补丁逐个验证

## 补丁全部落地 (00:2x)
- 11/11 PATCH_OK（p01 常量/p02 _seg_nav_metrics/p03 compute_holdout_metrics/p04 _shadow_update/p05 holdout变量+report字段/p06 gate.score_holdout 回写/p07a+b 晋升链/shadow_watch·holdout_hold 分支/p08 decision-log 双段/p09 _do_activate 晋升前双检查/p10 activate 日志加 shadow_clean·holdout_pass）
- 每补丁 assert 锚点唯一+py_compile OK；grep -cE "shadow|holdout"=43(≥6)；64079→71547B
