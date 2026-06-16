# 多 Agent 多 Session 上下文延续方案

## 1. OpenClaw Session 机制详解

### 1.1 Session 的生命周期

OpenClaw 的 Session 有以下几种生命周期策略：

| 策略 | 行为 | 配置方式 |
|------|------|----------|
| **Daily Reset** | 每天 4:00 AM（本地时间）自动创建新 Session | 默认行为 |
| **Idle Reset** | 空闲指定分钟后创建新 Session | `session.reset.idleMinutes` |
| **Manual Reset** | 用户在聊天中输入 `/new` 或 `/reset` | 用户触发 |

Session 存储位置：
- **索引**：`~/.openclaw/agents/<agentId>/sessions/sessions.json`
- **Transcript**：`~/.openclaw/agents/<agentId>/sessions/<sessionId>.jsonl`

### 1.2 Session 隔离策略

OpenClaw 支持多层次 Session 隔离：

```
session.dmScope 配置选项：
- "main"               — 所有 DMs 共享一个 Session（默认）
- "per-peer"           — 按发送者隔离（跨渠道）
- "per-channel-peer"   — 按渠道+发送者隔离（推荐）
- "per-account-channel-peer" — 按账号+渠道+发送者隔离
```

关键机制：`session.identityLinks` 可将同一用户跨渠道的身份关联起来，使其共享同一 Session。

### 1.3 消息路由与会话隔离

| 消息来源 | 默认行为 |
|----------|----------|
| Direct Messages | 默认共享 Session |
| Group Chats | 按群隔离 |
| Rooms/Channels | 按房间隔离 |
| Cron Jobs | 每次运行全新 Session |
| Webhooks | 按 Hook 隔离 |

### 1.4 Session 维护

```json
// openclaw.json 配置示例
{
  "session": {
    "maintenance": {
      "mode": "enforce",     // warn | enforce
      "pruneAfter": "30d",   // 30天后清理
      "maxEntries": 500      // 最大条目数
    }
  }
}
```

预览清理：`openclaw sessions cleanup --dry-run`

---

## 2. Session 持久化与复用

### 2.1 Thread-Bound Session

OpenClaw 支持 **thread-bound session**（线程绑定 Session），通过 `sessions_spawn` 的参数控制：

```typescript
// mode="session" vs mode="run" 的区别：
sessions_spawn({
  mode: "session",  // 持久 Session，线程绑定，可接收后续消息
  thread: true,      // 创建线程绑定会话
  label: "my-project", // Session 标签，用于识别
  // ...
})

sessions_spawn({
  mode: "run",  // 一次性运行，不持久化上下文
  // ...
})
```

### 2.2 Session Resume

通过 `resumeSessionId` 参数可以恢复已有 Session：

```typescript
sessions_spawn({
  runtime: "acp",
  resumeSessionId: "previous-session-uuid", // 恢复指定 Session
  // ...
})
```

这允许新 Session 继承之前 Session 的上下文历史。

### 2.3 Session Label

`label` 参数用于给 Session 打标签，便于管理和识别：

```typescript
sessions_spawn({
  label: "project-alpha-research",  // 标签不是隔离机制，是识别机制
  // ...
})
```

### 2.4 Session 持久化存储

OpenClaw 的 Session 默认是**持久化**的，存储在 `sessions.json` 中，而不是仅存于内存。这意味着一旦创建，Session 会保留直到过期或被清理。

---

## 3. sessions_spawn 参数详解

### 3.1 mode="session" vs mode="run"

| 特性 | mode="session" | mode="run" |
|------|---------------|------------|
| 生命周期 | 持久，可接收后续消息 | 一次性，运行完即结束 |
| 上下文 | 保留完整历史 | 每次全新上下文 |
| 线程绑定 | 是（thread=true 时） | 否 |
| 适用场景 | 长期项目、持续对话 | 独立任务、批量处理 |

### 3.2 关键参数

```typescript
interface SpawnOptions {
  agentId: string;              // Agent ID
  mode: "session" | "run";     // 运行模式
  thread?: boolean;            // 是否线程绑定
  label?: string;              // Session 标签
  resumeSessionId?: string;     // 恢复的 Session ID
  runTimeoutSeconds?: number;   // 运行超时
  cleanup?: "delete" | "keep";  // 完成后是否删除 Session
  cwd?: string;                 // 工作目录
  attachments?: Attachment[];    // 附件
}
```

### 3.3 子 Agent 继承

当 spawn 子 Agent 时：
- 子 Agent **不自动继承**父 Agent 的完整上下文
- 子 Agent 继承 **workspace 目录路径**（通过 `cwd` 参数）
- Workspace 文件（如 `research/knowledge-base.json`）是跨 Session 共享数据的标准方式

---

## 4. 多项目多 Session 隔离方案

### 4.1 问题分析

当前问题：
1. 一个项目迭代时，新 Session 不知道上次做到哪了
2. 不同项目之间 Session 可能冲突（如 dev-lead 同时服务两个项目）
3. 同一项目多次迭代需要延续上下文，但不能简单合并

### 4.2 解决方案一：基于 Workspace 的项目隔离

每个项目使用独立的 workspace，通过 Workspace 文件传递上下文：

```
~/.openclaw/workspace-project-alpha/
  research/
    knowledge-base.json   # 项目知识库
    gaps.json             # 未解决问题
  sessions/               # 项目专用 Session 存储
  outputs/                # 项目输出

~/.openclaw/workspace-project-beta/
  research/
    knowledge-base.json
  ...
```

配置各 Agent 的 workspace：
```json
{
  "agents": {
    "research-lead": {
      "workspace": "workspace-{project-id}"
    }
  }
}
```

### 4.3 解决方案二：基于 Session Label 的项目隔离

在 spawn 时为每个项目指定唯一 label：

```typescript
// 项目 A
sessions_spawn({
  agentId: "research-lead",
  label: "project-A-research",
  mode: "session",
})

// 项目 B
sessions_spawn({
  agentId: "research-lead", 
  label: "project-B-research",
  mode: "session",
})
```

**注意**：`label` 本身不提供硬隔离，只是识别标记。真正的隔离需要结合 workspace。

### 4.4 解决方案三：ClawFlow 跨 Session 工作流

ClawFlow 提供了更结构化的跨 Session 工作方式：

```typescript
const flow = createFlow({
  ownerSessionKey: parentSessionKey,
  goal: "完成项目研究",
});

// 启动子任务
runTaskInFlow({
  flowId: flow.flowId,
  runtime: "subagent",
  task: "研究子问题 A",
  currentStep: "step_a",
});

// 等待结果
setFlowWaiting({
  flowId: flow.flowId,
  waitFor: "subagent_complete",
});

// 获取结果
setFlowOutput({
  flowId: flow.flowId,
  key: "research_results",
  value: { findings: [...] },
});
```

**ClawFlow 的核心价值**：
- Flow ID 提供了跨 Session 的身份标识
- Flow Output 提供了跨 Session 的数据传递机制
- 支持等待和恢复模式

---

## 5. 历史上下文摘要传递方案

### 5.1 核心问题

新 Session 如何读取历史上下文摘要而不加载全部历史？

### 5.2 Workspace 文件模式（推荐）

OpenClaw 的 Workspace 机制允许跨 Session 共享文件。最佳实践：

**在项目 workspace 中维护以下文件：**

```
research/
  knowledge-base.json    # 累积的研究发现（JSON）
  gaps.json              # 待解决的缺口（JSON）
  summary.md             # 最新摘要（Markdown，供人工阅读）
  checkpoint.json        # 检查点状态（当前进度）
```

**knowledge-base.json 结构示例：**
```json
{
  "project": "project-alpha",
  "lastUpdated": "2026-04-06T15:00:00Z",
  "findings": [
    {
      "id": "f-001",
      "claim": "...",
      "evidence": "...",
      "source": "...",
      "verified": true,
      "confidence": "high"
    }
  ],
  "activeAgent": "research-lead",
  "currentPhase": "phase-2-iteration"
}
```

### 5.3 Session 摘要提取流程

在新 Session 启动时：
1. 读取 `workspace/research/summary.md` 获取项目状态
2. 读取 `workspace/research/checkpoint.json` 获取当前进度
3. 基于摘要决定从哪里继续

### 5.4 OpenClaw 内置的 Compaction 机制

OpenClaw 文档提到了 **Compaction**（压缩）功能：
- 用途：总结长对话
- 位置：`~/.openclaw/agents/<agentId>/sessions/<sessionId>.jsonl` 的压缩版本
- 这意味着即使 Session 历史很长，也可以被压缩成摘要

### 5.5 Session Pruning

OpenClaw 的 **Session Pruning** 功能可以裁剪工具结果：
- 减少 Session 中的冗余内容
- 保留关键决策点
- 清理临时工具输出

---

## 6. 业界多 Agent 上下文管理最佳实践

### 6.1 Anthropic Claude

Claude 使用 **Session/Thread** 模型：
- 每个对话是一个独立 Session
- 通过 **Context Compression** 处理长对话
- 支持 **Project** 概念来组织相关会话
- MCP (Model Context Protocol) 用于跨工具共享上下文

**对 OpenClaw 的启示**：
- OpenClaw 的 workspace 类似 Project 概念
- Compaction 功能类似 Context Compression

### 6.2 OpenAI Assistants API

OpenAI 的方案：
- **Thread** = 对话线程
- **Message** = 消息
- **Run** = 单次执行
- **Assistant** = Agent 定义

关键区别：OpenAI 的 Thread 是独立资源，可被多个 Run 引用。

**对 OpenClaw 的启示**：
- `mode="session"` 类似 Thread
- `mode="run"` 类似 Run
- `resumeSessionId` 允许 Session 复用，类似 Thread 续活

### 6.3 Devin (Cognition)

Devin 的方案：
- 每个任务有独立 **Task ID**
- 任务状态持久化
- 支持任务恢复和检查点

**对 OpenClaw 的启示**：
- ClawFlow 的 `flowId` 类似 Task ID
- `setFlowOutput` / `finishFlow` 类似任务状态更新

### 6.4 LangGraph / LangChain

LangGraph 的方案（从文档中获取）：
- **StateGraph**：状态图定义工作流
- **Checkpoint**：状态检查点，支持恢复
- **Persistence**：通过 checkpointer 实现跨会话持久化
- **Send**：并行任务分发
- **Command**：状态更新+路由控制

关键概念：
```python
# 状态定义
class State(TypedDict):
    messages: Annotated[list, add_messages]
    context: str

# Checkpoint 保存/恢复
graph.checkpointer = MemorySaver()
config = {"configurable": {"thread_id": "1"}}
graph.invoke(input, config)
```

**对 OpenClaw 的启示**：
- ClawFlow 的 `setFlowOutput` 类似 Checkpoint
- Workspace 文件类似外部状态存储
- OpenClaw 可以考虑实现 Checkpoint 机制

### 6.5 跨系统共性模式

| 模式 | OpenClaw 实现 | 其他系统实现 |
|------|---------------|-------------|
| Session 隔离 | `session.dmScope` | OpenAI Thread |
| 状态持久化 | `sessions.json` | LangGraph Checkpointer |
| 上下文压缩 | Compaction | Claude Context Compression |
| 跨任务状态 | ClawFlow | LangGraph State |
| 检查点恢复 | `resumeSessionId` | Devin Task ID |

---

## 7. 推荐实施方案

### 7.1 针对问题 1：新 Session 不知道上次做到哪了

**方案：Workspace 检查点模式**

1. 每个项目有独立 workspace
2. 在 workspace 中维护 `checkpoint.json`：
```json
{
  "project": "my-project",
  "lastUpdated": "2026-04-06T15:00:00Z",
  "currentPhase": "phase-2-research",
  "pendingTasks": ["review-findings", "iterate-analysis"],
  "completedTasks": ["initial-research", "source-verification"]
}
```
3. 新 Session 启动时读取检查点
4. 任务完成后更新检查点

### 7.2 针对问题 2：不同项目 Session 冲突

**方案：Session Label + Workspace 隔离**

```typescript
// 为每个项目创建独立 Session
sessions_spawn({
  agentId: "dev-lead",
  label: `project-${projectId}-lead`,
  mode: "session",
  cwd: `/root/.openclaw/workspace-${projectId}`,
  // ...
})
```

同时配置 OpenClaw：
```json
{
  "session": {
    "dmScope": "per-channel-peer"
  },
  "agents": {
    "dev-lead": {
      "workspace": "workspace-{projectId}"
    }
  }
}
```

### 7.3 针对问题 3：项目迭代需要延续上下文但不能合并

**方案：ClawFlow + Workspace 摘要**

1. 使用 ClawFlow 管理项目生命周期
2. 每个迭代阶段结束后：
   - 将关键发现写入 `workspace/research/knowledge-base.json`
   - 更新 `workspace/research/gaps.json`
   - 更新 `workspace/research/summary.md`
3. 新迭代开始时：
   - 从 `summary.md` 读取上次状态
   - 从 `knowledge-base.json` 加载历史发现
   - 避免重复工作

### 7.4 混合架构推荐

```
项目 Workspace 结构：
/root/.openclaw/workspace-{projectId}/
├── SOUL.md                    # 项目角色定义
├── AGENTS.md                  # 项目 Agent 规范
├── research/
│   ├── knowledge-base.json    # 研究发现库
│   ├── gaps.json              # 待解决问题
│   ├── summary.md             # 当前摘要
│   └── checkpoint.json         # 进度检查点
├── sessions/                  # Session 存储
└── outputs/                  # 产出文件
```

**Session 策略**：
- **Lead Agent**（research-lead/dev-lead）：使用 `mode="session"`, `label="project-{id}-lead"`，长期存活
- **Worker Agents**（research-searcher 等）：使用 `mode="run"`，完成即结束
- **结果汇总**：Worker 结果通过 Workspace 文件传递给 Lead

---

## 8. 关键发现总结

1. **OpenClaw Session 本质**：OpenClaw 的 Session 是持久化存储的（`sessions.json` + `.jsonl` transcript），不是纯内存。

2. **mode="session" vs mode="run"**：session 模式创建持久线程，可接收后续消息；run 模式是一次性任务。

3. **跨 Session 上下文传递**：没有内置的自动摘要传递机制，但 Workspace 文件模式是官方推荐的标准方式。

4. **ClawFlow 的定位**：ClawFlow 是为**跨 detached 任务的工作流**设计的，不是为 Session 上下文延续设计的。它的价值在于提供 Flow ID 和 Output 持久化。

5. **Session 隔离层次**：
   - 消息来源隔离（DM/Group/Room）
   - dmScope 配置（main/per-peer/per-channel-peer）
   - Workspace 隔离（不同项目用不同 workspace）

6. **Compaction 和 Pruning**：OpenClaw 有内置的 Compaction（长对话压缩）和 Session Pruning（工具结果裁剪）功能，但具体 API 需要查阅 Session Tools 文档。

---

## 9. 待进一步研究的问题

1. **Session Tools API**：文档中提到的 "Session Tools - agent tools for cross-session work" 的具体 API 和用法未能在本次研究中获取详细信息（docs 站点访问问题）。

2. **Compaction 具体机制**：压缩的具体算法和触发条件需要进一步确认。

3. **resumeSessionId 的完整行为**：恢复 Session 时如何处理并发和状态冲突。

4. **Multi-Agent Routing 详情**：文档中提到的 "Multi-Agent Routing" 如何与 Session 隔离配合工作。

---

## 10. 参考资料

- OpenClaw Session Management 文档（https://docs.openclaw.ai/reference/rpc）
- ClawFlow SKILL.md（`skills/clawflow/SKILL.md`）
- ClawFlow Inbox Triage SKILL.md（`skills/clawflow-inbox-triage/SKILL.md`）
- OpenClaw README.md
- LangGraph 文档（用于对比）

---

*报告生成时间：2026-04-06*
*调研工具：OpenClaw docs, browser, 本地源码*
