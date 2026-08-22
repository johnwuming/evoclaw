# task-0446 状态协议修复笔记

任务：三处最小修复（模板补 PUT 回写 / session-key 端点翻转 spawn_owner / PUT 状态白名单）
依据：R-276 审计（高-1、高-2、中-1）

## 步骤 0：审计要点确认（已读 §四 冲突清单 + §五 修复建议）

- 高-1：模板 spawn-task.md 完成回报段只有 jsonl 写入，无 PUT pending_review → 补一行。
- 高-2：PUT /api/tasks/:id（:921-960）无状态白名单，非法字符串入库。审计建议白名单 9 态：pending/running/pending_review/done/failed/failed_final/rejected/paused/cancelled（以 server.js 实际代码出现的集合为准再定）。
- 中-1：session-key 端点(:1044-1060)回写 agent_session_key 时不翻转 spawn_owner，130/148 任务错标 web → 补 UPDATE tasks SET spawn_owner='main'。

## 备份

（进行中）

## 改动 1：spawn-task.md 完成回报段（高-1）

diff（53a54,58）：
```
> 随后 MUST 将任务状态回写为待审（completions→pending_review 闭环）：
> ```
> curl -s -X PUT http://127.0.0.1:8055/api/tasks/task-XXXX -H 'Content-Type: application/json' -d '{"status":"pending_review"}' | head -c 2000
> ```
```

## 白名单集合依据（高-2）

grep 统计：前端 TASK_STATUS(:7184) 9 态 = pending/running/done/failed/paused/cancelled/pending_review/rejected/failed_final；stats 循环 6 态是子集；审计建议 9 态一致。DB 无 CHECK 约束。addEvent 存在于 :363。事件名沿用小写下划线惯例（如 reviewed_approved/session_key），新增 'status_changed'。

## 改动 2+3：server.js（node --check 已过 SYNTAX OK）

diff 摘要：
- :944-947 新增 STATUS_WHITELIST（9 态）+ 非法值 return 400
- :954 pending_review 分支补 addEvent 'status_changed'（审计指出原来无事件痕迹）
- :956 非 paused 来源退回 pending 补 addEvent（僵尸退回留痕）
- :1059 session-key 端点 pending 分支 UPDATE 补 spawn_owner='main'
- :1063 session-key 端点 else 分支 UPDATE 补 spawn_owner='main'

服务重启与四条实测：见下节。
