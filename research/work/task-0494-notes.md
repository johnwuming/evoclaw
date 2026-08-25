# R-316 / task-0494 过程笔记（A降仓黄金补位满仓 F6）

## 1. 基础事实（承接 R-314/task-0492）
- 数据已核：a13_full_nav.csv（日频 nav 2006-01 起，A=a13_rsraw_e1f10dz）；gold_shadow_nav.csv（月频 net，2013-08 起，含 w_applied/gold_ret/mmf_ret/net 字段）
- monthly_returns.csv：2013-08..2026-07，月频 A 与 gold(net) 已对齐（R-314 五框架同源）
- 成本口径：0.13%×(|Δw_A|+|Δw_gold|) 双腿，月初调仓；引擎内部成本已含于各自 nav
- 现役 A full_metrics：drawdown_control=0（未启用）、dd_thresh=0.2、dd_reduce=0.5 → F6 需假想启用版，从 A 日频 nav 反推逐月仓位（PIT：t 月仓位由 t-1 月末回撤状态决定）
- R-314 基准：A 单独 ann18.93%/mdd-16.95%/Sharpe1.111；F1 等权 13.54%/-8.28%/1.428/Calmar1.636

## 2. dd 规则语义确认（HP 只读源码，2026-08-25 实查）
源文件：`/home/noname/quant-evolve/scripts/backtest_dividend_quality_iter.py` 行 533-540：
```python
if dd_ctl:
    peak_nav = max(peak_nav, cur_nav)          # 运行高水位（受控净值自身）
    cur_dd = cur_nav / peak_nav - 1.0
    if pos_ratio > 0.999 and cur_dd <= -dd_thresh:
        pos_ratio = dd_reduce                  # 单级降仓：直接降到 dd_reduce（如 0.5）
    elif pos_ratio < 0.999 and cur_dd >= -dd_recover:
        pos_ratio = 1.0                        # 回补条件：dd 收窄到 >= -dd_recover(0.05)
```
要点：
- **单级**降仓（非分级）；阈值 dd_thresh=0.20、降仓后仓位 dd_reduce=0.5、回补阈值 dd_recover=0.05（引擎默认）
- 回撤基准 = **受控净值自身的运行高点**（自反馈：降仓改变后续净值路径，dd 恢复更慢）
- 状态在**日频收盘后**更新，次日生效（PIT 安全）
- 现役 a13_rsraw_e1f10dz 的 drawdown_control=0（未启用），全仓运行——与主 agent 前置事实一致

## 2b. 独立交叉验证锚点（HP 已跑 a15_ddc20 = dd_ctl 1 / 0.20 / 0.5 / 0.05）
- a15_ddc20_full_trades.csv 中 DD_CONTROL 事件仅 4 条：
  - 2008-09-01 REDUCE_TO_50%；2009-08-05 RESTORE_FULL
  - **2015-06-29 REDUCE_TO_50%；2020-07-08 RESTORE_FULL**（降仓状态持续约 5 年！）
- a15_ddc20_full_metrics：ann 19.92% / mdd -27.16% / Sharpe 1.3735（2006-2026 全期，含控制）
- 我的日频状态机模拟（基于 a13 日频 nav）应复现 ~2015-06 触发、~2020-07 回补（a13 与 a15 净值相近，日期允许小偏差）
- 含义：现役默认参数下 F6 并非零事件——2015-07..2020-06 期间 A 引擎半仓，闲置 50% 由 gold 补位
