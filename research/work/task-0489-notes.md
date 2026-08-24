# task-0489 (R-311) HP 时区统一 Asia/Shanghai 专项评估 — 过程笔记

- 开始：2026-08-25 06:35 CST；结束：2026-08-25（同日）
- 纪律：HP 全程只读（/tmp 除外）；本会话对 HP 零写入。

## 0. 初始状态记录（零改动基线）

- `crontab -l` md5（BEFORE）：`3983e350b74051d45860502954270ab1`，36 行（23 条任务+13 注释/PATH/空行）
- 系统：`timedatectl` → Time zone: Etc/UTC，NTP active/synchronized（chrony）；`/etc/timezone` 为空文件
- cron：Debian `cron 3.0pl1-200ubuntu1`（vixie 系），进程 `/usr/sbin/cron -f -P`（root，Aug18 起）
- root crontab：空；/etc/cron.d 仅 e2scrub_all；/etc/cron.daily|weekly 为系统维护
- systemd timers：全部系统维护类，无量化 timer；running 服务：openclaw.service、docker、chrony 等
- 脚本 mtime 审计快照（+0000）：
  - paper_engine.py 2026-08-24 22:27:57（R-308/488 备用行情源版）
  - paper_engine_gold.py 2026-08-24 16:55:31（R-312 部署版）
  - cron_qfq_daily.py 2026-08-19 17:42、refresh_data.py 2026-08-09 17:24、risk_patrol.py 2026-08-18 08:39、notify_hub.py 2026-08-15 08:42

## 1. crontab 全量映射（36 行）

完整表已落 `/tmp/r311_crontab_map.md`（VPS）。要点：

- **核心错位 4 行（交易日链）**：
  - paper daily `30 16 * * 1-5`：意图 CST 16:30（注释+R-248 均为 CST 口径），实际次日 00:30 CST → 滞后 8.5h（R-308 根因①）
  - qfq 日更 `0 18 * * 1-5`：意图 18:00 CST（注释「与 16:30 paper 错峰」），实际次日 02:00 CST，反而在 paper 之后 → 结构性滞后（R-308 根因②）
  - rebalance `0 15 * * 1-5`：意图 15:00 CST，实际 23:00 CST（无墙钟门控、价取 parquet，无数据危害）
  - risk_patrol `45 16 * * 1-5`：意图 16:45 CST（paper 后 15min 跟随），实际次日 00:45（跟随关系当前仍成立）
- **UTC 显式授权 4 行（黄金链，R-306/R-312）**：`40 7 * * 1-5`=15:40 CST（收盘后40min，正确设计）；`0 3 * * 0`=周日 11:00 CST；`38 9 3`/`40 9 3`=3日 17:38/17:40 CST。R-312 报告原文确认这 4 行按 UTC 授权。
- **a12** `10 17 2 * *`：R-248 原文「每月 2 日 17:10（HP 本地）」——「HP 本地」当时=UTC；切换后原表达式恰好=2日 17:10 CST，自然对齐文档口径，免改。
- **注释意图差 8h（无业务危害）**：p3_3（注释「凌晨2点」实际 10:00 CST）、a10（注释「3日09:05」实际 17:05 CST）。
- 时区无关 4 行：collect-metrics(每分钟)、notify_hub(每小时)、heartbeat(*/5)、@reboot。
- 其余周末/月度行在两个时区下业务等效（周末窗口/月粒度）。

## 2. 脚本时区依赖审计（grep datetime/utcnow/fromtimestamp/localtime/TZ/astimezone/ZoneInfo）

逐文件命中最多的先查（计数）：paper_engine.py=11、paper_engine_gold.py=1、cron_qfq_daily.py=0、refresh_data.py=4、risk_patrol.py=4、collect_crowding.py=2、fetch_valuation_data.py=2、snapshot_crowding.py=1、engines_shadow_nav_gold.py=0、engines_shadow_evaluate_gold.py=1、notify_hub.py=3、heartbeat_selfheal.sh=0、reboot_autostart.sh=0。

- **paper_engine.py（唯一墙钟门控）**：L1357-1358 `_now_min = datetime.now().hour*60+minute; if str(d)==str(today) and _now_min >= 15*60+5` → 当日行 spot 覆盖门（注释「已收盘>=15:05」=CST 语义，实际按本地=UTC 执行）。现状 16:30 UTC 触发→990≥905 恒过；**若切 CST 而 cron 不变则 16:30 CST→990≥905 仍过（语义修复）**；若仅把 cron 改到 08:30 UTC（路径 C）→510<905 门 FAIL→当日行退化 parquet T-1（**路径 C 对 baseline paper 不可行的决定性证据**）。
  - `today=date.today()`×2（L342 rebalance/L1327 daily）+`get_latest_trade_date()` 同源 → 业务日取本地时钟；UTC 下 16:30 触发时 UTC 日期=当日 CST 交易日（未跨日），现状输出行日期正确、仅滞后。
  - 其余 8 处为日志/状态时戳标签（表示层）；L124 `expires_at_ts>timestamp()` 为 epoch，TZ 无关。
  - rebalance 无墙钟门控：仅月首交易日 calendar 判定；成交价 `get_price(code,d)`=parquet qfq 收盘，无实时依赖。
- **paper_engine_gold.py**：L54 `datetime.now().astimezone().isoformat()` 唯一命中——TZ 感知写法，切换后输出 +08:00（正确）；无 date.today()，跨月/调仓判定全部数据驱动（marks/month_end 数据日期）。
- **refresh_data.py**：L87 `today=datetime.now().strftime("%Y%m%d")` 业务日取本地时钟（增量上界/already_latest 判定 L119）；周度刷新场景下周末窗口等效，切 TZ 无危害。
- **cron_qfq_daily.py / engines_shadow_nav_gold.py**：零时钟依赖，纯数据驱动（DONE 行解析+增量 update）。
- **risk_patrol / collect_crowding / fetch_valuation_data / notify_hub**：全部命中为 generated_at/ts 标签或日粒度去重键（notify_hub L213-215 today 键），无时刻门控。
- **snapshot_crowding.py**：L48 `now=datetime.now()` 仅取 (year,month) 判「当月未完→回退上一完整月」，月粒度 TZ 安全。
- **engines_shadow_evaluate_gold.py**：L148 硬编码 `+08:00` 后缀贴在 `datetime.now()`（当前=UTC）上 → **现状 ts 标签即错误**，切 CST 后自愈。
- **heartbeat_selfheal.sh / reboot_autostart.sh**：无 date/datetime 逻辑（后者= sleep 后跑 heartbeat 两次）。
- shell 侧 a12/a10 wrapper：`date '+%F %T'` 仅日志标签；a10 去重键 `date +%Y%m%d` 日粒度，触发时刻 09:05/17:05 同日，切换安全。

**结论（改 TZ 后 datetime.now() 行为面）**：唯一会改变控制流的是 paper_engine.py L1357 门控（切 CST+cron 不变→语义正确化）；其余全部是表示层（时戳标签从 UTC 变 CST）或 TZ 感知写法（gold）。已运行进程在重启前由 glibc 进程内缓存保持 UTC 表示（混跑窗口仅影响日志可读性，不影响业务）。

## 3. 三路径评估（详见正式报告）

- **A 改系统时区 Asia/Shanghai（timedatectl）**：影响=全部 cron 排程+新进程 datetime。cron 须 restart（man 证实按守护进程 TZ 排程）。CST 意图授权的 15 行自动回归设计时刻（含 R-308 两个根因的修复）；黄金链 4 行须同步等效改写（`40 7`→`40 15`、`0 3`→`0 11`、`38 9`→`38 17`、`40 9`→`40 17`）保持现网行为。回滚=set-timezone Etc/UTC + restart cron + 4 行还原（crontab 先备份）。
- **B CRON_TZ=Asia/Shanghai：不可行（否决）**。HP cron=Debian 3.0pl1-200ubuntu1，man 5 crontab LIMITATIONS 原文："The cron daemon runs with a defined timezone. It currently does not support per-user timezones... Even if a user specifies the TZ environment variable in his crontab this will affect only the commands executed in the crontab, not the execution of the crontab tasks themselves."（CRON_TZ 根本不被解析；唯一落地方式=换装 cronie，改动面反超 A。）
- **C 逐行 UTC 换算改写：不推荐，且对 baseline paper 实际不可行**。paper daily 改 `30 8 * * 1-5` 后触发时 UTC 08:30 → L1357 门 `_now_min=510<905` FAIL → 当日行退化 T-1，**比现状更差**；补救须改 paper_engine.py 门控（违反「不修改 paper_engine」实施红线）。且全部注释/文档是 CST 口径，维护永久心算 -8h。

## 4. 推荐：路径 A（一次性协调变更），关键点

- 时机：**不要在 9/1 当天切**（黄金首调仓+月首 rebalance+task-0400 抽查叠加日）；推荐 9/5（周六）或 9/6（周日）低负载窗口，或交易日 10:00-11:00 CST。
- 步骤：①备份 crontab → ②改写黄金 4 行（等效，行为零变化）→ ③`sudo timedatectl set-timezone Asia/Shanghai` → ④`sudo systemctl restart cron` → ⑤验证：`date`、下一分钟 cron 日志触发、collect-metrics 每分钟照常 → ⑥观察首个 16:30 CST paper daily + 18:00 qfq。
- 需用户批准：②（HP crontab 属不可自动清单）③④（sudo 系统变更）。
- 9/1 在途：若 9/1 前完成 A → 黄金首调仓按 R-312 设计 15:40 CST 精确触发（4 行已等效改写，零变化）；paper daily 当日 16:30 落账（提升）；task-0400 抽查行日期语义不变。若来不及 → 顺延至 9/5-9/7，9/1 全部按现状（UTC）执行，互不干扰。
- 遗留低优先项：rebalance 15:00:00 CST 恰在收盘撮合瞬间，可顺移 `5 15`（可选项，非必需）；p3_3/a10 将自动回到注释宣称时刻。

## 5. 零改动自检（任务结束时复核）

- crontab md5 AFTER：`3983e350b74051d45860502954270ab1`（与 BEFORE 一致）
- paper_engine.py / paper_engine_gold.py mtime AFTER：与 §0 快照一致（见报告附）
- 本会话 HP 侧操作全部为读：crontab -l / grep / sed -n / man / stat / timedatectl(查询) / systemctl list(查询) / sudo -S crontab -l(读)
