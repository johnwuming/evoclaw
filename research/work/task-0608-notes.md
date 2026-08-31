# task-0608 过程笔记 — gold paper audit 追加 NaN 更正事件

## 时间线
- 2026-09-01 07:16 开始。任务：09-01 gold 引擎记录 9 月信号后，向 HP gold paper 账本 audit 追加「NaN 更正事件」（08-31 用户预批方案二）。只追加，不改写。

## 步骤记录

### [07:16] 步骤1：cron 核验（只读）
- `paper_engine_gold.py --action daily`：`40 7 * * 1-5`（工作日 07:40）
- shadow_nav append：38 9 3 * *；shadow_evaluate：40 9 3 * *（每月 3 号）
- 09-01 周二触发点 07:40，当前 07:16 → 距触发 ~24 分钟 → 进入轮询等待分支（间隔 ≥5 分钟）

### [07:18] 账本定位 + schema
- 账本：`~/quant-evolve/results/engines/gold/paper_state.json`（1980B，内嵌 audit list，当前 N=1）
- audit[0] schema：ts / event / w_cur / signal_month_end / px_basis / basis_date / stub_month / note
- 触发表达式核验：last_signal.month_end=2026-07-31，open.month=2026-08 → 2026-09 期未落盘
- cron 07:40 触发（~22 分钟后）→ 轮询等待分支（间隔 ≥5 分钟）

### [07:20] daily 写入形态（代码只读，未改动）
- `close_and_roll()`（paper_engine_gold.py L156-199）：跨月时结账上月 → audit append `{event:"month_close+rebalance", month_closed, net, w_new, mmf_est, stub}` → `open.month` 推进到 2026-09
- 触发表达式落实为：`open.month=="2026-09"` 且 `last_signal.month_end=="2026-08-31"`（NaN 路径：sma200=NaN→w=0）
- 开始轮询：等待 07:40 cron 触发后核验
