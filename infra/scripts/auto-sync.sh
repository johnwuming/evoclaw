#!/bin/bash
# evolving-claw 自动同步脚本
# 由 inotifywait 触发，也可由 cron 兜底调用

REPO_DIR="/root/.openclaw/evolving-claw-repo"
RESULTS_DIR="/root/.openclaw/workspace/shared/results"
DEV_PROJECTS_DIR="/root/.openclaw/workspace-dev/projects"
RESEARCH_INTERNAL_DIR="/root/.openclaw/workspace-research/research"
MAIN_WS_DIR="/root/.openclaw/workspace"

# 排除的文件名（agent 配置文件）
EXCLUDE_FILES="AGENTS.md|SOUL.md|IDENTITY.md|USER.md|TOOLS.md|HEARTBEAT.md|BOOTSTRAP.md|MEMORY.md"

# 研究报告分类：根据文件名关键词判断放 reports 还是 plans
classify_research_file() {
    local name="$1"
    if echo "$name" | grep -qiE "design|plan|scheme|architecture|strategy"; then
        echo "plans"
    else
        echo "reports"
    fi
}

# main 目录文件分类
classify_main_file() {
    local name="$1"
    if echo "$name" | grep -qiE "config|agent-config|prompt"; then
        echo "config"
    elif echo "$name" | grep -qiE "plan|feasibility|strategy"; then
        echo "plans"
    else
        echo "analysis"
    fi
}

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

    # 研究团队交付物
    if [[ "$src" == "$RESULTS_DIR"* ]]; then
        local subdir=$(classify_research_file "$name")
        dest="$REPO_DIR/research/$subdir/$name"
    # 开发团队交付物
    elif [[ "$src" == "$DEV_PROJECTS_DIR"* ]]; then
        local rel="${src#$DEV_PROJECTS_DIR/}"
        dest="$REPO_DIR/dev/$rel"
    # 研究过程文件
    elif [[ "$src" == "$RESEARCH_INTERNAL_DIR"* ]]; then
        local rel="${src#$RESEARCH_INTERNAL_DIR/}"
        dest="$REPO_DIR/research/internal/$rel"
    # 主 agent 产出
    elif [[ "$src" == "$MAIN_WS_DIR"/* ]]; then
        local subdir=$(classify_main_file "$name")
        dest="$REPO_DIR/main/$subdir/$name"
    fi

    if [ -n "$dest" ]; then
        mkdir -p "$(dirname "$dest")"
        cp "$src" "$dest"
    fi
}

# 如果带参数 --all，全量同步
if [ "$1" = "--all" ]; then
    # 研究报告
    for f in $(ls "$RESULTS_DIR"/*.md "$RESULTS_DIR"/*.json 2>/dev/null); do
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
    # 主 agent
    for f in $(ls "$MAIN_WS_DIR"/*.md 2>/dev/null); do
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
