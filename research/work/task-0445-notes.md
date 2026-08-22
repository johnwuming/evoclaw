# task-0445 三端一致性审计 · 过程笔记

时间：2026-08-22 23:28 起。只读审计，不改 server.js/HEARTBEAT.md/tasks.db。

## 文件清单与大小（2026-08-22 23:30 实测）
- tools/agent-dashboard/server.js: 760,669 B（禁止全读，grep+sed 分段）
- HEARTBEAT.md: 2,248 B（可全读）
- scripts/heartbeat.sh: 3,885 B（可全读）
- scripts/.task-completions.jsonl: 146,038 B（只 tail/grep）
- tools/agent-dashboard/dispatch.js.bak-task0265-20260814: 18,267 B（可全读）
- tools/agent-dashboard/tasks.db: 2,064,384 B（只读模式查询）

## 待查清单
1. 状态机定义（server.js status 分支、PUT 校验）
2. 各状态写入方
3. spawn_owner 语义与 DB 分布
4. agent_session_key 回写协议
5. 时间字段口径（completed_at/dispatched_at/updated_at）
6. completions→pending_review 同步链路（真空点重点）
7. HEARTBEAT 契约 1-7 条 vs server.js 状态机
8. 冲突清单

（以下按核验顺序追加结论）

## N1 状态机与写入方（行号均已核实）
- tasks.status 无 CHECK 约束（server.js:143）。POST /api/tasks 固定 status='pending'（857）。
- PUT /api/tasks/:id（921）**无状态白名单**：944-950 对任意 status 值直接入库；仅 running/done/failed/paused/pending(自paused) 有副作用分支；写 pending_review / running→pending 退回 **无 addEvent**。
- /internal/review（1014，requireInternalAuth）：approve→done+completed_at=COALESCE（1026-1028）；reject→rejected（1030-1032）。
- session-key（1044，requireInternalAuth）：pending→running+key+dispatched_at（1051-1054）；其他状态仅补 key（1056-1058）。**不翻转 spawn_owner**。
- retry（963-967）：任意→pending 且清 dispatched_at/completed_at。
- paused/cancelled/failed_final 已无任何服务端写入方（只剩 PUT 手动）；failed_final/cancelled 曾由 dispatch.js 写（312/331/338）。
- 前端任务 Tab 只读（task-0283，7975-7979 仅徽章）；状态筛选器 6965-6974 缺 paused/cancelled；TASK_STATUS 9 态（7184）。
- /api/stats totals 只统计 6 态（1296-1298），pending_review/rejected/failed_final 不进 total。
- nowCST（316-320）：CST 分钟级字符串，parseCST 反解，口径一致。

## N2 completions→pending_review 真空（核心发现）
- server.js 对 `task-completions` 0 引用（grep 证实）。
- heartbeat.sh sync_completions()（28-37）为空操作，注释称改由"任务中心自身…或主 agent 处理"——"任务中心自身"从未实现。
- dispatch.js.bak 曾做：读 jsonl→验产物→pending_review→消费行（156-233）；僵尸：session 结束→pending_review/failed/retry/failed_final（248-338）。2026-08-14 停用。
- 现行真实机制 = 主 agent 任务书里 ad-hoc 写"完成后 PUT pending_review"（task-0445 任务书即有），但模板 spawn-task.md 完成回报段只有 jsonl 写入，**未成文**。
- jsonl 151 行/143 任务，从未被消费，重复回报存在（task-0362×3）。当前 141 个有回执任务 DB 全为终态——真空暂无存量伤害，靠 ad-hoc PUT + 僵尸补丁兜住。

## N3 spawn_owner 语义失效
- 迁移注释（275-278）：web=dispatch 自动调度 / main=主agent原生spawn。dispatch 已死 → 'web' 实际=POST 未传 'main' 的一切来源（网页/心跳lane/主agent默认）。
- POST 默认（860）：非 'main' 一律 'web'。
- DB：web 344 vs main 31；有 session_key 的任务中 web 标记 130 vs main 18（88% 错标）。task-0445（本任务，主agent spawn）仍标 web。
- session-key 端点事件文案就叫"主agent原生spawn回写"却不设 owner=main —— 事故①根因。

## N4 时间口径与僵尸判定
- updated_at：任何 PUT 字段编辑都刷新 → 主 agent 改 notes 会把僵尸"洗白"重计 90min；执行中无人写 updated_at（=派发时间）。
- 僵尸退回用 PUT status=pending：不清 dispatched_at（0442 现状 pending+dispatched_at=15:44+无后续事件），与 retry 可区分但无事件痕迹。
- 0440/0441/0442 事件：created 15:16（"由 web 创建"）→ dispatched 15:44（session-key 回写）；0440 22:54 approved；0441 23:28 approved；0442 无后续（pending 等重派）。
- GET /api/tasks 只支持 project_id/status/type（805-830），HEARTBEAT 第6条的 ?limit=100 被忽略，返回全量 375 条。

## N5 心跳契约衔接
- 契约消费的状态 pending_review/failed/pending/running 均有 ?status= 过滤支持（heartbeat.sh 50-61）。✓
- review 动作与 /internal/review 字段吻合（heartbeat.sh 65-82）。✓
- 服务绑 127.0.0.1:8055（6204），PUT 无鉴权但仅本地可达——子 agent 可直写任意状态（含 done），属设计取舍。
- CLAUDE.md 仍写 "pending → running → done / failed"，落后 9 态现实。

## 冲突清单（严重度）
高2：H1 状态同步无成文写入方；H2 PUT 无状态白名单+关键流转无事件
中3：M1 spawn_owner 失效（88% 错标）；M2 僵尸退回不清 dispatched_at/无事件；M3 updated_at 僵尸判据可被无关编辑洗白
低3：L1 ?limit=100 被忽略；L2 前端筛选缺 2 态+stats 口径 6 态+CLAUDE.md 状态机过时；L3 pending_review 不写 completed_at（语义=审核时间）
