# task-0541 Phase B 动作3：组合回测选择器化 + vC-0 复现门 — 过程笔记

开始: 2026-08-28 23:5x

## 1. 需求定位（R-336 v1.4 L375）
- Phase B 动作3 = 组合回测选择器化（R-335 M2）：F6/F7 改参数化口径插件，跑通 vC-0 复现（F1 md5 915e446388… 逐位对齐 + PIT 四锚点断言）
- PIT 四锚点（R-317/R-345）：2015-06=FULL / 2015-07=REDUCE / 2020-06=REDUCE / 2020-07=FULL
- 报告编号确认：R-346 为最大已用号 → 本任务用 R-347 ✅（2026-08-28 ls 确认）

## 2. 关键发现：F1/F6/F7 原始引擎代码在 VPS 本地（非 HP）
- `/root/.openclaw/workspace/work/task-0492/scripts/backtest.py` ← F1 基线引擎（产出 all_results.json，md5 基线 915e446388…）
- `/root/.openclaw/workspace/work/task-0495/scripts/f7_backtest.py` ← F7 引擎
- `/root/.openclaw/workspace/work/task-0494/scripts/f6_backtest.py` ← F6 引擎
- R-345 L38 说"脚本本体随 /tmp 清理已不在盘"指 HP 侧 /tmp；VPS work/ 副本在。待核 task-0492 scripts 是否即产出 md5 基线的原版。
- 输入数据源（task-0492 notes §1/§5，HP 只读）：
  - A nav: HP ~/quant-evolve/results/a13_rsraw_e1f10dz_full_nav.csv md5=358ce8192880d615d620d2297387601d（日频 2006-01→2026-08）
  - gold nav: HP ~/quant-evolve/results/engines/gold/shadow_nav.csv md5=3654c3e80103fc313e24c9eb641de4e2（月频 2013-08→2026-08，157月 net 列）
- F1 口径（R-317 L13 + task-0492 notes §3）：w_A=0.5/w_gold=0.5 月度再平衡；窗口 2013-08..2026-07 n=156；成本 0.13%×(|Δw_A|+|Δw_gold|) 双腿，首月部署 0.13%×1.0；现金腿 0 利息；月内漂移不建模
- dd 状态机：task-0494（th20_rd50 默认参数，源码 :533-540 语义）；episode 2015-06-29 REDUCE → 2020-06-19 RESTORE（60 REDUCE 月）

### 5.3 选择器实现与本地干跑（2026-08-29 00:0x）✅
- 代码：work/task-0541/combo_selector/{caliber.py(口径插件), state_machine.py(dd状态机+PIT+四锚点), combo_backtest.py(选择器入口 F1/F6/F7a/F7b), run_vc0_repro.py(复现门 G1-G5), engine/backtest_f1_drift_engine.py(task-0492 字节级副本, md5=ed95aa7603fdefec7110959bbd3a77c9 核验一致)}
- vC-0 口径实现：vC-0.json → gross=1.0 双 sleeve 等权分割 0.5/0.5 + ddc 从 equity_sleeve.risk_control.ddc + cost 从 gold.frozen_form.cost_per_absdw=0.0013 + F7a/b 降仓权重由规则推导后断言==在役常量
- 本地干跑（VPS, pandas 3.0.5, 数据=task-0492/data 同 md5 副本）：**OVERALL PASS，G1-G5 全过**
  - G1 两输入 md5 对齐；G2 四变体 in_service==vc0 等价；G3 重跑 all_results.json=915e446388fc8e63c281378c3dd66580 + nav_curves.csv=9704a300… + monthly_returns.csv=0113f40d… **三件逐位对齐**；G4 四锚点+episode(2015-06-29 REDUCE→2020-06-19 RESTORE)+60 REDUCE 月全过；G5 四变体指标==在役原脚本在案值（f7_results.json md5=c8866a2d…）
- 对照表：combo_selector/results/vc0_repro_comparison.csv（18 行逐项）+ repro_gate.json

## 6. HP 权威跑与零改动核验
（进行中）
- 目录：~/quant-evolve/portfolio_v1/{portfolio_version.py, solver_equal_vol.py, event_ledger.py, trading_calendar.py, build_vc0.py, run_solver_demo.py, tests/, portfolio/}
- vC-0 快照：portfolio/versions/vC-0.json（另有 .trash-dev/ 副本=开发残留）
- 待细读：vC-0.json 字段、portfolio_version.py 接口

## 4. 执行方案（草）
- 在 HP portfolio_v1/ 下新建 selector 子模块（wrapper，新文件，不改在役）
- 「在役原样口径」= task-0492/0495 引擎口径原样；「vC-0 口径」= 权重从 vC-0.json 读
- vC-0 权重应 = 50/50 等权（当前在役三元组）→ vC-0 口径跑组合回测应复现 F1 → all_results.json md5 逐位对齐 915e446388… + PIT 四锚点断言
- 产物落 portfolio_v1/，报告 R-347

## 5. 核验记录（边查边写）

### 5.1 task-0492 本地产物 md5 核验（2026-08-28 23:5x）✅
- all_results.json=**915e446388fc8e63c281378c3dd66580**（完整 32 位，与 R-317 基线 915e446388… 逐位对齐）
- nav_curves.csv=9704a300767613523815173a5881c304；monthly_returns.csv=0113f40d7218d53f49f53b33052a3369
- 输入 data/a13_full_nav.csv=358ce8192880d615d620d2297387601d、data/gold_shadow_nav.csv=3654c3e80103fc313e24c9eb641de4e2（与 task-0492 notes §5 记录一致）

### 5.2 引擎口径关键结论
- task-0492 backtest.py：漂移引擎（收益后权重漂移，月初再平衡）；F1=static_w(0.5)+allT 全月度再平衡；输出 json.dump(indent=1, ensure_ascii=False) 无时间戳 → md5 可逐位复现
- f7_backtest.py（task-0495）：简化引擎（无月内漂移）；F1 简化口径 ann 13.57% vs task-0492 漂移引擎 13.54%（<0.05pt，R-317 已声明）
- **推论：md5 基线 915e446388… 对应 task-0492 漂移引擎 all_results.json → vC-0 复现门必须驱动 task-0492 引擎，不能用 f7 简化引擎**
- f7_backtest.py 内建 PIT 四锚点 assert：2015-06=FULL/2015-07=REDUCE/2020-06=REDUCE/2020-07=FULL + 首月非 REDUCE；状态机 sim_dd(th=0.2, reduce=0.5, recover=0.05) 跑 a13 full 日频 nav
