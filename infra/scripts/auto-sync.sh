#!/bin/bash
# evolving-claw 自动同步脚本
# 支持 git push 重试 + non-fast-forward 自动恢复

REPO_DIR="/root/.openclaw/evolving-claw-repo"
RESULTS_DIR="/root/.openclaw/workspace/shared/results"
DEV_PROJECTS_DIR="/root/.openclaw/workspace-dev"
RESEARCH_INTERNAL_DIR="/root/.openclaw/workspace-research/research"
MAIN_WS_DIR="/root/.openclaw/workspace"
LOG_FILE="/root/.openclaw/evolving-claw-repo/infra/sync.log"

EXCLUDE_FILES="AGENTS.md|SOUL.md|IDENTITY.md|USER.md|TOOLS.md|HEARTBEAT.md|BOOTSTRAP.md|MEMORY.md|PATHS.md"

MAX_RETRIES=3
RETRY_DELAY=10

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

is_excluded() {
    local name=$(basename "$1")
    echo "$name" | grep -qE "$EXCLUDE_FILES" && return 0
    echo "$name" | grep -qE "\.(md|json|sh)$" || return 0
    return 1
}

map_dest() {
    local src="$1"
    local dest=""
    if [[ "$src" == "$RESULTS_DIR"/R-*.md || "$src" == "$RESULTS_DIR"/M-*.md ]]; then
        dest="$REPO_DIR/research/$(basename "$src")"
    elif [[ "$src" == "$DEV_PROJECTS_DIR"/* ]]; then
        local rel="${src#$DEV_PROJECTS_DIR/}"
        dest="$REPO_DIR/dev/$rel"
    elif [[ "$src" == "$RESEARCH_INTERNAL_DIR"/* ]]; then
        local rel="${src#$RESEARCH_INTERNAL_DIR/}"
        dest="$REPO_DIR/research/internal/$rel"
    fi
    echo "$dest"
}

sync_file() {
    local src="$1"
    is_excluded "$src" && return
    local dest=$(map_dest "$src")
    if [ -n "$dest" ]; then
        mkdir -p "$(dirname "$dest")"
        cp "$src" "$dest"
    fi
}

cleanup_deleted() {
    local local_dir="$1"
    local repo_dir="$2"
    [ ! -d "$repo_dir" ] && return
    while IFS= read -r repo_file; do
        local rel="${repo_file#$repo_dir/}"
        local local_file="$local_dir/$rel"
        if [ ! -e "$local_file" ]; then
            (cd "$REPO_DIR" && git rm -f "$repo_file" 2>/dev/null)
        fi
    done < <(find "$repo_dir" -type f 2>/dev/null)
}

# === 同步文件 ===

if [ "$1" = "--all" ]; then
    for f in $(ls "$RESULTS_DIR"/*.md 2>/dev/null); do
        [ -f "$f" ] && sync_file "$f"
    done
    for f in $(find "$DEV_PROJECTS_DIR" -type f 2>/dev/null); do
        sync_file "$f"
    done
    for f in $(find "$RESEARCH_INTERNAL_DIR" -type f 2>/dev/null); do
        sync_file "$f"
    done
    for f in $(find "$REPO_DIR/research" -type f \( -name "R-*.md" -o -name "M-*.md" \) 2>/dev/null); do
        fname=$(basename "$f")
        if [ ! -e "$RESULTS_DIR/$fname" ]; then
            (cd "$REPO_DIR" && git rm -f "$f" 2>/dev/null)
        fi
    done
    cleanup_deleted "$DEV_PROJECTS_DIR" "$REPO_DIR/dev"
    cleanup_deleted "$RESEARCH_INTERNAL_DIR" "$REPO_DIR/research/internal"
fi

if [ -n "$1" ] && [ "$1" != "--all" ]; then
    local_path="$1"
    if [ -e "$local_path" ]; then
        sync_file "$local_path"
    fi
fi

# === Git commit + push（带重试） ===

cd "$REPO_DIR"

if [ -n "$(git status --porcelain)" ]; then
    git add -A
    local_time=$(date +%Y-%m-%d\ %H:%M)
    git commit -m "auto: $local_time" --quiet
    log "Committed: auto: $local_time"

    push_success=false
    for attempt in $(seq 1 $MAX_RETRIES); do
        push_output=$(git push --quiet 2>&1)
        push_exit=$?

        if [ $push_exit -eq 0 ]; then
            log "Push succeeded (attempt $attempt)"
            push_success=true
            break
        fi

        log "Push failed (attempt $attempt/$MAX_RETRIES): $push_output"

        # 处理 non-fast-forward：先 pull --rebase 再重试
        if echo "$push_output" | grep -q "non-fast-forward\|fetch first"; then
            log "Non-fast-forward detected, pulling..."
            pull_output=$(git pull --rebase --quiet 2>&1)
            pull_exit=$?
            if [ $pull_exit -eq 0 ]; then
                log "Pull rebase succeeded, will retry push"
            else
                log "Pull rebase failed: $pull_output"
            fi
        fi

        # 处理网络错误：等待后重试
        if echo "$push_output" | grep -qi "TLS\|timeout\|connect\|refused\|network"; then
            log "Network error detected, waiting ${RETRY_DELAY}s before retry..."
            sleep $RETRY_DELAY
        fi
    done

    if [ "$push_success" = false ]; then
        log "FAILED: All $MAX_RETRIES push attempts failed"
    fi
fi
