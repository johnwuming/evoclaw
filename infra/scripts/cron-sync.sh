#!/bin/bash
# Cron 兜底：每 10 分钟检查一次是否有未同步的文件
# 由 /etc/cron.d/evolving-claw-sync 调用

bash /root/.openclaw/evolving-claw-repo/infra/scripts/auto-sync.sh --all
