# 多 Agent 多 Session 上下文延续方案

> 调研时间：2026-04-06  
> 核心参考：OpenClaw docs（`~/.local/share/pnpm/global/5/.pnpm/openclaw@2026.4.2_@napi-rs+canvas@0.1.97/node_modules/openclaw/docs/`）

---

## 1. OpenClaw Session 机制详解

### 1.1 Session Key 格式

OpenClaw 的 sessionKey 遵循固定格式，用于路由消息到对应 Session：

| 消息来源 | sessionKey 格式 |
|----------|----------------|
| DM / 私聊 | `agent:<agentId>:<mainKey>`（mainKey 默认 `main`） |
| 群聊 | `agent:<agentId>:<channel>:group:<id>` |
| 子 Agent | `agent:<agentId>:subagent:<uuid>` |
| ACP Runtime | `agent:<agentId>:acp:<uuid>` |

**关键**：sessionKey 包含完整 agentId 前缀，这是实现硬隔离的基础。

### 1.2 Session 两层持久化机制

OpenClaw Session 有**两层**持久化：

1. **`sessions.json`**：可变元数据键值对（存 token 计数、toggles、sessionId 等）
2. **`<sessionId>.jsonl`**：追加式会话记录（包含 `message` / `compaction` / `branch_summary` 条目）

存储路径：
```
~/.openclaw/agents/<agentId>/sessions/
├── sessions.json              # 元数据索引
└── <sessionId>.jsonl          # 完整 transcript
```

### 1.3 Session 生命周期

有**三种重置策略**，以先到期者为准：

| 策略 | 触发条件 | 配置方式 |
|------|----------|----------|
| **Daily Reset** | 每天 4:00 AM 本地时间 | 默认行为 |
| **Idle Reset** | 空闲指定分钟 | `session.reset.idleMinutes` |
| **Manual Reset** | 用户输入 `/new` 或 `/reset` | `/new <model>` 可同时切换模型 |

### 1.4 DM 隔离策略（dmScope）

```json
{
  "session": {
    "dmScope": "per-channel-peer"  // 推荐配置
  }
}
```

可用级别：`main`（默认共享）/ `per-peer`（按发送者）/ `per-channel-peer`（按 channel+发送者）/ `per-account-channel-peer`（最细粒度）

### 1.5 Session 维护

```json
{
  "session": {
    "maintenance": {
      "mode": "enforce",    // warn | enforce
      "pruneAfter": "30d",  // 30天后清理
      "maxEntries": 500
    }
  }
}
```

---

## 2. sessions_spawn 参数详解

### 2.1 mode="session" vs mode="run"

| 特性 | mode="session" | mode="run" |
|------|---------------|------------|
| 默认值 | 否 | **是（默认）** |
| 生命周期 | 持久化 | 一次性，non-blocking 返回 runId |
| 线程绑定 | 需 `thread=true` | 否 |
| 适用场景 | 长期项目、持续对话 | 独立任务、批量处理 |

**重要**：`mode="session"` 需要同时设置 `thread=true` 才能开启线程绑定。

### 2.2 Thread-Bound Session

Thread-bound session 使后续 thread 内消息路由到同一 sub-agent session。

**当前仅 Discord 正式支持**（Telegram topics 在开发中）。

```typescript
sessions_spawn({
  agentId: "research-lead",
  mode: "session",
  thread: true,  // 仅 Discord 支持
})
```

### 2.3 resumeSessionId（关键限制）

**仅 ACP runtime 支持 resume，sub-agent runtime 不支持。**

```typescript
sessions_spawn({
  runtime: "acp",           // 必须是 acp
  resumeSessionId: "xxx",   // 恢复指定 ACP session
})
```

目标 Agent 必须支持 `session/load`（Codex 和 Claude Code 支持）。

### 2.4 label 参数

可选，用于标识子 agent：
- 可通过 `/subagents list/info/log` 查看
- 可通过 `/focus <label>` 绑定线程到指定 session

### 2.5 子 Agent Context 注入

子 agent 只注入 **AGENTS.md + TOOLS.md**，不注入 SOUL/IDENTITY/USER/HEARTBEAT/BOOTSTRAP，以减少上下文大小。

### 2.6 嵌套深度限制

- `maxSpawnDepth` 范围 1-5，默认 1，推荐 2
- Depth-1 orchestrator 可获得 `sessions_spawn/subagents/sessions_list/sessions_history` 工具
- Depth-2 leaf workers **永远不能 spawn**

---

## 3. Compaction 与 Memory Flush（关键发现）

### 3.1 Compaction（压缩）

当 `contextTokens > contextWindow - reserveTokens` 时触发：
- 将旧对话历史**持久化总结**为 transcript 中的 `compaction` 条目
- 只保留最近消息 + 摘要
- 是持久化的上下文缩减机制（写入 .jsonl）

### 3.2 Pruning（修剪）

- **仅内存级**修整工具结果
- **不修改** transcript
- 在 compaction 周期之间保持工具输出精简

### 3.3 Memory Flush（关键：防止信息丢失）

**Compaction 前自动运行**，通过 NO_REPLY 机制对用户不可见：

- 将重要上下文写入 `memory/YYYY-MM-DD.md` 或 `MEMORY.md`
- 防止 compaction 时丢失关键信息
- 配置：`memoryFlush.enabled=true`，`softThresholdTokens=4000` 时触发

### 3.4 Compaction vs Pruning 对比

| 特性 | Compaction | Pruning |
|------|-----------|---------|
| 作用层级 | **持久化**（写入 .jsonl） | 仅内存级 |
| 修改 transcript | 是 | **否** |
| 触发条件 | contextTokens 超出窗口 | 自动在 compaction 周期之间运行 |
| 信息保留 | 摘要化，保留关键信息 | 修整工具结果，保留对话结构 |

---

## 4. QMD Memory Engine（跨 Session 搜索）

QMD engine 可对 session transcript 建**语义索引**，实现跨 Session 上下文传递：

```json
{
  "memory": {
    "backend": "qmd",
    "sessions": {
      "enabled": true
    }
  }
}
```

功能：
- 对 transcript 进行语义索引
- 新 Session 能**语义搜索**历史会话内容
- 实现上下文传递**而不加载全部历史 transcript**
- 特别适合"上次研究做到哪了"的场景

---

## 5. 多项目多 Session 隔离方案

### 5.1 核心隔离机制

每个 `agentId` = 完全独立的 brain：
- 独立 workspace（含 AGENTS.md / SOUL.md / USER.md 等）
- 独立 agentDir（auth-profiles）
- 独立 session store（`~/.openclaw/agents/<agentId>/sessions/`）

跨 agent 路由通过 `bindings` 配置。

### 5.2 绑定路由优先级

```
peer match > guildId > accountId > channel > fallback to default agent
```

### 5.3 实现"一个项目一个 Session"的具体方案

**方案 A：不同 Agent ID（完全隔离）**

```json
// openclaw.json
{
  "agents": {
    "project-alpha-lead": { "workspace": "workspace-alpha" },
    "project-beta-lead":   { "workspace": "workspace-beta" }
  }
}
```

- 每个项目有独立 agentId
- 天然硬隔离（不同 workspace + 不同 session store）
- 适合长期、复杂的项目

**方案 B：同一 Agent + Session Label（逻辑隔离）**

```typescript
sessions_spawn({
  agentId: "research-lead",
  label: "project-alpha",      // 标识项目
  mode: "session",
  cwd: "/root/.openclaw/workspace-alpha",  // 项目专属 workspace
})
```

- 适合项目数量多、不需要完全硬隔离的场景
- Workspace 文件模式传递上下文

**方案 C：Workspace 隔离 + 检查点（推荐）**

每个项目独立 workspace，维护：

```
/root/.openclaw/workspace-{projectId}/
├── SOUL.md
├── AGENTS.md
├── research/
│   ├── knowledge-base.json    # 研究发现库
│   ├── gaps.json              # 待解决问题
│   ├── summary.md              # 当前摘要
│   └── checkpoint.json        # 进度检查点
└── sessions/
```

新 Session 启动时：
1. 读取 `checkpoint.json` 获取当前进度
2. 读取 `summary.md` 了解项目状态
3. 从 `knowledge-base.json` 加载已完成的工作

---

## 6. 上下文摘要传递方案

### 6.1 问题分析

新 Session 如何读取历史上下文摘要而不加载全部历史？

### 6.2 解决方案对比

| 方案 | 原理 | 适用场景 |
|------|------|----------|
| **QMD semantic index** | 对 transcript 建语义索引，新 session 可搜索历史 | 需要语义查询的项目 |
| **Memory flush** | compaction 前自动写入 memory/*.md | 自动保存关键上下文 |
| **Workspace 文件** | 人工维护 knowledge-base.json | 结构化项目知识管理 |
| **Compaction** | transcript 中的摘要条目 | 自动压缩长对话 |

### 6.3 推荐：Workspace + QMD 混合模式

```
阶段 1：任务执行
  └── 子 agent 输出结果
  
阶段 2：结果汇总（Lead Agent）
  └── 将发现写入 workspace/research/knowledge-base.json
  └── 更新 workspace/research/gaps.json
  └── 更新 workspace/research/checkpoint.json
  
阶段 3：新迭代开始
  └── 读取 checkpoint.json 了解进度
  └── 读取 knowledge-base.json 加载已完成工作
  └── 通过 QMD 语义搜索历史会话（如需要）
```

### 6.4 Workspace 文件结构示例

**checkpoint.json**：
```json
{
  "project": "project-alpha",
  "lastUpdated": "2026-04-06T15:00:00Z",
  "currentPhase": "phase-2-research",
  "pendingTasks": ["review-findings", "iterate-analysis"],
  "completedTasks": ["initial-research", "source-verification"],
  "lastSessionId": "agent:research-lead:subagent:xxx"
}
```

**knowledge-base.json**：
```json
{
  "project": "project-alpha",
  "findings": [
    {
      "id": "f-001",
      "claim": "...",
      "evidence": "...",
      "source": "...",
      "verified": true,
      "confidence": "high"
    }
  ]
}
```

---

## 7. Session Tools 与 Visibility

### 7.1 Visibility 四级别

| 级别 | 范围 |
|------|------|
| `self` | 仅当前 session |
| `tree` | 当前 + 衍生的 sub-agent |
| `agent` | 本 agent 所有 sessions |
| `all` | 跨所有 agent（需配置） |

**注意**：sandboxed sessions 被强制限制为 `tree`。

### 7.2 适用场景

- **团队协作**：使用 `agent` 级别让 team lead 查看所有成员 session
- **审计**：使用 `all` 级别跨 agent 查询（需注意安全）
- **隔离**：保持 `self` 或 `tree` 避免信息泄露

---

## 8. ClawFlow 在上下文延续中的角色

### 8.1 ClawFlow 是什么

ClawFlow 是为**跨 detached 任务的工作流**设计的运行时：
- 提供 Flow ID（跨 Session 身份标识）
- 提供 Flow Output 持久化
- 支持等待/恢复模式
- 通过 `createFlow / runTaskInFlow / setFlowOutput / finishFlow` 管理

### 8.2 ClawFlow vs 直接 Session 延续

| 场景 | 推荐方案 |
|------|----------|
| 项目内多阶段任务，有明确工作流 | ClawFlow |
| 同一项目迭代延续（每次新 session） | Workspace 文件模式 |
| 需要语义搜索历史 | QMD engine |
| ACP runtime 任务恢复 | `resumeSessionId` |

### 8.3 ClawFlow 不解决的问题

- Session 上下文延续（Compaction/Memory Flush 是为此设计）
- 跨 Session 的语义搜索（QMD 是为此设计）
- 项目维度的上下文管理（Workspace 文件是为此设计）

---

## 9. 业界方案参考（文档获取受限）

> 注：由于网络限制，无法获取 Anthropic / OpenAI / Devin / LangGraph 官方文档。LangChain 文档可访问，但重定向后页面内容与预期不符。

### 9.1 LangGraph 的启示（从文档片段推断）

LangGraph 的关键概念：
- **StateGraph**：通过 state + reducer 管理跨 node 共享状态
- **Checkpoint**：持久化状态快照，支持恢复
- **Persistence**：通过 checkpointer 接口实现跨会话持久化
- **Send**：并行任务分发
- **Command**：状态更新 + 路由控制

**对 OpenClaw 的对应关系**：
- OpenClaw 的 `sessions.json` + `.jsonl` ≈ LangGraph Checkpointer
- OpenClaw 的 Workspace 文件 ≈ LangGraph 外部状态存储
- OpenClaw 的 ClawFlow ≈ LangGraph StateGraph 的轻量版

---

## 10. 推荐实施方案总结

### 问题 1：新 Session 不知道上次做到哪了

**方案：Workspace 检查点 + QMD**

1. 任务完成后更新 `workspace/checkpoint.json`
2. 将发现写入 `workspace/research/knowledge-base.json`
3. 新 Session 读取检查点 + 知识库
4. 如需语义搜索历史，通过 QMD engine 查询

### 问题 2：不同项目 Session 冲突

**方案：独立 Agent ID 或 Workspace 隔离**

- 长期项目 → 不同 `agentId`（硬隔离）
- 短期/轻量项目 → 同一 `agentId` + 不同 `label` + 不同 `cwd`

### 问题 3：项目迭代需要延续上下文但不能合并

**方案：Compaction + Memory Flush + Workspace 文件**

- 依赖 OpenClaw 内置 Compaction 自动压缩长对话
- 依赖 Memory Flush 防止关键信息丢失
- Workspace 文件存储结构化知识库

### 具体配置示例

```json
// openclaw.json
{
  "session": {
    "dmScope": "per-channel-peer",
    "reset": { "idleMinutes": 120 }
  },
  "memory": {
    "backend": "qmd",
    "sessions": { "enabled": true }
  },
  "session": {
    "maintenance": {
      "mode": "enforce",
      "pruneAfter": "30d"
    }
  }
}
```

---

## 11. 关键发现汇总

1. **Session 两层持久化**：`sessions.json`（元数据）+ `<sessionId>.jsonl`（完整 transcript）

2. **mode="session" 需要 thread=true**：且 thread-bound 仅 Discord 正式支持

3. **resumeSessionId 仅 ACP runtime**：sub-agent runtime 不支持 session 恢复

4. **Compaction 是持久化的**：写入 transcript（.jsonl）；Pruning 仅内存级

5. **Memory Flush 防止信息丢失**：compaction 前自动写入 `memory/*.md`，NO_REPLY 机制

6. **QMD engine 实现语义搜索**：跨 session 搜索历史而不加载全部 transcript

7. **每个 agentId 是独立 brain**：独立 workspace + session store

8. **子 agent 只注入 AGENTS.md + TOOLS.md**：不注入 SOUL/IDENTITY/USER

9. **嵌套深度 maxSpawnDepth**：默认 1，推荐 2；depth-2 workers 永远不能 spawn

10. **Session Tool visibility 四级别**：self / tree / agent / all

---

## 12. 参考资料

| 文档 | 路径 |
|------|------|
| Session Management | `docs/concepts/session.md` |
| Session Management Deep Dive | `docs/reference/session-management-compaction.md` |
| Compaction | `docs/concepts/compaction.md` |
| Session Pruning | `docs/concepts/session-pruning.md` |
| Memory QMD | `docs/concepts/memory-qmd.md` |
| Multi-Agent | `docs/concepts/multi-agent.md` |
| Sub-agents | `docs/tools/subagents.md` |
| ACP Agents | `docs/tools/acp-agents.md` |
| Session Tools | `docs/concepts/session-tool.md` |

---

*报告生成时间：2026-04-06*
*调研工具：OpenClaw 本地 docs 目录（已验证可读）、browser、web_search*
*子 Agent findings 文件：`/root/.openclaw/workspace-search/findings-session-mechanism.json`*
