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

## 3. HP portfolio_v1 上游交付（task-0540，已盘点）
- 目录：~/quant-evolve/portfolio_v1/{portfolio_version.py, solver_equal_vol.py, event_ledger.py, trading_calendar.py, build_vc0.py, run_solver_demo.py, tests/, portfolio/}
- vC-0 快照：portfolio/versions/vC-0.json（另有 .trash-dev/ 副本=开发残留）
- 待细读：vC-0.json 字段、portfolio_version.py 接口

## 4. 执行方案（草）
- 在 HP portfolio_v1/ 下新建 selector 子模块（wrapper，新文件，不改在役）
- 「在役原样口径」= task-0492/0495 引擎口径原样；「vC-0 口径」= 权重从 vC-0.json 读
- vC-0 权重应 = 50/50 等权（当前在役三元组）→ vC-0 口径跑组合回测应复现 F1 → all_results.json md5 逐位对齐 915e446388… + PIT 四锚点断言
- 产物落 portfolio_v1/，报告 R-347

## 5. 核验记录（边查边写）
（进行中）
