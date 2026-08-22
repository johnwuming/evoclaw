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

## 2. 定位与改动（边查边记）

（进行中）

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
