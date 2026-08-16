# task-0307 任务中心功能全景梳理 + 新架构冗余改造方案调研

> 调研时间：2026-08-16 14:09 起。调研者：subagent（task-0307）。
> 对象：/root/.openclaw/workspace/tools/agent-dashboard/server.js（11262 行，端口 8055）任务域功能。
> 架构背景：v4（2026-08-15 起）主 agent 自己登记/自己 spawn/自己审核/自己汇报；dispatch.js 自动调度已停用；task-monitor.sh 已删。
> 本文件边查边写，作为恢复点。

## 状态记录（边查边更新）

- [x] Step 1: server.js 任务域 API 端点代码逻辑（L805-L1400 全段已读）
- [ ] Step 2: 前端任务 Tab 按钮
- [ ] Step 3: dispatch.js 存在性 + 引用排查
- [ ] Step 4: crontab 关联条目
- [ ] Step 5: tasks.db 表结构
- [ ] Step 6: .task-* 文件链路
- [ ] Step 7: 调用方排查（主 agent 脚本/心跳模板里 grep API 路径）
- [ ] Step 8: 汇总功能全景表 + 作废清单 + 简化方案 + 最小集 + 风险

---

## Step 1 调研笔记：server.js 任务域 API 端点（L805-L1400）

### 1.1 GET /api/tasks（L809-L836）— 列表
- 支持 ?project_id / ?status / ?type 过滤，按 created_at DESC。
- 性能优化（task-0256）：列表剔除 task_prompt / spawn_config / parent_task_id 大字段。
- running 任务计算 runtime_min（基于 dispatched_at）。
- **判定：在用，核心**（Dashboard 看板渲染 + 主 agent 可能查列表）。

### 1.2 GET /api/tasks/:id（L838-L850）— 详情
- 返回完整 task + events（eventsByTask 预编译查询 → task_events 子表）。
- **判定：在用，核心**（前端详情弹窗用）。

### 1.3 POST /api/tasks（L852-L924）— 创建/登记
- 必填 project_id + title；type 默认 dev。
- R-编号自动分配：research 类型扫描已有报告文件 + tasks.db 未完结任务占号，防撞号（含手工指定 R-xxx 时撞号自动改号）。**这段逻辑重要，v4 仍在用（主 agent 登记研究任务时自动分号）**。
- task-0265 双入口：spawn_owner=main → 主 agent 原生 spawn（dispatch 跳过）；其余 → web（dispatch 自动调度）。
- task-0300：可选 sourceSession 字段（≤200 字符，白名单字符校验）。
- 写入字段全集：id/project_id/version/title/type/status(pending)/priority/expected_output/assigned_agent/spawn_config/dispatched_at/completed_at/parent_task_id/retry_count(0)/max_retries(默认2)/schedule_window/notes/created_at/created_by/spawn_owner/updated_at/task_prompt/source_session。
- addEvent(id, 'created', ...) 写事件流。
- **判定：在用，核心**（v4 主 agent 登记唯一入口）。

### 1.4 PUT /api/tasks/:id（L926-L966）— 更新/状态流转
- 可更新 16 个字段（version/title/type/priority/expected_output/assigned_agent/spawn_config/parent_task_id/max_retries/schedule_window/notes/project_id/completion_summary/task_prompt/spawn_owner/source_session）。
- status 变更联动：running 且无 dispatched_at → 补 dispatched_at + 'dispatched' 事件；done → completed_at + 'completed' 事件；failed/paused → 对应事件；pending←paused → '恢复为待办' 事件。
- **判定：在用，核心**（主 agent PUT 改 running 的现行路径）。

### 1.5 POST /api/tasks/:id/dispatch（L968-L977）— "提交执行"
- 逻辑：status 置回 **pending** + addEvent 'dispatched 提交到队列'。注释说"写入 dispatch 队列"，但队队列文件 .task-dispatch-queue.jsonl 已删（task-monitor 残留），**现在只是把状态改 pending**。
- 若无人再跑 dispatch 轮询（dispatch.js 停用、无内嵌定时器——待 Step 3/4 确认 server.js 内是否有 setInterval 调 dispatchPendingTasks），则任务永远停在 pending → **静默死单**。
- **判定：疑似死按钮/死端点**（待确认 server.js 是否有内嵌定时轮询）。

### 1.6 POST /api/tasks/:id/retry（L979-L988）— 重试
- status→pending + retry_count+1 + 清 dispatched_at/completed_at + 'retried' 事件。
- 依赖后续调度轮次才会真正重派 → 与 dispatch 同理疑似死端点（重置状态本身可用作"重开"）。
- **判定：可简化**（保留"重置为 pending"语义，但不再有自动重派）。

### 1.7 POST /api/tasks/:id/pause（L990-L998）— 暂停
- status→paused + 事件。v4 下主 agent 自己控制状态，暂停按钮用户已不用。
- **判定：冗余可裁（或降级为 PUT status 的别名，实际上 PUT 已支持 status=paused，纯重复）**。

### 1.8 DELETE /api/tasks/:id（L1000-L1005）— 删除
- 删 task_events + tasks 两行。无级联风险（无外键依赖方向其他表）。
- **判定：在用（用户清理旧任务？待查前端按钮）。低风险。**

### 1.9 任务中枢编排段（L1009-L1300）— R-126 旧调度引擎
- 常量：OPENCLAW_CONFIG_PATH、GATEWAY_BASE_URL(localhost:12145)、COMPLETIONS_FILE_R126(.task-completions.jsonl)、NOTIFY_FILE(.task-notifications.jsonl)、SPAWN_MAX_FAILURES=3。
- **SPAWN_TEAMS 硬编码旧团队成员名单**：research(research-lead/searcher/reviewer/citation)、dev(claude-code-local/claude)、quant(quant-compute)、ops(main)。v4 已无固定团队 → **死名单**。
- buildSpawnPrompt(task)：按 assigned_agent 选角色模板（quant/research/ACP Claude Code），末尾注入 completions.jsonl 回报指令。
- spawnAgentViaCLI(task)：**dev 团队走 openclaw cron add --agent claude --at +1m**（ACP 老路径，v4 已停）。
- spawnAgentViaGateway(task)：POST gateway /tools/invoke sessions_spawn（research/quant 用）。
- dispatchPendingTasks()（L1219-L1300）：团队串行控制（busyTeams）、每团队每轮至多 1 个、**只调度 spawn_owner='web' 的任务**（跳过 main 的会打日志）、spawn 成功→running+agent_session_key、失败 retry_count++ → ≥3 次 failed_final、429 不计数。
- isDispatching 进程内互斥锁。
- **关键问题：这段代码只在 POST /internal/dispatch 被调时执行。若无 cron/心跳再调 /internal/dispatch，则整段为死代码（无人触发）。待 Step 4/7 确认。**

### 1.10 POST /internal/dispatch（L1306-L1313）
- requireInternalAuth（X-Internal-Token，读 scripts/.task-center-internal-token）。
- 触发一次 dispatchPendingTasks() 轮次。
- 注释称"由 dispatch.js 的 processPendingReview() 或主 agent 心跳调用"。
- **判定：待查调用方；疑似死端点（v4 主 agent 自己 spawn，不该再调它）**。

### 1.11 POST /internal/review（L1320-L1368）— 审核
- requireInternalAuth。body: {taskId, decision: approve|reject, summary}。
- approve → status=done + review_summary + completed_at + 'reviewed_approved' 事件 + **写通知队列 NOTIFY_FILE**（含 task-0300 source_session 供路由）。
- reject → status=rejected + review_summary + 'reviewed_rejected' 事件 + 也写通知队列。
- **判定：在用，核心**（v4 主 agent 审核唯一写入口——用户判断②成立，待 Step 7 确认无其他写 done 路径被依赖）。
- 通知队列写入：任务审核通知（approved/rejected）+ 量化 cron（auto_sync_notify.py）是两个写入方。用户判断③：任务类审核通知是否冗余可砍——主 agent 审核完自己就要去向用户汇报（用自己的话+task-XXXX），队列里的审核通知对主 agent 是"自己写给自己的备忘"，仅当心跳错峰消费时有价值；量化例报必须保留。

### 1.12 POST /api/tasks/:id/session-key（L1372-L1398）— sessionKey 回写胶水
- requireInternalAuth。pending → 置 running + dispatched_at + 回写 agent_session_key；其他状态仅回写 key。
- task-0265 产物：主 agent 原生 spawn 成功后回写。
- **判定：v4 核心辅助**（主 agent spawn 后回写，看板能看到 key；若主 agent 已改用 PUT status=running 则可能重复，但此端点一步到位含 key，保留合理）。
