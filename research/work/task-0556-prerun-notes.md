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

## 2. 沙箱模拟 8-29 日更全链 — PASS
- 机制：ROOT=os.path.expanduser(~/quant-evolve)（governance.py L32），沙箱 = HP `/tmp/task0556-sb/quant-evolve/` 完整最小树（governance+projections+event_ledger+events 账本 16 行+results 3 权威文件），运行时 `HOME=/tmp/task0556-sb` 重定向；两 .py 均无硬编码 /home 字面量（grep=0）
- 模拟日更：沙箱 CSV 追加 `2026-08-29,1.01234`（nav）+ `2026-08-29,600519,sell,100,1450.00,13.56`（trade）
- mirror #1（HOME 重定向）：`nav_appended=1, trades_appended=1`，账本 16→18 行，seq17 nav.daily / seq18 trade.fill 落盘；总耗时 **0.064s**（append 0.0053s）；runtime 投影 sha 36a9b304… 更新且含 2026-08-29；五静态投影 sha 与 runbook 基线逐字一致（registry 551b271e/engines 61e88ab/composites c0e08eb/paper a6159e00）
- mirror #2 幂等复跑：`0/0`，0.0027s，sha 不变
- **逐字段断言：10/10 全 True**（8 条 8-14 trade.fill + 新 nav.daily date+nav + 新 trade.fill shares/price/fee=cost）。注：自检脚本曾报 MISMATCH，系计数断言未计入 baseline 事件内嵌的 11 行历史 NAV（runbook 设计：首次实跑 0 nav，历史行在 governance.baseline 内）；按基线偏移解释 = nav 新增 1/1、trades 9 CSV 行 vs 9 事件，一致
- 在役零写入证据：沙箱运行后真实账本（绝对路径）仍 16 行、真实 nav.csv 尾行 2026-08-28/12 行、真实 trades.csv 尾行 8-14，均未动
- 备忘：脚本中 `~` 会随 HOME 重定向展开，「在役」路径校验必须用绝对路径 /home/noname/quant-evolve

## 3. 结论
| 项 | 结果 |
|---|---|
| ① recon 三方对账 | **PASS**（10 checks，2 null 为已知降级） |
| ② watch 监视器 | **PASS**（在位 PID 2217470，until 17:05 覆盖 16:30，0 缺口/error） |
| ③ 账本 verify+计数 | **PASS**（diff=0，五投影 ok，16 事件 ≥15） |
| 沙箱日更全链 | **PASS**（mirror 1/1 落盘、幂等、逐字段 10/10、0.064s、在役零触碰） |

## 4. 16:30 正式实跑终验清单（给主 agent）
1. **watch 自动镜像**：16:30 equity daily cron 落 8-29 NAV 行后 ≤20s，`governance/logs/watch-2026-08-29.log` 应出现 change→mirror 记录；17:05 后 `pgrep -af governance.py watch` 应为空（设计自退出，不留残留）
2. **recon 复跑 = PASS**：mirror_nav_rows_match_csv / mirror_nav_fields_match / mirror_trades_count_match_csv 全 true、nav_fresh=true（last_daily=8-29）
3. **账本**：事件数 16→18（+nav.daily×1；当日有交易则再 +trade.fill×n）；`governance.py verify` diff=0、五投影 headers ok；runtime 投影 sha 随镜像变化
4. **引擎数值**：8-29 官方 NAV 与 results/baseline-paper-nav.csv 尾行一致；paper-state last_daily 更新为 8-29
5. **零越界**：registry active 条目、crontab、engines 文件未变（本轮沙箱已证镜像写路径不触在役，正式跑后抽 sha 复核即可）
6. **BFF**：`:8180/api/v1/portfolios` 仍返回 vC-0 行

—— task-0556 提前执行完成 13:45，全程未触碰在役文件/进程/crontab。
