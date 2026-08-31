# task-0604：修复 qqbot_remind add 动作 cron.add 参数映射 bug

- 终态：**完成**
- 日期：2026-09-01
- 修复文件：`/root/.openclaw/extensions/qqbot/dist/tools-CeUI9pG-.js`（@openclaw/qqbot 2026.6.11 dist 构建产物）
- 备份：`/root/.openclaw/extensions/qqbot/dist/tools-CeUI9pG-.js.bak-20260901`（改前逐字节副本）

## 1. 根因

bug 位置两处（均在 tools-CeUI9pG-.js）：

1. **`defaultDeps.callCron` add 分支**：`callGatewayTool("cron.add", {timeoutMs}, { job: params.job })` 把 job 对象整体包在 `job` 键里发给 Gateway。
2. **`buildOnceJob`**：一次性提醒用 `schedule: { kind: "at", atMs }`，但 Gateway 的 at 变体要求 `{ kind: "at", at: <ISO-8601 字符串> }`。

对照 Gateway（openclaw 2026.7.1-2）源码确认：

- wire schema `CronAddParamsSchema`（`dist/schema-BuOFpc7K.js:2547`）：平铺对象，`additionalProperties: false`，必填 `name`(NonEmptyString)/`schedule`/`sessionTarget`/`wakeMode`/`payload`。`{job:{...}}` 因此报 `unexpected property 'job'` + `missing name`，与线上症状逐字吻合（已用真实校验器复现，见 §4）。
- schedule at 变体为严格对象 `{kind:"at", at: NonEmptyString}`，`atMs` 属性不存在（服务端 `dist/cron-BXksovqf.js:166` 用 `parseAbsoluteTimeMs(at)` 解析 ISO 串）。
- CLI 正常路径佐证：`dist/cron-tool-C9qaFGtt.js:1025` `callGateway("cron.add", gatewayOpts, { ...job })` —— job 字段平铺 spread；其内部 122–129 行正是 atMs→ISO `at` 的转换。

## 2. 字段级旧→新映射对照

| 旧（bug 版 wire params） | 新（修复后 wire params） | 说明 |
|---|---|---|
| `{ job: { … } }` 顶层包装 | job 内容平铺到请求顶层 | callCron add 分支 `{ job: params.job }` → `params.job` |
| `job.name` | 顶层 `name` | NonEmptyString，值不变（name 或 "Reminder: 内容前20字"） |
| `job.schedule = {kind:"at", atMs:<number>}` | `schedule = {kind:"at", at:"<ISO-8601>"}` | `new Date(atMs).toISOString()`；Gateway 严格 schema 不认 atMs |
| `job.schedule = {kind:"cron", expr, tz}` | 顶层 `schedule` 同形 | 已符合 schema，不动 |
| `job.sessionTarget: "isolated"` | 顶层 `sessionTarget` | 合法字面量，不动 |
| `job.wakeMode: "now"` | 顶层 `wakeMode` | 合法字面量，不动 |
| `job.payload = {kind:"agentTurn", message}` | 顶层 `payload` | 已符合（message 必填非空），不动 |
| `job.delivery = {mode:"announce", channel:"qqbot", to, accountId}` | 顶层 `delivery` | 已符合（channel 非空串合法、to NonBlankString、accountId 可选），不动 |
| `job.deleteAfterRun: true`（仅一次性） | 顶层 `deleteAfterRun` | 可选 boolean，不动 |

list/remove 分支结构本就正确（`{action:"list"}` / `{jobId}`），未改动。

## 3. Diff 摘要（完整 diff，共 2 处）

```diff
--- tools-CeUI9pG-.js.bak-20260901
+++ tools-CeUI9pG-.js
@@ buildOnceJob（一次性提醒 schedule）
-				atMs
+				at: new Date(atMs).toISOString()
@@ defaultDeps.callCron add 分支（wire params 平铺）
-		case "add": return await callGatewayTool("cron.add", { timeoutMs: DEFAULT_GATEWAY_TIMEOUT_MS }, { job: params.job });
+		case "add": return await callGatewayTool("cron.add", { timeoutMs: DEFAULT_GATEWAY_TIMEOUT_MS }, params.job);
```

无其他改动；未动 SKILL.md、CLI 备用路径、crontab、node_modules。

## 4. 验证（全部实际运行）

1. **语法**：`node --check /root/.openclaw/extensions/qqbot/dist/tools-CeUI9pG-.js` → 通过（package.json 声明 `"type":"module"`，按 ESM 解析）。退出码 0。
2. **模块加载 + Gateway 真实 schema 校验**（/tmp/task-0604-verify 独立 harness，真实 openclaw 2026.7.1-2 包的 `validateCronAddParams` 校验器，不触网、不改插件 node_modules）：
   - `[1] MODULE_LOAD_OK exports=n,r,t` —— 修复后完整 import 链加载成功
   - `[2] REGISTER_OK name=qqbot_remind` —— 工具注册冒烟通过
   - `[3] FIXED_CRON_VALID=true` / `FIXED_ONCE_VALID=true` —— 修复后 cron/一次性两种请求体均通过 Gateway 真实 schema
   - `[4] OLD_WRAPPED_VALID=false errors=must have required property 'name'; at root: unexpected property 'job'` —— 旧请求体被拒，错误与线上症状逐字一致（根因实锤）
   - `[5] OLD_ATMS_VALID=false errors=…unexpected property 'atMs'…` —— 旧 atMs 写法同样被拒（第二处修复必要）
   - `ALL_CHECKS_PASSED`（退出码 0）
3. **diff 审查**：`diff 备份 新文件` 仅上述 2 处映射改动，无无关变更。

## 5. 生效条件与重启说明（给主 agent）

- Gateway 进程内加载的仍是旧代码，**需重启 openclaw gateway 后修复才生效**（由主 agent/用户决定，本任务未重启）。
- 重启后建议冒烟：`qqbot_remind action=add time=5m content=...` 建一次性提醒 + `time="0 8 * * *"` 建 cron 提醒，再 `action=list` 确认任务出现。
- 回滚方式：`cp /root/.openclaw/extensions/qqbot/dist/tools-CeUI9pG-.js.bak-20260901 /root/.openclaw/extensions/qqbot/dist/tools-CeUI9pG-.js` 后再重启。
- 备注：插件 `node_modules/openclaw` 符号链接指向已卸载的 2026.6.11 store（预存问题，独立加载会 ERR_MODULE_NOT_FOUND），运行时经 gateway 进程内解析不受影响；未改动。验证 harness 留存于 /tmp/task-0604-verify/。

## 过程笔记（边查边写留档）

- 目标文件 18270 字节，可整读；已全文审读，定位 add 链路：`prepareRemindCronAction` → `buildOnceJob/buildCronJob`（产出 `{action:"add", job:{...}}`）→ `executeScheduledRemind` → `deps.callCron` → `callGatewayTool("cron.add", …, { job: params.job })`。
- Gateway schema 逐字段核验自 openclaw@2026.7.1-2 dist：CronAddParamsSchema（schema-BuOFpc7K.js:2547，additionalProperties:false）、CronScheduleSchema（2296）、CronPayloadSchema/cronAgentTurnPayloadSchema（2121/2327）、CronDeliveryAnnounceSchema+SharedProperties（2387/2422）、CronSessionTargetSchema/WakeModeSchema（2149/2156）；服务端 at 解析 cron-BXksovqf.js:166、cron.add 校验点 510–515；CLI 平铺佐证 cron-tool-C9qaFGtt.js:1025。
