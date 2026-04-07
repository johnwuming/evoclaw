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
# 只在 shared/results/ 下有 R-*.md 或 M-*.md 变更时才更新

update_results_readme() {
    local readme="$RESULTS_DIR/README.md"
    local today=$(date +%Y-%m-%d)
    local -a new_entries=()

    # 读取 staged 变更，git 对含特殊字符的路径会加引号，需要去掉首尾引号
    while IFS= read -r line; do
        # line 格式: 状态\t路径  （git 可能在路径两端加引号）
        local status="${line%%$'\t'*}"
        local filepath="${line#"$status"$'\t'}"
        filepath="${filepath#\"}"       # 去掉首引号
        filepath="${filepath%\"}"       # 去掉尾引号

        [[ "$filepath" == "research/README.md" ]] && continue
        [[ "$filepath" != research/* ]] && continue
        local fname=$(basename "$filepath")
        [[ "$fname" != R-*.md && "$fname" != M-*.md ]] && continue
        [[ "$status" == "D" ]] && continue  # 不记录删除

        local rel_path="${filepath#research/}"
        local code=$(echo "$fname" | grep -oE '^(R|M)-[0-9]+')
        local title=$(echo "$fname" | sed -E "s/^${code}-//; s/\.md$//")
        local action="修改"
        [[ "$status" == "A" ]] && action="新增"

        new_entries+=("| ${today} | ${action} | ${code} | ${title} | ${rel_path} |")
    done < <(cd "$REPO_DIR" && git diff --cached --name-status 2>/dev/null)

    # 没有 R-/M- 文件变更则跳过
    [[ ${#new_entries[@]} -eq 0 ]] && return

    # ---- 迁移旧格式（4列）到新格式（5列含操作列） ----
    if [[ -f "$readme" ]] && grep -q '| 日期 | 编号 |' "$readme" && ! grep -q '| 日期 | 操作 | 编号 |' "$readme"; then
        sed -i '/^| [0-9]/s/^| \([^|]*\) | /| \1 | 修改 | /' "$readme"
        sed -i 's/^| 日期 | 编号 |/| 日期 | 操作 | 编号 |/' "$readme"
        sed -i 's/^|------|------|$/|------|------|------|/' "$readme"
    fi

    # ---- 插入新行 ----
    if [[ -f "$readme" ]]; then
        local inserted=0
        local tmpfile="${readme}.tmp.$$"
        {
            while IFS= read -r rl; do
                echo "$rl"
                # 检测到分隔行 |------|...| 后，插入所有新记录
                if [[ $inserted -eq 0 && "$rl" =~ ^\|[-|[:space:]]+\|$ ]]; then
                    for entry in "${new_entries[@]}"; do
                        echo "$entry"
                    done
                    inserted=1
                fi
            done < "$readme"
        } > "$tmpfile" && mv "$tmpfile" "$readme"
    else
        mkdir -p "$(dirname "$readme")"
        {
            echo "# 研究交付物"
            echo ""
            echo "## 变更记录"
            echo ""
            echo "| 日期 | 操作 | 编号 | 标题 | 路径 |"
            echo "|------|------|------|------|------|"
            for entry in "${new_entries[@]}"; do
                echo "$entry"
            done
        } > "$readme"
    fi

    log "Updated $readme with ${#new_entries[@]} entries"
}

# === 同步文件 ===

if [ "$1" = "--all" ]; then
    # shared/results/ 整体镜像到 evoclaw/research/（保留目录结构）
    if [ -d "$RESULTS_DIR" ]; then
        rsync -a --delete --exclude="$EXCLUDE_PATTERN" "$RESULTS_DIR/" "$REPO_DIR/research/" 2>/dev/null
    fi
    # dev 项目同步
    for f in $(find "$DEV_PROJECTS_DIR" -type f 2>/dev/null); do
        sync_file "$f"
    done
    # 研究过程文件同步
    for f in $(find "$RESEARCH_INTERNAL_DIR" -type f 2>/dev/null); do
        sync_file "$f"
    done
    cleanup_deleted "$DEV_PROJECTS_DIR" "$REPO_DIR/dev"
    cleanup_deleted "$RESEARCH_INTERNAL_DIR" "$REPO_DIR/research/internal"
fi

if [ -n "$1" ] && [ "$1" != "--all" ]; then
    local_path="$1"
    if [ -e "$local_path" ]; then
        # 如果是 shared/results/ 下的文件，用 rsync 增量同步
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

    # 在 commit 前更新 README.md（读取当前已 staged 的变更）
    update_results_readme

    # README.md 更新后也 stage 进去
    if [ -f "$RESULTS_DIR/README.md" ]; then
        git add "research/README.md" 2>/dev/null
    fi

    local_time=$(date +%Y-%m-%d\ %H:%M)
    # 生成变更文件摘要
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
