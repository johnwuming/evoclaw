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
EXCLUDE_PATTERN="AGENTS.md SOUL.md IDENTITY.md USER.md TOOLS.md HEARTBEAT.md BOOTSTRAP.md MEMORY.md PATHS.md"

MAX_RETRIES=3
RETRY_DELAY=10
TAB=$'\t'

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

# === 自动更新 shared/results/README.md ===

update_results_readme() {
    local readme="$RESULTS_DIR/README.md"
    local today
    today=$(date +%Y-%m-%d)
    local entries_file
    entries_file=$(mktemp)

    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        local status="${line%%"$TAB"*}"
        local filepath="${line#*"$TAB"}"
        filepath="${filepath#\"}"
        filepath="${filepath%\"}"
        # Decode git octal-encoded paths
        filepath=$(printf '%b' "$filepath")

        [[ "$filepath" == "research/README.md" ]] && continue
        [[ "$filepath" != research/* ]] && continue
        local fname
        fname=$(basename "$filepath")
        [[ "$fname" != R-*.md && "$fname" != M-*.md ]] && continue
        [[ "$status" == "D" ]] && continue

        local rel_path="${filepath#research/}"
        local code
        code=$(printf '%s' "$fname" | grep -oE '^(R|M)-[0-9]+')
        local title
        title=$(printf '%s' "$fname" | sed "s/^${code}-//" | sed 's/\.md$//')
        # Try to extract title from file content if filename lacks it
        if [[ -z "$title" || "$title" == "$code" ]]; then
            local real_file="$RESULTS_DIR/$rel_path"
            if [[ -f "$real_file" ]]; then
                local first_line
                first_line=$(head -1 "$real_file" 2>/dev/null)
                local extracted
                extracted=$(echo "$first_line" | sed -E 's/^#\s*(R|M)-[0-9]+\s*[:：-]\s*//' | sed -E 's/^#\s*//')
                if [[ -n "$extracted" && "$extracted" != "$first_line" ]]; then
                    title="$extracted"
                fi
            fi
        fi

        local action="修改"
        [[ "$status" == "A" ]] && action="新增"

        local project=$(echo "$rel_path" | grep -q '/' && echo "$rel_path" | cut -d'/' -f1 || echo "根目录")
        printf '| %s | %s | %s | %s | %s | %s |\n' "$today" "$action" "$code" "$title" "$project" "$rel_path" >> "$entries_file"
    done < <(cd "$REPO_DIR" && git diff --cached --name-status 2>/dev/null)

    # Remove existing entries with same code to prevent duplicates
    if [[ -f "$readme" ]]; then
        while IFS= read -r entry; do
            local entry_code
            entry_code=$(echo "$entry" | awk -F'|' '{gsub(/^ +| +$/, "", $4); print $4}')
            if [[ -n "$entry_code" ]]; then
                sed -i "/| ${entry_code} |/d" "$readme"
            fi
        done < "$entries_file"
    fi

    if [[ ! -s "$entries_file" ]]; then
        rm -f "$entries_file"
        return
    fi

    local entry_count
    entry_count=$(wc -l < "$entries_file")

    # 迁移旧4列格式到新6列格式
    if [[ -f "$readme" ]] && grep -q '| 日期 | 编号 |' "$readme" && ! grep -q '| 日期 | 操作 | 编号 |' "$readme"; then
        sed -i '/^| [0-9]/s/^| \([^|]*\) | \([^|]*\) | \([^|]*\) |$/| \1 | 修改 | \2 | from旧格式 | \3 |/' "$readme"
        sed -i 's/^| 日期 | 编号 |$/| 日期 | 操作 | 编号 | 标题 | 项目 |/' "$readme"
        sed -i 's/^|------|------|$/|------|------|------|------|------|------|/' "$readme"
    fi

    if [[ -f "$readme" ]]; then
        local inserted=0
        local tmpfile="${readme}.tmp.$$"
        {
            while IFS= read -r rl; do
                printf '%s\n' "$rl"
                if [[ $inserted -eq 0 && "$rl" =~ ^\|[-|[:space:]]+\|$ ]]; then
                    cat "$entries_file"
                    inserted=1
                fi
            done < "$readme"
        } > "$tmpfile" && mv "$tmpfile" "$readme"
    else
        mkdir -p "$(dirname "$readme")"
        {
            printf '%s\n\n' "# 研究交付物"
            printf '%s\n\n' "## 变更记录"
            printf '%s\n' "| 日期 | 操作 | 编号 | 标题 | 项目 | 路径 |"
            printf '%s\n' "|------|------|------|------|------|------|"
            cat "$entries_file"
        } > "$readme"
    fi

    rm -f "$entries_file"
    log "Updated $readme with $entry_count entries"
}

# === 同步文件 ===

if [ "$1" = "--all" ]; then
    if [ -d "$RESULTS_DIR" ]; then
        rsync -a --delete --exclude="$EXCLUDE_PATTERN" "$RESULTS_DIR/" "$REPO_DIR/research/" 2>/dev/null
    fi
    for f in $(find "$DEV_PROJECTS_DIR" -type f 2>/dev/null); do
        sync_file "$f"
    done
    for f in $(find "$RESEARCH_INTERNAL_DIR" -type f 2>/dev/null); do
        sync_file "$f"
    done
    cleanup_deleted "$DEV_PROJECTS_DIR" "$REPO_DIR/dev"
    cleanup_deleted "$RESEARCH_INTERNAL_DIR" "$REPO_DIR/research/internal"
fi

if [ -n "$1" ] && [ "$1" != "--all" ]; then
    local_path="$1"
    if [ -e "$local_path" ]; then
        if [[ "$local_path" == "$RESULTS_DIR"/* ]]; then
            rsync -a --exclude="$EXCLUDE_PATTERN" "$RESULTS_DIR/" "$REPO_DIR/research/" 2>/dev/null
        else
            sync_file "$local_path"
        fi
    fi
fi

# === Git commit + push（带重试） ===

cd "$REPO_DIR"

if [ -n "$(git status --porcelain)" ]; then
    git add -A

    # 在 commit 前更新 README.md
    update_results_readme

    # README.md 更新后也 stage 进去
    if [ -f "$RESULTS_DIR/README.md" ]; then
        git add "research/README.md" 2>/dev/null
    fi

    local_time=$(date +%Y-%m-%d\ %H:%M)
    changed=$(git diff --cached --name-only | sed 's|^research/||' | tr '\n' ', ' | sed 's/,$//')
    git commit -m "auto: $local_time | $changed" --quiet
    log "Committed: auto: $local_time | $changed"

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

        if echo "$push_output" | grep -qi "TLS\|timeout\|connect\|refused\|network"; then
            log "Network error detected, waiting ${RETRY_DELAY}s before retry..."
            sleep $RETRY_DELAY
        fi
    done

    if [ "$push_success" = false ]; then
        log "FAILED: All $MAX_RETRIES push attempts failed"
    fi
fi
