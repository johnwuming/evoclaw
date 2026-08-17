# task-0347 notes (R220-#37 paper调仓口径对齐)
开始: 2026-08-17 20:17 GMT+8

## 1. 盘点

- crontab 现状（全量已核）：`30 16 25 * *` 固定每月25日16:30 直接调 paper_trade.py --action rebalance → cron_rebalance.log（该文件不存在=自该行加入后未触发过，8/25未到）
- cron_paper_rebalance.sh 存在(434B, 8/9)但未被 crontab 引用；头部注释还是"月末最后工作日"旧口径
- paper_trade.py (24.9KB)：action_rebalance 无任何日期/月份自检（"不强制检查月份，允许手动触发"）；REBALANCE_MONTHS=[3,6,9,12] 仅用于算 next_rebalance 显示，不拦截
- 回测口径确认：backtest_dividend_quality.py L193 `rebalance_dates = df_dates.groupby(df_dates.dt.to_period("M")).min()` = 每月首个交易日（来源=K线日期集）
- baseline paper_engine.py 有 --check-month-start 模式（已暂停 #PAUSED-20260816-seedB）：取本地K线最新交易日d，比d与当月日历首日——**缺陷**：数据周日批量刷新，月首交易日当天本地无当月K线 → d 停在上月末 → 判断永远 skip（多数月份永不触发）。日志证据：8/13、8/14 15:00 均显示"今日 2026-08-07"（数据滞后数日）
- akshare 1.18.83 可用（quant env）
- 2026-08 月首交易日 = 08-03（官方口径，baseline 日志佐证）

## 2. 方案
不碰 paper_trade.py / paper_engine.py。三件套：
1. 新增 scripts/rebalance_gate.py：判断"今天是否当月首个交易日"。日历优先级：官方日历缓存 data/trade_calendar.csv（akshare tool_trade_date_hist_sina 预生成）→ 本地K线日历（与回测同源）→ akshare 在线补缓存 → 兜底当月首个工作日。exit 0=执行调仓 / 3=跳过。支持 --date 供推演验证。
2. 改写 cron_paper_rebalance.sh（备份 *.bak-r220n37-20260817）：先过 gate，PASS 才跑 paper_trade.py --action rebalance + rsync 同步 VPS。
3. crontab：`30 16 25 * *` → `30 16 * * 1-5`（每工作日16:30触发，gate 自检月首才执行）。16:30 与 daily 任务同时点保持一致（收盘后）。
其他 cron 行一律不动；已暂停 baseline 行不动；不杀任何进程。
