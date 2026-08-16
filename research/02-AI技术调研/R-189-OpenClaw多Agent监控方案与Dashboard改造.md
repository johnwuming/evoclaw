# R-189: OpenClaw 多 Agent 监控方案与 Dashboard 改造

**报告编号:** R-189
**分类:** 02-AI技术调研
**日期:** 2026-08-09
**状态:** 初版

---

## 目录

1. [执行摘要](#1-执行摘要)
2. [OpenClaw 现有监控能力盘点](#2-openclaw-现有监控能力盘点)
3. [监控缺口分析](#3-监控缺口分析)
4. [行业参考与最佳实践](#4-行业参考与最佳实践)
5. [推荐监控架构](#5-推荐监控架构)
6. [Dashboard Agent Tab 改造方案](#6-dashboard-agent-tab-改造方案)
7. [实施路线图](#7-实施路线图)
8. [附录](#8-附录)

---

## 1. 执行摘要

OpenClaw 是一个多渠道 AI 网关，运行多个独立 agent（main、research-lead、research-searcher、research-reviewer、dev-lead、dev-coder 等），每个 agent 拥有独立 workspace、session store 和工具集。当前系统已具备基础的可观测性设施——session state event log、agent-watchdog 超时检测、cron 遥测、dead-letter 错误处理、gateway health endpoint——但这些能力分散在不同子系统中，缺乏统一的监控面板和告警闭环。

**核心建议：** 不引入重量级外部可观测性平台（如 Langfuse/LangSmith），而是基于 OpenClaw 已有的 Control UI（Web Dashboard）和 session state event log，构建轻量级、内生的多 Agent 监控层。重点改造 Dashboard 的 Agent Tab，使其从静态状态展示升级为实时监控中心，并增加阈值告警能力。

**理由：** OpenClaw 是个人 AI 助手（非企业 SaaS），数据量有限（单机部署、数十个并发 session），自建轻量监控比引入外部平台更合适——部署简单、零额外成本、数据不出本地。

---

## 2. OpenClaw 现有监控能力盘点

### 2.1 CLI 监控命令

OpenClaw v2026.7.1-2 提供以下与监控相关的 CLI 命令：

| 命令 | 用途 | 监控价值 |
|------|------|----------|
| `openclaw status` | 渠道健康 + 最近 session 接收者 | 渠道层健康快照 |
| `openclaw health` | 获取 gateway 健康状态 | Gateway 存活检测 |
| `openclaw doctor` | 健康检查 + 快速修复 | 诊断与修复 |
| `openclaw logs` | 通过 RPC 尾随 gateway 文件日志 | 实时日志流 |
| `openclaw sessions *` | 列出存储的会话 | Session 审计 |
| `openclaw transcripts *` | 检查存储的对话记录 | 对话回放 |
| `openclaw tasks *` | 检查持久化后台任务和 TaskFlow 状态 | 后台任务监控 |
| `openclaw audit` | 检查 agent 运行和工具操作记录 | 审计与合规 |
| `openclaw system *` | events / heartbeat / presence | 系统事件与心跳 |
| `openclaw cron *` | 管理 cron 作业 | 定时任务监控 |
| `openclaw gateway status` | 探测 daemon 健康端点 | Gateway 健康 |
| `openclaw memory *` | 搜索/检查/重索引记忆文件 | 记忆系统监控 |

### 2.2 Gateway 控制平面

OpenClaw Gateway 提供内部 RPC 和事件推送机制：

- **EventFrame 推送** — Gateway 通过 WebSocket 异步推送状态变更：新消息、审批请求、session 事件
- **ErrorShape 结构化错误** — 每个错误包含 code、message、details、retryability、retry-after hints
- **Connection state machine** — Connected → RequestSent → Failed → SocketOpen（带指数退避重连）
- **Dead Letter 处理** — 失败的事件以 tombstone 形式保留为 dead letter，含错误原因

### 2.3 Session 生命周期与 State Event Log

**这是 OpenClaw 最核心的监控数据源。**

- 每个有意义的 session 状态变更——消息到达、工具执行、compaction、reset——都被记录为 **session state event**，持久化在 SQLite 后端
- **Watch 系统** — 一个 "watcher" session 可以订阅 "target" session 的 state events，通过 `session_watch_cursors` 行实现跨 session 通知
- **Lifecycle events** — Session 通过进程内 pub/sub 系统向注册的观察者广播生命周期事件
- **Session metadata** — 持久化 inbound event 的 session key、context、group resolution 元数据

### 2.4 Agent Watchdog（Cron 子系统）

Cron 子系统中已有 `agent-watchdog.ts` 模块：

- 检测 stuck runs（卡住的 agent 执行）
- 执行 per-job timeout policies（每作业超时策略）
- Isolated agent runner 管理完整生命周期：session 创建、模型选择与预检、delivery policy、watchdog 监控、session 清理
- `CronRunTelemetry` 类型记录 model、provider、token usage 数据——**这是已有的成本与性能遥测**

### 2.5 模型回退与遥测

- Cron `agentTurn` payload 支持 per-job model overrides、explicit fallback model chains、thinking mode 配置
- 系统在 model 级别做了 streaming 和 retry 逻辑委托
- 渠道路由层有失败处理：错误事件 → tombstone as dead letter 或 released for retry（取决于 retry policy）

### 2.6 Control UI（Web Dashboard）

Dashboard 运行在 gateway 端口（默认 18789），是 OpenClaw 的管理界面：

- **路径结构：** `/` → Control UI，`/config/` → 构建配置，`/docs/` → 文档源码
- **功能：** 监控 session、配置 channel、检查 agent 状态
- **Config Tab：** 可视化编辑、表单验证
- **当前 Agent Tab：** 仅展示 agent 状态（idle/running），尚未充分利用

### 2.7 多 Agent 配置现状

从 `openclaw.json` 配置可见：

```
agents.entries:
  main        → 主会话 agent
  research-lead → 研究主管（本 agent）
  research-searcher → 搜索执行
  research-reviewer → 审稿
  research-citation → 引文处理
  dev-lead    → 开发主管
  dev-coder   → 编码执行
  dev-qa      → QA 测试
  ...
```

每个 agent 有独立的 workspace、model 配置和工具策略。

---

## 3. 监控缺口分析

### 3.1 当前缺失的关键能力

| 缺口 | 影响 | 优先级 |
|------|------|--------|
| **子 Agent 超时/卡死检测** — 无法在 Dashboard 实时发现卡住的 subagent session | 子 agent 可能运行数小时不被发现，浪费 token | 🔴 高 |
| **统一监控面板** — Agent Tab 只显示 idle/running，无执行详情 | 无法快速判断系统健康状态 | 🔴 高 |
| **告警通知** — 无阈值告警，问题只能事后发现 | 模型故障、session 堆积无法及时响应 | 🔴 高 |
| **Token/Cost 聚合视图** — CronRunTelemetry 已有数据但未在 Dashboard 展示 | 无法了解整体消耗趋势 | 🟡 中 |
| **模型回退追踪** — 回退事件未在 UI 可见 | 不了解回退频率和影响 | 🟡 中 |
| **Session 异常清理** — 已知 idle/cap sweeper 对某些路径（如新 tab）不生效 | 内存泄漏（已知问题：2 天 ~2.1GB） | 🟡 中 |
| **Subagent 完成率统计** — 无法快速了解子任务成功率 | 难以评估 agent 编排可靠性 | 🟢 低 |

### 3.2 已知系统问题（来自 OpenClaw Issues）

- Browser tabs 在 session 结束后未关闭（52 个 Chrome 进程，8 个孤立 tab，~2.1GB RAM）
- 新 tab 逃逸了 idle/cap sweeper 和 lifecycle cleanup
- Subagent session lane 的工具注入失败（特定路径下 100% 可复现）
- Codex runtime 的 prior conversation messages 在 subagent 流程中丢失

---

## 4. 行业参考与最佳实践

> 详细行业调研见：`shared/results/work/R-189-industry-reference.md`（30+ 页完整报告）

### 4.1 主流框架的监控方法对比

| 框架/平台 | 监控方式 | 对 OpenClaw 的启发 |
|-----------|----------|-------------------|
| **AutoGen** | 原生 OpenTelemetry，框架级 instrument，遵循 GenAI 语义约定 | 理想模型：session/tool/model 三层 span |
| **CrewAI** | 集成优先（AgentOps 2 行代码），框架本身不做监控 | 轻量集成 > 重新造轮子 |
| **LangGraph/LangSmith** | 最成熟平台：Run→Trace→Thread→Trajectory 层次，自动规则引擎，阈值告警 | Agent Tab 可借鉴 trajectory 展示 |
| **Langfuse** | 开源自托管，OTel-native，100+ 框架集成 | 证明自托管可观测可行且够用 |
| **AgentOps** | 开发者体验最佳，session waterfall + time-travel debugging | Dashboard 可借鉴 session waterfall |

### 4.2 适用于 OpenClaw 的关键实践

1. **三层可观测架构**（AutoGen 模型）：
   - L1: 框架级事件发射（session lifecycle, tool call, model call）
   - L2: 监控平台（Dashboard 聚合展示）
   - L3: 告警与自动化

2. **Agent 专有可视化**（LangSmith/AgentOps 模型）：
   - Session waterfall（时间线 + 嵌套调用）
   - Trajectory view（扁平化消息历史）
   - Agent graph（多 agent 通信图）

3. **阈值告警设计**（LangSmith 模型）：
   - 多指标：error rate、latency、cost、dispatch failure
   - Filter scoping（per agent / per model / per task type）
   - Historical preview（设置阈值前预览历史触发情况）

4. **成本追踪是一等公民**（所有平台的共识）：
   - Token consumption per session and aggregate
   - Per-model cost breakdown
   - Cost anomaly detection

### 4.3 推荐初始阈值（适配 OpenClaw 规模）

| 指标 | 警告 | 严重 | 窗口 |
|------|------|------|------|
| Agent 错误率 | >5% | >15% | 5 min |
| Agent 延迟 p95 | >60s | >180s | 15 min |
| Task dispatch 失败率 | >2% | >10% | 5 min |
| 模型回退率 | >10% | >30% | 15 min |
| 并发 session 数 | >80% limit | >95% limit | 实时 |
| Session 超时率 | >5% | >15% | 15 min |

---

## 5. 推荐监控架构

### 5.1 设计原则

1. **内生优先** — 利用已有 session state event log 和 CronRunTelemetry，不引入外部依赖
2. **轻量级** — 个人 AI 助手场景，无需企业级可观测性平台
3. **Dashboard 为中心** — 所有监控信息汇聚到 Control UI
4. **渐进式** — 从最小可行方案起步，按需扩展

### 5.2 架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenClaw Gateway                          │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  Agent Loop  │  │  Cron Runner │  │  Channel    │          │
│  │  (per agent) │  │  + Watchdog  │  │  Router     │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘         │
│         │                 │                  │                │
│         ▼                 ▼                  ▼                │
│  ┌─────────────────────────────────────────────────┐        │
│  │         Session State Event Log (SQLite)         │        │
│  │  • message arrival  • tool execution             │        │
│  │  • compaction       • reset                      │        │
│  │  • lifecycle events • watch cursors              │        │
│  └─────────────────────┬───────────────────────────┘        │
│                        │                                     │
│         ┌──────────────┼──────────────┐                     │
│         ▼              ▼              ▼                      │
│  ┌────────────┐ ┌────────────┐ ┌──────────────┐             │
│  │  Metrics    │ │  Alert     │ │  Audit Log   │             │
│  │  Aggregator │ │  Engine    │ │  (existing)  │             │
│  │  (new)      │ │  (new)     │ │              │             │
│  └──────┬──────┘ └──────┬─────┘ └──────────────┘             │
│         │               │                                     │
│         ▼               ▼                                     │
│  ┌──────────────────────────────────────────────┐           │
│  │           Control UI / Dashboard              │           │
│  │                                                │           │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────┐  │           │
│  │  │ Agent    │ │ Session  │ │  Alerts      │  │           │
│  │  │ Monitor  │ │ Explorer │ │  Panel       │  │           │
│  │  │ (改造)   │ │ (新)     │ │  (新)        │  │           │
│  │  └──────────┘ └──────────┘ └──────────────┘  │           │
│  └──────────────────────────────────────────────┘           │
│                                                              │
│  通知渠道:                                                    │
│  • Dashboard 内联告警横幅                                     │
│  • 主 Agent session 消息（通过 watch 系统）                    │
│  • 可选: Webhook → Slack/Discord/Telegram                    │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 核心组件说明

#### 5.3.1 Metrics Aggregator（新增）

**数据源：** Session State Event Log + CronRunTelemetry + Gateway RPC error logs

**聚合指标：**

| 指标类别 | 具体指标 | 数据来源 |
|----------|----------|----------|
| **Session 健康** | 活跃 session 数、平均存活时间、超时率 | session state events |
| **Agent 性能** | per-agent 延迟(p50/p95)、错误率、吞吐量 | session state events |
| **模型使用** | per-model 调用数、token 消耗、回退率 | CronRunTelemetry + model call events |
| **工具执行** | per-tool 调用数、错误率、平均耗时 | tool execution state events |
| **任务编排** | subagent spawn 成功率、完成时间分布、级联失败率 | session spawn/yield events |
| **系统资源** | 并发 session 数、内存占用（如可获取） | gateway health endpoint |

**实现方式：** 在 Gateway 内部添加一个 metrics aggregator 模块，定期（如每 30s）从 SQLite event log 聚合数据，缓存在内存中供 Dashboard 查询。

#### 5.3.2 Alert Engine（新增）

**告警流程：**

```
Metric Check → Threshold Evaluation → Dedup/Grouping → Notification Routing
```

**告警规则示例：**

```json
{
  "rules": [
    {
      "name": "agent-timeout",
      "metric": "session.duration",
      "condition": ">",
      "threshold_warning": 300,
      "threshold_critical": 900,
      "window_seconds": 60,
      "scope": { "agent_id": "*" },
      "dedup_key": ["agent_id", "session_key"],
      "cooldown_seconds": 900
    },
    {
      "name": "model-fallback-rate",
      "metric": "model.fallback_rate",
      "condition": ">",
      "threshold_warning": 0.10,
      "threshold_critical": 0.30,
      "window_seconds": 900,
      "scope": { "provider": "*" }
    },
    {
      "name": "subagent-spawn-failure",
      "metric": "subagent.spawn_failure_rate",
      "condition": ">",
      "threshold_warning": 0.02,
      "threshold_critical": 0.10,
      "window_seconds": 300
    }
  ]
}
```

**去重策略：**
- Alert fingerprint = hash(metric_type, agent_id, error_code, severity)
- 同一 fingerprint 在 cooldown 窗口内只通知一次
- 依赖感知：如果 Agent A 因 Agent B 失败而失败，只告警 Agent B

**通知路由：**

| 严重度 | 通知方式 |
|--------|----------|
| Info | Dashboard 指示器（黄色标记） |
| Warning | Dashboard 横幅 + 主 agent session 消息 |
| Critical | Dashboard 横幅 + 主 agent session 消息 + 可选 webhook |

#### 5.3.3 利用已有 Watch 系统

OpenClaw 的 session watch system 天然支持跨 session 监控：

- Watcher session（如 main agent）订阅 target session（如 subagent）的 state events
- 当 target 发出新事件，系统自动更新 watcher 的 `last_seen_sequence` cursor
- **建议：** 让 main agent 或专门的 monitor agent watch 所有活跃 subagent session，在心跳中检查异常

---

## 6. Dashboard Agent Tab 改造方案

### 6.1 当前状态

Agent Tab 目前只展示 agent 状态（idle/running），功能极其简单。

### 6.2 改造目标

将 Agent Tab 从「静态状态列表」升级为「实时监控中心」，包含以下功能区：

### 6.3 改造后的 Agent Tab 布局

```
┌─────────────────────────────────────────────────────────────────┐
│  Agent Monitor                              [刷新] [设置] [告警🔔]│
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ⚠️ 告警摘要: research-searcher 超时 (8min) | dev-coder 回退率 35%│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Agent 总览卡片                            ││
│  │                                                              ││
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       ││
│  │  │ main     │ │ research │ │ search   │ │ dev-lead │       ││
│  │  │ 🟢 idle  │ │ 🟢 idle  │ │ 🔴 stuck │ │ 🟡 running│      ││
│  │  │ 0 active │ │ 2 active │ │ 1 (8min) │ │ 1 active │       ││
│  │  │ $0.12    │ │ $1.85    │ │ $3.20    │ │ $0.45    │       ││
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘       ││
│  │                                                              ││
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       ││
│  │  │ dev-coder│ │ dev-qa   │ │ citation │ │ reviewer │       ││
│  │  │ 🟡 running│ │ 🟢 idle  │ │ 🟢 idle  │ │ 🟢 idle  │       ││
│  │  │ 1 active │ │ 0 active │ │ 0 active │ │ 0 active │       ││
│  │  │ $2.10    │ │ $0.00    │ │ $0.00    │ │ $0.00    │       ││
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘       ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  选中 Agent 详情: research-searcher                          ││
│  │                                                              ││
│  │  状态: 🔴 卡住 (最后活动 8 分钟前)                            ││
│  │  当前 Session: agent:research-lead:subagent:abc123...       ││
│  │  任务: "搜索 LangGraph 监控文档"                              ││
│  │  开始时间: 23:30:15    持续: 8m 22s                          ││
│  │  模型: glmcode/glm-5.2    Token: 12.5k in / 3.2k out        ││
│  │  成本: $3.20    工具调用: 8 次 (6 成功 / 2 失败)              ││
│  │                                                              ││
│  │  ┌─ Session Timeline (Waterfall) ──────────────────────────┐││
│  │  │ 23:30:15 ████████ Session Created                        │││
│  │  │ 23:30:18 ██████████ Model Call (glm-5.2)                │││
│  │  │ 23:30:25 ████████████ Tool: web_search (2.1s)          │││
│  │  │ 23:30:32 ████████████ Tool: web_search (1.8s)          │││
│  │  │ 23:30:40 ████████████ Tool: web_fetch (3.5s)  ✗ FAILED │││
│  │  │ 23:30:48 ████████████ Tool: web_search (2.0s)          │││
│  │  │ 23:30:55 ████████████ Tool: web_fetch (4.2s)  ✗ FAILED │││
│  │  │ 23:31:02 ████████████ Model Call (glm-5.2)             │││
│  │  │ 23:31:10 ░░░░░░░░░░░░░ No activity (7+ minutes)         │││
│  │  └────────────────────────────────────────────────────────┘││
│  │                                                              ││
│  │  [查看完整日志] [终止 Session] [注入消息]                     ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  系统趋势 (最近 24h)                                         ││
│  │                                                              ││
│  │  Token 消耗: ████████████████████ $48.20                     ││
│  │  Session 数: ████████ 142 total / 3 active                   ││
│  │  错误率:     ██ 4.2% (warning threshold: 5%)                 ││
│  │  平均延迟:   ████████████ 45s p95                            ││
│  │  回退率:     ████ 12% (warning threshold: 10%)               ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 6.4 功能详细设计

#### 6.4.1 Agent 总览卡片（Overview Cards）

每个 agent 一张卡片，实时显示：

| 字段 | 来源 | 展示方式 |
|------|------|----------|
| Agent 名称 | `agents.entries` 配置 | 标题 |
| 状态 | session state event log | 🟢 idle / 🟡 running / 🔴 stuck / ⚫ error |
| 活跃 session 数 | session store count | 数字 |
| 今日 token 消耗 | CronRunTelemetry + model call events | `$金额` |
| 最后活动时间 | session state event log | "N min ago" |
| 当前任务摘要 | 最新 session 的 task 字段 | 简短文本 |

**状态判定逻辑：**

```
idle: 无活跃 session
running: 有活跃 session 且最近 state event < 2 min
stuck: 有活跃 session 但最近 state event > 5 min（可配置）
error: 最近 session 以 error 状态结束
```

#### 6.4.2 Agent 详情面板（Detail Panel）

点击 agent 卡片展开详情，包含三个子面板：

**A. Session Timeline（瀑布图）**

借鉴 AgentOps 的 session waterfall 设计：
- 每行一个事件（model call / tool call / message / state change）
- 横条长度 = 持续时间
- 颜色编码：蓝色=model call、绿色=tool success、红色=tool failure、灰色=wait
- 点击任意事件可展开详细信息（输入/输出、token 消耗、错误信息）

**B. 实时指标**

- 当前 session 的 token in/out
- 工具调用次数与成功率
- 模型调用次数与回退记录
- Session 持续时间

**C. 操作按钮**

- `查看完整日志` — 跳转到 transcript 视图
- `终止 Session` — 发送 abort 信号（利用已有 session management）
- `注入消息` — 向 session 发送 steering message（利用已有 `/steer` 机制）

#### 6.4.3 告警面板（Alerts Panel）

**Dashboard 顶部横幅** — 当有活跃告警时显示：

```
⚠️ [Critical] research-searcher session 卡住超过 8 分钟 (阈值: 5min)
⚠️ [Warning]  dev-coder 模型回退率 35% (阈值: 30%)
```

**告警设置页面** — 可配置：
- 阈值规则（per-agent 或全局）
- 通知方式（仅 Dashboard / + 主 session 消息 / + webhook）
- 冷却时间
- 静默时段（如 23:00-08:00）

#### 6.4.4 系统趋势面板（Trends Panel）

展示最近 24h（可切换 7d / 30d）的聚合指标：
- Token 消耗趋势图（按 agent 分色）
- Session 数量趋势
- 错误率趋势
- 模型分布饼图

### 6.5 Dashboard API 端点设计

基于现有 Gateway RPC 扩展：

| 端点 | 方法 | 用途 |
|------|------|------|
| `/api/agents/overview` | GET | 所有 agent 的状态摘要 |
| `/api/agents/:agentId/detail` | GET | 指定 agent 的详细指标 |
| `/api/agents/:agentId/sessions` | GET | 指定 agent 的活跃 session 列表 |
| `/api/agents/:agentId/sessions/:sessionId/timeline` | GET | Session 事件时间线 |
| `/api/agents/:agentId/sessions/:sessionId/abort` | POST | 终止 session |
| `/api/metrics/aggregate` | GET | 聚合指标（token/cost/error rate） |
| `/api/alerts/active` | GET | 当前活跃告警 |
| `/api/alerts/rules` | GET/PUT | 告警规则管理 |
| `/api/alerts/acknowledge` | POST | 确认告警 |
| `/api/trends` | GET | 历史趋势数据 |

### 6.6 数据流实现

```
Session State Event Log (SQLite)
        │
        ├──→ Metrics Aggregator (每 30s 轮询)
        │       │
        │       ├──→ In-memory metrics cache
        │       │       │
        │       │       └──→ Dashboard API (/api/metrics/*)
        │       │                   │
        │       │                   └──→ Control UI (Agent Tab)
        │       │
        │       └──→ Alert Engine (每次聚合后检查)
        │               │
        │               ├──→ Dashboard 横幅 (实时 push)
        │               ├──→ Main agent session (via watch system)
        │               └──→ Webhook (可选)
        │
        └──→ Session Timeline API (按需查询)
                │
                └──→ Dashboard 瀑布图
```

---

## 7. 实施路线图

### Phase 1: 基础监控（1-2 周）

**目标：** 让 Agent Tab 有用，能看到实时状态

| 任务 | 描述 | 复杂度 |
|------|------|--------|
| Metrics Aggregator 模块 | 从 session state event log 聚合 per-agent 指标 | 中 |
| Agent Overview Cards | Dashboard 改造：展示实时状态卡片 | 低 |
| Session Timeline | 瀑布图展示 session 事件 | 中 |
| 基础指标 API | `/api/agents/overview` + `/api/agents/:id/detail` | 低 |

### Phase 2: 告警闭环（2-3 周）

**目标：** 问题能主动发现并通知

| 任务 | 描述 | 复杂度 |
|------|------|--------|
| Alert Engine | 阈值检查 + 去重 + 通知路由 | 高 |
| 告警规则配置 | YAML/JSON 规则文件 + Dashboard 设置页 | 中 |
| Dashboard 告警横幅 | 实时 push 告警到 Control UI | 低 |
| Stuck session 检测 | 基于最后活动时间的自动检测 | 低 |
| Terminate/Steer 操作 | 从 Dashboard 操作 session | 中 |

### Phase 3: 趋势分析（3-4 周）

**目标：** 能看到历史趋势，辅助决策

| 任务 | 描述 | 复杂度 |
|------|------|--------|
| 指标持久化 | 将聚合指标写入 SQLite 持久化表 | 中 |
| Trends Panel | Dashboard 历史趋势图表 | 中 |
| Cost breakdown | Per-agent / per-model 成本分析 | 中 |
| Subagent 编排可视化 | 父子 session 关系图 | 高 |

### Phase 4: 高级功能（按需）

**目标：** 深度可观测性

| 任务 | 描述 | 复杂度 |
|------|------|--------|
| OpenTelemetry 导出 | 可选的 OTel span 导出（兼容 Jaeger/Langfuse） | 高 |
| Webhook 通知 | Slack/Discord/Telegram 外部通知 | 低 |
| 自动恢复 | 基于规则的自动 restart/fallback | 高 |
| Session replay | 完整对话回放（基于 transcript） | 中 |
| 异常检测 | 基于统计的自动异常检测（替代固定阈值） | 高 |

---

## 8. 附录

### 8.1 OpenClaw 监控相关 CLI 命令速查

```bash
# 系统健康
openclaw health                    # Gateway 健康
openclaw doctor                    # 完整健康检查
openclaw status                    # 渠道 + session 快照
openclaw gateway status            # Gateway daemon 状态

# 日志与审计
openclaw logs                      # 实时 gateway 日志
openclaw audit                     # Agent 运行审计
openclaw transcripts *             # 对话记录检查

# Session 与任务
openclaw sessions *                # Session 管理
openclaw tasks *                   # 后台任务/TaskFlow
openclaw system *                  # events/heartbeat/presence

# 模型与记忆
openclaw models *                  # 模型扫描与配置
openclaw memory *                  # 记忆搜索与重索引
```

### 8.2 关键配置项（openclaw.json）

```jsonc
{
  "agents": {
    "defaults": {
      "workspace": "~/.openclaw/workspace",
      // 可扩展: monitoring config
    },
    "entries": {
      "main": { /* ... */ },
      "research-lead": { /* ... */ },
      // ... 其他 agent
    }
  }
  // 建议新增配置节:
  // "monitoring": {
  //   "metricsAggregator": { "intervalSeconds": 30 },
  //   "alerts": { "rulesFile": "~/.openclaw/alert-rules.json" },
  //   "trends": { "retentionDays": 30 }
  // }
}
```

### 8.3 行业调研参考文档

- 完整行业调研报告: `shared/results/work/R-189-industry-reference.md`
- AutoGen OTel: https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/framework/telemetry.html
- LangSmith Alerts: https://docs.langchain.com/langsmith/alerts
- Langfuse: https://langfuse.com/docs
- AgentOps: https://docs.agentops.ai
- OpenTelemetry GenAI Semantic Conventions: https://opentelemetry.io/docs/specs/semconv/gen-ai/

### 8.4 OpenClaw 文档参考

- Agent Loop and Sessions: https://zread.ai/openclaw/openclaw/9-agent-loop-and-sessions
- Cron Jobs and Webhooks: https://zread.ai/openclaw/openclaw/18-cron-jobs-and-webhooks
- Channel Routing and Delivery: https://zread.ai/openclaw/openclaw/10-channel-routing-and-delivery
- Gateway Protocol and RPC: https://zread.ai/openclaw/openclaw/25-gateway-protocol-and-rpc
- Configuration Reference: https://zread.ai/openclaw/openclaw/24-configuration-reference
- Built-in Tools Overview: https://zread.ai/openclaw/openclaw/16-built-in-tools-overview

---

## 变更日志

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-08-09 | v1.0 | 初版：现状盘点、缺口分析、架构设计、Dashboard 改造方案、实施路线图 |
