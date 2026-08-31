# task-0604 修复笔记（边查边写）

## 事实
- 目标文件：/root/.openclaw/extensions/qqbot/dist/tools-CeUI9pG-.js（18270 字节，可整读）
- bug：qqbot_remind add 动作向 Gateway 发 cron.add 时把参数包在 `job: {...}` 里；Gateway openclaw 2026.7.1-2 期望字段平铺在顶层

## 已核验结论（2026-09-01）

### 根因
1. `defaultDeps.callCron` add 分支：`callGatewayTool("cron.add", {timeoutMs}, { job: params.job })` 把 job 对象整体包在 `job` 键里发出去。
2. Gateway wire schema `CronAddParamsSchema`（schema-BuOFpc7K.js:2547，openclaw 2026.7.1-2）是平铺对象且 `additionalProperties: false`：
   - 必填：`name`(NonEmptyString)、`schedule`、`sessionTarget`、`wakeMode`、`payload`
   - 可选：declarationKey/displayName/owner/trigger/delivery/failureAlert/agentId/sessionKey/description/enabled/deleteAfterRun
   - 所以 `{job:{...}}` 报 `unexpected property 'job'` + `missing name`，与症状完全吻合。
3. 次要 bug：`buildOnceJob` 用 `schedule:{kind:"at", atMs}`，但 Gateway 的 at 变体是严格对象 `{kind:"at", at: NonEmptyString}`（ISO-8601 字符串），不认 `atMs`（additionalProperties:false 会直接拒）。客户端 CLI 路径（cron-tool-C9qaFGtt.js:122-129）就是 atMs→ISO at 转换后再发。

### Gateway 字段 schema（逐字段核验）
- schedule union（严格）：`{kind:"at", at}` / `{kind:"every", everyMs, anchorMs?}` / `{kind:"cron", expr, tz?, staggerMs?}` / `{kind:"on-exit", command, cwd?}`；服务端 cron-BXksovqf.js:166 用 parseAbsoluteTimeMs 解析 `at`
- payload agentTurn 变体（严格）：`{kind:"agentTurn", message(必填), model?, fallbacks?, thinking?, timeoutSeconds?, allowUnsafeExternalContent?, lightContext?, toolsAllow?, toolsAllowIsDefault?}`
- delivery announce 变体（严格）：`{mode:"announce", channel?(非空串,"qqbot"合法), threadId?, accountId?, bestEffort?, failureDestination?, completionDestination?, to?(NonBlankString)}`
- sessionTarget: "main"|"isolated"|"current"|"session:<id>"；wakeMode: "next-heartbeat"|"now"
- CLI 正常路径佐证：cron-tool-C9qaFGtt.js:1025 `callGateway("cron.add", gatewayOpts, { ...job })` —— 平铺 spread。

### 修复方案（最小 diff，2 处）
1. callCron add 分支：`{ job: params.job }` → `params.job`（平铺）
2. buildOnceJob：`schedule:{kind:"at", atMs}` → `schedule:{kind:"at", at: new Date(atMs).toISOString()}`

### 字段级旧→新映射对照
- 顶层 `job` 包装 → 移除（job 内字段平铺到请求顶层）
- `job.name` → 顶层 `name`
- `job.schedule.{kind:"at",atMs}` → 顶层 `schedule:{kind:"at",at:<ISO-8601>}`
- `job.schedule.{kind:"cron",expr,tz}` → 顶层 `schedule:{kind:"cron",expr,tz}`（已符合，不动）
- `job.sessionTarget` → 顶层 `sessionTarget`（"isolated" 合法）
- `job.wakeMode` → 顶层 `wakeMode`（"now" 合法）
- `job.payload.{kind:"agentTurn",message}` → 顶层 `payload`（已符合）
- `job.delivery.{mode:"announce",channel,to,accountId}` → 顶层 `delivery`（已符合）
- `job.deleteAfterRun` → 顶层 `deleteAfterRun`（已符合）

## 待办
- [ ] 备份原文件
- [ ] 应用 2 处最小 diff
- [ ] node --check 验证（确认 ESM 处理方式）
- [ ] 写交付文件 + .task-completions.jsonl + 任务状态回写
