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

## 指标口径验证（VPS 本地 python 预演，/tmp/task-0549/）
- md5 落盘核验: nav_curves.csv=9704a300… all_results.json=915e4463… monthly_returns.csv=0113f40d… 全部与 G3 门一致
- 选定口径（从 nav_curves.csv F1_quarterly 列全期计算，基期 1.0，N=156 月收益）:
  - 年化收益 = (NAV末/1.0)^(12/156)-1 = 0.1357
  - 年化波动 = 月收益样本std(ddof=1)×sqrt(12) = 0.0947
  - 夏普 = 年化收益÷年化波动 = 1.433（无风险利率=0）
  - maxDD = min(1-NAV/峰值)（含基期1.0）= -0.0908
- 交叉验证: 与 all_results.json F1_quarterly 条目 ann=0.1357/vol=0.0947/mdd=-0.0908 完全一致；其 sharpe=1.397 为算术年化口径（mean×12÷vol≈0.1323/0.0947），与我们几何口径 1.433 的差异已定位
- 与 vc0 在案指标(0.0923/1.431/-0.0825)差异根因: 在役原脚本曲线含 DDC REDUCE 月现金段，nav_curves.csv F1_quarterly 列为满仓复现曲线（final_nav 5.229 一致到 4dp）；performance.json 将如实注明口径

## 导出脚本（deliverable: tools/quant-bff/live/export/hp_export_metrics.py）
- bugfix 1 次：基期 1.0 前插后误加首月特殊项导致 157 条收益，修复为纯环比 156 条
- 本地验证输出: ann=0.135706 vol=0.094703 sharpe=1.433 mdd=-0.090794（与口径B预演一致）
- 输出默认 /tmp/performance.json（HP results/ 不写盘，保持只读）

## HP 正式执行与数据落位（2026-08-29 02:11）
- HP quant python 执行 /tmp/hp_export_metrics.py：OK md5=9704a300… n=156 ann=0.135702 vol=0.094679 sharpe=1.4333 mdd=-0.090794
- scp 落位：live/data/performance.json(1518B) + live/data/nav_curves.csv(23721B, md5 9704a300… 与 HP 源一致)
- live/data 现有 engines.json(597B, 00:24 别任务新增) migration/overview/portfolios/versions 原样未动

## BFF 设计（对齐既有数据文件驱动模式）
- portfolioDetailHandler 扩展：doc + performance 字段
- loadPerformance(config,id)：读 performance.json（portfolio_version_id 必须匹配 :id，否则 null）+ 解析 nav_curves.csv 取 curve_source.column 列 → nav_curve[{date,nav(6dp)}]；任一文件缺失 → performance=null（加性字段不 503）
- fixtures/good/data 增加 performance.json/nav_curves.csv(小样本含干扰列 A)/versions/vC-0.json(最小快照) → 契约测试可跑
