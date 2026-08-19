# task-0403 notes：A10 月度画像/IC 衰减监控接入 cron

- 开始时间：2026-08-20 00:12
- 目标：HP crontab 新增 a10 月度行 + 通知接入 + 手动触发验证

## 步骤进度
1. [x] 读 a10 两个脚本，确认数据依赖与定时依据
2. [x] 设计 cron 行：`5 9 3 * *`（每月3日 09:05，依据见步骤1）
3. [x] 通知 wrapper：`scripts/a10_monthly_monitor.sh`（md5 8310c1d7，bash -n 通过，已部署 HP）
4. [x] crontab 快照 + 追加安装 + 验证
5. [x] 手动触发全链路验证（RC=0）
6. [x] VPS 侧通知队列验证（已收到 hp-notify 条目）

## 安装记录（2026-08-20 01:4x 北京时间）

**前快照**：HP `/tmp/crontab-before-task0403-20260819-1729.txt`（25 行）；安装前 grep 确认无 a10/qfq/0402 行（无竞态冲突，当时 0402 尚未装行）

**追加安装**（未动既有行）：
```
# task-0403 (A10-4) a10月度画像+IC衰减监控: 每月3日09:05 (notify→notifications-queue→auto_sync)
5 9 3 * * cd /home/noname/quant-evolve && bash scripts/a10_monthly_monitor.sh >> /home/noname/quant-evolve/logs/a10-monthly-monitor.log 2>&1
```
安装后 `crontab -l | grep -n a10` → 26/27 行在位，总 27 行。与既有 16:30 调仓、1/15日 02:00 evolution、2日 17:10 a12、周六 09:00 cycle 全部错峰。

**回滚命令**（推荐定向移除，不受 0402 后续装行影响）：
```
sshpass -p "$QUANT_SSH_PASSWORD" ssh noname@10.12.192.174 '(crontab -l | grep -v "a10_monthly_monitor.sh" | grep -v "task-0403 (A10-4)") | crontab -'
# 可选：移除 wrapper：rm ~/quant-evolve/scripts/a10_monthly_monitor.sh
# 全量回退（会连带移除快照后新增的他人行，慎用）：crontab /tmp/crontab-before-task0403-20260819-1729.txt
```

## 手动触发验证输出（2026-08-19 17:42 UTC）
```
[2026-08-19 17:42:41] === a10 月度监控开始 ===
[up-to-date] inputs unchanged (panel_md5=c0a1db23...), outputs intact, as_of=2026-07, skip recompute   ← 幂等确认
[ic-decay-monitor] as_of=2026-07 factors=17 alerts=0
（17 因子全 OK k=1.0，无 ALERT/WARN）
[notify:info] ✅ a10 月度监控完成：17 因子 0 告警（as_of 2026-07）
RC=0
```

## 通知链路验证
1. HP 队列 tail：`{"ts":"2026-08-19 17:42:42","level":"info","type":"a10_ic_decay","title":"✅ a10 月度监控完成：17 因子 0 告警…","_dedupe_key":"a10|2026-07"}` ✓
2. VPS 手动跑 `auto_sync_notify.py --job-name task-0403-verify`（幂等，同 cron */30 逻辑）：
   `.task-notifications.jsonl` 出现 `{"taskId":"hp-notify","type":"info","message":"✅ a10 月度监控完成：17 因子 0 告警…"}` ✓ 告警可达任务中心队列
3. 附带同步 6 个结果文件到 VPS shared/results/04-投资研究/

## 遗留/说明
- IC 底表 `factor_ic_monthly.csv` 无 cron 更新（a2_ic_data.py/factor_ic_analysis.py 手动跑）；a10 月度行对 md5 变化自动重算，面板月中刷新会被下次月度跑拾取；若未来给 a2_ic_data 装 cron，建议 a10 时间在其后
- wrapper 防重：同 as_of 同 dedupe key 只通知一次；失败发 red 通知（dedupe 按天）
- 未改任何既有 cron 行/脚本本体；未杀任何进程

## 步骤2/3 设计（2026-08-20 00:3x）

**通知链路实证**：VPS `crontab -l` 有 `*/30 auto_sync_notify.py`；该脚本 `forward_hp_notifications()` 把 HP `results/notifications-queue.jsonl` 水位后的新行 → VPS `/root/.openclaw/workspace/scripts/.task-notifications.jsonl`（幂等）。a12_shadow_eval.notify() 直接 append 队列（schema: ts/level/type/title/body/source/severity/_dedupe_key）→ 同样方式接入。

**wrapper 设计**（新增 `scripts/a10_monthly_monitor.sh`，不动 a10 脚本本体）：
- flock 防并发；依次跑 profile_update（幂等）+ ic_decay_monitor（原子写）
- 任一非0 exit → red 通知；否则 n_alerts>0 → warn 通知、=0 → info 通知
- dedupe key `a10|{as_of_ym}`，队列尾部同 key 已存在则跳过（防同月重复通知）
- cron 行：`5 9 3 * *  cd /home/noname/quant-evolve && bash scripts/a10_monthly_monitor.sh >> logs/a10-monthly-monitor.log 2>&1`

## 步骤1 结论：数据依赖与定时依据（2026-08-20 00:2x）

**a10 两脚本共同输入**：`results/factor_ic_monthly.csv`（月频 IC 面板）+ `results/factor_catalog_v3.json`。

**IC 底表更新机制（关键发现）**：
- 全仓 grep：写 `factor_ic_monthly.csv` 的只有 `a2_ic_data.py`（手动 nohup 运行，**不在 cron 中**）
- 每月 1/15 的 `p3_3_evolution_standalone.py` evolution **不产出**该面板；`evolution_pipeline.py` 只是消费方（load_ic_monthly 门禁用）
- `a13_score.py` 产出的是独立文件 `a13_supp_ic_monthly.csv`（08-19 更新），不直接改主面板
- 面板最近 mtime：2026-08-16 14:14（手动刷新，含 as_of 2026-07 行）

**结论**：IC 底表无固定 cron 更新点 → 不满足"依赖 1/15 evolution 产出→改 16 日跑"的条件。a10 脚本自身 md 报告（task-0370 交付、用户已阅）建议每月 3 日上午。采纳：**每月 3 日 09:05**（任务建议 09:0x/10:0x 白天时段），理由：
1. 避开月首交易日 16:30 调仓窗口与 1/15 日 02:00 evolution
2. 在 a12 月度评估（2 日 17:10）之后、当月内尽早出告警
3. a10_monthly_profile_update 幂等（md5 变才重算），即使面板延迟刷新，月度跑无害；面板月中刷新会被下月 3 日自动拾取（md5 变化触发重算）
4. notify_hub 每小时 :10 聚合，09:05 跑完 → 09:10 或 10:10 取走通知

**脚本行为确认**：
- `a10_monthly_profile_update.py`：md5 未变+产物完好 → skip exit 0；`--force` 强制重算
- `a10_ic_decay_monitor.py`：无 state、每次重算但原子写幂等，无 --force 需求；exit 0（含告警时）/2（数据错误）
- 两者 exit code 设计适合 cron 链式 `&&`

