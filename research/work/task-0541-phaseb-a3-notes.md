# task-0541 Phase B 动作3：组合回测选择器化 + vC-0 复现门 — 过程笔记

开始: 2026-08-28 23:5x｜本文件为唯一恢复点（边查边写）

## 1. 需求定位（R-336 v1.4 L375）
- Phase B 动作3 = 组合回测选择器化（R-335 M2）：F6/F7 改参数化口径插件，跑通 vC-0 复现（F1 md5 915e446388… 逐位对齐 + PIT 四锚点断言）
- PIT 四锚点（R-317/R-345）：2015-06=FULL / 2015-07=REDUCE / 2020-06=REDUCE / 2020-07=FULL
- 报告编号确认：R-346 为最大已用号 → 本任务用 R-347 ✅（2026-08-28 ls 确认）
- 在役零改动约束：禁改 F6/F7 原文件；产物只落 portfolio_v1/ 新目录

## 2. 关键事实盘点
### 2.1 F1/F6/F7 原始引擎代码在 VPS 本地（非 HP）
- `/root/.openclaw/workspace/work/task-0492/scripts/backtest.py`（md5=ed95aa7603fdefec7110959bbd3a77c9）← F1 基线引擎（漂移引擎，产出 all_results.json）
- `/root/.openclaw/workspace/work/task-0495/scripts/f7_backtest.py` ← F7 引擎（简化目标权重引擎，无月内漂移）
- `/root/.openclaw/workspace/work/task-0494/scripts/f6_backtest.py` ← F6 引擎（月均仓位 w̄A + 黄金补满 f=1−w̄A）
- R-345 L38「脚本随 /tmp 清理不在盘」指 HP 侧；VPS work/ 副本在
### 2.2 md5 基线（2026-08-28 23:5x 本地核验 ✅）
- all_results.json=**915e446388fc8e63c281378c3dd66580**（R-317 L9 基线 915e446388… 完整 32 位）
- nav_curves.csv=9704a300767613523815173a5881c304；monthly_returns.csv=0113f40d7218d53f49f53b33052a3369
- 输入：a13_full_nav.csv=358ce8192880d615d620d2297387601d、gold_shadow_nav.csv=3654c3e80103fc313e24c9eb641de4e2（= HP results/ 只读源）
### 2.3 引擎口径结论
- task-0492 漂移引擎：收益后权重漂移+月初再平衡；F1=static_w(0.5) 全月再平衡；输出 json.dump(indent=1) 无时间戳 → md5 可逐位复现；F1=13.54%
- f7 简化引擎：F1=13.57%（<0.05pt 差，R-317 已声明）→ **md5 基线必须用 task-0492 漂移引擎复现，不能用简化引擎**
- f7_backtest.py 内建四锚点 assert + sim_dd(th=0.2, reduce=0.5, recover=0.05) 跑 a13 full 日频 nav；episode 2015-06-29 REDUCE(dd=-0.2026) → 2020-06-19 RESTORE(dd=-0.0499)，60 个 REDUCE 月
### 2.4 vC-0.json（task-0540 交付，HP portfolio/versions/vC-0.json）
- schema=portfolio_version@v1.2-A1；sleeves={equity_sleeve(A a13_rsraw_e1f10dz, ddc 0.2/0.5/0.05), hedge_sleeve_gold(gold_trend_sma200, cost_per_absdw=0.0013)}
- capital_policy.gross/net=1.0；provenance.weighting.in_service=dual_independent_paper_chains；f6_f7_selector=待拍板
- 注意：vC-0 无显式权重字段 → vC-0 口径=由 gross=1.0 双 sleeve 等权分割 0.5/0.5 + ddc/cost 字段推导，推导结果断言==在役常量

## 3. 实现（combo_selector/，全部新文件）
- caliber.py：口径插件。in_service=原脚本常量逐字对应；vc0=从 vC-0.json 读取+断言。缝合点=CaliberSpec 流入引擎；vC-1 换权重不换代码；偏离即复现门如实 FAIL
- state_machine.py：dd 状态机（sim_dd 同构，r_ctrl 列）+ PIT 月度状态（t 月用 t-1 月末收盘状态）+ 四锚点断言 + anchor_results 逐项对照
- combo_backtest.py：选择器入口 `python -m combo_selector.combo_backtest --caliber {in_service,vc0} --variant {F1,F6,F7a,F7b}`；F1/F7a/F7b=目标权重引擎（run_f1/run_f7 同构）；F6=月均仓位引擎（f6 monthly 同构，F6 序列 round(5) 与原 CSV 口径一致）
- run_vc0_repro.py：复现门 G1-G5（见 §4）
- engine/backtest_f1_drift_engine.py：task-0492 backtest.py **字节级副本**（md5=ed95aa7603fdefec7110959bbd3a77c9 两端核验一致）；以 __file__ 定位 BASE → 读 data/ 写 results/
- 本地代码：/root/.openclaw/workspace/work/task-0541/combo_selector/（VPS 暂存 + 同步 HP）

## 4. 复现门 G1-G5 定义与本地干跑结果（2026-08-29 00:0x，VPS pandas 3.0.5）✅
- G1 数据入位：两输入 md5 对齐（358ce819…/3654c3e8…）PASS
- G2 口径等价：F1/F6/F7a/F7b 四变体 in_service==vc0 数值字段逐项相等 PASS
- G3 F1 md5 基线：引擎副本 md5 一致 + 重跑 all_results.json=915e446388fc8e63c281378c3dd66580、nav_curves.csv=9704a300…、monthly_returns.csv=0113f40d… **三件逐位对齐** PASS
- G4 PIT 四锚点：vC-0 ddc 驱动状态机 → 四锚点+首月 FULL+episode 两事件+60 REDUCE 月全过 PASS
- G5 选择器交叉验证：vc0 口径四变体指标==在役原脚本在案值（task-0495/out/f7_results.json md5=c8866a2d137ab7c7e7fa9954fd1500e4 落盘值：F1 13.57%/F7a 13.61%/F7b 13.26%/F6 19.11%…）PASS
- **OVERALL: PASS**；对照表 combo_selector/results/vc0_repro_comparison.csv（18 行）+ repro_gate.json

## 5. HP 权威跑与零改动核验（2026-08-29 00:1x）✅
- 部署：tar 管道 → HP ~/quant-evolve/portfolio_v1/combo_selector/（引擎副本 HP 端 md5=ed95aa7603fdefec7110959bbd3a77c9 核验一致）
- 部署后清除 VPS 带来的 data/results 缓存，数据从 HP 只读源重新入位+md5 校验
- **HP 权威跑（quant python）：OVERALL PASS，G1-G5 全过**
- HP 端 md5 直接证据：results/all_results.json=915e446388fc8e63c281378c3dd66580、results/nav_curves.csv=9704a300767613523815173a5881c304、data/monthly_returns.csv=0113f40d7218d53f49f53b33052a3369
- 选择器 CLI 独立入口验证：vc0 口径 F7a → ann 0.1361/sharpe 1.483/calmar 2.001/mdd -0.068 == 在役在案值
- **在役零改动核验**：find scripts results model config registry.json evolution_pipeline.py paper_engine*.py -newermt "2026-08-28 23:50" → 空（无任何在役文件被触碰）；产物全部落在 portfolio_v1/combo_selector/ 新目录
- HP 产物清单：combo_selector/{caliber.py, state_machine.py, combo_backtest.py, run_vc0_repro.py, engine/backtest_f1_drift_engine.py, data/(3 文件), results/(all_results.json, nav_curves.csv, weights_f3_f4.csv, repro_gate.json, vc0_repro_comparison.csv 21 行 True, selector/*_check.json + monthly csv)}
- README 更新日志：portfolio_v1/README.md 追加 task-0541 一行（见下）

## 6. 报告与收尾（2026-08-29 00:2x）✅
- 报告：shared/results/05-量化投资/R-347-PhaseB动作3-选择器化与vC0复现门.md（本笔记取材）
- completions jsonl 已追加；task-0541 状态已 PUT pending_review
- README 更新日志一行已追加（HP portfolio_v1/README.md）
