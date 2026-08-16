# HEARTBEAT.md — 心跳执行契约（优化稿）

> 规则冲突以 `AGENTS.md` §0 优先级为准。
> 任务状态一律以任务中心 API 为准；完成项不抄进本文件。
> 目标体积 ≤2KB，活跃任务不在这里存详情。

## 触发后只做两件事

1. 执行：`bash /root/.openclaw/workspace/scripts/heartbeat.sh`
2. 按脚本输出处理，**禁止手工 `cat`/`curl` 拼查询**。

## 脚本输出契约

```json
{
  "action": "OK | NOTIFY | REVIEW | CHECK",
  "notifications": [],
  "pending_review": [],
  "running": []
}
```

处理顺序（不管 action 是什么，逐项检查三个数组）：

1. `notifications` 非空 → 按每条 `source_session` 路由转述（微信会话 → `openclaw-weixin`；无来源/主会话 → 当前对话）。转述后执行 `bash /root/.openclaw/workspace/scripts/heartbeat.sh clear-notifications`。
2. `pending_review` 非空 → 读交付物**摘要 + 抽验**，然后：
   - 通过：`bash /root/.openclaw/workspace/scripts/heartbeat.sh review <taskId> approve "<审核摘要>"`
   - 拒绝：`bash /root/.openclaw/workspace/scripts/heartbeat.sh review <taskId> reject "<原因>"`
3. `running` 非空 → 判断是否超预期时长；有对应子 agent 会话/进程/日志可查则查，真死才告知用户并决定重派。长跑采集任务不误杀。
4. 全部为空 → 只回复 `HEARTBEAT_OK`，不解释。

## 输出规则

- 无事项：只回 `HEARTBEAT_OK`。
- 有事项：≤3 行摘要，任务必带 `task-XXXX`。
- 不推断、不重复旧任务；只处理脚本输出里出现的内容。
