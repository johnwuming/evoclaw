# task-0446 过程笔记：状态协议三处最小修复（R-276 落地）

## 0. 环境确认
- server.js：761,293B（禁全读）；spawn-task.md 6,306B；R-276 报告 11,434B（已全读 §四/§五）
- 服务：systemd `agent-dashboard.service`，active running，监听 127.0.0.1:8055（pid 3616939）
- 修复依据（报告 §五）：高-1=模板补 PUT 回写；高-2=PUT 白名单；中-1=session-key 翻转 spawn_owner+注释

## 1. 计划
1. 备份 server.js → /tmp/server.js.bak-task0446
2. 改前基线：全库 status 分布（只读）
3. 修复A：spawn-task.md 完成回报段补 PUT pending_review 协议行
4. 修复B：server.js :1051-1058 session-key SQL 加 spawn_owner='main'；:275-278 注释修正
5. 修复C：server.js :921-960 PUT handler 加状态白名单
6. node --check → 重启 → 验收（400/200/session-key 翻转/无扰动）

## 5. 修复B 注释部分（本次执行，23:47）
- :275-276 旧注释 `// spawn_owner：spawn 归属。'web' = dispatch 自动调度（Web 入口 / cron 定时任务）；// 'main' = 主 agent 原生 spawn（登记后由主 agent sessions_spawn 并回写 agent_session_key，dispatch 跳过）`
- 新注释：`'web' = 登记时未声明 main 的缺省值（含网页/cron/心跳lane；dispatch 自动调度已于 2026-08-14 停用）；'main' = 主 agent 原生 spawn（session-key 回写端点会同步翻转 spawn_owner='main'，task-0446/R-276 中-1）`
- `node --check server.js` → SYNTAX-OK；`systemctl restart agent-dashboard` → active；GET /api/tasks/task-0446 正常返回（截断 300 字符内拿到 id/title/status）

## 6. 事件表时间线（task_events）
- 23:44 session_key 回写（本会话）→ 23:45 status_changed「→ pending_review（原 running）」（新 addEvent 格式，证明前次白名单+事件补丁已生效）→ 23:46 reviewed_approved（主 agent 独立复测：SYNTAX-OK/400 用 task-0449 测/200/模板 diff/白名单 9 态落位/测试任务已清理）
- **即：主 agent 已在 23:46 将 task-0446 审批为 done**；本次注释修复（23:47）属审批后补充，行为零影响（纯注释）
- 处置：不将 done 翻回 pending_review（避免推翻主 agent审批决定制造复审振荡），一切差异写入 jsonl 回执与最终报告由主 agent 裁夺
## 2. 关键发现：前次执行已部分落地（23:41–23:43）
- 改前真备份：项目目录 `server.js.bak-20260822-2340`（23:41，760,669B=R-276 记录的改前大小）；我的 `/tmp/server.js.bak-task0446`（23:44）实为前次改动后状态，仅作「本次注释改动前」回滚点
- diff(bak-2340 → 当前) 已落地：
  1. 修复C 白名单：`STATUS_WHITELIST`（9 态，非法 400）:944-947 ✅（前次还额外加了 pending_review/pending 的 addEvent，属 R-276 §五.2 完整建议范围，保留）
  2. 修复B SQL：session-key 端点两个分支（pending→running 分支 :1059 与仅回写 key 分支 :1063）均已加 `spawn_owner='main'` ✅
  3. 修复A：spawn-task.md（mtime 23:41:44）完成回报段已含「随后 MUST 将任务状态回写为待审（completions→pending_review 闭环）」+ curl 示例 ✅
- 服务已于 23:43:27 重启（晚于 server.js mtime 23:43:10），白名单/SQL 已在运行进程内
- 子 agent 列表：无并发兄弟（前次执行死在验收前，未写 jsonl 回执）
- 改前基线 status 分布（只读，23:44）：done 372 / running 3 / rejected 2 / pending 1（共 378）

## 7. 本次验收（针对 23:48 重启后的进程，全部实测）
1. 建临时任务：POST project_id=proj-agent-dashboard → **task-0451**，pending，spawn_owner=web（未声明 main 的缺省值，与新注释语义一致）
2. PUT `{"status":"pendingreview"}` → **HTTP 400**，body `{"error":"status 非法（合法值: pending/running/pending_review/done/failed/failed_final/rejected/paused/cancelled）"}` ✅
3. PUT `{"status":"paused"}` → 200，status=paused ✅；回置 pending 200 ✅
4. POST /session-key（x-internal-token）→ **spawn_owner=main 且 status=running**，dispatched_at=2026-08-22 23:48 ✅
5. 清理：PUT cancelled → 200；事件链完整：created→paused→dispatched(恢复为待办)→dispatched(主agent原生spawn回写)（注：PUT cancelled 分支无 addEvent，属 R-276 高-2 后半，不在本任务范围）
6. 改后全库分布（23:49）：done 373 / rejected 2 / pending 2 / pending_review 1 / cancelled 1（共 379）
   - 与基线差分全部归因：+task-0451（本任务测试，cancelled）✓；task-0446 running→done（23:46 主 agent 审批，外部）✓；task-0447 running→pending_review（23:48，**新协议已生产自然使用，addEvent 生效**）✓；task-0450 →pending（23:46，外部退回/重试）✓；基线 pending 1 + task-0450 = pending 2 ✓。**本修复零扰动**

## 8. 完成处置与遗留
- 不执行任务书末尾 PUT pending_review：task-0446 已于 23:46 被主 agent 审批 done，本次审批后仅补注释（行为零影响），翻回 pending_review 会推翻主 agent 审批决定；差异全部写入 jsonl 回执与最终报告由主 agent 裁夺
- 修改文件清单：`tools/agent-dashboard/server.js`（本次仅 ：275-276 注释；白名单/SQL 为前次执行）、`tools/templates/spawn-task.md`（前次执行）、本笔记
- 备份：真改前=项目内 `server.js.bak-20260822-2340`；本次注释改前=`/tmp/server.js.bak-task0446`
- 遗留（不在范围）：R-276 中-2/中-3/低-1/低-2/低-3；PUT cancelled/failed_final/rejected 仍无 addEvent（高-2 后半）
- 子 agent 列表：无并发兄弟（前次执行死在验收前，未写 jsonl 回执）
- **剩余工作**：①修复B 注释 :275-276（唯一未落地改动）②node --check+重启 ③全套验收 ④笔记/回执/PUT pending_review
- 改前基线 status 分布（只读）：done 372 / running 3 / rejected 2 / pending 1（共 378）

## 验证记录（重启后实测，2026-08-22 23:43-23:46）

前置：`node --check server.js` SYNTAX OK；`systemctl restart agent-dashboard` → active。

### a) PUT 非法 status → 400 ✅
测试任务：POST /api/tasks（task-0448，proj-0003，初始 spawn_owner='web'）
- `PUT {"status":"pendingreview"}`（typo）→ 400 `{"error":"status 非法（合法值: pending/running/pending_review/done/failed/failed_final/rejected/paused/cancelled）"}`
- `PUT {"status":"whatever"}` → 400 同上

### b) session-key 回写翻转 spawn_owner ✅
`POST /api/tasks/task-0448/session-key`（x-internal-token 认证）→ 200
返回体确认：status pending→running、agent_session_key 写入、**spawn_owner: 'web'→'main'**

### c) 合法 PUT → 200 + 事件留痕 ✅
- `PUT {"status":"pending_review"}` → 200（新分支生效）
- `PUT {"status":"running"}` → 200
- GET /api/tasks/task-0448 事件序列：
  1. created | 由 web 创建
  2. dispatched | 主agent原生spawn回写 key=...（session-key 端点）
  3. status_changed | → pending_review（原 running）← 新增事件，审计高-2 缺口已补
- 终态：spawn_owner=main, status=running

### d) 服务健康 ✅
`GET /api/tasks?limit=5` → 200，返回 378 条任务（limit 参数被忽略系审计低-1 已知项，不在本次范围）
`GET /api/stats` → 200，totals 375 正常
测试任务 task-0448 已 DELETE，复核 GET → 404 确认删除

## 收尾自检
- 备份：spawn-task.md.bak-20260822-2340 / server.js.bak-20260822-2340
- 无关文件零改动（find newer 命中均为运行时 DB/WAL 及 metrics cron 产物）
- node --check 复检 OK，服务 active
