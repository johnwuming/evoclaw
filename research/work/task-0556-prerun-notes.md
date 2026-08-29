# task-0556 提前执行笔记（2026-08-29 13:36 启动）

目标：Phase C 治理层即时对账核对（在役只读）+ 沙箱模拟 8-29 日更全链。三项结论 + 16:30 终验清单。
纪律：在役零改动；写入仅 /tmp/task0556-sb/。

## 0. 工具入口（runbook L1-45 摘录）
- HP: sshpass+ssh noname@10.12.192.174；python=/home/noname/miniconda3/envs/quant/bin/python；目录 ~/quant-evolve
- 治理模块: portfolio_v1/governance/governance.py（子命令含 switch/mirror/watch/recon/checkpoint/breaker）
- 账本: portfolio_v1/portfolio/events/（iteration-ledger-2026-08.jsonl，切换后基线 15 事件）
- watch 日志: portfolio_v1/governance/logs/watch-2026-08-29.log（17:05 设计自退出）
- 权威文件: results/paper-nav.csv、results/trades.csv（如有）、results/paper-state.json
