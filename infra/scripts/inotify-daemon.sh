#!/bin/bash
# inotifywait 守护脚本
# 监控交付物目录，文件变更时触发同步

SYNC_SCRIPT="/root/.openclaw/evolving-claw-repo/infra/scripts/auto-sync.sh"
DEBOUNCE_SEC=3

# 监控的目录
WATCH_DIRS=(
    "/root/.openclaw/workspace/shared/results"
    "/root/.openclaw/workspace-dev"
    "/root/.openclaw/workspace-research/research"
    "/root/.openclaw/workspace"
)

# 构建 inotifywait 参数
WATCH_ARGS=()
for d in "${WATCH_DIRS[@]}"; do
    WATCH_ARGS+=("$d")
done

inotifywait -m -e create,modify,moved_to,moved_from,delete --format '%w%f' "${WATCH_ARGS[@]}" | while read filepath; do
    # 只处理 md/json/sh 文件
    if ! echo "$filepath" | grep -qE "\.(md|json|sh)$"; then
        continue
    fi
    # 跳过仓库自身和配置文件
    if echo "$filepath" | grep -qE "evolving-claw-repo|AGENTS\.md|SOUL\.md|IDENTITY\.md|USER\.md|TOOLS\.md|HEARTBEAT\.md|BOOTSTRAP\.md|MEMORY\.md"; then
        continue
    fi
    sleep $DEBOUNCE_SEC
    bash "$SYNC_SCRIPT" "$filepath" 2>&1
done
