# OpenClaw 多Agent编排能力分析报告

> **生成时间**: 2026-08-10 02:30 CST  
> **分析目的**: 为外部系统集成设计提供OpenClaw能力参考  
> **版本**: OpenClaw 2026.7.1-2 (MIT License)  
> **运行环境**: 腾讯云 VPS 82.156.124.186 | Linux 6.8.0-124-generic | Node.js v22.23.2

---

## 目录

1. [系统概述](#1-系统概述)
2. [会话管理（Session Management）](#2-会话管理)
3. [Agent派生与通信（Agent Spawning & Communication）](#3-agent派生与通信)
4. [ACP协议集成（ACP Protocol）](#4-acp协议集成)
5. [Cron调度与自动化（Cron & Automations）](#5-cron调度与自动化)
6. [任务中心/仪表盘（Task Center / Dashboard）](#6-任务中心仪表盘)
7. [SSH/ZeroTier连通性](#7-sshzerotier连通性)
8. [微信通知模式（WeChat Notification Patterns）](#8-微信通知模式)
9. [配置系统](#9-配置系统)
10. [外部集成设计建议](#10-外部集成设计建议)

---

## 1. 系统概述

OpenClaw 是一个**本地优先的个人AI助手网关**（Personal AI Assistant Gateway），运行在用户自有设备上。

### 核心架构

```
┌──────────────────────────────────────────────────────────┐
│                    OpenClaw Gateway                       │
│                   (守护进程, 默认 127.0.0.1:18789)         │
│                                                          │
│  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌───────────┐ │
│  │ 消息通道  │  │ Agent    │  │ Cron    │  │ Tool      │ │
│  │ Channels │  │ Runtime  │  │ Scheduler│  │ Registry  │ │
│  └────┬─────┘  └────┬─────┘  └────┬────┘  └─────┬─────┘ │
│       │              │              │             │       │
│  ┌────▼──────────────▼──────────────▼─────────────▼────┐ │
│  │              WebSocket Control Plane                 │ │
│  │         (JSON Schema 校验, 事件推送)                   │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌───────────┐ │
│  │ SQLite   │  │ Skills   │  │ Sandbox │  │ Memory    │ │
│  │ State DB │  │ System   │  │ Runtime │  │ Engine    │ │
│  └─────────┘  └──────────┘  └─────────┘  └───────────┘ │
└──────────────────────────────────────────────────────────┘
         │              │                │
    ┌────▼────┐   ┌─────▼─────┐   ┌─────▼─────┐
    │ Nodes   │   │ Control   │   │ External  │
    │ (macOS/ │   │ UI (Web)  │   │ Services  │
    │ iOS/    │   │ CLI       │   │ (Webhook) │
    │ Android)│   │           │   │           │
    └─────────┘   └───────────┘   └───────────┘
```

### 关键特征（实际部署配置）

- **单网关架构**: 每台主机运行一个Gateway实例，统一管理所有消息面、工具、事件
- **WebSocket通信**: 控制面板客户端和节点均通过WebSocket连接
- **JSON Schema校验**: 所有入站帧根据JSON Schema严格校验
- **JSON5配置**: 配置文件 `~/.openclaw/openclaw.json` (JSON5格式)
- **运行端口**: `12145`（非默认18789），绑定模式 `lan`，Control UI路径 `/df0s6p`
- **认证模式**: token模式，`dangerouslyDisableDeviceAuth: true`
- **子Agent限制**: 最大8个并发，嵌套深度4层，超时2400秒，60分钟后归档
- **Heartbeat**: 每30分钟
- **Compaction**: safeguard模式，150K token下限

### 已配置的消息通道

| 通道 | 状态 | 说明 |
|------|------|------|
| **lightclawbot** | ✅ 启用 | 站点=cn, 2个API Key + 1个账户 |
| **qqbot** | ✅ 启用 | appId=1903765716, 2个账户 |
| **openclaw-weixin (微信)** | ✅ 启用 | 暂无账户配置 |
| **telegram** | ❌ 禁用 | Bot token已配置 |
| **webchat** | ✅ 默认 | Web聊天界面 |

### OpenClaw官方支持的完整通道列表

WhatsApp, Telegram, Slack, Discord, Google Chat, Signal, iMessage, IRC, Microsoft Teams, Matrix, Feishu（飞书）, LINE, Mattermost, Nextcloud Talk, Nostr, Synology Chat, Tlon, Twitch, Zalo, Zalo Personal, **WeChat（微信）**, **QQ**, WebChat

---

## 2. 会话管理

### 会话路由机制

OpenClaw 根据消息来源将每条入站消息路由到一个**会话（Session）**：

| 来源 | 行为 |
|------|------|
| 直接消息 (DM) | 默认共享会话 |
| 群聊 | 按群隔离 |
| 频道/房间 | 按频道隔离 |
| Cron作业 | 每次运行全新会话 |
| Webhook | 按hook隔离 |

### DM隔离级别配置

```json5
{
  session: {
    dmScope: "per-channel-peer",  // 推荐多用户场景
    // 可选值: "main" | "per-peer" | "per-channel-peer" | "per-account-channel-peer"
    identityLinks: [  // 跨通道身份映射
      { peers: ["tg:123", "wa:+8613800138000"] }
    ]
  }
}
```

### 会话工具 (Session Tools)

- `sessions_list`: 列出其他会话（含子Agent）
- `sessions_history`: 获取其他会话/子Agent的历史记录
- `sessions_send`: 向其他会话发送消息
- `sessions_spawn`: 派生子Agent或ACP编码会话

### 会话类型

- **主会话 (main)**: 用户的主要对话会话，所有DM默认汇聚
- **子Agent会话 (subagent)**: 通过 `sessions_spawn` 创建的隔离工作会话
- **Incognito会话**: 仅存在于内存中，重启后消失，不写入磁盘
- **Cron会话**: 调度任务每次运行创建的隔离会话

### 会话标识符格式

```
agent:{agentName}:subagent:{uuid}           // 子Agent会话
agent:{agentName}:channel:{channelName}      // 通道会话
incognito-{uuid}                             // 隐身会话
```

---

## 3. Agent派生与通信

### 派生机制

通过 `sessions_spawn` 工具实现Agent派生，支持两种运行时：

#### 3.1 原生子Agent (runtime: "subagent")

```json
{
  "task": "分析A股市场情绪指标",
  "runtime": "subagent",
  "mode": "run",
  "taskName": "sentiment-analysis",
  "context": "isolated"  // 或 "fork" 需要父会话上下文
}
```

**特征**:
- 继承父工作空间
- 支持嵌套派生（最大深度限制）
- 自动推送完成事件给父会话（push-based）
- 每个子Agent获得完整任务描述

#### 3.2 ACP Harness会话 (runtime: "acp")

```json
{
  "task": "重构quant-evolve数据管道",
  "runtime": "acp",
  "agentId": "claude",
  "mode": "run"
}
```

**支持的Harness ID**:
- `claude` (Claude Code)
- `codex` (OpenAI Codex)
- `copilot` (GitHub Copilot)
- `cursor` (Cursor CLI)
- `gemini` (Gemini CLI)
- `opencode`, `qwen`, `kiro`, `kimi`, `iflow`, `droid`, `kilocode`
- `openclaw` (OpenClaw自身ACP)

### 通信模式

```
                    ┌─────────────────┐
                    │ Parent Orchestrator │
                    │ (主编排Agent)       │
                    └────────┬────────┘
                             │
              sessions_spawn │
               ┌─────────────┼─────────────┐
               ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ Child A  │  │ Child B  │  │ Child C  │
        │ (subagent)│  │ (acp)   │  │ (subagent)│
        └──────────┘  └──────────┘  └──────────┘
               │             │             │
               └─────────────┼─────────────┘
                             │
                    自动推送完成事件 │
                             ▼
                    ┌─────────────────┐
                    │ Parent 收到结果   │
                    │ 综合报告返回      │
                    └─────────────────┘
```

### 关键通信规则

- **Push-based完成通知**: 子Agent完成后自动向父Agent推送结果
- **非轮询**: 不应使用 `sessions_list` 进行忙轮询
- `sessions_yield`: 当需要等待子Agent完成时使用
- **最大嵌套深度**: 当前配置为 4 层 (depth/4)
- **结果综合**: 父Agent负责协调和综合所有子Agent结果

---

## 4. ACP协议集成

### ACP (Agent Client Protocol) 概述

OpenClaw 实现了 ACP 协议，允许与外部编码Agent框架标准化交互：

- **SDK依赖**: `@agentclientprotocol/sdk@1.1.0`
- **MCP支持**: `@modelcontextprotocol/sdk@1.29.0`

### ACP运行时路径

#### 路径1: OpenClaw ACP Runtime（默认）

通过 `sessions_spawn` + `runtime: "acp"` 使用OpenClaw内置的ACP生命周期管理。

#### 路径2: 直接acpx驱动（"电话游戏"模式）

通过 `acpx` CLI直接驱动外部Harness会话：

```bash
# 设置环境
ACPX_PLUGIN_ROOT="<bundled-acpx-plugin-root>"
ACPX_CMD="$ACPX_PLUGIN_ROOT/node_modules/.bin/acpx"

# 创建持久会话
${ACPX_CMD} codex sessions new --name oc-codex-${conversationId}

# 发送提示
${ACPX_CMD} codex -s oc-codex-${conversationId} --cwd /workspace --format quiet "分析数据"

# 一次性执行
${ACPX_CMD} codex exec --cwd /workspace --format quiet "快速分析"
```

### 内置适配器命令

| Harness | 适配器命令 |
|---------|-----------|
| openclaw | `openclaw acp` |
| claude | `@agentclientprotocol/claude-agent-acp@0.55.0` |
| codex | `@zed-industries/codex-acp@0.16.0` |
| copilot | `copilot --acp --stdio` |
| cursor | `cursor-agent acp` |
| gemini | `gemini --acp` |
| kimi | `kimi acp` |
| kiro | `kiro-cli acp` |
| opencode | `npx -y opencode-ai acp` |
| qwen | `qwen --acp` |

### 插件系统

OpenClaw 的 `plugin-sdk` 暴露了大量模块化运行时接口：

- `acp-runtime`: ACP会话运行时
- `acp-binding-runtime`: ACP绑定运行时
- `cron-store-runtime`: Cron存储运行时
- `session-store-runtime`: 会话存储运行时
- `agent-runtime`: Agent执行运行时
- `gateway-runtime`: 网关运行时
- `plugin-runtime`: 插件加载运行时

---

## 5. Cron调度与自动化

### Automations系统

OpenClaw 内置调度器，取代传统系统cron：

```bash
# 创建一次性提醒
openclaw automations create "2027-02-01T16:00:00Z" \
  --name "数据更新提醒" \
  --session main \
  --system-event "提醒: 检查因子库更新" \
  --wake now \
  --delete-after-run

# 创建周期任务
openclaw automations create --cron "0 9 * * 1-5" \
  --name "盘前分析" \
  --session main \
  --system-event "执行A股盘前数据分析"

# 管理任务
openclaw automations list
openclaw automations get <job-id>
openclaw automations runs --id <job-id>
```

### 关键特性

- **Gateway内运行**: 调度器在Gateway进程内运行，不依赖系统cron
- **持久化存储**: 作业定义和运行历史存储在SQLite数据库中
- **自动恢复**: Gateway重启后，逾期任务自动重新调度
- **后台任务记录**: 每次自动化运行创建后台任务记录
- **超时保护**: 
  - Agent轮任务: 调度器60分钟看门狗 + `agents.defaults.timeoutSeconds`（默认48小时）
  - 命令任务: 默认10分钟
  - 脚本任务: 默认5分钟
- **一次性任务**: `--at` 参数，默认成功后自动删除
- **会话投递**: 可指定投递到哪个会话 (`--session`)
- **通道投递**: 可指定投递到哪个聊天通道

### 调度 vs Heartbeat

| 特性 | Automations (Cron) | Heartbeat |
|------|-------------------|-----------|
| 精确时间 | ✅ 精确到秒 | ❌ ~30分钟漂移 |
| 隔离会话 | ✅ 每次全新 | ❌ 主会话内 |
| 自定义模型 | ✅ 支持 | ❌ 继承主会话 |
| 批量检查 | ❌ 每任务独立 | ✅ 可合并多检查 |
| 一次性提醒 | ✅ 支持 | ❌ 不适合 |

---

## 6. 任务中心/仪表盘

### TaskFlow 系统

OpenClaw 提供 **TaskFlow** 用于编排多步骤、可持续化的后台任务：

```typescript
const taskFlow = api.runtime.tasks.flow.fromToolContext(ctx);

// 创建托管Flow
const flow = taskFlow.createManaged({
  controllerId: "quant/data-pipeline",
  goal: "执行因子计算管道",
  currentStep: "fetch-data",
  stateJson: { symbols: [], factors: [] }
});

// 运行子任务
taskFlow.runTask({
  flowId: flow.flowId,
  runtime: "acp",
  childSessionKey: "agent:main:subagent:factor-calc",
  task: "计算动量因子",
  status: "running"
});

// 等待外部事件
taskFlow.setWaiting({
  flowId: flow.flowId,
  expectedRevision: flow.revision,
  currentStep: "await-data",
  waitJson: { kind: "reply", channel: "webhook" }
});

// 恢复执行
taskFlow.resume({ flowId: flow.flowId, ... });
taskFlow.finish({ flowId: flow.flowId, ... });
```

### TaskFlow 生命周期

```
createManaged → runTask → setWaiting → resume → finish/fail
                                      ↓
                                  requestCancel → cancel
```

### 关键特性

- **持久状态**: `stateJson` 作为状态包在步骤间持久化
- **修订跟踪**: 每次变更进行修订号校验，防止冲突
- **子任务链接**: `runTask()` 将子任务链接到Flow
- **取消传播**: `cancel()` 可同时取消所有关联的活跃子任务
- **健康检查**: `getTaskSummary(flowId)` 获取子任务健康概览

### Control UI (仪表盘)

- **访问地址**: `http://127.0.0.1:12145/df0s6p` (实际部署)
- **功能**: 
  - 配置管理（表单 + 原始JSON编辑）
  - 会话查看和管理
  - 自动化/Cron任务管理
  - 健康监控
  - 实时聊天（WebChat）

### 外部任务中心 (Task Center)

实际部署中还有一个独立的外部任务编排服务：

- **API端点**: `http://127.0.0.1:8055/api/tasks`
- **技术**: 独立Node.js服务
- **用途**: 更复杂的任务编排和工作流管理
- **集成方式**: 通过main agent的HEARTBEAT.md进行轮询检查

### Memory后端

- **memory-tencentdb**: 腾讯云数据库插件，持久化长期记忆
- **嵌入模型**: embedding-3 (智谱API)
- **搜索**: 支持语义搜索

---

## 7. SSH/ZeroTier连通性

### 远程访问方式

#### 方式1: Tailscale（推荐）

```json5
{
  gateway: {
    auth: {
      allowTailscale: true  // 允许Tailscale身份认证
    }
  }
}
```

- 支持Tailscale Serve作为身份认证模式
- 无需共享密钥
- 自动加密传输

#### 方式2: SSH隧道

```bash
# 本地端口转发
ssh -N -L 18789:127.0.0.1:18789 user@gateway-host

# 然后本地访问
openclaw gateway status  # 连接到远程Gateway
```

#### 方式3: 直接暴露（需谨慎）

```json5
{
  gateway: {
    bind: "0.0.0.0",  // 绑定所有接口
    auth: {
      mode: "token",  // 必须启用认证
      token: "strong-secret"
    }
  }
}
```

### 节点连接

- macOS/iOS/Android 设备作为 **Node** 连接
- WebSocket连接，声明 `role: node`
- 基于设备的配对审批机制
- 支持能力声明（caps/commands）

### 安全模型

- **沙箱模式**: `agents.defaults.sandbox.mode: "non-main"` 对非主会话启用沙箱
- **Docker沙箱**: 默认后端，也支持SSH和OpenShell后端
- **DM配对**: 未知发送者收到配对码，需手动审批
- **工具限制**: 沙箱默认禁止 browser, canvas, nodes, cron, discord, gateway

### ZeroTier集成（实际部署）

当前环境已在使用ZeroTier进行设备互联：

- **Synology NAS**: `10.12.192.241` (通过ZeroTier虚拟网络访问)
- **Docker容器**: NAS上运行多个Docker容器服务
- **SSH凭据**: 存储在main workspace的TOOLS.md中
- **GitHub仓库**: `evoclaw` (OpenClaw配置版本控制)

ZeroTier与OpenClaw配合方式：
1. **网络层**: ZeroTier创建虚拟局域网，Gateway可绑定ZeroTier接口IP
2. **设备互联**: 通过ZeroTier IP直接SSH/访问NAS等设备
3. **Node连接**: 远程Node可通过ZeroTier网络连接Gateway WebSocket

---

## 8. 微信通知模式

### WeChat通道集成

OpenClaw 内置 WeChat 通道支持：

```json5
{
  channels: {
    wechat: {
      enabled: true,
      dmPolicy: "pairing",   // 配对模式
      allowFrom: ["wx:wxid_xxx"]
    }
  }
}
```

### 通知投递路径

```
Agent/Cron任务 → Gateway → WeChat通道 → 用户微信
                     │
                     ├→ 消息发送 (send)
                     ├→ 系统事件推送
                     └→ Heartbeat检查结果
```

### QQ通道（补充）

```json5
{
  channels: {
    qqbot: {
      enabled: true,
      // QQ频道管理
      // 支持富媒体发送（图片、语音、视频、文件）
      // 支持定时提醒
    }
  }
}
```

### 多通道路由策略

OpenClaw 支持将同一Agent的输出路由到多个通道：

- **DM共享**: 所有DM通道共享主会话
- **通道停靠 (Channel Docking)**: 将当前回复路由切换到另一通道
- **Webhook触发**: 外部系统通过Webhook触发Agent响应并投递到指定通道

---

## 9. 配置系统

### 配置文件

- **路径**: `~/.openclaw/openclaw.json` (JSON5格式)
- **热重载**: Gateway监视配置文件变更并自动应用
- **严格校验**: 配置必须完全匹配schema，否则Gateway拒绝启动
- **回退机制**: 保留最后已知良好配置副本

### 已配置的Agent定义（6个Agent）

| Agent ID | 名称 | 工作空间 | 主要模型 | 角色 |
|----------|------|-----------|----------|------|
| `main` | 小朱桑 🦞 | `/root/.openclaw/workspace` | glmcode/glm-5.2 | 总调度/分发器 |
| `research-lead` | 研究主管 | `/root/.openclaw/workspace-research` | glmcode/glm-5.2 | 研究团队负责人 |
| `research-searcher` | 研究搜索员 | `/root/.openclaw/workspace-search` | glmcode/glm-5.2 | 搜索专员 |
| `research-reviewer` | 研究审核员 | `/root/.openclaw/workspace-reviewer` | glmcode/glm-5.2 | 审核专员 |
| `research-citation` | 研究引用员 | `/root/.openclaw/workspace-citation` | glmcode/glm-5.2 | 引用专员 |
| `quant-compute` | 量化员 | `/root/.openclaw/workspace-quant` | deepseek-v4-flash | 量化计算 |

### Agent派生层次结构

```
main (小朱桑)
├── research-lead (研究主管)
│   ├── research-searcher (搜索员)
│   ├── research-reviewer (审核员)
│   ├── research-citation (引用员)
│   └── quant-compute (量化员)
├── claude (ACP)
└── quant-compute (量化员)
```

### 已配置的模型提供商

| 提供商 | API端点 | 模型 | 说明 |
|--------|---------|------|------|
| **glmcode** (智谱) | `open.bigmodel.cn/api/coding/paas/v4` | GLM-5.2 (1M ctx), GLM-5.1, GLM-5-Turbo, glm-4.7/4.6/4.5-air | 主力模型 |
| **deepseek** | `api.deepseek.com/v1` | DeepSeek V4 Flash/Pro | 推理模型 (200K ctx) |
| **volcengine-agent-plan** (火山方舟) | `ark.cn-beijing.volces.com/api/plan/v3` | ark-code-latest, glm-5.2, deepseek-v4-flash/pro, doubao-seed-2.0 | 备用提供商 |

**模型Failover链**: GLM-5.2 → GLM-5.1 → deepseek-v4-flash → volcengine deepseek-v4-pro/flash

### 已配置的MCP服务器

| 服务器 | 协议 | 用途 |
|--------|------|------|
| `luckin` (瑞幸咖啡) | streamable-http | 瑞幸咖啡点单 |
| `web-search-prime` | SSE | 智谱网络搜索 |
| `zhipu-reader` | SSE | 智谱网页阅读 |
| `zread` | SSE | 智谱文档阅读 |

### 已启用的插件 (7个)

`browser`, `acpx`, `parallel`, `qqbot`, `openclaw-weixin`, `lightclawbot`, `memory-tencentdb`

### ACP配置

- **默认Agent**: `claude`
- **允许的Harness**: claude, codex, gemini, opencode

### 配置操作方式

```bash
# CLI读写
openclaw config get agents.defaults.workspace
openclaw config set agents.defaults.heartbeat.every "2h"

# Schema查询
openclaw config schema
# 或通过gateway工具:
config.schema.lookup  # 查询单个路径的schema
config.schema.get     # 获取配置值
config.schema.patch   # 补丁修改
config.schema.apply   # 应用配置
```

---

## 10. 外部集成设计建议

### 10.1 量化系统集成架构

#### 现有量化基础设施（已部署）

当前系统已建立完整的量化计算环境，分布在两台设备上：

```
┌───────────────────────────────────────────────────────────────┐
│              本地 HP 800 G1 (计算主力)                          │
│            10.12.192.174 (ZeroTier内网, SSH免密)                │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  ~/quant-evolve/                                        │ │
│  │  ├── data/all_stocks_qfq/   5205只A股日K线 (parquet)    │ │
│  │  ├── data/financial-ths/    同花顺财务数据               │ │
│  │  ├── data/*.parquet         指数数据 (沪深300/中证500)   │ │
│  │  ├── scripts/               Python计算脚本               │ │
│  │  └── results/               回测结果/图表/报告            │ │
│  │       ├── factor-db.json    因子库快照 (Dashboard消费)   │ │
│  │       ├── evolution-history.json  进化历史               │ │
│  │       └── quant-summary.json 最新回测摘要               │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  Python: ~/miniconda3/envs/quant/bin/python3 (3.11+Qlib+     │
│          AKShare+pandas+backtrader+vectorbt)                  │
└───────────────────────────┬───────────────────────────────────┘
                            │ SSH (ZeroTier)
                            │ rsync 同步结果
                    ┌───────▼───────┐
                    │   VPS (编排)   │
                    │  腾讯云 82.156  │
                    │  124.186       │
                    │  2核3.6G内存    │
                    │               │
                    │ ┌───────────┐ │
                    │ │OpenClaw   │ │ ← quant-compute Agent
                    │ │Gateway    │ │   (编排, 不跑计算)
                    │ │:12145     │ │
                    │ └─────┬─────┘ │
                    │       │       │
                    │ ┌─────▼─────┐ │
                    │ │ 通知通道   │ │
                    │ │ WeChat/QQ │ │
                    │ └───────────┘ │
                    └───────────────┘
```

#### 数据契约（Dashboard消费）

quant-evolve项目已定义严格的JSON数据契约：

n**`factor-db.json`（因子库快照）**:
```json
[{"id":"market_cap","name":"总市值","status":"active",
  "ic_mean":0.035,"ic_ir":1.2,"weight":1.0,
  "source":"seed","created_at":"2026-08-09",
  "llm_hypothesis":""}]
```

**`evolution-history.json`（进化历史）**:
```json
[{"iteration":1,"date":"2026-08-09",
  "actions":[{"type":"propose","factor_id":"xxx","details":"..."}],
  "backtest_nav":537323,"backtest_sharpe":0.941}]
```

**`quant-summary.json`（最新回测摘要）**:
```json
{"nav":537323,"total_return":4.37,"annual_return":0.1934,
 "sharpe":0.941,"max_drawdown":-0.2359,"calmar":0.82,
 "last_update":"2026-08-09"}
```

#### 目标集成架构

```
┌─────────────────────────────────────────────────────────────┐
│                     外部量化系统                              │
│                                                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ 数据源    │  │ 因子计算  │  │ 回测引擎  │  │ Dashboard │  │
│  │ (AKShare)│  │ (Qlib)   │  │(vectorbt)│  │ (Node.js) │  │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘  │
│        └─────────────┴─────────────┴─────────────┘        │
│              本地 HP 800 G1 (10.12.192.174)                │
└───────────────────────────┼────────────────────────────────┘
                            │ SSH/rsync
                    ┌───────▼───────┐
                    │   OpenClaw    │
                    │   Gateway     │
                    │   (VPS)       │
                    │               │
                    │ ┌───────────┐ │
                    │ │ Webhook    │ │  ← 接收外部触发
                    │ │ Ingress   │ │
                    │ └─────┬─────┘ │
                    │       │       │
                    │ ┌─────▼─────┐ │
                    │ │quant-     │ │  ← SSH到HP执行计算
                    │ │compute    │ │
                    │ └─────┬─────┘ │
                    │       │       │
                    │ ┌─────▼─────┐ │
                    │ │ Cron      │ │  ← 定时任务
                    │ │ Scheduler │ │
                    │ └─────┬─────┘ │
                    │       │       │
                    │ ┌─────▼─────┐ │
                    │ │ Channel   │ │  ← 通知投递
                    │ │ Router    │ │
                    │ └───────────┘ │
                    └───────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         ┌────────┐  ┌────────┐  ┌────────┐
         │ WeChat │  │  QQ    │  │WebChat │
         │ 微信   │  │        │  │        │
         └────────┘  └────────┘  └────────┘
```

#### 全局路径规范

系统已定义严格的路径契约（PATHS.md），关键路径：

| 名称 | 路径 |
|------|------|
| 全局共享目录 | `/root/.openclaw/workspace/shared/` |
| 研究报告 | `/root/.openclaw/workspace/shared/results/` (R-xxx.md) |
| 投资研究报告 | `.../shared/results/04-投资研究/` |
| 量化结果同步 | `.../shared/results/04-投资研究/*.json` |
| quant workspace | `/root/.openclaw/workspace-quant/` |
| quant-evolve项目 | `~/quant-evolve/` (本地HP) |
| 任务完成记录 | `/root/.openclaw/workspace/scripts/.task-completions.jsonl` |

### 10.2 推荐集成路径

#### A. 数据更新通知（外部 → OpenClaw → 用户）

```
外部数据源 → Webhook POST → Gateway → Agent分析 → 微信/QQ推送
```

**Webhook配置**:
```json5
{
  // OpenClaw支持webhook ingress
  // 外部系统通过HTTP POST触发Agent响应
}
```

#### A2. 量化计算触发（已有模式）

quant-compute Agent 已建立完整的SSH远程计算模式：
```bash
#quant-compute通过SSH调用本地HP执行计算
ssh noname@10.12.192.174 'cd ~/quant-evolve && ~/miniconda3/envs/quant/bin/python3 scripts/backtest_momentum.py'

#结果同步回VPS
rsync -avz ~/quant-evolve/results/*.json \
  ~/quant-evolve/results/*.md \
  root@10.12.192.225:/root/.openclaw/workspace/shared/results/04-投资研究/
```

**关键纪律**: VPS (2核3.6G) 仅做编排，所有计算在本地HP执行

#### B. 定时分析任务（OpenClaw内部）

```bash
# 每个交易日盘前8:30执行
openclaw automations create --cron "30 8 * * 1-5" \
  --name "盘前量化分析" \
  --session main \
  --system-event "执行盘前分析流程" \
  --timeout-seconds 600
```

#### C. Agent编排（多Agent协作，已实现）

当前系统已建立的Agent编排层次：
```
main (小朱桑, 总调度)
├── research-lead (研究主管)
│   ├── research-searcher (搜索员)    → 文献/资料搜索
│   ├── research-reviewer (审核员)    → 内容审核
│   ├── research-citation (引用员)    → 引用验证
│   └── quant-compute (量化员)        → SSH到HP执行计算
├── dev-lead (开发主管)
│   ├── dev-designer (设计师)
│   ├── dev-coder (编码员)
│   └── dev-qa (测试员)
└── claude/gemini/codex (ACP编码Agent)
```

**扩展建议** — 量化专用编排：
```
research-lead (主编排)
├── data-fetcher (subagent)     → SSH获取HP上的市场数据快照
├── factor-calculator (quant)    → SSH到HP计算因子
├── signal-generator (quant)    → SSH到HP生成信号
└── report-formatter (subagent)  → 格式化报告并投递
```

#### D. ACP编码任务

```json
{
  "task": "重构quant-evolve的因子计算模块",
  "runtime": "acp",
  "agentId": "claude",
  "mode": "run"
}
```

### 10.3 关键设计原则

1. **单网关原则**: 所有通信通过Gateway，不绕过
2. **异步优先**: 使用Cron/Automations进行调度，避免阻塞
3. **Webhook桥梁**: 外部系统通过Webhook与OpenClaw交互
4. **多通道投递**: 优先微信/QQ推送，WebChat为备用
5. **沙箱隔离**: 外部触发的任务应在沙箱中运行
6. **状态持久化**: 重要状态写入SQLite或workspace文件系统
7. **TaskFlow编排**: 复杂多步骤任务使用TaskFlow管理生命周期

### 10.4 API接口要点

| 接口 | 方法 | 用途 |
|------|------|------|
| WebSocket `connect` | 必须 | 建立连接 |
| WebSocket `req:agent` | POST | 触发Agent响应 |
| WebSocket `req:send` | POST | 发送消息 |
| WebSocket `event:agent` | Subscribe | 接收Agent流式输出 |
| Webhook Ingress | HTTP POST | 接收外部触发 |
| `openclaw automations` | CLI | 管理调度任务 |
| `openclaw config` | CLI | 管理配置 |
| `config.schema.*` | Gateway工具 | 编程式配置管理 |

---

## 附录A: 关键技术栈

| 组件 | 技术 |
|------|------|
| 运行时 | Node.js 22.22.3+ / 24.15+ / 25.9+ |
| 通信协议 | WebSocket + JSON |
| 配置格式 | JSON5 |
| 状态存储 | SQLite (Kysley ORM) |
| 包管理 | pnpm |
| ACP SDK | @agentclientprotocol/sdk@1.1.0 |
| MCP SDK | @modelcontextprotocol/sdk@1.29.0 |
| 浏览器自动化 | Playwright |
| 向量搜索 | sqlite-vec (可选) |
| TTS | ElevenLabs + 系统TTS |
| 模板 | TypeBox + JSON Schema |

## 附录C: 开发团队Agent

除研究团队外，系统还配置了开发团队Agent（定义在PATHS.md中）：

| Agent | Workspace | 角色 |
|-------|-----------|------|
| `dev-lead` | `/root/.openclaw/workspace-dev/` | 开发主管，维护PRODUCT.md |
| `dev-designer` | `/root/.openclaw/workspace-dev-init/` | 设计师，创建feature_list.json |
| `dev-coder` | `/root/.openclaw/workspace-dev-coder/` | 编码员，实现功能 |
| `dev-qa` | `/root/.openclaw/workspace-dev-qa/` | 测试员，验证功能 |

### 开发团队工作流

```
研究团队 → 研究报告(R-xxx.md) → Main Agent → dev-lead
                                                ↓
                                    dev-lead初始化项目
                                    ├── PRODUCT.md (活文档)
                                    ├── dev-designer → feature_list.json + init.sh
                                    ├── dev-coder → 实现功能代码
                                    └── dev-qa → 验证 + 更新passes
```

### 团队间文件传递

```
研究报告: /root/.openclaw/workspace/shared/results/R-xxx.md
项目文件: /root/.openclaw/workspace-dev/<项目名>/
任务完成: /root/.openclaw/workspace/scripts/.task-completions.jsonl
```

---

## 附录D: 量化计算环境详情

### Python环境（本地HP）
- **路径**: `/home/noname/miniconda3/envs/quant/bin/python3`
- **版本**: Python 3.11
- **关键库**: Qlib, AKShare, pandas, backtrader, vectorbt, matplotlib, seaborn

### Python环境（VPS）
- **路径**: `/root/.openclaw/workspace-quant/venv-quant/bin/python3`
- **版本**: Python 3.12+
- **关键库**: akshare, pandas, numpy, scipy, backtrader, vectorbt, matplotlib, seaborn
- **注意**: VPS环境仅用于轻量数据处理，不跑回测

### 数据资产（本地HP）
| 数据 | 路径 | 说明 |
|------|------|------|
| A股日K线 | `data/all_stocks_qfq/` | 5205只股票，前复权 |
| 财务数据 | `data/financial-ths/` | 同花顺财务指标 |
| 指数数据 | `data/*.parquet` | 沪深300/中证500等 |

### AKShare常用接口
```python
import akshare as ak

# 指数日K线
ak.index_zh_a_hist(symbol="000300", period="daily", start_date="20200101", end_date="20260808")

# 个股日K线 (前复权)
ak.stock_zh_a_hist(symbol="000001", period="daily", start_date="20200101", adjust="qfq")

# 财务指标
ak.stock_financial_analysis_indicator(symbol="000001")

# 全市场股票列表
ak.stock_info_a_code_name()
```

---

## 附录B: 已安装的插件技能

### 系统内置技能
- **clawhub**: 技能市场搜索/安装
- **diagram-maker**: SVG/HTML图表制作
- **healthcheck**: 主机安全审计
- **mcporter**: MCP服务器管理
- **meme-maker**: 表情包生成
- **node-connect**: 节点配对诊断
- **notion**: Notion API集成
- **skill-creator**: 技能创建/编辑
- **spike**: 原型验证
- **taskflow**: 多步骤任务编排
- **tmux**: tmux会话控制
- **video-frames**: 视频帧提取
- **weather**: 天气查询
- 调试技能: node-inspect-debugger, python-debugpy

### 插件技能 (Plugin Skills)
- **acp-router**: ACP Harness路由
- **browser-automation**: 浏览器自动化
- **lightclaw-cron**: LightClawBot定时提醒
- **qqbot-channel**: QQ频道管理
- **qqbot-media**: QQ富媒体收发
- **qqbot-remind**: QQ定时提醒

### 工作空间技能 (Workspace Skills)
- **ai-berkshire**: 价值投资研究框架（巴菲特/芒格/段永平/李录方法论）
- **apple-design**: Apple风格UI设计
- **ikigai**: Ikigai发现工具

---

*本报告基于OpenClaw 2026.7.1-2版本的本地安装分析、官方文档和源代码包元数据编写。*
