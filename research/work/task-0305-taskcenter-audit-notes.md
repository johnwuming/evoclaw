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

---

## Step 2 调研笔记：前端任务 Tab（server.js 内嵌 HTML/JS，L5483-8060）

- **任务 Tab 已只读化（task-0283）**：L7131-7138 注释明确"仅保留状态徽章与概要展开，不提供任何行内操作按钮"。`actions` 变量只剩状态徽章 + done 任务的"概要"折叠按钮。
- **无新建任务表单**：grep `newTaskBtn|taskForm|showNewTask|创建任务|新建任务` 全部 0 命中 → **web 登记入口已经物理删除**（用户判断①的前提已成立）。
- **无任务详情弹窗**：只有 agent-detail-modal（L6207）；前端不调 `GET /api/tasks/:id`（grep 0 命中）→ **详情端点无前端消费者**。
- **前端唯一任务请求**：`loadTasks()`（L7032）→ `GET /api/tasks?project_id=&status=`。看板 6 列（L7060-7070）：pending / running(含failed) / pending_review / rejected / failed_final / done。
- 状态过滤下拉（L6173-6184）含 pending_review 选项；TASK_STATUS 标签全集（L6361）9 态：pending/running/done/failed/paused/cancelled/pending_review/rejected/failed_final。
- `del(p)` 助手（L6349）定义后无任何任务相关调用（前端对任务零写操作）。
- 告警 tab 消费 `GET /api/alerts/active`（L10614），alert 引擎间接读任务表（见 Step 5）。
- 邻域发现（超出任务域但相关）：Agents tab（/api/agents L1571-1618）仍按旧固定团队（TEAMS L1564-1569：research/quant/dev/ops + 旧 agent 名单）分组，从 tasks.assigned_agent 推导 running——v4 子 agent 是匿名原生的，此 tab 展示语义已过时。

## Step 3 调研笔记：dispatch.js 存在性与引用

- **文件仍在**：`dispatch.js` 19KB（8月14日 21:12 改，task-0265 双入口版），另有 `dispatch.js.bak-task0265-20260814`、`dispatch.log` 17.8MB（最后写入 **8-15 13:36**，与"8-15 停用"吻合）。
- **crontab 已无 dispatch.js 条目**（root crontab 仅 5 条：stargate / backup / collect-metrics */1min / pull-hp-metrics */2min / auto_sync_notify */30min+每日3点）→ **孤儿文件，无任何定时触发**。
- **server.js 无内嵌调度定时器**：全部 setInterval（L267/1699/1848/1918/1970/4151/5442）是 metrics/quota/告警/快照，无一个调 dispatchPendingTasks；它唯一调用点是 POST /internal/dispatch（L1308）。
- **/internal/dispatch 调用方**：全 workspace grep 仅 ①dispatch.js 自身（processPendingReview L355-365，已死）②AGENTS.md 文档提及 → **无人调用，死端点**。
- dispatch.js 五大职责现状：processCompletions（完成回报→pending_review + 写通知 L218-220）— 死；detectEndedSessions（死会话→pending_review/failed）— 死，被 HEARTBEAT Step 2b 人工替代；retryFailed — 死；团队串行 — 死；触发 /internal/dispatch — 死。
- **连带后果（重要）**：现在**没有任何程序自动把任务置 pending_review**——主 agent 靠自己 PUT status=pending_review（或审 HEARTBEAT Step 2 列表）；completions.jsonl 也没有自动消费方（原 consumeCompletionFor 已死），文件只增不减（当前 27 行 25KB）。

## Step 4 调研笔记：crontab / systemd 关联

- crontab 与任务中心相关条目：**无**（dispatch、task-monitor 均已无条目）。量化 auto_sync_notify */30min 与每日 03:00 full-sync 直写 .task-notifications.jsonl（脚本 L51 默认路径确认）——这是通知队列现存的唯一外部写入方。
- systemd：agent-dashboard.service active running（server.js 宿主）；无 dispatch 相关 unit。
- /api/tasks/:id/dispatch 与 /retry 的实际行为：纯改 DB 状态（置 pending），不再写队列文件（writeDispatchQueue 已不被调用，见 Step 6），也无后续调度 → **点了只会让任务永远卡在 pending（静默死单）**。实例：task-0296（13:10 登记，spawn_owner=web，仅 created 事件，至今 pending 无人接手）。

## Step 5 调研笔记：tasks.db 表结构与在用消费者

- **tasks 表 28 列**（.schema 全文见上）：v4 真正在用子集 = id/project_id/title/type/status/priority/expected_output/task_prompt/notes/created_at/updated_at/dispatched_at/completed_at/completion_summary/review_summary/agent_session_key/spawn_owner(弱化)/source_session/created_by(失真)。
- **task_events 子表**：addEvent（L357-360）在 created/dispatched/completed/failed/paused/retried/reviewed_approved/reviewed_rejected/session_key/pending_review(dispatch死前) 全链路写；**前端不展示 events**（grep 无 .events 消费）→ 纯审计留痕（GET /api/tasks/:id 返回但无人调）。
- 状态分布（243 任务）：done 240 / pending 2 / running 1——**failed/paused/cancelled/pending_review/rejected/failed_final 当前 0 条**，后六态的产生路径只剩 PUT 手动改 + 死代码。
- 字段死活（按非空计数）：schedule_window **0**（全死）、spawn_config **0**（全死）、assigned_agent 210 条全为历史（近期全 NULL）、parent_task_id 1 / version 3（历史残留）、retry_count>0 共 7 条（全历史）。
- spawn_owner 现状失真：近期主 agent 登记的任务一半是 'web' 一半 'main'（task-0307=我登记为 web）→ 该字段已无可靠语义，且唯一消费者（死调度循环按 spawn_owner='web' 过滤）已死。
- created_by 失真：鉴权已整体禁用（L571 注释掉 app.use(authenticate)），req.user 恒空 → 一律落 'web'。近期 235 条 created_by 全 'web'。
- **alert 引擎是任务表的活跃读者**（L3977-4158，每 2min）：running>30min → task_timeout critical（依赖 dispatched_at）；retry_count≥2 → task_retry warning（依赖 retry_count）；任务终态（done/cancelled/failed_final/rejected）自动 resolve。**删字段前必须照顾它**。
- /api/stats（L1621-1639）统计含 paused/cancelled 列——两态已无生产者，统计恒 0。
- 一次性迁移残留：importHeartbeat/seedAgents 仅在 agent_status 空表时跑（L453-457），现已休眠，可留可删。

## Step 6 调研笔记：.task-* 文件链路

- `.task-notifications.jsonl`（当前 0 字节，活跃）：写入方 ①/internal/review（approved/rejected，带 source_session，task-0300）②量化 auto_sync_notify.py（格式 {task_id,timestamp,message,files}，**无 source_session 字段**）③(dispatch.js 已死)。消费方：HEARTBEAT.md Step 0（cat → 按 source_session 路由 → 微信/当前对话 → 清空文件）。**队列机制本身健康在用**。
- `.task-completions.jsonl`（27 行 25KB，仍在增写）：写入方=各子 agent spawn prompt 强制要求（AGENTS.md 模板 L332）；消费方 ①主 agent 审核参考+死亡恢复点（AGENTS.md L279）②~~dispatch.js processCompletions~~（已死）。无自动清理 → 缓慢无限增长（量级：每任务 1 行 ~1KB，可控）。
- `.task-completions.jsonl.tmp`（8-10 残留）：垃圾，可删。
- `.task-center-internal-token`：/internal/* 鉴权 + review-task.sh + HEARTBEAT Step 2 curl 均用 → **核心保留**。
- `.task-dispatch-queue.jsonl`：文件已删；server.js 仍残留 DISPATCH_QUEUE 常量（L113）与 writeDispatchQueue 函数（L363-379，**定义后零调用**）——死代码；docs（V4-DESIGN.md、security-audit.md）里的引用是过时文档。

## Step 7 调研笔记：调用方全景（谁还在打任务 API）

- **主 agent（活跃，v4 核心）**：POST /api/tasks 登记（AGENTS.md v4 流程）→ PUT /api/tasks/:id 置 running / 置 pending_review → POST /api/tasks/:id/session-key 回写 key → GET /api/tasks?status=pending_review|running（HEARTBEAT Step 2/2b）→ POST /internal/review（HEARTBEAT Step 2 + scripts/review-task.sh 封装）。
- **前端（活跃）**：GET /api/tasks（列表+过滤）+ /api/stats + /api/agents + /api/alerts/active。零写操作。
- **量化 cron（活跃）**：auto_sync_notify.py 只写通知文件，不碰任务 API。
- **无人调用**：POST /api/tasks/:id/dispatch、POST /api/tasks/:id/pause、POST /api/tasks/:id/retry、DELETE /api/tasks/:id、GET /api/tasks/:id、POST /internal/dispatch。

---

# ══════════ 正式报告（task-0307 交付）══════════

# 任务中心功能全景与新架构（v4）冗余改造方案

调研范围：agent-dashboard 任务域（server.js L805-1400 端点 + L1009-1313 调度引擎 + 前端任务 Tab + dispatch.js + crontab/systemd + tasks.db + .task-* 文件链路）。只读调研，未改任何生产文件。

## 1. 功能全景表

### 1.1 API 端点（12 个）

| # | 端点 | 行号 | 逻辑摘要 | 现状 | 调用方 | v4 判定 |
|---|------|------|---------|------|--------|---------|
| 1 | GET /api/tasks | L809-836 | 列表+project/status/type 过滤，剔大字段，算 runtime_min | 在用 | 前端看板、主agent心跳 Step2/2b | **核心保留** |
| 2 | GET /api/tasks/:id | L838-850 | 详情+events 历史 | 在用但无人调 | 无（前端0命中） | 可选保留（调试用，成本≈0） |
| 3 | POST /api/tasks | L852-924 | 登记：R-编号防撞分配、spawn_owner、sourceSession 校验 | 在用 | **主 agent 唯一登记口** | **核心保留** |
| 4 | PUT /api/tasks/:id | L926-966 | 字段更新+状态流转（联动时间戳/事件） | 在用 | 主 agent（置 running/pending_review） | **核心保留** |
| 5 | POST /api/tasks/:id/session-key | L1372-1398 | spawn 胶水：pending→running+key 一步到位 | 在用 | 主 agent | **核心保留** |
| 6 | POST /internal/review | L1320-1368 | approve→done+review_summary+通知；reject→rejected+通知（带 source_session） | 在用 | 主 agent（HEARTBEAT Step2 + review-task.sh） | **核心保留**（通知写入可议，见 §3.3） |
| 7 | POST /api/tasks/:id/dispatch | L968-977 | 仅置 pending（队列写入已不发生） | **半死**：无前端按钮；置 pending 后无人拾取→静默死单 | 无人 | **作废** |
| 8 | POST /api/tasks/:id/retry | L979-988 | 置 pending + retry_count+1 | 同上，无自动重派 | 无人 | 作废（语义并入 PUT） |
| 9 | POST /api/tasks/:id/pause | L990-998 | 置 paused | PUT 已支持 status=paused，纯重复 | 无人 | 作废 |
| 10 | DELETE /api/tasks/:id | L1000-1005 | 删任务+事件 | 无按钮无脚本 | 无人 | 作废（或留作主agent清理口） |
| 11 | POST /internal/dispatch | L1306-1313 | 触发一次 dispatchPendingTasks 轮次 | **死**：唯一调用方 dispatch.js 已无 crontab | 无人 | **作废** |
| 12 | （R-126 调度引擎） | L1009-1313 | SPAWN_TEAMS 旧名单、buildSpawnPrompt、CLI/gateway 双路 spawn、团队串行、failed_final 状态机 | **死代码**：无定时器、无外部调用 | 无人 | **作废**（约 300 行） |

### 1.2 前端任务 Tab

| 元素 | 行号 | 现状 | v4 判定 |
|------|------|------|---------|
| 任务看板 6 列 | L7060-7070 | 在用（只读） | 核心保留（v4 定位=登记簿/进度看板） |
| 状态过滤/项目过滤 | L6172-6184 | 在用 | 保留 |
| 任务卡操作按钮 | L7131-7138 | **task-0283 已只读化**，无任何操作按钮 | 已完成裁剪 ✓ |
| 新建任务表单 | — | **已物理删除**（grep 0 命中） | 已完成 ✓ |
| 任务详情弹窗/events 展示 | — | 不存在（前端不调 /api/tasks/:id） | events=纯审计留痕 |
| Agents tab | L1564-1618 | 在用但按旧固定团队分组，assigned_agent 近期全 NULL → 展示语义过时 | 邻域发现，可后置处理 |

### 1.3 文件链路

| 文件 | 写入方 | 消费方 | v4 判定 |
|------|--------|--------|---------|
| .task-notifications.jsonl | ①/internal/review（带 source_session）②量化 cron（无 source_session） | 心跳 Step 0（路由+清空） | **机制核心保留**；写入方可裁（见 §3.3） |
| .task-completions.jsonl | 子 agent（spawn prompt 强制） | 主 agent 审核+恢复点；（自动消费方已死） | 保留，降级为"参考性"（见 §3.2） |
| .task-center-internal-token | 人工 | /internal/* 鉴权 + review-task.sh | 核心保留 |
| .task-dispatch-queue.jsonl | 已删（server.js 残留常量 L113+死函数 writeDispatchQueue L363-379） | — | 死代码清除 |
| .task-completions.jsonl.tmp | 8-10 残留 | — | 垃圾删除 |
| dispatch.js（19KB） | — | 无（crontab 已移除，dispatch.log 止于 8-15 13:36） | 作废删除 |
| dispatch.log（17.8MB） | — | — | 归档/删除 |

### 1.4 定时器/cron

| 条目 | 频率 | 与任务中心关系 | 判定 |
|------|------|---------------|------|
| agent-dashboard.service（systemd） | 常驻 | server.js 宿主 | 核心 |
| collect-metrics / pull-hp-metrics（cron） | 1min/2min | metrics 域，非任务域（不动） | 保留（域外） |
| auto_sync_notify.py（cron） | 30min + 每日3点 | 写通知队列 | **核心保留** |
| alert 引擎（server.js 内 setInterval 2min） | 2min | 读 tasks.status/dispatched_at/retry_count → 告警 + 自动 resolve | 保留（注意 §5 字段约束） |
| ~~dispatch.js cron~~ / ~~task-monitor~~ | — | 已移除 | 已完成 ✓ |

## 2. 作废清单（可安全删，逐项证据）

1. **dispatch.js + dispatch.js.bak + dispatch.log**：crontab 0 条目（Step 4 实查），日志止于 8-15 13:36；五大职责全部由主 agent 人工流程替代（HEARTBEAT Step 2/2b）。影响面：无——删除后无任何定时器/端点受影响。
2. **R-126 调度引擎（server.js L1009-1313）**：dispatchPendingTasks 唯一调用点 L1308（/internal/dispatch）；/internal/dispatch 全 workspace 调用方=已死的 dispatch.js；server.js 内无定时器调它（Step 3 grep 全量 setInterval 核对）。删 300 行。
3. **POST /api/tasks/:id/dispatch（L968-977）**：注释声称"写 dispatch 队列"但 writeDispatchQueue 零调用（L363 定义后无人引用）；实际效果=置 pending 无人拾取（实证 task-0296 卡死）。前端无按钮（task-0283 只读化）。
4. **POST /api/tasks/:id/pause（L990-998）**：PUT status=paused 完全覆盖；前端无按钮；当前 0 条 paused 任务。
5. **writeDispatchQueue 函数 + DISPATCH_QUEUE 常量（L363-379, L113）**：死函数，队列文件本身已删。
6. **.task-completions.jsonl.tmp**：8-10 的残留临时文件。
7. **过时文档**：V4-DESIGN.md（描述 dispatch 队列架构）、docs/security-audit.md L64/L247（引用已删文件与旧行号）——更新或标注归档。

**不建议物理删列**（SQLite 列保留、仅停止写入/接受）：schedule_window（0/243 非空）、spawn_config（0/243）、parent_task_id（1）、version（3）——历史数据在列里，DROP COLUMN 得不偿失。

## 3. 简化方案（可保留但该改）

### 3.1 端点收敛（6+1 → 5+1）
- 删 dispatch/pause 两个作废端点；retry 语义（重置 pending）并入 PUT；DELETE 若主 agent 需要清理口可留，否则删。
- PUT 字段白名单（L932）裁掉 spawn_config/schedule_window/max_retries/parent_task_id/version；POST 同步（L913-916）。
- **created_by 修正**：鉴权禁用导致恒为 'web'（235/235 失真）。要么 POST 接受显式 created_by（主 agent 传 'main'），要么把默认值改 'main-agent'——一行改动，审计价值大。
- **spawn_owner 退役**：近期登记 main/web 混乱无语义，且唯一消费者（死调度循环）已删。POST 可默认 main，PUT 白名单移除，列保留。
- **assigned_agent**：v4 子 agent 匿名，建议 POST 不再接受（或仅作展示标签）；但 /api/agents 与 alert 引擎以它为 key——若 Agents tab 后置不改，则此字段留作可选展示。

### 3.2 completions.jsonl 降级为可选
- 现状：无自动消费（dispatch.js 死），唯一价值=主 agent 审核参考+死亡恢复点+spawn prompt 的"完成回报"纪律锚。
- 方案：**保留机制、明确为可选**——spawn prompt 里继续要求写（成本低、有恢复价值），主 agent 不再依赖它做状态流转；加一条简单轮转（如 >500 行归档）或在心跳闲时清理已完结任务的行。不做也行（27 行/月量级）。

### 3.3 通知队列写入方裁剪（用户判断③落地）
- /internal/review 的 approved/rejected 通知写入（L1338-1348、L1358-1368）：主 agent 审核完**当轮就会**按 AGENTS.md 向用户汇报（带 task-XXXX），通知条目要到下一次心跳才被消费——大概率变成"重复告知"或空转。**建议砍掉这两处 append**（或仅在 summary 里带 source_session 且主 agent 预期跨渠道转述时写）。
- **量化 cron 写入必须保留**：auto_sync_notify.py 是队列现存的独立价值（HP 侧无人格化 agent，只能靠文件+心跳接力）。
- 心跳 Step 0 逻辑不动（文件仍在，只是条目变少）。

### 3.4 状态机收紧
- 现行 9 态枚举中，failed/paused/cancelled/failed_final 四态在 v4 下已无自然产生路径（生产者全是死代码或无人调端点）。建议：TASK_STATUS 标签与 /api/stats 保留枚举（历史任务要渲染），但文档明确 v4 有效态=**pending → running → pending_review → done/rejected**（rejected→pending 重开走 PUT）。
- retry_count：alert 引擎有 task_retry 告警读它（L4079-4082）——要么保留列+告警（无害，恒0），要么连告警分支一起清。建议保留（未来主 agent 重派时可自增）。

## 4. 保留核心（v4 最小集）

**API 面（5 个）**：
1. `POST /api/tasks` — 登记（含 R-编号分配 + sourceSession）
2. `GET /api/tasks`（+过滤）— 看板 + 心跳 Step2/2b
3. `PUT /api/tasks/:id` — 状态流转与字段更新（唯一状态写口）
4. `POST /api/tasks/:id/session-key` — spawn 胶水（pending→running+key 一步到位）
5. `POST /internal/review` — 审核写口（token 鉴权）

**辅助（可选）**：GET /api/tasks/:id（调试）、addEvent/task_events（审计留痕，写不展示）、DELETE /api/tasks/:id（清理口，可选）。

**文件**：.task-notifications.jsonl（量化 cron→心跳接力）+ .task-completions.jsonl（可选参考）+ .task-center-internal-token。

**流程闭环**：登记(1) → spawn 后回写(4) → 子 agent 完成 → 主 agent 审核列表(2) → PUT pending_review → /internal/review(5) done/rejected → 看板(2)。全部现行链路不受影响。

## 5. 改造风险与顺序

**顺序（风险递增）**：
- **P0（零风险，随时）**：删 dispatch.js/bak、归档 dispatch.log、删 .tmp、清 V4-DESIGN 等过时文档标注。纯孤儿文件。
- **P1（低风险，一次 systemd restart）**：删 server.js 死代码——writeDispatchQueue+常量、R-126 引擎 L1009-1313（含 /internal/dispatch）、dispatch/pause 端点。重启前 grep 确认无引用；重启后验证：`curl /api/tasks`（看板）、心跳 Step 2 curl、review-task.sh 试跑（GET 类验证）。
- **P2（低风险）**：/internal/review 砍通知写入（§3.3）；PUT/POST 字段白名单裁剪；created_by 修正。
- **P3（可选）**：completions 轮转、Agents tab 重构（按 session 而非旧团队）、spawn_owner 退役。
- **P4（善后）**：task-0296 孤儿任务处置——需主 agent 决策（接手重派 or 标 cancelled 归档，这是当前唯一卡 pending 的真实死单案例）。

**风险红线（动=破坏现行循环）**：
- PUT /api/tasks/:id 的状态联动逻辑（L947-958）——主 agent 调度循环主干。
- /internal/review 的 token 鉴权与字段名（decision 不是 action，HEARTBEAT 有专门提醒）。
- 通知文件路径与心跳 Step 0 的 cat/清空约定。
- alert 引擎读的 tasks 列：status/dispatched_at/retry_count/assigned_agent——P2 裁字段时**不要**从表里删列。
- 前端看板 6 列渲染对 status 枚举的依赖——保留 TASK_STATUS 全集。

## 6. 用户三个判断的核实结论

1. **web 登记入口可关 → 已经关了**：前端新建任务表单在 task-0283（8-15）只读化时已物理删除（grep 零命中），任务卡无任何操作按钮。无需再动前端。POST /api/tasks 不是"web 入口"而是主 agent 的登记 API，**必须保留**。
2. **/internal/review 是主 agent 审核写口（保留）→ 属实**：HEARTBEAT.md Step 2 + scripts/review-task.sh 双路径依赖；是唯一能写 done/rejected+review_summary 的入口（PUT 也能改 status 但绕过了事件与通知语义）。保留，仅其通知写入可按 §3.3 裁剪。
3. **任务类审核通知冗余可砍 → 成立**：主 agent 审核当轮即自行汇报用户（AGENTS.md 铁律"通知必带 task-XXXX"），审核通知隔心跳才消费=重复/空转；source_session 路由价值在"跨渠道回话"场景，主 agent 审核时本就在具备上下文的会话里，边际价值低。**砍 /internal/review 两处 append 即可；量化 cron 通知（auto_sync_notify）必须保留**——那是通知队列现存的独立价值（30min 周期例报 + HP 队列转发）。

---

*报告完。调研只读未动生产文件；所有结论附行号可复核。*
