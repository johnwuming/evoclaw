#!/bin/bash
# evolving-claw 自动同步脚本
# 由 inotifywait 触发，也可由 cron 兜底调用

REPO_DIR="/root/.openclaw/evolving-claw-repo"
RESULTS_DIR="/root/.openclaw/workspace/shared/results"
DEV_PROJECTS_DIR="/root/.openclaw/workspace-dev"
RESEARCH_INTERNAL_DIR="/root/.openclaw/workspace-research/research"
MAIN_WS_DIR="/root/.openclaw/workspace"

# 排除的文件名（agent 配置文件）
EXCLUDE_FILES="AGENTS.md|SOUL.md|IDENTITY.md|USER.md|TOOLS.md|HEARTBEAT.md|BOOTSTRAP.md|MEMORY.md"

sync_file() {
    local src="$1"
    local name=$(basename "$src")

    # 跳过排除文件
    if echo "$name" | grep -qE "$EXCLUDE_FILES"; then
        return
    fi

    # 跳过非 md/json/sh 文件
    if ! echo "$name" | grep -qE "\.(md|json|sh)$"; then
        return
    fi

    local dest=""

    # 研究团队 R-*.md / M-*.md 交付物 → research/
    if [[ "$src" == "$RESULTS_DIR"/R-*.md || "$src" == "$RESULTS_DIR"/M-*.md ]]; then
        dest="$REPO_DIR/research/$name"
    # 开发项目 → dev/<project>/*
    elif [[ "$src" == "$DEV_PROJECTS_DIR"/* ]]; then
        local rel="${src#$DEV_PROJECTS_DIR/}"
        dest="$REPO_DIR/dev/$rel"
    # 研究过程文件 → research/internal/*
    elif [[ "$src" == "$RESEARCH_INTERNAL_DIR"/* ]]; then
        local rel="${src#$RESEARCH_INTERNAL_DIR/}"
        dest="$REPO_DIR/research/internal/$rel"
    fi

    if [ -n "$dest" ]; then
        mkdir -p "$(dirname "$dest")"
        cp "$src" "$dest"
    fi
}

# 如果带参数 --all，全量同步
if [ "$1" = "--all" ]; then
    # 研究交付物
    for f in $(ls "$RESULTS_DIR"/*.md 2>/dev/null); do
        [ -f "$f" ] && sync_file "$f"
    done
    # 开发项目
    for f in $(find "$DEV_PROJECTS_DIR" -type f 2>/dev/null); do
        sync_file "$f"
    done
    # 研究内部
    for f in $(ls "$RESEARCH_INTERNAL_DIR"/* 2>/dev/null); do
        [ -f "$f" ] && sync_file "$f"
    done
fi

# 检查是否有变更，有则 commit + push
cd "$REPO_DIR"
if [ -n "$(git status --porcelain)" ]; then
    git add -A
    local_time=$(date +%Y-%m-%d\ %H:%M)
    git commit -m "auto: $local_time" --quiet
    git push --quiet 2>&1
fi
