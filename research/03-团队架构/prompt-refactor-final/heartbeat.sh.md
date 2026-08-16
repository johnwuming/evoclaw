# heartbeat.sh — 心跳查询/审核脚本（文档稿）

> 保存为：`/root/.openclaw/workspace/scripts/heartbeat.sh`
> 执行：`bash /root/.openclaw/workspace/scripts/heartbeat.sh [run|review|clear-notifications]`
> 部署后先 `bash heartbeat.sh` 跑一次，按实际任务中心 API 返回字段核对 jq 提取键名。

```bash
#!/usr/bin/env bash
set -euo pipefail

WS=/root/.openclaw/workspace
API=http://127.0.0.1:8055
NOTIFY_QUEUE="$WS/scripts/.task-notifications.jsonl"
TOKEN_FILE="$WS/scripts/.task-center-internal-token"

usage() {
  echo "用法: heartbeat.sh [run|review <taskId> <approve|reject> <summary>|clear-notifications]" >&2
  exit 1
}

summarize_tasks() {
  local payload="$1"
  printf '%s' "$payload" | jq -c '
    (if type == "array" then . else (.tasks // .data // .items // []) end)
    | [.[]? | {
        taskId: (.taskId // .id // "?"),
        title: ((.title // .subject // .description // "")[0:120]),
        status: (.status // "?"),
        output: ((.expected_output // .output // .outputFiles // "")[0:200])
      }]'
}

run() {
  local notifications='[]' pending='[]' running='[]'
  local action="OK"

  if [[ -s "$NOTIFY_QUEUE" ]]; then
    notifications=$(tail -n 10 "$NOTIFY_QUEUE" | jq -Rsc 'split("\n") | map(select(length > 0) | .[0:300])')
    action="NOTIFY"
  fi

  pending=$(summarize_tasks "$(curl -s --max-time 5 "$API/api/tasks?status=pending_review" || true)" || echo '[]')
  if [[ -n "$(printf '%s' "$pending" | jq 'select(length > 0)' 2>/dev/null || true)" ]]; then
    [[ "$action" == "OK" ]] && action="REVIEW"
  fi

  running=$(summarize_tasks "$(curl -s --max-time 5 "$API/api/tasks?status=running" || true)" || echo '[]')
  if [[ "$action" == "OK" && -n "$(printf '%s' "$running" | jq 'select(length > 0)' 2>/dev/null || true)" ]]; then
    action="CHECK"
  fi

  jq -cn \
    --arg action "$action" \
    --argjson notifications "$notifications" \
    --argjson pending "$pending" \
    --argjson running "$running" \
    '{action: $action, notifications: $notifications, pending_review: $pending, running: $running}'
}

review() {
  local task_id="${1:-}"; shift || true
  local decision="${1:-}"; shift || true
  local summary="${1:-}"

  [[ -n "$task_id" && -n "$decision" ]] || usage
  [[ "$decision" == "approve" || "$decision" == "reject" ]] || usage

  local token
  token=$(cat "$TOKEN_FILE")

  local body
  body=$(jq -cn --arg id "$task_id" --arg d "$decision" --arg s "$summary" \
    '{taskId: $id, decision: $d, summary: $s}')

  curl -s --max-time 10 -X POST "$API/internal/review" \
    -H "x-internal-token: $token" \
    -H 'content-type: application/json' \
    -d "$body"
}

clear_notifications() {
  : > "$NOTIFY_QUEUE"
  echo '{"action":"OK","notifications":[],"pending_review":[],"running":[]}'
}

case "${1:-run}" in
  run) run ;;
  review) shift; review "$@" ;;
  clear-notifications) clear_notifications ;;
  *) usage ;;
esac
```

## 说明

- `run` 只返回**摘要字段**（标题 120 字符、输出 200 字符），从源头截断，防止心跳烧 token。
- `review` 封装内部审核请求，字段固定为 `decision`，避免模型手拼 JSON 出错。
- `clear-notifications` 必须在转述成功后再调用；脚本本身不清空，防止消息丢失。
- 若任务中心 API 返回结构不同，只需修改 `summarize_tasks` 的字段提取，不改 HEARTBEAT.md。
