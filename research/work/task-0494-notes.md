# R-316 / task-0494 过程笔记（A降仓黄金补位满仓 F6）

## 1. 基础事实（承接 R-314/task-0492）
- 数据已核：a13_full_nav.csv（日频 nav 2006-01 起，A=a13_rsraw_e1f10dz）；gold_shadow_nav.csv（月频 net，2013-08 起，含 w_applied/gold_ret/mmf_ret/net 字段）
- monthly_returns.csv：2013-08..2026-07，月频 A 与 gold(net) 已对齐（R-314 五框架同源）
- 成本口径：0.13%×(|Δw_A|+|Δw_gold|) 双腿，月初调仓；引擎内部成本已含于各自 nav
- 现役 A full_metrics：drawdown_control=0（未启用）、dd_thresh=0.2、dd_reduce=0.5 → F6 需假想启用版，从 A 日频 nav 反推逐月仓位（PIT：t 月仓位由 t-1 月末回撤状态决定）
- R-314 基准：A 单独 ann18.93%/mdd-16.95%/Sharpe1.111；F1 等权 13.54%/-8.28%/1.428/Calmar1.636

## 2. dd 规则语义确认（HP 只读源码）
（待查）
