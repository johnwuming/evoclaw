# task-0446 状态协议修复笔记

任务：三处最小修复（模板补 PUT 回写 / session-key 端点翻转 spawn_owner / PUT 状态白名单）
依据：R-276 审计（高-1、高-2、中-1）

## 步骤 0：审计要点确认（已读 §四 冲突清单 + §五 修复建议）

- 高-1：模板 spawn-task.md 完成回报段只有 jsonl 写入，无 PUT pending_review → 补一行。
- 高-2：PUT /api/tasks/:id（:921-960）无状态白名单，非法字符串入库。审计建议白名单 9 态：pending/running/pending_review/done/failed/failed_final/rejected/paused/cancelled（以 server.js 实际代码出现的集合为准再定）。
- 中-1：session-key 端点(:1044-1060)回写 agent_session_key 时不翻转 spawn_owner，130/148 任务错标 web → 补 UPDATE tasks SET spawn_owner='main'。

## 备份

（进行中）
