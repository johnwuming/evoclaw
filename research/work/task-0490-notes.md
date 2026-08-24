# task-0490 / R-312 过程笔记（黄金 paper 引擎逐日 cron 部署）

目标：HP 主机 crontab 新增 2 行（gold daily + 周度 verify），2026-09-01 首调仓前就位。

## 时间线 / 核验点（边查边写）

### 1. 现状核验（HP：noname@10.12.192.174，UTC 2026-08-24 22:03 = CST 08-25 06:03）
- SSH 连通 OK；`crontab -l | wc -l` = **34 行**（与 R-309 交接一致）。
- 已落盘本地快照 `/tmp/r312-crontab-before.txt`（34 行）。
- 冲突检查（hour=3/7/16 全量枚举）：
  - `0 7 * * 0` collect_crowding（仅周日 07:00 UTC）
  - `30 16 * * 1-5` paper_engine.py daily；`45 16 * * 1-5` risk_patrol
  - **hour=3 无任何行；工作日 07:xx 无任何行** → 计划时间窗全空，无冲突。
- 脚本/目录：`scripts/paper_engine_gold.py` 存在（16474B, Aug 24 16:55）；`logs/`、`results/archive/` 均在。
- state 现状：`results/engines/gold/paper_state.json` → status=active_paper, current_weight=0.0, marks_n=1（2026-08-24 px=9.5640）。

### 2. cron 计划设计（理由）
| 行 | 计划 | 理由 |
|---|---|---|
| gold daily | `40 7 * * 1-5` (UTC) | = CST 15:40 周一~五，A股 15:00 收盘后 40 分钟，腾讯 sh518880 fqkline 日线已可得；避开在役 paper_engine 16:30 UTC 时段；工作日 07:xx UTC 现有 crontab 全空，零冲突 |
| gold verify | `0 3 * * 0` (UTC) | = 周日 11:00 CST，低负载时段；与周日 07:00 UTC collect_crowding 错开 4 小时；hour=3 现有 crontab 全空；verify 失败仅留日志不配自动通知（按任务书） |
- 命令体（与任务书一致）：`cd ~/quant-evolve && ~/miniconda3/envs/quant/bin/python scripts/paper_engine_gold.py --action daily >> logs/paper_gold_daily.log 2>&1`；verify 同构 → `logs/paper_gold_verify.log`。

### 3. 安装执行

