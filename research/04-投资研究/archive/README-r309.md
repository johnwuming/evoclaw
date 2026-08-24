# R-309 / task-0487 旧链 paper_trade.py 退役归档（2026-08-25）

## 归档内容
- paper-nav.csv.r309-retired —— 旧链 paper_trade.py 产生的 NAV 序列（329B，末次写于 2026-08-24 17:40 UTC，R-308 行日期纠正）
- paper-summary.json.r309-retired —— 旧链摘要（1307B，同上）
- crontab.bak.r309-202608242151 —— crontab 退役前完整备份（36 行）

## 退役原因（详见 R-308 / task-0486 报告）
旧链 paper_trade.py 存在三重问题：
1. 价格查找静默失败导致 NAV 长期冻结；
2. 与在役引擎共享 paper-state.json，整字典覆盖写有状态互踩风险；
3. 月首 rebalance cron 按 v5h 选股，会在 2026-09-01 覆盖在役 a13 引擎持仓。

R-308（task-0486）已冻结旧链 rebalance 并纠正数据口径；R-309（task-0487）经用户 2026-08-25 05:46 批准后整体退役：
移除两行 crontab（paper_trade daily + cron_paper_rebalance.sh），产物移入本目录留档。

## 在役链
唯一模拟实盘链路为 scripts/paper_engine.py（baseline-paper-* 产物，model_version=a13_rsraw_e1f10dz）。
报告：VPS shared/results/05-量化投资/R-308-模拟实盘超期修复与数据完整性核查.md 与 R-309-模拟实盘单引擎收敛实施.md
