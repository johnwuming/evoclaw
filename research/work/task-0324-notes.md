# A2 模型迭代过程笔记 (task-0324)

## 阶段0 环境
- registry v0_seed: params div≥2%/roe≥15%/roa≥10%/sort=mv/n=20/cap10; baseline.status=pending (ledger有数: full 26.35%/locked 26.26%, runner=q4b_run_BC.py)
- ledger 2行(reset+baseline_v0_seed), decision-log 1行(SEEDB-RESET)
- catalog: results/factor_catalog_v3.json 81KB; pipeline: scripts/evolution_pipeline.py 55KB

## 阶段0 完成
- 基线复现 PASS: rerun md5 与原件一致; full 26.35%/-69.49%/0.9027/248reb; locked 26.26%/-69.49%/0.885/222reb (与ledger完全一致)
- catalog 构成破解: v3(107) = v2存量72 + pv新14 + fin新22 - dupguard(debt_to_asset)1; v2重建= v3剔除新增36 再补回 debt_to_asset
- IC 数据缺失(门禁1/2/3输入): results/factor_ic_monthly.csv+factor_ic_corr.csv 需再生, scripts/a2_ic_data.py 复用 v3ak 机制, W1方向调整约定(factor_ic_analysis L152 rank*sign)
- 关键口径: catalog mean_ic 为原始方向; 门禁IC csv 为 direction 调整后(正=按使用方向有预测力); v0_seed 四因子调整后复合预期 ≈ +0.0165 meanIC

## 阶段1 迭代设计 (2026-08-16 22:0x CST)
原则: 对照 v0_seed 只改一个维度; 每候选一句经济逻辑(g5预埋); 引擎原生优先, 新因子经 run_backtest_ext(源码级patch+等价性校验)
| IT编号 | 版本 | 改动维度(唯一) | 经济逻辑 |
|---|---|---|---|
| IT-A2-01 | v1a_score | 排序: mv→质量复合分(0.4div/0.3roe/0.3roa/−0.3mv z) | 池内用股息+盈利+市值标准化合成替代纯市值排序,捕捉"便宜的高质量小盘",降低纯壳股暴露 |
| IT-A2-02 | v1b_mvq | 排序: mv→小盘主导复合(0.7mv+0.3质量) | 保留规模溢价主贝塔(0.7),质量价值微调边际选股(0.3),与v1a构成质量/小盘两极对照 |
| IT-A2-03 | v1c_liq | 流动性: min_amt 0→500万(20日均额) | 剔除极端不可交易标的,降冲击成本与一字板损耗;本金1000万/20票=单票50万,500万日额≈10%日换手容量 |
| IT-A2-04 | v1d_cv | 排序: mv→0.5·(−z mv)+0.5·(−z amount_cv) | A1最强新因子(t=−11.8,adj ICIR 2.64):成交额波动低=筹码节奏平稳无游资炒作;与市值水平(簇7)信息互补,规避炒作型小盘 |
| IT-A2-05 | v1e_vol | 排序: mv→0.5·(−z mv)+0.5·(−z vol_20d) | A股小盘池低波动异象(t=−7.0,adj ICIR 1.57,簇4独立):低波动博弈溢价低回撤浅,利好MDD门禁 |
- v1d/v1e 用 A1 量价新因子 = "107因子进管线"实质落点; factors 列表新增 amount_cv / volatility_20d → 门禁1/2/3 有真实增量内容
- 引擎支持核查: sort=mv/div/score 原生(L405-417); min_amt 原生(L383); ext 需源码patch(锚点=else mv分支, exec进副本globals, 原engine.__dict__不动)
- 等价性校验设计: ext runner 以 v0 参数(sort=mv)跑 full+locked, 指标须与 seedB_v0 基线逐位一致才继续
- 评估窗口决策: registry backtest_refs.endtoend/metrics 一律用 locked(审计锁=正式口径), full 留 results 文件与报告作补充证据; parent v0_seed 同口径 → g6 可比

## 阶段2 完成 (2026-08-16 14:20 UTC)
- 等价性校验: ext runner full+locked diffs={} PASS (与seedB基线逐位一致)
- 候选回测结果 (locked=正式口径):
  v0_seed parent: ann 0.2626 mdd -0.6949 sharpe 0.885 (基线)
  v1a_score: full 0.2200 / locked 0.2155 / mdd -0.7017 / sharpe 0.810
  v1b_mvq : full 0.2509 / locked 0.2475 / mdd -0.6688 / sharpe 0.874
  v1c_liq : full 0.2629 / locked 0.2619 / mdd -0.7036 / sharpe 0.882
  v1d_cv  : full 0.2192 / locked 0.2158 / mdd -0.7231 / sharpe 0.792
  v1e_vol : full 0.1773 / locked 0.1689 / mdd -0.6671 / sharpe 0.724
- ledger 5行追加 (type=backtest, n_trials_cum 34->38); registry backtest_refs 已写(locked=正式窗口)
- 初判: v1b_mvq 收益最高(mdd改善最显著 -0.6688 vs -0.6949) 是唯一收益超基线候选方向

## 阶段3 五门禁裁决 (2026-08-16 14:21 UTC) — 全部 REJECT
逐候选门禁表 (n_trials=39, oos_split=2021-01, eval_window=locked):
| 候选 | g1 icir_is | g2 p | g3 max_corr | g4 dsr | g5 | g6 mdd_det_pp | verdict |
|---|---|---|---|---|---|---|---|
| v1a_score | PASS 0.599 | PASS 0.071 | N/A | FAIL 0.712 | PASS | PASS +0.68 | REJECT |
| v1b_mvq | PASS 0.599 | PASS 0.071 | N/A | FAIL 0.760 | PASS | PASS -2.61 | REJECT |
| v1c_liq | PASS 0.599 | PASS 0.071 | N/A | FAIL 0.723 | PASS | PASS +0.87 | REJECT |
| v1d_cv | PASS 1.025 | PASS 0.055 | PASS | FAIL 0.644 | PASS | FAIL +2.82 | REJECT |
| v1e_vol | PASS 1.113 | PASS 0.352 | PASS | FAIL 0.691 | PASS | PASS -2.78 | REJECT |
- 关键: g4 DSR 全灭 (阈值0.95, 实际0.644-0.760). DSR = Φ((sr-sr0)*√T/√denom), n_trials=39 → sr0=0.0425 日度, 候选 sr=0.0456-0.0550, 距离不足
- v1b_mvq/v1e_vol MDD 实际改善(-2.61pp/-2.78pp, g6 PASS); v1e_vol 因子门禁全绿(g1 1.113/g2 p0.352/g3 PASS) — 仅DSR未达
- v1d_cv 因子信号最强(amount_cv, g1 1.025)但 MDD 恶化 2.82pp(g6 FAIL) — 高换手因子尾部风险
- 结论: 本轮 5 候选全 REJECT, 无 activate (不强行); 保留 registry 候选与 gate-report 供下轮参考
