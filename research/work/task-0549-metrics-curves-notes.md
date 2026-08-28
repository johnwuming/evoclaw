# task-0549 过程笔记（新看板接入回测指标与曲线）

## 现状核验
- BFF live/data 现有: migration.json(708B) overview.json(130B) portfolios.json(422B) versions/vC-0.json（快照文件，含 data_cut=2026-08-26）
- portfolios.json: vC-0, status=paper, solver=solver_equal_vol_v1, data_cut=2026-08-26
- BFF src: app.js(11.8KB) config.js ctx.js ledger.js pending-risks.js replay.js risk-gates.js server.js
- test: api-contract / api-degrade / api-risk-gates / replay；PRD 26.6KB、架构 45KB（>30KB 分段读）

## HP 数据核验（2026-08-29）
- results/: all_results.json(9.7KB) nav_curves.csv(23.7KB) vc0_repro_comparison.csv selector/ vc0_repro_comparison
- nav_curves.csv: 月频 156 行（2013-08-31..2026-07-31），列: month,A,gold,F0_buyhold50,F1_equal,F1_quarterly,F3_volparity,F4_erc,F5_b50_tilt65_80
- md5: nav_curves.csv=9704a300767613523815173a5881c304（与 vc0_repro_comparison.csv G3 门一致，逐位复现 PASS）
- monthly_returns.csv 实际位于 data/monthly_returns.csv（md5 0113f40d…，G3 PASS）
- 在役组合曲线判定：vc0_F1_check.json metrics ann=0.1357 vol=0.0923 sharpe=1.431 mdd=-0.0825 final_nav=5.229，match=true；final_nav 与 nav_curves.csv F1_quarterly 末值 5.22921278108852 一致 → 在役回测曲线=F1_quarterly 列
- 注意：all_results.json 里 F1_quarterly 条目(vol 0.0947/mdd -0.0908)与 vc0 口径在案指标(0.0923/-0.0825)略异；本任务口径=从 nav_curves.csv 全期自行计算并在 performance.json 注明
