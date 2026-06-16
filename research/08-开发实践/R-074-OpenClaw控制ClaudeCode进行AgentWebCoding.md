# R-074：OpenClaw 控制 Claude Code 进行 Agent Web Coding 完整指南

> 调研日期：2026-06-16
> 分类：06-开发实践
> 状态：已完成

## 核心发现

OpenClaw 与 Claude Code 的集成已经**非常成熟**，存在 **5 种正式支持的集成路径**，其中 **ACP（Agent Client Protocol）+ openclaw-code-agent 插件**是当前最佳实践方案。Claude Code 本身支持 headless 模式（`claude -p`）和 Agent SDK，可以从编程角度被外部工具完全控制。

---

## 1. 架构全景图

```
┌─────────────────────────────────────────────────────────────┐
│                    用户交互层                                  │
│  WhatsApp / Telegram / Discord / iMessage / WeChat / QQ      │
│                    │                                          │
└────────────────────┼────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│              OpenClaw Gateway                                 │
│  ┌───────────────────────────────────────────────────┐      │
│  │           Main Agent（编排层）                        │      │
│  │  接收需求 → 拆解任务 → 分派给子 Agent → 整合结果     │      │
│  └──────┬──────────────┬───────────────┬──────────────┘      │
│         │              │               │                      │
│  ┌──────▼──────┐ ┌─────▼──────┐ ┌─────▼────────────────┐    │
│  │ Sub-agent    │ │ ACP Session │ │ openclaw-code-agent  │    │
│  │ (原生运行时)  │ │ (外部harness)│ │ 插件 (Plan→Review   │    │
│  │             │ │             │ │  →Execute 工作流)    │    │
│  └──────────────┘ └──────┬──────┘ └──────┬──────────────┘    │
└─────────────────────────┼───────────────┼───────────────────┘
                          │               │
          ┌───────────────▼───────────────▼───────────────┐
          │           Claude Code CLI                        │
          │  (claude -p / ACP harness / Agent SDK)          │
          │  - 读写文件、执行命令、运行测试、管理 Git          │
          │  - 隔离 worktree、权限控制、会话持久化             │
          └──────────────────────┬──────────────────────────┘
                                 │
          ┌──────────────────────▼──────────────────────────┐
          │              项目代码库                              │
          │  src/ → 构建 → 测试 → Git → 部署                  │
          └─────────────────────────────────────────────────┘
```

---

## 2. 五种集成路径详解

### 路径一：Claude Code 作为推理引擎（agentRuntime: claude-cli）

**适用场景**：让 OpenClaw 自身用 Claude Code 来执行推理，而不是用 OpenAI 或 Anthropic API 直连。

```jsonc
// ~/.openclaw/openclaw.json
{
  agents: {
    defaults: {
      model: { primary: "anthropic/claude-sonnet-4-6" },
      models: {
        // 指定某个模型通过 Claude CLI 运行
        "anthropic/claude-opus-4-8": {
          agentRuntime: { id: "claude-cli" }
        }
      }
    }
  }
}
```

**工作原理**：OpenClaw 内置了 Anthropic 插件，它提供 `claude-cli` 这个 agentRuntime。当配置了 `agentRuntime: { id: "claude-cli" }` 时，OpenClaw 会以 non-interactive print 模式运行本地安装的 Claude Code CLI 来执行推理。

> ⚠️ **费用注意**：从 2026-06-15 起，Claude Code 的 `-p`（Agent SDK）模式不再从 Claude Pro/Max 订阅中扣除，而是先从 Agent SDK credit 中扣，然后按标准 API 费率从 usage credits 扣。长期运行的 Gateway 主机推荐使用 Anthropic API key。

**优势**：
- 无需额外 API key，复用已有的 Claude Code 登录
- 配置简单，一行 runtime 声明即可

**劣势**：
- 费用模型变化后，Pro/Max 订阅用户可能更贵
- 不适合生产环境（推荐 API key）

---

### 路径二：ACP 会话（sessions_spawn + runtime: "acp"）⭐推荐

**适用场景**：让 Claude Code 作为独立的外部编码 harness 运行，OpenClaw 只负责编排和通信。

#### 2.1 安装 ACPX 运行时

```bash
# 安装官方 ACP 运行时后端
openclaw plugins install @openclaw/acpx

# 启用插件
openclaw config set plugins.entries.acpx.enabled true

# 声明信任
openclaw config set plugins.allow '["acpx"]'

# 重启 Gateway
openclaw gateway restart
```

> 最低 OpenClaw 版本：2026.4.25

#### 2.2 聊天中直接使用自然语言

在 Telegram/Discord 等渠道中直接说：
- "Start a persistent Claude Code session in a thread here and keep it focused."
- "Run this as a one-shot Claude Code ACP session and summarize the result."

OpenClaw 会自动：
1. 选择 `runtime: "acp"`
2. 解析 harness target（`agentId` = `claude-code`）
3. 如果支持 thread binding，绑定到线程
4. 后续消息自动路由到同一 ACP 会话

#### 2.3 通过 /acp 命令控制

```
/acp spawn claude-code --mode persistent --thread auto
/acp status
/acp model anthropic/claude-opus-4-8
/acp permissions full-auto
/acp timeout 600
/acp steer "add error handling and tests"
/acp cancel    # 停止当前轮次
/acp close     # 关闭会话
```

#### 2.4 通过 sessions_spawn 编程调用

```javascript
// 在 AGENTS.md 或脚本中
sessions_spawn({
  runtime: "acp",
  agentId: "claude-code",
  task: "在这个 React 项目中实现用户注册表单，包含验证逻辑",
  cwd: "/path/to/project",
  // 可选配置
})
```

**ACP 会话 vs Sub-agent 对比**：

| 维度 | ACP 会话 | Sub-agent |
|------|----------|-----------|
| 运行时 | acpx 后端插件 | OpenClaw 原生子 agent 运行时 |
| Session key | `agent:<id>:acp:<uuid>` | `agent:<id>:subagent:<uuid>` |
| 指令 | `/acp ...` | `/subagents ...` |
| Spawn | `sessions_spawn` + `runtime:"acp"` | `sessions_spawn`（默认） |
| 会话生命周期 | 跨 Gateway 重启存活 | Gateway 重启后丢失 |
| 工作目录隔离 | 每个会话独立工作区 | 继承父 workspace |
| Context 隔离 | 完全隔离，无 context bleed | 共享上下文 |

**优势**：
- ✅ 会话跨 Gateway 重启存活
- ✅ 独立工作区，无 context bleed
- ✅ 线程绑定（Telegram/Discord topic）
- ✅ 协议级优势，随 ACP 协议演进受益

**劣势**：
- 需要安装 acpx 插件
- Claude Code CLI 必须已安装

---

### 路径三：openclaw-code-agent 插件（Plan→Review→Execute 工作流）⭐⭐最佳实践

**适用场景**：需要完整的编码工作流（计划→审批→执行→合并）。

```bash
# 从 ClawHub 安装
openclaw plugins install clawhub:openclaw-code-agent
```

**核心工作流**：

```
用户需求 → plan（默认启动模式）
         → delegate 审批（orchestrator 审查计划）
         → 批准后 execute（Claude Code 执行编码）
         → 验证 → Merge/Open PR
         → 结果回传到原始聊天
```

**关键特性**：

| 特性 | 说明 |
|------|------|
| Plan → Review → Execute | `plan` 为默认启动模式，审批默认 `delegate` |
| Git worktree 隔离 | 新会话在独立 worktree 中工作 |
| 分支策略 | `delegate`（默认）/ `ask` / `off` / `manual` / `auto-merge` / `auto-pr` |
| 状态驱动 UX | `ask` 模式发送 Merge/Open PR/Later/Discard 按钮 |
| 会话管理 | 暂停、恢复、fork、中断、跨重启恢复 |
| 成本追踪 | `agent_sessions`、`agent_output`、`agent_stats` |
| 多 harness | Claude Code、Codex、OpenCode 共享控制平面 |
| 目标循环 | 可选 verifier-driven repair loops 或 completion loops |

**使用示例**（在聊天中）：
> "帮我写一个用户认证模块，用 React + TypeScript，包含登录、注册、密码重置"

OpenClaw 会自动启动 plan 模式，Claude Code 在隔离 worktree 中编写代码，完成后提示合并。

---

### 路径四：exec 直接调用 claude -p（最简单）

**适用场景**：简单的编码任务，无需复杂工作流。

```bash
# 单次任务
claude -p "在 src/utils/ 下添加日期格式化函数" \
  --allowedTools "Read,Write,Edit" \
  --output-format json \
  --max-turns 5

# 带输出捕获
claude -p "重构 auth 模块为 TypeScript" \
  --output-format stream-json > claude-output.jsonl
```

**OpenClaw agent 中通过 exec 调用**：

在 AGENTS.md 中指示 agent：
```
当需要执行编码任务时，使用以下命令调用 Claude Code：
claude -p "<具体任务描述>" --output-format json --max-turns 10 --allowedTools "Read,Write,Edit,Bash"
读取 stdout 作为结果返回。
```

**优势**：
- 零额外配置
- Unix 风格，易于管道组合

**劣势**：
- 无会话持久化
- 无计划审批
- 无 worktree 隔离
- 每次启动新进程，冷启动慢

---

### 路径五：MCP Bridge（Claude Code 访问 OpenClaw 工具）

**适用场景**：反过来——让 Claude Code 在编码时调用 OpenClaw 的 IM 渠道工具。

```bash
# 在 Claude Code 的 MCP 配置中添加
# ~/.claude/mcp-config.json 或项目 .claude/mcp-config.json
{
  "mcpServers": {
    "openclaw": {
      "command": "openclaw",
      "args": ["mcp", "serve"]
    }
  }
}
```

这样 Claude Code 可以：
- 在编码过程中读取 IM 消息
- 向 Telegram/Discord 频道发送进度更新
- 控制跨渠道会话

---

## 3. Claude Code 的 Agent 模式详解

### 3.1 CLI 基础用法

```bash
# 安装
npm install -g @anthropic-ai/claude-code

# 登录（Pro/Max 订阅）
claude auth login

# 交互模式
claude

# Headless 模式（最关键）
claude -p "你的任务"

# Bare 模式（更快启动，跳过 TUI 初始化）
claude --bare -p "你的任务"
```

### 3.2 Headless 模式完整参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `-p "prompt"` | 单次提示，非交互执行 | `claude -p "重构代码"` |
| `--output-format` | 输出格式：text/json/stream-json | `--output-format json` |
| `--max-turns N` | 限制对话轮次 | `--max-turns 10` |
| `--allowedTools` | 允许的工具列表 | `--allowedTools "Read,Write,Edit"` |
| `--verbose` | 详细日志 | `--verbose` |
| `--bare` | 跳过 TUI 初始化，更快启动 | `claude --bare -p "query"` |
| `--model` | 指定模型 | `--model claude-opus-4-8` |
| `--permission-mode` | 权限模式 | `--permission-mode full-auto` |
| `--settings` | 指定 settings 文件 | |
| `--mcp-config` | MCP 服务器配置 | |

### 3.3 Agent SDK / 编程调用

Claude Code 的 `-p` 模式即 Agent SDK 入口，Anthropic 官方文档描述为 "Agent SDK/programmatic usage"。

```bash
# Python SDK（通过 Anthropic SDK）
pip install anthropic

# TypeScript SDK（通过 @anthropic-ai/claude-code）
npm install @anthropic-ai/claude-code
```

### 3.4 权限模式

| 模式 | 说明 | 适用 |
|------|------|------|
| `suggest` | 只建议变更，需人工批准 | 学习、审查 |
| `auto-edit` | 自动编辑文件，命令需批准 | 日常编码 |
| `full-auto` | 完全自主（编辑+执行命令） | CI/CD、自动化 |

---

## 4. 完整工作流示例

### 场景：从 Telegram 发起 Web Coding 任务

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ 用户在Telegram │────▶│ OpenClaw     │────▶│ Claude Code  │────▶│ 项目代码库    │
│ "写一个TODO   │     │ Gateway      │     │ (ACP 会话)    │     │ (worktree)   │
│  应用"        │     │              │     │              │     │              │
└──────────────┘     └──────┬───────┘     └──────┬───────┘     └──────────────┘
                            │                    │
                     1.接收需求            3.执行编码
                     2.启动ACP会话         4.读写文件/测试
                            │                    │
                     5.收集结果◄───────────────┘
                            │
                     6.发送摘要到Telegram
```

### 配置文件示例

#### openclaw.json（dev agent 配置）

```jsonc
{
  // ACPX 插件配置
  plugins: {
    allow: ["acpx", "openclaw-code-agent"],
    entries: {
      acpx: { enabled: true },
      "openclaw-code-agent": { enabled: true }
    }
  },

  agents: {
    list: [
      {
        id: "dev-lead",
        workspace: "/root/.openclaw/workspace-dev",
        agentDir: "/root/.openclaw/agents/dev-lead",
        model: "anthropic/claude-sonnet-4-6",
        // dev-lead 用 Claude Code 的 CLI 运行时
        models: {
          "anthropic/claude-sonnet-4-6": {
            agentRuntime: { id: "claude-cli" }
          }
        }
      }
    ],
    defaults: {
      // 全局默认模型（非编码任务）
      model: { primary: "openai/gpt-5.4" }
    }
  }
}
```

#### Dev Agent 的 AGENTS.md 片段

```markdown
## 编码任务处理

当收到编码需求时：

1. 分析需求，确定任务范围
2. 启动 Claude Code ACP 会话：
   - 使用 /acp spawn claude-code --mode persistent
   - 设置 cwd 为项目目录
3. 传入具体的编码指令
4. 监控执行进度（/acp status）
5. 收集结果并发送给用户

### 一键编码指令模板
/acp spawn claude-code --mode persistent --thread auto
```

---

## 5. 替代方案对比

| 维度 | exec 调 claude -p | ACP 集成 | openclaw-code-agent 插件 | MCP Bridge |
|------|-------------------|----------|--------------------------|------------|
| **复杂度** | ⭐ 最简单 | ⭐⭐ 中等 | ⭐⭐⭐ 较复杂 | ⭐⭐ 中等 |
| **会话持久化** | ❌ | ✅ 跨重启 | ✅ 跨重启 | N/A |
| **工作目录隔离** | ❌ | ✅ | ✅ Git worktree | N/A |
| **计划审批** | ❌ | ❌ | ✅ Plan→Review→Execute | N/A |
| **进度监控** | ❌（需手动） | ✅ /acp status | ✅ agent_sessions | N/A |
| **多 harness** | ❌ 仅 Claude | ✅ Claude/Codex/Gemini | ✅ Claude/Codex/OpenCode | N/A |
| **合并/PR** | ❌ | ❌ | ✅ auto-merge/auto-pr | N/A |
| **成本追踪** | ❌ | ❌ | ✅ agent_stats | N/A |
| **适用场景** | 一次性脚本 | 通用编码任务 | 生产级开发流程 | 反向控制 |

### 推荐决策树

```
需要 Claude Code 编码？
├── 简单一次性任务 → exec 调 claude -p
├── 需要会话持久化和监控 → ACP 集成
├── 需要完整开发流程（计划/审批/合并）→ openclaw-code-agent 插件
└── Claude Code 需要访问 OpenClaw IM → MCP Bridge
```

---

## 6. 社区实践与案例

### 6.1 官方资源

| 资源 | URL | 说明 |
|------|-----|------|
| OpenClaw ACP 文档 | https://docs.openclaw.ai/tools/acp-agents | 官方 ACP 集成指南 |
| ACP Setup 指南 | https://docs.openclaw.ai/tools/acp-agents-setup | Harness 配置详解 |
| Anthropic 提供者文档 | https://docs.openclaw.ai/providers/anthropic | Claude CLI 和 API 配置 |
| Runtime Policy | https://docs.openclaw.ai/gateway/config-agents | agentRuntime 配置 |
| Claude Code 官方文档 | https://code.claude.com/docs/en/cli-reference | CLI 完整参考 |
| Claude Code Headless | https://code.claude.com/docs/en/headless | Agent SDK 文档 |

### 6.2 社区项目与文章

| 项目/文章 | 链接 | 说明 |
|-----------|------|------|
| **acpx（官方 ACPX 运行时）** | https://github.com/openclaw/acpx | OpenClaw 官方 ACP 后端插件 |
| **openclaw-code-agent** | https://clawhub.ai/plugins/openclaw-code-agent | Plan→Review→Execute 工作流插件 |
| **claude-code-acp** | https://github.com/harukitosa/claude-code-acp | 第三方 ACP bridge，让 Claude Code 以 Pro/Max 订阅接入 ACP 编辑器 |
| **Nemo Feng 的 ACP 配置指南** | https://www.nemofq.com/p/configuration-for-better-harness | 将 Codex 和 Claude Code 绑定到 Telegram forum topics 的完整教程 |
| **SegmentFault 配置指南** | https://segmentfault.com/a/1190000047778092 | OpenClaw + Claude Code 两种集成方式的中文详细指南 |
| **腾讯云实战指南** | https://cloud.tencent.com/developer/article/2655802 | OpenClaw + Claude Code 全链路开发实战，含 Council 多 Agent 系统 |
| **Claude Code Agent Skill** | https://clawhub.ai/skills/openclaw-claude-code | ClawHub 社区 skill，通过 MCP 控制 Claude Code（5.3k 下载） |
| **OpenClaw Discord** | https://discord.gg/clawd | 官方 Discord 社区，有 ACP 讨论频道 |

### 6.3 Claude Code 自身的远程控制能力

Claude Code 本身在 2026 年 2 月推出了 **Remote Control** 功能：
- `claude remote-control` 命令注册本地会话
- 通过 claude.ai/code、iOS/Android App 远程控制
- 也支持 **Channels**（Telegram/Discord）直接控制 Claude Code 会话
- 这与 OpenClaw 的 ACP 路径并行，不冲突

---

## 7. 实操快速上手

### 最简方案（5 分钟）

```bash
# 1. 确认 Claude Code 已安装
claude --version

# 2. 在 OpenClaw 中直接 exec 调用
claude -p "在当前项目中创建一个 Hello World 页面" --output-format json

# 完成！
```

### 推荐方案（15 分钟）

```bash
# 1. 安装 acpx 插件
openclaw plugins install @openclaw/acpx
openclaw config set plugins.entries.acpx.enabled true
openclaw config set plugins.allow '["acpx"]'

# 2. 重启 Gateway
openclaw gateway restart

# 3. 在聊天中说：
# "Start a persistent Claude Code session for my web project"
# 或使用命令：
# /acp spawn claude-code --mode persistent --thread auto

# 完成！
```

### 完整方案（30 分钟）

```bash
# 1. 安装 openclaw-code-agent
openclaw plugins install clawhub:openclaw-code-agent
openclaw plugins install @openclaw/acpx

# 2. 配置并重启
openclaw config set plugins.entries.acpx.enabled true
openclaw config set plugins.allow '["acpx", "openclaw-code-agent"]'
openclaw gateway restart

# 3. 在聊天中描述需求，自动走 Plan→Review→Execute 工作流
# "帮我开发一个 React TODO 应用，包含增删改查功能"
```

---

## 8. 知识缺口

1. **Claude Code 的 `--bare` 模式与 ACP 的性能对比**：缺乏官方 benchmark
2. **Claude Code Channels vs OpenClaw ACP 的详细对比**：两条并行路径的优劣需要实际测试
3. **Claude Code 新费用模型（2026-06-15 后）的实际成本**：需要实际使用数据
4. **多个 Claude Code ACP 会话的资源占用**：并发场景下的内存/CPU 消耗未知

---

## 9. 来源列表

| # | 来源 | URL | 访问日期 |
|---|------|-----|----------|
| 1 | OpenClaw Agent Runtime 文档 | https://docs.openclaw.ai/concepts/agent | 2026-06-16 |
| 2 | OpenClaw Agent Configuration | https://docs.openclaw.ai/gateway/config-agents | 2026-06-16 |
| 3 | OpenClaw ACP Agents | https://docs.openclaw.ai/tools/acp-agents | 2026-06-16 |
| 4 | OpenClaw Anthropic Provider | https://docs.openclaw.ai/providers/anthropic | 2026-06-16 |
| 5 | Claude Code CLI Reference | https://code.claude.com/docs/en/cli-reference | 2026-06-16 |
| 6 | Claude Code Headless Mode | https://code.claude.com/docs/en/headless | 2026-06-16 |
| 7 | ACPX Plugin (ClawHub) | https://clawhub.ai/plugins/@openclaw/acpx | 2026-06-16 |
| 8 | openclaw-code-agent Plugin | https://clawhub.ai/plugins/openclaw-code-agent | 2026-06-16 |
| 9 | acpx GitHub | https://github.com/openclaw/acpx | 2026-06-16 |
| 10 | claude-code-acp (community) | https://github.com/harukitosa/claude-code-acp | 2026-06-16 |
| 11 | Nemo Feng ACP Guide | https://www.nemofq.com/p/configuration-for-better-harness | 2026-06-16 |
| 12 | SegmentFault 完整指南 | https://segmentfault.com/a/1190000047778092 | 2026-06-16 |
| 13 | 腾讯云实战指南 | https://cloud.tencent.com/developer/article/2655802 | 2026-06-16 |
| 14 | ACP 协议说明 | https://www.morphllm.com/agent-client-protocol | 2026-06-16 |
| 15 | Claude Code Remote Control | https://claudefa.st/blog/guide/development/remote-control-guide | 2026-06-16 |
