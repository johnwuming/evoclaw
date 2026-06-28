# Agent 看板任务执行路径与延迟分析

> 报告编号：R-119
> 分类：08-开发实践
> 日期：2026-06-28
> 研究方法：代码审计 + 配置分析

## 核心结论

**「创建并执行」按钮不会立即执行任务，也不会通过 2 分钟 cron 消费——实际上 dispatch 队列的消费者根本不存在。**

| 环节 | 设计预期 | 实际状态 |
|------|---------|---------|
| 按钮点击 → 写入队列 | ✅ 已实现 | 正常工作 |
| OpenClaw cron 每 2 分钟消费队列 | ❌ 未实现 | **jobs.json 为空，无任何 cron job** |
| 主 agent 心跳(30min)拾取 | ❌ 未实现 | HEARTBEAT.md 中无消费队列的步骤 |
| task-monitor.sh 消费队列 | ❌ 未实现 | 脚本定义了 QUEUE_FILE 但从未读取 |

**任务一旦通过「创建并执行」按钮提交，会永久停留在 `running` 状态，直到：**
1. 主 agent 碰巧在对话中手动处理（概率极低）
2. task-monitor.sh（10 分钟 cron）发现超时后标记为 `failed`（30 分钟后）

## 详细执行路径分析

### 1. 按钮点击的代码路径

```
前端: submitTask(true)
  → POST /api/tasks  { dispatch: true }
  → server.js: status = 'running', dispatched_at = now
  → writeDispatchQueue(task)
    → 追加一条 JSON 到 scripts/.task-dispatch-queue.jsonl
  → 返回 { ok: true }
```

**前端代码**（server.js L1213-1230）：
```javascript
async function submitTask(dispatch) {
  var body = {
    project_id: project_id,
    title: title,
    type: taskType,
    assigned_agent: agent,
    dispatch: !!dispatch  // true = "创建并执行"
  };
  var r = await post('tasks', body);
}
```

**后端代码**（server.js L472-488）：
```javascript
const status = b.status || (b.dispatch ? 'running' : 'pending');
// ...
if (status === 'running') {
    addEvent(id, 'dispatched', '创建并执行');
    writeDispatchQueue(getTask.get(id));  // 写入队列文件
}
```

### 2. 队列文件的实际状态

```
文件: /root/.openclaw/workspace/scripts/.task-dispatch-queue.jsonl
大小: 0 bytes（空文件）
```

队列文件存在但为空，说明：
- 要么从未有任务通过此路径提交
- 要么曾经有但被清空了
- 无论哪种情况，**没有任何消费者读取此文件**

### 3. 消费者缺失的证据

#### 3a. OpenClaw cron jobs — 空
```
/root/.openclaw/cron/jobs.json.migrated → { "version": 1, "jobs": [] }
```
V4 设计文档声称「OpenClaw cron 每 2 分钟扫描队列文件」，但 **OpenClaw cron 系统中没有任何 job 注册**。

#### 3b. 系统 crontab — 只有监控
```crontab
*/10 * * * * /root/.openclaw/workspace/scripts/task-monitor.sh
```
task-monitor.sh 只做超时检测（标记 running → failed），**不消费 dispatch 队列**。

#### 3c. HEARTBEAT.md — 无队列消费步骤
心跳流程只有：
1. Step 1：检查用户待办
2. Step 2：检查告警文件

**没有「读取 dispatch 队列」的步骤。**

#### 3d. task-monitor.sh — 定义了变量但未使用
```bash
QUEUE_FILE="$WORKSPACE/scripts/.task-dispatch-queue.jsonl"  # 定义了但从未读取
```

### 4. 延迟分析

| 路径 | 延迟 | 说明 |
|------|------|------|
| 理想：cron 2 分钟消费 | ~2 min | ❌ 消费者不存在 |
| 心跳拾取 | ~30 min | ❌ 心跳无此步骤 |
| task-monitor.sh 超时标记 | 30+10 min | ⚠️ 但这是标记失败，不是执行 |
| 主 agent 对话中手动处理 | 不确定 | 唯一可能的执行路径 |

**实际延迟：无限大（永远不执行）**，除非主 agent 在对话中恰好看到并手动处理。

## 优化建议

### 方案 A：立即生效 — 主 agent 心跳消费（推荐，改动最小）

在 HEARTBEAT.md 中增加一步队列消费：

```markdown
### Step 0.5：检查 dispatch 队列
> 读取 `/root/.openclaw/workspace/scripts/.task-dispatch-queue.jsonl`
> - 文件有内容 → 解析 JSON，对每个任务执行 sessions_spawn
> - 执行后清空文件（或删除已处理的行）
> - 这一步在 Step 1 之前执行
```

**效果**：延迟从「永远」降为 ≤30 分钟（心跳间隔）。

### 方案 B：系统 cron 快速消费 — 2 分钟级延迟

创建 `/root/.openclaw/workspace/scripts/dispatch-consumer.sh`：

```bash
#!/bin/bash
# 每 2 分钟检查 dispatch 队列，通过 openclaw CLI 触发主 agent
QUEUE="/root/.openclaw/workspace/scripts/.task-dispatch-queue.jsonl"
if [ -s "$QUEUE" ]; then
  # 通过 openclaw 向主 agent 发送 systemEvent
  openclaw event --agent main --message "dispatch-queue-pending"
  # 或直接调用 openclaw cron trigger
fi
```

加入 crontab：`*/2 * * * * /root/.openclaw/workspace/scripts/dispatch-consumer.sh`

**效果**：延迟降至 ~2 分钟。但需要 openclaw CLI 支持主动触发 agent。

### 方案 C：看板直连 OpenClaw API（最佳，改动较大）

让 server.js 直接调用 OpenClaw Gateway API spawn agent：

```javascript
// 在 writeDispatchQueue 之后或替代它
async function directSpawn(task) {
  const resp = await fetch('http://localhost:12145/api/sessions/spawn', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${TOKEN}` },
    body: JSON.stringify({
      agentId: task.assigned_agent,
      task: task.title,
      mode: 'run'
    })
  });
}
```

**效果**：延迟降至秒级（真正的「创建并执行」）。

**风险**：Dashboard 进程需要 OpenClaw 认证 token；增加耦合度。

### 方案 D：改为「待办」状态 — 最务实的折中

修改前端，将「创建并执行」改为「创建任务」，所有 Web 创建的任务默认 `pending`。
主 agent 在心跳中检查 `pending` 任务并主动 spawn。

```javascript
// server.js L472 改为：
const status = 'pending';  // 总是先创建为待办
```

**效果**：
- 不产生误导（用户不会以为任务在执行）
- 主 agent 心跳时自然发现 pending 任务并 spawn（≤30 分钟）
- 用户也可以在对话中主动提醒「看一下看板有没有待办」

## 总结

| 维度 | 现状 |
|------|------|
| 「创建并执行」是否立即执行 | **否** |
| 通过 2 分钟 cron 消费 | **消费者不存在** |
| 通过 30 分钟心跳消费 | **心跳中无此步骤** |
| 实际执行路径 | **无（设计未落地）** |
| 最佳短期方案 | D（改为待办）+ A（心跳消费） |
| 最佳中期方案 | C（直连 API spawn） |

## 来源

- 前端代码：`tools/agent-dashboard/server.js` L1213-1230（submitTask）、L993（按钮）
- 后端代码：`tools/agent-dashboard/server.js` L472-488（POST /api/tasks）、L524-532（POST /api/tasks/:id/dispatch）
- 队列写入：`tools/agent-dashboard/server.js` L151-165（writeDispatchQueue）
- 监控脚本：`scripts/task-monitor.sh`（L11 定义 QUEUE_FILE 但未使用）
- cron 状态：`/root/.openclaw/cron/jobs.json.migrated` → 空
- 心跳配置：`openclaw.json` → `heartbeat.every: "30m"`
- 心跳流程：`HEARTBEAT.md`（无队列消费步骤）
- 设计文档：`tools/agent-dashboard/V4-DESIGN.md`（Section 三：Spawn 机制设计）
