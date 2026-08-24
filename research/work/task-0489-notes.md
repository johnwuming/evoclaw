# task-0489 / R-311 HP 时区统一专项评估 — 过程笔记（原始证据）

> 只读调研，边查边写。每条证据附命令+输出摘录。

## E1 系统事实（2026-08-25 07:15 GMT+8 采集）

### E1.1 timedatectl
命令：`ssh noname@10.12.192.174 'timedatectl'`
```
Local time: Mon 2026-08-24 23:15:47 UTC
Universal time: Mon 2026-08-24 23:15:47 UTC
Time zone: Etc/UTC (UTC, +0000)
System clock synchronized: yes
NTP service: active
RTC in local TZ: no
```
结论：**HP 系统时区 = Etc/UTC**，NTP 同步正常，shell 环境 TZ 变量为空。

### E1.2 cron 守护进程
命令：`systemctl status cron --no-pager | head -8; dpkg -l | grep -i cron`
```
● cron.service - Regular background program processing daemon
Active: active (running) since Tue 2026-08-18 03:55:10 UTC; 6 days ago
Main PID: 116137 (cron)
---
ii  cron 3.0pl1-200ubuntu1 amd64 process scheduling daemon
ii  cron-daemon-common 3.0pl1-200ubuntu1 all
```
结论：Ubuntu 官方源 **Debian cron 3.0pl1**（vixie-cron 血统），非 cronie。CRON_TZ 支持性待 E3 实证。

（后续证据继续追加）

## 6. 持久化

- 映射表持久化副本：`shared/results/work/task-0489-crontab-map.md`（/tmp 副本 r311_crontab_map.md）。
- 零改动终验：crontab md5 前后均 3983e350b74051d45860502954270ab1；paper_engine.py/gold mtime 未变；/usr/share/zoneinfo/Asia/Shanghai 存在（TZDATA_OK，路径 A 前置条件满足）。
