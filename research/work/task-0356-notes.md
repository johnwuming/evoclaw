# task-0356 [A10-2] v6a_def 正式回测笔记（VPS 侧）

目标：v6a_def 补正式回测产物 full+locked 10 文件 + EQUIV 校验 + registry backtest_refs 更新 + decision-log。

## 事实收集（HP: ssh -i /root/.ssh/id_hp -p 2222 noname@10.12.192.174）

- 引擎机制确认：
  - 正式回测 = `a9_common.patch_engine` 补丁链端到端引擎（a8_bucket.py 同款，已验证 equiv ≡ a7_v5h_xsub_formal 逐位）
  - a9_grid.py = 单遍选择 + 40 择时变体后验递推；最终重跑 anchor diffs={}（PASS）
  - 引擎 `run_backtest` 写 full 产物（nav/trades/holdings/yearly/metrics，需 force_save_artifacts=1 + date_range）；`a9_common.write_dual_artifacts` 写 locked 5 件
- v6a_def 配置（model/registry/v6a_def.json）= v5h_xsub 选股层 + 择时 q3z(w_min=0.0)×MA15(趋势0.6) = a9 网格 MA15_on_f0
- V5H 选股 cfg（a8_bucket.py 原文）：sort=ext, ext_mode=zscore, ext_specs=[("amt20",0.0,-1),("circ_mv",1.0,-1)], ext_filter_all=1, e1_guard=1, xsub_days=365.0
  - 即 registry 的 ext_factor=low_amount / ext_weights=[1,0]（circ_mv 权1 + amt20 权0但 notna 过滤）
- BASE cfg（a8 原文）：div_min=0.02 roe_min=0.15 roa_min=0.10 n_hold=20 price_cap=10.0 min_amt=0.0 drawdown_control=0 cost_model=v2 limit_board=on capital_base=1e7 cost_rate=0.001 limit_up_pct=0.098
- FULL_RANGE=("2006-01-01","2026-08-31")；AUDIT_LOCK_END=2024-06-30（locked 窗）
- 锚 nav：results/a9_timing_MA15_on_f0_nav.csv — 5008 行，2006-01-04 ~ 2026-08-14，末值 16.24248131782566
- 网格表 MA15_on_f0 行：full ann=0.1448 mdd=-0.2467 sharpe=1.0453 calmar=0.5871；locked ann=0.1463 mdd=-0.2467 sharpe=1.0412 calmar=0.5931
- 等价性论证：引擎 eff_ret = day_ret*pos_ratio*timing_ratio − cost_v2(与网格 run_variant 同公式同序)；a8 equiv 锚(a8x_equiv_v5h vs a7_v5h_xsub_formal)已背书补丁链逐位；故本跑只需与 MA15_on_f0 nav 直接逐位比对
- runtime 参考：市场加载 ~70s + 选择路径 ~50-120s，全程 <10min
- registry: model/registry/v6a_def.json（含 gate.score_holdout，今晚 task-0353 写入——只动 backtest_refs，不碰 gate）
- decision-log: model/decision-log.jsonl（ts/decision_id/type/...格式已抄录）
- 结果目录 results/ 已有 201 个 formal 文件；v5h_xsub formal 10 件为命名模板

## 执行记录

- [00:30] 脚本 scripts/a10_v6a_formal.py 写入（新文件 108 行，不改引擎；py_compile PASS），nohup 启动 PID 49714
- [00:33] **回测完成（141s，exit 0）**：
  - full ann=0.1448 mdd=-0.2467 sharpe=1.0453 calmar=0.5871
  - locked ann=0.1463 mdd=-0.2467 sharpe=1.0412 calmar=0.5931
  - 与网格表 MA15_on_f0 行完全一致（grid_metrics_match=true）
- [00:33] **EQUIV BIT_EXACT**（results/a10_v6a_formal_equiv.json）：
  - 正式 full nav vs a9_timing_MA15_on_f0_nav.csv：5008 日 2006-01-04~2026-08-14，dates_eq=true，vals_bit_exact=true，**max_abs_diff=0.0**
  - locked 前缀（≤2024-06-30）同样逐位一致
- [00:33] 产物 10 件（验收1 ✓）：full/locked × metrics/nav/yearly/trades/holdings，大小 491B~162KB 合理
- [00:40] **registry 更新完成**（验收3 ✓）：
  - 备份：model/registry/v6a_def.json.bak-a10-20260818 留存
  - backtest_refs 新结构（对齐 v5h_xsub 口径）：endtoend=locked_nav / baseline=full_nav / metrics(222 调仓) / metrics_full(248) / eval_window / formal(含 equiv_report 指针) / grid_refs(旧网格引用降级归档)
  - gate.score_holdout 逐字段比对前后一致（pass=true 未覆盖）；status=candidate 未 activate；g1-g6/审计锁未动
- [00:41] decision-log 追加 D-20260818-A10-2（type=v6a_formal_backtest，第 58 条）

## 验收自检（全部通过）

1. `ls results/ | grep -c "^a10_v6a_def_formal"` = **10** ✓
2. EQUIV：results/a10_v6a_formal_equiv.json — equiv=BIT_EXACT，dates_eq/vals_bit_exact/locked_bit_exact=true，max_abs_diff=0.0，grid_metrics_match=true ✓
3. registry backtest_refs → 正式产物；.bak 留存；score_holdout 未覆盖 ✓
4. decision-log D-20260818-A10-2 ✓；本笔记 ✓；completions task-0356 ✓

红线遵守：未改引擎代码（新文件 scripts/a10_v6a_formal.py 用 a9_common.patch_engine 现有机制）；registry 仅动 backtest_refs；未 activate；未杀已有进程。
