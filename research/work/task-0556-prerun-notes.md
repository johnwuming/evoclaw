# task-0556 提前执行笔记（2026-08-29 13:36 启动）

目标：Phase C 治理层即时对账核对（在役只读）+ 沙箱模拟 8-29 日更全链。三项结论 + 16:30 终验清单。
纪律：在役零改动；写入仅 /tmp/task0556-sb/。

## 0. 工具入口（runbook L1-45 摘录）
- HP: sshpass+ssh noname@10.12.192.174；python=/home/noname/miniconda3/envs/quant/bin/python；目录 ~/quant-evolve
- 治理模块: portfolio_v1/governance/governance.py（子命令含 switch/mirror/watch/recon/checkpoint/breaker）
- 账本: portfolio_v1/portfolio/events/（iteration-ledger-2026-08.jsonl，切换后基线 15 事件）
- watch 日志: portfolio_v1/governance/logs/watch-2026-08-29.log（17:05 设计自退出）
- 权威文件实际路径（governance.py L44-50）: ROOT/results/baseline-paper-nav.csv、ROOT/results/baseline-paper-trades.csv、ROOT/results/paper-state.json（ROOT=~/quant-evolve）

## 1. 即时核对（在役只读）— 全部完成
### ① recon 复跑（13:37）→ **PASS**
```json
{"result": "PASS", "checks": {"holdings_set_equal": true, "nav_present_for_last_row": true, "cash_band_0.5pct_nav": null, "equity_registry_entry_active": true, "gold_engine_active_paper": true, "weight_solution_sums_1": null, "mirror_nav_rows_match_csv": true, "mirror_nav_fields_match": true, "mirror_trades_count_match_csv": true, "nav_fresh": true}}
```
两个 null 与 runbook §6 已知如实降级一致，无新增异常。
### ② watch 监视器 → **在位（未退出）**
- PID 2217470：`governance.py watch --until 2026-08-29 17:05:00 --interval 20`（17:05 为设计自退出时点，将覆盖 16:30 实跑）
- 日志 watch-2026-08-29.log：02:51:41+00:00（=北京 10:51）start 后无变更记录（权威 CSV 自切换后无新写入，符合预期）
- gap/缺口/error 计数 = **0**
### ③ 账本 verify + 计数 → **PASS**
- `governance.py verify`：registry_entry_a13/gold_state/vC-0 = identical，五投影 headers 全 ok，paper_state numeric diff=[]，result=diff=0
- 事件计数 **16 ≥ 15** ✅：version.created 1 + weight.solved 1（Phase B）+ governance.baseline 1 + calibration.recorded 1 + paper.pointer.switched 1（切换）+ trade.fill 8（镜像）+ reconciliation.passed 2（原 1 + 本次复跑 1）+ checkpoint.created 1
- 最后事件 = 本次 recon 落的 reconciliation.passed @ 13:37:16 北京时间（正常审计写入）
