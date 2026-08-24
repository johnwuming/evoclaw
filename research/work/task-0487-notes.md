2026-08-25 05:51:07 [R-309/task-0487] 启动：旧链 paper_trade.py 退役 + 在役链冒烟验证

## 1. 环境与现状（2026-08-25 05:51 GMT+8）
- SSH 连通：noname@10.12.192.174，主机名 nonameopenclawhomebase，UTC 时区（当地 2026-08-24 21:51）
- crontab 共 36 行，已落盘 /tmp/hp-crontab-before.txt（VPS 侧）
- 目标行定位（恰好 2 行匹配 paper_trade|cron_paper_rebalance）：
  - L3: `30 16 * * 1-5 cd /home/noname/quant-evolve && .../python3 scripts/paper_trade.py --action daily >> logs/cron_daily.log 2>&1`
  - L5: `30 16 * * 1-5 cd /home/noname/quant-evolve && .../cron_paper_rebalance.sh >> logs/cron_rebalance.log 2>&1`

## 2. crontab 退役（步骤1）✅
- 备份：HP `~/quant-evolve/results/archive/crontab.bak.r309-202608242151`（5103B, 36 行）
- 移除方式：`crontab -l | grep -v "scripts/paper_trade.py --action daily" | grep -v "scripts/cron_paper_rebalance.sh" | crontab -`（未用 crontab -r）
- 验证：写回后 34 行；`grep -c "paper_trade\|cron_paper_rebalance"` = 0
- diff 备份 vs 现状：仅 `3d2`（paper_trade daily 行）与 `5d3`（cron_paper_rebalance.sh 行）两个删除，无任何其他行变化 → 恰好少 2 行 ✅
