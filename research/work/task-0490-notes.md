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


### 3. 安装执行（管道方式，无 crontab -r）
- 备份：`~/quant-evolve/results/archive/crontab.bak.r312-202608242207`（34 行原文）。
- 安装：`crontab -l > $BAK && (crontab -l; echo L1; echo L2) > /tmp/r312-newcron && crontab /tmp/r312-newcron`。
- 结果：`crontab -l | wc -l` = **36**（34+2）；`grep -c paper_engine_gold` = **2**；
  `diff $BAK <(crontab -l)` = 仅 `34a35,36`（恰好 +2 行，前 34 行逐字不变）。
- 新增两行：
  - `40 7 * * 1-5  cd ~/quant-evolve && ~/miniconda3/envs/quant/bin/python scripts/paper_engine_gold.py --action daily >> logs/paper_gold_daily.log 2>&1`
  - `0 3 * * 0  cd ~/quant-evolve && ~/miniconda3/envs/quant/bin/python scripts/paper_engine_gold.py --action verify >> logs/paper_gold_verify.log 2>&1`

### 4. 部署后验证（全部实际执行）
- 手动 daily ×1：输出 `mark 2026-08-24: px=9.5640 ... [dup: 未重复记账]`，exit=0（当前 8-25 CST 盘前，最新完整日线仍为 8-24，已标记过 → 正确去重）。
- 二次/三次 daily 幂等：marks_n 前后均 =1；state 关键字段 status=active_paper、current_weight=0.0 不变。
- **字段级 diff（python 递归对比第 2、3 次 daily 前后 state）**：唯一变动 `/updated_at` 时间戳；marks/open/nav/weight 逐字节相同 → 幂等性确证。
- verify：`w_state=0.0000 w_signal=0.0000 match=True; nav_chain=True; nav_open=True; marks=True; months_closed=0`，exit=0。
- audit 仍 1 条（init）；daily dup 不写审计（符合 append-only 设计）。

### 5. 9/1 调仓预案（说明，未执行）
- 9/1（周二）15:40 CST cron 首次自动触发 daily：引擎检测 8 月→9 月跨月 → 自动结账 8 月 stub 月 + 按 8-31 月末冻结信号调仓。
- 8-24 px=9.5640 已逼近 SMA200≈9.479（last_signal 显示 7-31 时 px=8.433 < sma200=9.479, w=0）；若 8-31 收盘 px>SMA200 且 vol60 达标 → w 将从 0 升至 vol_target/vol60 对应目标仓位。
- 人工复核命令（9/1 后抽查）：
  - `~/miniconda3/envs/quant/bin/python scripts/paper_engine_gold.py --action verify`（应全 True 且 months_closed=1）
  - `~/miniconda3/envs/quant/bin/python scripts/paper_engine_gold.py --action monthly`（输出月度摘要）
  - `tail -20 ~/quant-evolve/logs/paper_gold_daily.log`

### 6. crontab 全文快照（部署后，36 行）
```cron
# === 模拟实盘定时任务 ===
PATH=/home/noname/miniconda3/envs/quant/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
# task-0347 (R220-#37) 月首交易日口径: 每工作日16:30触发,gate自检月首才调仓 (旧: 30 16 25 * * 见 crontab.bak-r220n37-20260817)
0 20 * * 0 cd /home/noname/quant-evolve && /home/noname/miniconda3/envs/quant/bin/python3 scripts/refresh_data.py >> /home/noname/quant-evolve/logs/cron_refresh.log 2>&1
# === 半月度因子进化（每月1日和15日凌晨2点）===
0 2 1,15 * * cd /home/noname/quant-evolve && /home/noname/miniconda3/envs/quant/bin/python3 scripts/p3_3_evolution_standalone.py --rounds 5 >> /home/noname/quant-evolve/logs/cron_evolution.log 2>&1
# --- baseline paper_engine (task-0251) ---
30 16 * * 1-5  cd ~/quant-evolve && ~/miniconda3/envs/quant/bin/python scripts/paper_engine.py --action daily >> ~/quant-evolve/logs/paper_daily.log 2>&1
0  15 * * 1-5  cd ~/quant-evolve && ~/miniconda3/envs/quant/bin/python scripts/paper_engine.py --action rebalance --check-month-start >> ~/quant-evolve/logs/paper_rebalance.log 2>&1
0  20 * * 0    cd ~/quant-evolve && ~/miniconda3/envs/quant/bin/python scripts/paper_engine.py --action validate >> ~/quant-evolve/logs/paper_validate.log 2>&1
* * * * * COLLECT_VPS_URL=http://82.156.124.186:8055 /home/noname/.openclaw/workspace-quant/scripts/collect-metrics.sh hp >/dev/null 2>&1
30 6 * * 0  cd ~/quant-evolve && ~/miniconda3/envs/quant/bin/python scripts/fetch_valuation_data.py >> ~/quant-evolve/logs/valuation_fetch.log 2>&1
# --- W7 risk module (task-0276) ---
45 16 * * 1-5  cd ~/quant-evolve && ~/miniconda3/envs/quant/bin/python scripts/risk_patrol.py >> ~/quant-evolve/logs/risk_patrol.log 2>&1
0  7  * * 0    cd ~/quant-evolve && ~/miniconda3/envs/quant/bin/python scripts/collect_crowding.py >> ~/quant-evolve/logs/collect_crowding.log 2>&1
# --- evolution pipeline cycle (task-0275 W5) ---
0  9 * * 6  cd ~/quant-evolve && ~/miniconda3/envs/quant/bin/python scripts/evolution_pipeline.py cycle >> ~/quant-evolve/logs/cycle.log 2>&1
# --- W8 notify_hub 统一通知聚合器 (task-0279) ---
10 * * * * cd /home/noname/quant-evolve && /home/noname/miniconda3/envs/quant/bin/python scripts/notify_hub.py >> /home/noname/quant-evolve/logs/notify_hub.log 2>&1
0 6 1 * * cd /home/noname/quant-evolve && /home/noname/miniconda3/envs/quant/bin/python3 scripts/w6_collect_delisted.py >> results/w6-cron-delisted.log 2>&1 # W6-DELISTED-MONTHLY
@reboot /home/noname/quant-evolve/scripts/reboot_autostart.sh >> /home/noname/quant-evolve/logs/reboot_autostart.log 2>&1
*/5 * * * * /home/noname/quant-evolve/scripts/heartbeat_selfheal.sh >> /home/noname/quant-evolve/logs/heartbeat.log 2>&1
10 17 2 * * cd /home/noname/quant-evolve && /home/noname/miniconda3/envs/quant/bin/python3 scripts/a12_monthly_evaluate.sh >> /home/noname/quant-evolve/logs/a12_monthly_eval.log 2>&1
# task-0403 (A10-4) a10月度画像+IC衰减监控: 每月3日09:05 (notify→notifications-queue→auto_sync)
5 9 3 * * cd /home/noname/quant-evolve && bash scripts/a10_monthly_monitor.sh >> /home/noname/quant-evolve/logs/a10-monthly-monitor.log 2>&1
# --- task-0402 qfq 日更（R-244 §4.2 两阶段 baostock 增量，与 16:30 paper / 20:00 周任务错峰）---
0 18 * * 1-5 cd /home/noname/quant-evolve && /home/noname/miniconda3/envs/quant/bin/python3 scripts/cron_qfq_daily.py >> /home/noname/quant-evolve/logs/cron_qfq_daily.log 2>&1
# --- task-0402 周日 init 全量校验 + rebuild merged（R-244 兜底③）---
0 18 * * 0 cd /home/noname/quant-evolve && /home/noname/miniconda3/envs/quant/bin/python3 scripts/collect_qfq_baostock.py --mode init >> /home/noname/quant-evolve/logs/cron_qfq_sunday.log 2>&1; /home/noname/miniconda3/envs/quant/bin/python3 scripts/rebuild_merged.py >> /home/noname/quant-evolve/logs/cron_qfq_sunday.log 2>&1
# --- task-0408 crowding 月度快照（R-250 §4.1a，锁存最近完整月，幂等 append-only）---
35 19 1 * * cd /home/noname/quant-evolve && flock -n /tmp/snapshot_crowding.lock /home/noname/miniconda3/envs/quant/bin/python scripts/snapshot_crowding.py >> /home/noname/quant-evolve/logs/snapshot_crowding.log 2>&1
# --- task-0485 gold shadow append+evaluate（R-306 部署，激活后 evaluate 语义=正式监控，R-307）---
38 9 3 * * cd /home/noname/quant-evolve && /home/noname/miniconda3/envs/quant/bin/python scripts/engines_shadow_nav_gold.py append --out results/engines/gold/shadow_nav.csv --mmf-file results/engines/gold/mmf_monthly_push.csv >> logs/gold_shadow_nav.log 2>&1
40 9 3 * * cd /home/noname/quant-evolve && /home/noname/miniconda3/envs/quant/bin/python scripts/engines_shadow_evaluate_gold.py --mode monthly --engines model/registry/engines.json >> logs/gold_shadow_evaluate.log 2>&1
40 7 * * 1-5  cd ~/quant-evolve && ~/miniconda3/envs/quant/bin/python scripts/paper_engine_gold.py --action daily >> logs/paper_gold_daily.log 2>&1
0 3 * * 0  cd ~/quant-evolve && ~/miniconda3/envs/quant/bin/python scripts/paper_engine_gold.py --action verify >> logs/paper_gold_verify.log 2>&1
```
