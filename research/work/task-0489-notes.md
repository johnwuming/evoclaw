# task-0489 / R-311 HP 时区统一专项评估 — 过程笔记（原始证据）

> 只读调研，边查边写。每条证据附命令+输出摘录。采集时间：2026-08-25 07:15–07:30 GMT+8。

## E1 系统事实

### E1.1 timedatectl（HP）
```
Local time: Mon 2026-08-24 23:15:47 UTC
Time zone: Etc/UTC (UTC, +0000)
System clock synchronized: yes / NTP service: active / RTC in local TZ: no
```
shell TZ 变量为空。**HP 系统时区 = Etc/UTC。**

### E1.2 cron 守护进程
`systemctl status cron` + `dpkg -l | grep cron`：
```
Active: active (running) since 2026-08-18 03:55:10 UTC
ii cron 3.0pl1-200ubuntu1 amd64
```
Ubuntu 官方源 **Debian cron 3.0pl1**（vixie-cron 血统），非 cronie。

### E1.3 CRON_TZ 支持性实证（关键）
`zcat /usr/share/man/man5/crontab.5.gz` LIMITATIONS 节：
> "The cron daemon runs with a defined timezone. It currently does not support per-user timezones. ... Even if a user specifies the TZ environment variable in his crontab this will affect only the commands executed in the crontab, not the execution of the crontab tasks themselves."
`man8/cron.8`：
> "The daemon will use, if present, the definition from /etc/localtime for the timezone. ... cron will only handle tasks in a single timezone."
**结论：该 cron 版本不支持 CRON_TZ=，路径 B 排除（换 cronie 才可用，不建议在量化主机换守护进程包）。**

### E1.4 系统级 cron/timers 无量化任务
- root：`no crontab for root`
- /etc/cron.d/：仅 `e2scrub_all`（系统维护）
- systemd timers 含 quant/evolve/paper 关键词：0 条

### E1.5 在跑量化进程（勿动）
```
5903  7-13:34:37 python3 /home/noname/quant-evolve/scripts/hp_api_server.py
(每分钟的 collect-metrics.sh 瞬时进程)
```

## E2 noname crontab 全量盘点

- 落盘：/tmp/hp-crontab-noname.txt（36 行原文）；`crontab -l | grep -cvE "^#|^$"` = **24 = 1 行 PATH + 23 条任务（22 条表达式 + 1 条 @reboot）**，本地数一致。
- 逐条换算（系统 UTC，北京 = UTC+8）见正式报告 §3 表格（内容同源本节，报告为准）。
- 关键换算示例：
  - `0 2 1,15 * *` 半月因子进化 = 北京 **10:00 盘中**（原心智"凌晨2点"被打破）
  - `30 16 * * 1-5` paper daily = 北京**次日 00:30**（心智"收盘后16:30"）
  - `0 15 * * 1-5` rebalance = 北京 23:00
  - `45 16 * * 1-5` risk_patrol = 北京次日 00:45
  - `0 18 * * 1-5` qfq 日更 = 北京次日 02:00
  - `40 7 * * 1-5` paper_gold daily = 北京 **15:40（收盘后）** ← 该条是按北京实际效果倒推写的 UTC 表达式，与其余条目心智相反 → **crontab 内部心智已分裂**
  - `5 9 3 * *` a10 注释写"每月3日09:05"= UTC 心智；北京实际 17:05
  - 每分钟/每5分/@reboot/月度/周末任务：时区无关或无实质影响

## E3 脚本时区依赖审计（crontab 涉及的 20 个脚本）

方法：`grep -c` 聚合每文件 `utcnow` / `datetime.now` / `Asia/Shanghai|ZoneInfo|tz_localize|tz_convert` / `TZ|timezone|+08:00`。

结果要点：
- **utcnow=0（全部脚本）**；**selftz=0（全部脚本无 ZoneInfo/tz_localize/Asia/Shanghai）**
- 裸 `datetime.now()`（=系统本地 UTC）：refresh_data(4)、p3_3_evolution(8)、paper_engine(11)、fetch_valuation(2)、risk_patrol(4)、collect_crowding(2)、evolution_pipeline(1)、notify_hub(3)、w6_delisted(2)、a10(1)、snapshot_crowding(1)、gold_eval(1)、paper_gold(1)；纯数据脚本（cron_qfq_daily/collect_qfq/rebuild_merged/engines_shadow_nav_gold）0 处；.sh 仅日志 `date '+%F %T'`
- 抽样核实 now() 用途：
  - paper_engine.py:124 `expires_at_ts > datetime.now().timestamp()` → **绝对 epoch，TZ 无关**
  - 其余多为日志时间戳 strftime（显示层，切换后一次性跳 8h，无逻辑破坏）
  - refresh_data.py:87 `today=datetime.now().strftime("%Y%m%d")` 仅作增量 end_date 上界；UTC 下周日晚跑时 today=周日(UTC)而北京已周一，切换后反而与交易日历更对齐
  - notify_hub.py:213 now() 用于去重窗口/展示，切换时一次性平移，无破坏
  - **engines_shadow_evaluate_gold.py:148 `"ts": datetime.now().strftime("...+08:00")` 把 UTC 时间错标 +08:00（现状 bug 级证据；切换后自动变正确）**
  - paper_engine_gold.py:54 `datetime.now().astimezone().isoformat()` → 随系统时区自洽，任一时区下正确
- 结论：**无任何脚本自处理时区（改系统 TZ 不会二次偏移）**；所有 naive now() 在 TZ 切换后统一 +8h，用途均安全（日志/上界/去重/绝对时间戳）。

## E4 通知/上报链路（Path A 连带影响面）
- collect-metrics.sh 每分钟上报 VPS:8055（心跳/metrics）；若其时间字段为 `date +%s`（epoch）则 TZ 无关，若为格式化时间需 VPS 侧核对——实施前列为检查项（本任务未验证其字段格式）。
- hp_api_server.py 已跑 7 天，glibc 会在 /etc/localtime 变更后自动重读（进程无需重启即感知新 TZ）；其对外时间戳语义从 UTC 变北京，下游若有假设需核查。

## E5 结论草案
- B（CRON_TZ）实证不可用；C（UTC 写死+注释）是现状且心智已分裂（E2/E3 证据）；推荐 A（系统时区→Asia/Shanghai + 同批按北京心智重写表达式 + restart cron），脚本层已审计安全。
- 不可自动项：timedatectl、restart cron、crontab 写入均属用户批准范围，本任务仅出草案。
