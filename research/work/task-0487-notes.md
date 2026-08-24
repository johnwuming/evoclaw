2026-08-25 05:51:07 [R-309/task-0487] 启动：旧链 paper_trade.py 退役 + 在役链冒烟验证

## 1. 环境与现状（2026-08-25 05:51 GMT+8）
- SSH 连通：noname@10.12.192.174，主机名 nonameopenclawhomebase，UTC 时区（当地 2026-08-24 21:51）
- crontab 共 36 行，已落盘 /tmp/hp-crontab-before.txt（VPS 侧）
- 目标行定位（恰好 2 行匹配 paper_trade|cron_paper_rebalance）：
  - L3: `30 16 * * 1-5 cd /home/noname/quant-evolve && .../python3 scripts/paper_trade.py --action daily >> logs/cron_daily.log 2>&1`
  - L5: `30 16 * * 1-5 cd /home/noname/quant-evolve && .../cron_paper_rebalance.sh >> logs/cron_rebalance.log 2>&1`
