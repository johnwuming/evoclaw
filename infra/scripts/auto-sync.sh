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

is_excluded() {
    local name=$(basename "$1")
    echo "$name" | grep -qE "$EXCLUDE_FILES" && return 0
    echo "$name" | grep -qE "\.(md|json|sh)$" || return 0
    return 1
}

map_dest() {
    local src="$1"
    local dest=""

    # 研究团队 R-*.md / M-*.md 交付物 → research/
    if [[ "$src" == "$RESULTS_DIR"/R-*.md || "$src" == "$RESULTS_DIR"/M-*.md ]]; then
        dest="$REPO_DIR/research/$(basename "$src")"
    # 开发项目 → dev/<project>/*
    elif [[ "$src" == "$DEV_PROJECTS_DIR"/* ]]; then
        local rel="${src#$DEV_PROJECTS_DIR/}"
        dest="$REPO_DIR/dev/$rel"
    # 研究过程文件 → research/internal/*
    elif [[ "$src" == "$RESEARCH_INTERNAL_DIR"/* ]]; then
        local rel="${src#$RESEARCH_INTERNAL_DIR/}"
        dest="$REPO_DIR/research/internal/$rel"
    fi

    echo "$dest"
}

# 同步单个文件（复制到仓库）
sync_file() {
    local src="$1"
    is_excluded "$src" && return

    local dest=$(map_dest "$src")
    if [ -n "$dest" ]; then
        mkdir -p "$(dirname "$dest")"
        cp "$src" "$dest"
    fi
}

# 清理仓库中本地已不存在的文件
cleanup_deleted() {
    local local_dir="$1"
    local repo_dir="$2"

    [ ! -d "$repo_dir" ] && return

    find "$repo_dir" -type f | while read repo_file; do
        local rel="${repo_file#$repo_dir/}"
        local local_file="$local_dir/$rel"
        if [ ! -e "$local_file" ]; then
            (cd "$REPO_DIR" && git rm -f "$repo_file" 2>/dev/null)
        fi
    done
}

# 全量同步（--all 模式）
if [ "$1" = "--all" ]; then
    # --- 复制/更新文件 ---
    # 研究交付物
    for f in $(ls "$RESULTS_DIR"/*.md 2>/dev/null); do
        [ -f "$f" ] && sync_file "$f"
    done
    # 开发项目
    for f in $(find "$DEV_PROJECTS_DIR" -type f 2>/dev/null); do
        sync_file "$f"
    done
    # 研究内部
    for f in $(find "$RESEARCH_INTERNAL_DIR" -type f 2>/dev/null); do
        sync_file "$f"
    done

    # --- 清理本地已删除的文件 ---
    # research/ 目录：只清理 R-*.md / M-*.md
    for f in $(find "$REPO_DIR/research" -type f \( -name "R-*.md" -o -name "M-*.md" \) 2>/dev/null); do
        local local_name=$(basename "$f")
        if [ ! -e "$RESULTS_DIR/$local_name" ]; then
            (cd "$REPO_DIR" && git rm -f "$f" 2>/dev/null)
        fi
    done
    # dev/ 目录
    cleanup_deleted "$DEV_PROJECTS_DIR" "$REPO_DIR/dev"
    # research/internal/ 目录
    cleanup_deleted "$RESEARCH_INTERNAL_DIR" "$REPO_DIR/research/internal"
fi

# 当 inotify 提供具体文件时（$1 不是 --all），只同步该文件并处理可能的删除
# 注意：删除事件只清理仓库，不复制文件
if [ -n "$1" ] && [ "$1" != "--all" ]; then
    local_path="$1"
    if [ -e "$local_path" ]; then
        sync_file "$local_path"
    fi
fi

# 检查是否有变更，有则 commit + push
cd "$REPO_DIR"
if [ -n "$(git status --porcelain)" ]; then
    git add -A
    local_time=$(date +%Y-%m-%d\ %H:%M)
    git commit -m "auto: $local_time" --quiet
    git push --quiet 2>&1
fi
