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

### [北京 07:58] 触发点核验结论：未到触发点，显式终态退出
- **未落盘证据**：paper_state.json 仍 open.month=2026-08 / last_signal=2026-07-31 / audit_len=1（07:42 与 07:58 两次核验一致）
- **时区事实**：HP Timezone=Etc/UTC（timedatectl）；北京当前 09-01 07:58 = HP 08-31 23:58 UTC
- **cron 计划时间**：`paper_engine_gold.py --action daily` = `40 7 * * 1-5`，按 HP 本地(UTC)执行 → **北京时间每个工作日 15:40**
- **上次执行**：log 与 paper_state mtime 均 2026-08-31 07:40:03 UTC（周一，北京 15:40），log 最后 mark=2026-08-28（周末无 bar，正常）
- **重查时机**：北京 09-01 15:40 触发，**建议 15:45 后重查** paper_state.json 是否 open.month=2026-09 且 last_signal=2026-08-31；确认后再执行 audit 追加（备份→追加→N→N+1 校验→证据回传）
- 备注：任务书叙述"08-31 为周日"与实际历法不符（2026-08-31 实为周一，HP date 输出 Mon），不影响 NaN 缺陷机制（8 月末 bar=08-28 周五，sma200 reindex 缺口仍存在）；09-01 周二 daily 触发时按 NaN 路径记录 9 月信号的预期不变
- 本阶段零写入：未改动账本/代码/registry/crontab，无备份需求

### 终态
task-0608 状态回退 pending，等待北京 15:45 后重查窗口再由主 agent 重新派发。

## 阶段二（并入 task-0612 派发，2026-09-01 16:2x 北京）
- 前置事实（R-393 已证，直接采用）：更正事件 asof=08-31 收盘 9.135（9.475=08-28 收盘禁用）；两口径 9 月 w 均=0。
- 方案二四点：①NaN 默认 w=0 非真实判定 ②人工核验真实信号一致 ③指向 task-0606/A2 修复 ④「该记录不得作为信号有效性证据使用」。
- 执行顺序：HP 前置自检（open.month=2026-09 且 last_signal=2026-08-31）→ 备份 paper_state → 追加 audit 事件（9.135）→ 校验长度+1。
