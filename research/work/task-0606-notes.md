# task-0606 过程笔记

## 已核实事实（HP 只读，2026-08-31 晚）
- 引擎代码 `~/quant-evolve/scripts/paper_engine_gold.py`（16474B）compute_signals：
  ```python
  m = s.resample("ME").last().dropna()               # px 用的是月内最后交易日收盘（asof 正确）
  sma200 = s.rolling(200).mean().reindex(m.index)     # BUG：按日历月末精确匹配 → 逢非交易日 = NaN
  vol60  = ...rolling(60).std()...reindex(m.index)    # 同样问题
  dir200 = (m.values > sma200.values)                 # NaN 比较 = False → 0
  vt10 = (0.10/vol60).clip(0,1);  w_sig = (dir200*vt10).fillna(0.0)   # NaN → w=0
  ```
- fetch_gold_daily：腾讯 fqkline sh518880 qfq 日频，FETCH_START=2013-01-01；本次复算 daily_rows=3183，2013-07-29 ~ 2026-08-28
- COST=0.0013×|Δw|；SMA_N=200；VOL_N=60；VOL_TARGET=0.10
- crontab（HP）：paper_engine daily 07:40 工作日；verify 周日 03:00；shadow append 每月 3 日 09:38；evaluate 3 日 09:40

## 复算结果（task-0606-hp-signals.csv / -summary.txt，脚本 task-0606-hp-recompute.py）
- 月末总数 158（2013-07-31 ~ 2026-08-31）
- **纯日历 NaN（is_cal_nan：sma_eng=NaN 且 asof 有值）= 51 个月**
- 热身 NaN（asof 也无值，2013-07~2014-04）= 10 个月
- **w 引擎值 ≠ asof 真值的月末 = 33 个**（全部落在 51 个日历 NaN 月内；其余 18 个 NaN 月碰巧两侧都=0）
- 现时点 2026-08-31：px=9.4750，sma_asof=9.4941 → w_asof=0，w_eng=0（结果一致、机制坏）
- 51 个日历 NaN 月清单见 task-0606-hp-summary.txt CAL_NAN_MONTHS
- 33 个分歧月末清单见 W_DISAGREE_MONTHS（注意：这是"月末"日期；受污染的是下一个月的账本行）

## 机制理解（用于账本行映射）
- 账本行 month=M 的 w_applied = 月末 M-1 的 w_sig；行内成本 = 0.0013×|w_applied(M)-w_applied(M-1)|
- 已抽验：2026-06 行 gross=mmf(w=0)、net 差 0.000279=0.0013×0.2143 → May 行 w=0.2143 来自 04-30 交易日信号，自洽

## 待办
- [x] 对账：w_eng(prev_me) vs shadow_nav w_applied → 157/157 全一致（<5e-5 舍入），账本=缺陷语义确认
- [x] 污染月名单：33 个账本行（18 错过涨幅/15 侥幸避跌，逐月毛差合计 +21.66pp）
- [x] 反事实净值：终点 2.6046→3.1707（+21.7%）、ann 7.59%→9.22%（+1.63pp）、MDD 5.90%→8.09%（+2.19pp，2017-06→2017-10）
- [x] 展示口径二阶影响（静态58/42无成本近似，复现官方MDD残差0.01pp）：终点 5.80→6.32（+9.0%）、ann +0.76pp、MDD 9.66% 持平（2015-08 A 腿主导）
- [x] 上游：R-380 42%金腿=nav_curves gold 列=shadow_nav nav → 受污染；evaluate 读 shadow_nav 算考核指标 → 受污染；R-372/R-386 用 gold_ret 裸B&H → 不受影响（复核成立）
- [x] R-389 L50 机制归因需更正：2026-06 行 w=0 是 05-31（周日）NaN 强制归零，真实 w_true=0.317（约-3.4%）——「接住组合」是缺陷侥幸非信号判断
- [x] 报告编号：R-390 被并行任务占用 → 取 R-391（报告头已注明）；check_rid_dup PASS 零碰撞
- [x] 报告已写：R-391-gold引擎月末NaN缺陷审计与修复方案.md（22313B）；推荐方案 A2（修复+全历史重算重发布），标注实施需用户批准
- 2026 年污染月：2026-02（w_true 0.369，少亏0.26pp）/2026-03（0.264，避跌2.98pp）/2026-06（0.317，避跌3.44pp）；2025-09 错过 +11.40pp 为最大单月损失
