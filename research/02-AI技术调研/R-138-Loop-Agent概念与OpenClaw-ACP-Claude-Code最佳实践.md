# R-138: Loop Agent 最新概念深度调研 + OpenClaw ACP Claude Code 最佳实践

> **调研编号**: R-138  
> **完成日期**: 2026-07-09  
> **调研角色**: research-lead  
> **标签**: Agent Loop, Agentic AI, OpenClaw ACP, Claude Code, MCP, 多智能体编排

---

## 目录

1. [Loop Agent 概念深度解析](#1-loop-agent-概念深度解析)
2. [Agentic Loop 的核心架构模式](#2-agentic-loop-的核心架构模式)
3. [Anthropic 的 Agent Loop 实践（Claude Code 内核）](#3-anthropic-的-agent-loop-实践claude-code-内核)
4. [Claude Agent SDK 详解](#4-claude-agent-sdk-详解)
5. [Model Context Protocol (MCP) 与 Agent 生态](#5-model-context-protocol-mcp-与-agent-生态)
6. [OpenClaw ACP 架构与最佳实践](#6-openclaw-acp-架构与最佳实践)
7. [多智能体编排模式对比](#7-多智能体编排模式对比)
8. [工程最佳实践清单](#8-工程最佳实践清单)
9. [参考来源](#9-参考来源)

---

## 1. Loop Agent 概念深度解析

### 1.1 什么是 Agent Loop？

Agent Loop（智能体循环）是现代 AI Agent 系统的核心运行机制。它的本质是一个 **"感知→推理→行动→观察"** 的迭代闭环：

```
用户指令 → [LLM 推理] → [工具调用/行动] → [环境反馈] → [LLM 推理] → ... → 任务完成
                ↑                                              │
                └──────────────── 反馈循环 ────────────────────┘
```

Anthropic 在其奠基性文章 *Building Effective AI Agents* 中明确定义了这一概念：

> "Agents are typically just LLMs using tools based on environmental feedback in a loop."  
> （Agent 本质上就是 LLM 在一个循环中基于环境反馈使用工具。）

### 1.2 Agent vs Workflow 的关键区别

| 维度 | Workflow（工作流） | Agent（智能体） |
|:---|:---|:---|
| **控制流** | 预定义代码路径编排 LLM | LLM 动态决定自身流程和工具使用 |
| **灵活性** | 适合明确定义的任务 | 适合开放式、难以预测步骤的任务 |
| **可预测性** | 高 — 行为路径确定 | 低 — 模型驱动决策 |
| **成本/延迟** | 较低 | 较高（用延迟和成本换取任务表现） |
| **适用场景** | 流水线式处理 | 需要灵活推理和动态规划的场景 |

### 1.3 Agent Loop 的三个核心阶段

Claude Code 文档将 Agentic Loop 明确划分为三个交织的阶段：

1. **Gather Context（收集上下文）**：读取文件、搜索代码、理解项目结构
2. **Take Action（执行行动）**：编辑代码、运行命令、修改文件
3. **Verify Results（验证结果）**：运行测试、检查构建状态、对比输出

关键特征：循环是**自适应的**——一个简单问题可能只需要一次上下文收集，而一个复杂的 Bug 修复会在三个阶段间反复迭代数十次。Claude 根据每一步的结果自主决定下一步做什么。

### 1.4 Agent Loop 的设计要点

- **Ground Truth 原则**：Agent 在每一步都必须从环境获取真实反馈（工具调用结果、代码执行输出），而非依赖假设
- **停止条件**：任务完成时终止，但必须设置最大迭代次数等安全边界
- **人类介入点**：Agent 可在遇到阻塞时暂停请求人类判断，或在检查点等待审批
- **工具设计至关重要**：因为 Agent 的能力边界完全由其工具集决定

---

## 2. Agentic Loop 的核心架构模式

Anthropic 总结了从简单到复杂的六种 Agentic 系统模式，每种都可作为 Loop 的具体实现策略：

### 2.1 增强型 LLM（Augmented LLM）— 基础构建块

所有 Agentic 系统的基础单元，包含三种增强能力：

- **检索（Retrieval）**：主动生成搜索查询、选择信息源
- **工具（Tools）**：调用外部 API、执行代码、操作文件系统
- **记忆（Memory）**：确定需要保留的信息、跨会话持久化

> 实现建议：通过 MCP (Model Context Protocol) 标准化工具接口，确保 LLM 可以发现和调用第三方工具。

### 2.2 六种 Workflow 模式

#### 模式一：Prompt Chaining（提示链）
```
[LLM-1] → gate → [LLM-2] → gate → [LLM-3] → 输出
```
- 将任务分解为固定子步骤，前一步输出作为后一步输入
- 适用：营销文案生成后翻译、大纲→检查→写作
- 优势：用延迟换取更高精度

#### 模式二：Routing（路由分发）
```
输入 → [分类器] → 路径A / 路径B / 路径C
```
- 按输入类型分发到专门处理的下游
- 适用：客服系统（普通问题 vs 技术支持 vs 退款处理）
- 优势：关注点分离，每个路径可使用不同模型

#### 模式三：Parallelization（并行化）
```
           ┌→ [LLM-A] ─┐
输入 ──┬──→ [LLM-B] ──┼→ 聚合 → 输出
           └→ [LLM-C] ─┘
```
- **Sectioning**：拆分为独立子任务并行执行
- **Voting**：同一任务多次执行以获得更可信结果
- 适用：代码安全审查（多角度并行检测）、内容审核

#### 模式四：Orchestrator-Workers（编排者-工作者）
```
         [Orchestrator LLM]
         ╱              ╲
   [Worker-1]       [Worker-2]
         ╲              ╱
         [Orchestrator 合成]
```
- 与并行化的关键区别：子任务不是预定义的，由编排者根据输入动态决定
- 适用：涉及多文件的复杂代码修改、跨源信息搜索

#### 模式五：Evaluator-Optimizer（评估者-优化者）
```
[Generator LLM] → [Evaluator LLM] → 反馈 → [Generator LLM] → ... 
```
- 一个 LLM 生成，另一个评估并给出反馈，形成精炼循环
- 适用：文学翻译精炼、复杂搜索的多轮迭代

#### 模式六：Autonomous Agent（自主智能体）
```
用户指令 → [Agent Loop: 推理 → 工具 → 观察 → 推理...] → 完成/停止条件
```
- 最灵活的模式，LLM 完全控制执行过程
- 内含检查点暂停和人类介入机制

---

## 3. Anthropic 的 Agent Loop 实践（Claude Code 内核）

### 3.1 Agentic Loop 架构

Claude Code 是目前最成熟的 Agent Loop 工业实现之一。其核心架构：

```
┌─────────────────────────────────────────────────┐
│                Agentic Harness                   │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐   │
│  │  Context   │  │   Tools   │  │  Session  │   │
│  │ Management │  │ Registry  │  │  Manager  │   │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘   │
│        │              │              │          │
│        └──────────────┼──────────────┘          │
│                       ▼                         │
│              ┌──────────────┐                   │
│              │  Claude LLM  │                   │
│              │   (推理核心)  │                   │
│              └──────────────┘                   │
└─────────────────────────────────────────────────┘
```

**Agentic Harness（智能体外壳）** 的职责：
- 提供工具集（文件操作、执行、搜索、Web、代码智能）
- 管理上下文窗口（最重要的资源）
- 管理执行环境（本地/云端/远程控制）
- 将语言模型转化为有能力的编码智能体

### 3.2 工具分类体系

| 类别 | 能力 | 代表工具 |
|:---|:---|:---|
| **文件操作** | 读取文件、编辑代码、创建文件、重命名 | Read, Write, Edit |
| **搜索** | 按模式查找文件、正则搜索内容、代码库探索 | Glob, Grep |
| **执行** | 运行 Shell 命令、启动服务、运行测试、Git | Bash |
| **Web** | 搜索互联网、获取文档、查看错误信息 | WebSearch, WebFetch |
| **代码智能** | 类型错误检查、定义跳转、引用查找 | 需插件支持 |
| **编排** | 生成子智能体、询问用户问题 | Agent, AskUserQuestion |

### 3.3 上下文窗口管理（核心挑战）

> "Claude's context window fills up fast, and performance degrades as it fills."

这是所有 Agent Loop 实现面临的最大工程挑战。Claude Code 的解决方案包括：

1. **会话独立**：每个新会话获得全新上下文窗口
2. **自动记忆（Auto Memory）**：跨会话持久化学到的模式和偏好
3. **CLAUDE.md**：项目级指令文件，每次启动加载
4. **上下文窗口可视化**：交互式展示启动加载内容和每次文件读取的成本
5. **子智能体上下文隔离**：子智能体在独立上下文窗口中运行，只将摘要返回主会话

---

## 4. Claude Agent SDK 详解

### 4.1 SDK 概览

Claude Agent SDK 将 Claude Code 的完整能力以可编程方式提供：

```python
from claude_agent_sdk import query, ClaudeAgentOptions

async for message in query(
    prompt="Find and fix the bug in auth.py",
    options=ClaudeAgentOptions(allowed_tools=["Read", "Edit", "Bash"]),
):
    print(message)
```

**核心特性**：
- 内置工具集（Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch, Monitor 等）
- 与 Claude Code 相同的 Agent Loop 和上下文管理
- 支持 Python 和 TypeScript
- 无需自行实现工具执行

### 4.2 Hooks 系统（生命周期拦截）

Hooks 是 Agent Loop 的可编程控制点：

| Hook 事件 | 触发时机 | 典型用途 |
|:---|:---|:---|
| `PreToolUse` | 工具调用前（可阻止或修改） | 阻止危险命令、保护敏感文件 |
| `PostToolUse` | 工具执行后 | 记录文件变更审计 |
| `PostToolUseFailure` | 工具执行失败 | 错误处理和日志 |
| `UserPromptSubmit` | 用户提交提示词 | 注入额外上下文 |
| `Stop` | Agent 停止执行 | 保存状态、验证完成 |
| `SubagentStart/Stop` | 子智能体启停 | 追踪并行任务 |
| `PreCompact` | 对话压缩前 | 归档完整记录 |
| `PermissionRequest` | 需要权限对话框 | 自定义权限处理 |
| `SessionStart/End` | 会话生命周期 | 初始化/清理 |

**Hook 的工作流程**：
1. 事件触发 → 2. SDK 收集已注册 Hook → 3. Matcher 过滤 → 4. 回调执行 → 5. 返回决策（允许/阻止/修改/注入上下文）

### 4.3 子智能体（Subagents）

```python
agents={
    "code-reviewer": AgentDefinition(
        description="Expert code reviewer for security and quality.",
        prompt="You are a code review specialist...",
        tools=["Read", "Grep", "Glob"],  # 只读权限
        model="sonnet",                   # 可使用不同模型
    ),
}
```

**三大价值**：
1. **上下文隔离**：子智能体的中间工具调用和结果不进入主会话，只返回最终摘要
2. **并行化**：多个子智能体可并发运行，总耗时 = 最慢的那个
3. **专业化和工具限制**：每个子智能体可以有定制的系统提示和受限的工具集

**内置子智能体**：
- **Explore**：快速只读代码库探索（模型继承主会话，API 上限 Opus）
- **Plan**：Plan Mode 下的研究智能体（只读工具）
- **General-purpose**：通用复杂任务（继承所有工具）

### 4.4 Agent Teams（实验性）

比子智能体更高级的多智能体协作模式：

| 维度 | Subagents | Agent Teams |
|:---|:---|:---|
| **上下文** | 独立窗口，结果返回调用者 | 完全独立 |
| **通信** | 仅向主智能体报告 | 队友间直接通信 |
| **协调** | 主智能体管理 | 共享任务列表自协调 |
| **适用** | 只需结果的聚焦任务 | 需要讨论和协作的复杂工作 |
| **Token 成本** | 较低（摘要返回） | 较高（每个队友独立实例） |

---

## 5. Model Context Protocol (MCP) 与 Agent 生态

### 5.1 MCP 架构

MCP 是连接 AI 应用与外部工具/数据源的标准化协议：

```
┌─────────────────────── MCP Host ───────────────────┐
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │ Client 1 │  │ Client 2 │  │ Client 3 │         │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘         │
└───────┼─────────────┼─────────────┼────────────────┘
        │             │             │
   ┌────▼────┐  ┌────▼────┐  ┌────▼────┐
   │Server A │  │Server B │  │Server C │
   │(本地IO) │  │(数据库) │  │(远程API)│
   └─────────┘  └─────────┘  └─────────┘
```

### 5.2 双层协议

**数据层**：
- 基于 JSON-RPC 2.0
- 生命周期管理：初始化 → 能力协商 → 连接终止
- 三大核心原语（Primitives）：
  - **Tools**：可执行函数（文件操作、API 调用、数据库查询）
  - **Resources**：数据源（文件内容、数据库记录、API 响应）
  - **Prompts**：可复用的交互模板

**传输层**：
- **Stdio transport**：标准输入/输出流，用于本地进程间通信，零网络开销
- **Streamable HTTP transport**：HTTP POST + SSE，用于远程服务器通信，支持 OAuth 认证

### 5.3 安全注意事项

MCP 规范明确要求：
1. 服务器**必须**验证 `Origin` 头以防止 DNS 重绑定攻击
2. 本地运行时**应当**只绑定 `127.0.0.1`
3. **应当**为所有连接实现认证

---

## 6. OpenClaw ACP 架构与最佳实践

### 6.1 ACP (Agent Communication Protocol) 概述

OpenClaw 的 ACP 是一个统一的智能体通信协议层，用于将多种外部编码智能体（Claude Code, Codex, Cursor, Gemini CLI 等）接入 OpenClaw 运行时。

### 6.2 ACP 核心架构

```
┌─────────────────────── OpenClaw Gateway ──────────────────────┐
│                                                               │
│   用户消息 → [ACP Router Skill] → sessions_spawn(runtime=acp) │
│                         │                                     │
│            ┌────────────┼────────────┐                        │
│            ▼            ▼            ▼                        │
│      [Claude]      [Codex]     [Gemini]  ...                  │
│      Agent         Agent       Agent                           │
│         │             │            │                           │
│         ▼             ▼            ▼                           │
│    ┌─────────────────────────────────┐                        │
│    │        acpx 适配器层             │                        │
│    │  (Agent Client Protocol 驱动)   │                        │
│    └─────────────────────────────────┘                        │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### 6.3 两种调用路径

#### 路径一：OpenClaw ACP Runtime（推荐默认）

通过 `sessions_spawn` 创建 ACP 运行时会话：

```json
{
  "task": "实现 OAuth 登录流程并编写测试",
  "runtime": "acp",
  "agentId": "claude",
  "mode": "run"
}
```

**优势**：
- 完整的 OpenClaw 生命周期管理
- 自动结果回传
- 与 OpenClaw 技能系统集成
- 支持子智能体编排

#### 路径二：直接 acpx 驱动（"电话游戏"模式）

通过 `acpx` CLI 直接驱动外部智能体：

```bash
# 创建持久会话
acpx claude sessions new --name oc-claude-conv123

# 发送提示
acpx claude -s oc-claude-conv123 --cwd /project --format quiet "修复 auth.py 中的 bug"

# 取消进行中的轮次
acpx claude cancel -s oc-claude-conv123

# 关闭会话
acpx claude sessions close oc-claude-conv123
```

**适用场景**：
- 用户明确要求直接 acpx 驱动
- ACP Runtime 不可用或不健康
- 仅需中继提示到外部智能体

### 6.4 支持的智能体映射

| 名称 | agentId | 适配器命令 |
|:---|:---|:---|
| OpenClaw | `openclaw` | `openclaw acp` |
| Claude Code | `claude` | `@agentclientprotocol/claude-agent-acp` |
| Codex | `codex` | `@zed-industries/codex-acp`（隔离 CODEX_HOME） |
| GitHub Copilot | `copilot` | `copilot --acp --stdio` |
| Cursor | `cursor` | `cursor-agent acp` |
| Factory Droid | `droid` | `droid exec --output-format acp` |
| Gemini CLI | `gemini` | `gemini --acp` |
| OpenCode | `opencode` | `npx -y opencode-ai acp` |
| Qwen Code | `qwen` | `qwen --acp` |
| Kiro | `kiro` | `kiro-cli acp` |
| Kimi CLI | `kimi` | `kimi acp` |
| Kilocode | `kilocode` | `npx -y @kilocode/cli acp` |
| iFlow | `iflow` | `iflow --experimental-acp` |

### 6.5 acpx 安装与版本策略

关键原则：
1. **优先使用插件本地二进制**，而非全局 PATH
2. 从扩展依赖中解析锁定版本
3. 安装后验证版本
4. 如果安装改变了 ACPX 制品，重启网关

```bash
ACPX_PLUGIN_ROOT="<bundled-acpx-plugin-root>"
ACPX_CMD="$ACPX_PLUGIN_ROOT/node_modules/.bin/acpx"

# 验证
$ACPX_CMD --version

# 如需安装锁定版本
cd "$ACPX_PLUGIN_ROOT" && npm install --omit=dev --no-save acpx@<pinnedVersion>
```

### 6.6 故障恢复策略

| 故障 | 处理 |
|:---|:---|
| `acpx: command not found` | 安装插件本地锁定版本 → 重启网关 → 重试一次 |
| 适配器命令缺失 | 恢复内置默认配置 → 重试 → 如用户需要则安装指定二进制 |
| `NO_SESSION` | 创建新会话后重试 |
| 队列繁忙 | 等待完成（默认）或使用 `--no-wait` |

---

## 7. 多智能体编排模式对比

### 7.1 编排层级体系

```
Layer 4: Agent Teams        ← 多实例直接通信（最高复杂度）
          │
Layer 3: Subagents           ← 隔离上下文并行执行
          │
Layer 2: Orchestrator-Workers ← 动态任务分配
          │
Layer 1: Prompt Chaining     ← 固定步骤顺序
          │
Layer 0: Augmented LLM       ← 基础调用（最低复杂度）
```

### 7.2 OpenClaw 中的多智能体模式

OpenClaw 通过 `sessions_spawn` 提供了独特的多智能体编排能力：

**推送式完成模型**：
1. 主智能体 spawn 子智能体并分配任务
2. 子智能体独立运行
3. 结果自动推送回主智能体（push-based，非轮询）
4. 主智能体综合所有结果后报告

**关键原则**：
- Spawn 后不进行忙轮询（busy-poll）
- 使用 `sessions_yield` 等待完成事件
- 跟踪预期的子会话 key
- 所有子智能体完成后才发送最终答案

### 7.3 OpenClaw Subagent vs ACP Runtime

| 维度 | OpenClaw Subagent | ACP Runtime Session |
|:---|:---|:---|
| **底层模型** | OpenClaw 内置模型 | 外部编码智能体（Claude Code, Codex 等） |
| **通信协议** | sessions_spawn + 自动推送 | ACP (acpx 适配) |
| **适用场景** | 研究、分析、文件操作 | 编码、代码修改、复杂开发任务 |
| **工具能力** | read/write/edit/exec/web 等 | 取决于具体智能体（通常含完整代码工具集） |
| **上下文模式** | 隔离或 fork | 独立会话 |
| **生命周期** | 一次性或持久 | 持久线程（可 resume） |

---

## 8. 工程最佳实践清单

### 8.1 Agent Loop 设计原则

| # | 原则 | 说明 |
|:---|:---|:---|
| 1 | **最简方案优先** | 不要一开始就构建 Agent 系统，先考虑单次 LLM 调用 + RAG |
| 2 | **从直接 API 调用开始** | 使用框架前先理解底层原理 |
| 3 | **工具文档即提示工程** | 工具的描述文档直接影响 Agent 决策质量 |
| 4 | **Ground Truth 反馈** | 每一步都要从环境获取真实反馈 |
| 5 | **设置停止条件** | 最大迭代次数、Token 预算等安全边界 |

### 8.2 上下文管理

| # | 实践 | 说明 |
|:---|:---|:---|
| 1 | **上下文窗口是最关键资源** | 性能随上下文填充而退化 |
| 2 | **用子智能体隔离上下文** | 探索和分析在子智能体中完成，只返回摘要 |
| 3 | **提供验证机制** | 给 Agent 可运行的检查（测试、构建、截图对比） |
| 4 | **先探索再规划再编码** | 用 Plan Mode 分离研究和实现 |
| 5 | **让 Agent 展示证据** | 测试输出、命令返回值、截图，而非仅声明完成 |

### 8.3 OpenClaw ACP 最佳实践

| # | 实践 | 说明 |
|:---|:---|:---|
| 1 | **默认使用 ACP Runtime 路径** | 通过 `sessions_spawn(runtime="acp")` |
| 2 | **显式设置 agentId** | 除非已配置 `acp.defaultAgent` |
| 3 | **优先使用插件本地 acpx** | 不用全局 PATH 版本 |
| 4 | **故障后自动修复重试** | 安装→重启→重试一次，再降级 |
| 5 | **不使用 subagent runtime 驱动 ACP** | ACP 智能体走 ACP 路径 |
| 6 | **不要求用户运行 CLI** | `sessions_spawn` 能做的，不转嫁给用户 |
| 7 | **输出中继只传最终结果** | 过滤本地工具噪声 |

### 8.4 Claude Code Hook 最佳实践

```python
# 实战模式：保护 .env 文件 + 审计所有文件变更
async def protect_env_files(input_data, tool_use_id, context):
    file_path = input_data["tool_input"].get("file_path", "")
    if file_path.split("/")[-1] == ".env":
        return {
            "hookSpecificOutput": {
                "hookEventName": input_data["hook_event_name"],
                "permissionDecision": "deny",
                "permissionDecisionReason": "Cannot modify .env files",
            }
        }
    return {}

# 注册 Hook
options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [
            HookMatcher(matcher="Write|Edit", hooks=[protect_env_files])
        ]
    }
)
```

### 8.5 验证策略层级

| 层级 | 策略 | 说明 |
|:---|:---|:---|
| 1 | **提示词内验证** | 在同一消息中要求 Agent 运行检查并迭代 |
| 2 | **目标条件** | 使用 `/goal` 设置检查点，每轮后独立评估 |
| 3 | **Stop Hook 门控** | 脚本验证，阻止未通过的停止（最多连续 8 次） |
| 4 | **第二意见** | 验证子智能体或动态工作流，用新模型审查结果 |

---

## 9. 参考来源

| # | 来源 | URL |
|:---|:---|:---|
| 1 | Anthropic — *Building Effective AI Agents* | https://www.anthropic.com/engineering/building-effective-agents |
| 2 | Claude Code — *How Claude Code Works* | https://code.claude.com/docs/en/how-claude-code-works |
| 3 | Claude Code — *Best Practices* | https://code.claude.com/docs/en/best-practices |
| 4 | Claude Agent SDK — *Overview* | https://code.claude.com/docs/en/agent-sdk/overview |
| 5 | Claude Agent SDK — *Subagents* | https://code.claude.com/docs/en/agent-sdk/subagents |
| 6 | Claude Agent SDK — *Hooks* | https://code.claude.com/docs/en/agent-sdk/hooks |
| 7 | Claude Code — *Sub-agents* | https://code.claude.com/docs/en/sub-agents |
| 8 | Claude Code — *Agent Teams* | https://code.claude.com/docs/en/agent-teams |
| 9 | MCP — *Architecture* | https://modelcontextprotocol.io/docs/concepts/architecture |
| 10 | MCP — *Transports Spec* | https://modelcontextprotocol.io/specification/2025-06-18/basic/transports |
| 11 | OpenClaw — *ACP Router Skill* (本地) | `~/.openclaw/plugin-skills/acp-router/SKILL.md` |

---

## 附录 A：Agent Loop 伪代码

```python
async def agent_loop(task: str, max_iterations: int = 50):
    """Agent Loop 的通用实现模式"""
    context = initialize_context(task)
    
    for i in range(max_iterations):
        # Phase 1: LLM 推理
        response = await llm.generate(
            messages=context.messages,
            tools=available_tools,
        )
        
        # Phase 2: 检查是否完成
        if response.has_tool_calls() == False:
            return response.text  # 任务完成
        
        # Phase 3: 执行工具调用
        for tool_call in response.tool_calls:
            # PreToolUse hook
            hook_result = run_hooks("PreToolUse", tool_call)
            if hook_result.decision == "deny":
                context.add_tool_result(tool_call.id, hook_result.reason)
                continue
            
            # 执行工具
            try:
                result = execute_tool(tool_call.name, tool_call.args)
                # PostToolUse hook
                run_hooks("PostToolUse", tool_call, result)
            except Exception as e:
                run_hooks("PostToolUseFailure", tool_call, e)
                result = f"Error: {e}"
            
            # 将结果加入上下文（Ground Truth）
            context.add_tool_result(tool_call.id, result)
        
        # 可选：人类检查点
        if needs_human_review(context):
            await request_human_input(context)
    
    return "Max iterations reached"
```

## 附录 B：OpenClaw ACP 调用决策树

```
用户请求编码智能体任务
        │
        ▼
   读取 ACP Router Skill
        │
        ▼
   ACP Runtime 可用？
    ├─ 是 → sessions_spawn(runtime="acp", agentId="...")
    │         │
    │         ├─ 成功 → 等待自动推送结果
    │         └─ 失败 → 自动修复（安装 acpx → 重启 → 重试）
    │
    └─ 否 → 检查 acpx 是否可用
              ├─ 是 → 直接 acpx 电话游戏模式
              └─ 否 → 报告错误，提供降级选项
```

---

> **结论**：Agent Loop 是当前 AI 工程的核心范式。其设计哲学——"LLM 在循环中基于环境反馈使用工具"——看似简单，但工业级实现需要在上下文管理、工具设计、安全控制、多智能体编排等多个维度上精心设计。OpenClaw ACP 通过统一的协议层将多种编码智能体纳入同一编排框架，结合 Claude Code 的 Agent Loop 内核和 MCP 工具生态，构成了当前最完整的 Agentic 工程实践栈。