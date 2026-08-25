# task-0495 过程笔记（F7 组合口径：等权50/50打底 + A降仓黄金补位）

## 基础件核验

- [2026-08-25 23:53] md5 校验：a13_full_nav.csv=358ce8192880d615d620d2297387601d、gold_shadow_nav.csv=3654c3e80103fc313e24c9eb641de4e2，与 task-0492/data/md5.txt 逐字一致 → 基础数据未漂移，可用。
- monthly_returns.csv（月频 A/gold 收益，2013-08 起）、a13_full_nav.csv（日频 nav 2006 起，用于 dd 状态机）均就位。

## F7 定义（任务书给定）
- w_A^base=0.5, w_gold^base=0.5，月度再平衡回 0.5/0.5，容忍带 ±5pp（同 F1）
- dd 状态机 REDUCE 态：F7a → w_A=0.25, w_gold=0.75；F7b → w_A=0.25, w_gold=0.625, cash=0.125
- RESTORE 后回 0.5/0.5
- PIT：状态机用 t-1 及更早日频数据判定 t 月仓位；成本 0.13%×|Δw| 双腿同口径

## 执行进度
