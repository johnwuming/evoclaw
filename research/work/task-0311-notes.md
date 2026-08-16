# task-0311 任务中心瘦身笔记

## 基线（2026-08-16 15:47）
- server.js: 11531 行 / 595778 字节
- 主 agent 确认：零 running 任务，死代码健在

## P0 孤儿文件
- [x] 15:48 dispatch.js → /root/backups/dispatch.js.task0311 (19238B, mv 成功)
- [x] 15:49 rm dispatch.log (17875509B=17.8MB) + dispatch.log.* + *.tmp
  - 未删 dispatch.js.bak-task0265-20260814（不在任务书范围，保留）

## P1 死代码删除（server.js 11531 → 11212 行，-319 行）
- [x] 备份 server.js.bak-task0311-20260816 (595778B)
- [x] 删 writeDispatchQueue(362-378) + DISPATCH_QUEUE 常量(L113)
- [x] 删 POST /api/tasks/:id/dispatch(975-985) 与 /pause(997-1006)
- [x] 删 R-126 引擎块：头注释1014-1022、COMPLETIONS_FILE_R126(1029)、SPAWN_MAX_FAILURES/RESEARCH_AGENTS/QUANT_AGENTS/SPAWN_TEAMS(1031-1041)、isResearchAgent/isQuantAgent/spawnTeamOf/buildSpawnPrompt/pickSessionKey/extractSessionKey/spawnAgentViaCLI/spawnAgentViaGateway/spawnAgent/dispatchPendingTasks(1055-1301)、调度注释(1302-1303)、POST /internal/dispatch(1314-1322)
- 保留（被块外引用）：OPENCLAW_CONFIG_PATH/BIN/PATH、GATEWAY_BASE_URL、NOTIFY_FILE、readGatewayToken(被abort会话用@3912)、requireInternalAuth、INTERNAL_TOKEN
- [x] grep 零残留：writeDispatchQueue/dispatchPendingTasks/SPAWN_TEAMS/buildSpawnQueue 等全部无匹配
- [x] node --check 通过

## P2 简化（同一份 server.js，未二次重启前完成）
- [x] /internal/review 两处 fs.appendFileSync(NOTIFY_FILE) 整块删除（approve/reject 分支各一处），状态更新+addEvent+鉴权+decision 校验原样保留；grep 'appendFileSync(NOTIFY_FILE' 计数=0
- [x] POST /api/tasks 白名单删 spawn_config/schedule_window/max_retries/parent_task_id/version（insertTask SQL 为迁移共用语句未动，POST 侧改硬编码默认 null/2）
- [x] PUT 白名单删同5项（保留 title/type/priority/expected_output/assigned_agent/notes/project_id/completion_summary/task_prompt/spawn_owner/source_session；status 走原有独立联动逻辑未动）
- [x] created_by INSERT 默认 'web' → 'main-agent'（req.user 缺省时）
- [x] retry 注释改"v4 重置 pending（主 agent 手动口，不再自动调度）"；DELETE 注释改"主 agent 清理口"
- [x] node --check 通过；11531 → 11189 行（P1+P2 合计 -342 行）
