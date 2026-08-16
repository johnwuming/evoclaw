# task-0291 跨家目录迁移工程笔记

> 目标：/home/ubuntu → /root 归口。边查边写，本文件是恢复点。

## 迁移前状态摸底（进行中）


## A. inotify 同步守护 ✅（12:05 完成）
- **迁移前**：systemd `evolving-claw-sync.service`（非 nohup！）ExecStart=/bin/bash /home/ubuntu/.openclaw/evolving-claw-repo/infra/scripts/inotify-daemon.sh，Restart=always；进程 PID 359508 自 8月14 运行，监视 /root 侧 3 目录（shared/results、workspace-research/research、workspace）
- **重要发现**：auto-sync.sh 内 REPO_DIR="/root/.openclaw/evolving-claw-repo"（同步目标仓库本应在 /root）但该目录**根本不存在** → 同步链一直是坏的（同步落不到 git 仓库）。本次迁移顺带修复
- **改动**：① cp -a 整仓 11M → /root/.openclaw/evolving-claw-repo（含 .git，dirty 状态原样保留）② 新副本 inotify-daemon.sh 的 SYNC_SCRIPT 改 /root 路径（auto-sync.sh 无 ubuntu 硬编码，无需改）③ systemd 单元 ExecStart 改 /root 路径 ④ daemon-reload + restart
- **验证**：is-active=active，PID 1543662 跑 /root 路径；inotifywait 监视 /root/.openclaw/workspace/shared/results + /root/.openclaw/workspace（workspace-research/research 目录已不存在，脚本按设计跳过——旧进程也如此）
- **回滚**：改回 service ExecStart + restart
- **后续遗留**：/root 仓库副本 git status 有 dirty（原样迁移，非本次引入）

## B. 每日备份脚本 ✅（12:06 完成）
- **迁移前**：cron `00 3 * * *` 调 /home/ubuntu/.lighthouse/scripts/backup_config.sh --type auto
- **"日期 bug"澄清：不是 bug**。文件名格式 openclaw-{毫秒时间戳}-{版本号}-{类型}.json；"20260701" 是 OpenClaw 版本 2026.7.1 的 %d%02d%02d 编码，恒定属正常；时间戳字段每天正确变化（bak/auto/ 目录 8月12/13/15/16 各一份为证）。**无需修复**
- **改动**：cp 整个 .lighthouse/scripts（68K，含 backup_config.sh + probe_model.py + upgrade_guard.sh + weixin_bot_creator.py，另 3 个无 cron/systemd 引用但一并归口）→ /root/.lighthouse/scripts/，chown root；crontab 行改 /root 路径
- **验证**：手动跑 --type auto 返回 success:true，产物 /etc/lighthouse/openclaw/bak/auto/openclaw-1786853166197-20260701-auto.json（12:06 落盘）
- **回滚**：crontab 行改回即可

## C. agent-dashboard ✅（12:07 完成，停服窗口 ~23 秒：12:06:45→12:07:08）
- **迁移前**：root 侧 tools/agent-dashboard 是指向 ubuntu 实体目录的软链（257M：node_modules 20M、metrics.db 110M + wal 97M、tasks.db 1.4M + wal 4M、dashboard.db 0 字节疑似弃用）；service ExecStart/WorkingDirectory 全在 ubuntu 侧 node v22.23.1；cron collect-metrics.sh 走 ubuntu 路径（pull-hp-metrics.sh 已是 /root 路径，确认无需改）
- **脚本内检查**：collect-metrics.sh / pull-hp-metrics.sh / server.js（PORT=8055，QUANT_REPORTS_DIR 已是 /root）均无 ubuntu 硬编码，无需改脚本内容
- **改动**：① stop 服务（SQLite 干净关闭 checkpoint WAL）② rm 软链 → cp -a 全目录（2.0 秒）③ crontab collect-metrics 行改 /root ④ service ExecStart=/root/.nvm/versions/node/v22.23.2/bin/node + WorkingDirectory=/root ⑤ daemon-reload + start
- **验证**：is-active=active；curl 8055/ → 200；curl /api/tasks → 返回真实 JSON（task-0292 等任务数据，db 可读）；新实例已在 root 侧写 metrics.db-wal（12:07 时间戳）
- **附带**：agent-dashboard.bak-20260801-194935（2.8M）→ tar 217K 移 /root/backups/agent-dashboard.bak-20260801-194935.tar.gz，原目录已删
- **回滚**：service 改回 ubuntu 路径 + restart；软链重建 ln -s（root 侧实体目录保留即可用）
