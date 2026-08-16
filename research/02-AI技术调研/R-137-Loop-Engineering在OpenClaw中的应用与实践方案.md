# Loop Engineering 在 OpenClaw 中的应用与实践方案

> **任务编号**: R-137
> **编写日期**: 2026-07-09
> **编写角色**: research-lead
> **标签**: AI技术调研 / Agent架构 / Loop Engineering

---

## 目录

1. [Loop Engineering 概述](#1-loop-engineering-概述)
2. [理论基础与核心模式](#2-理论基础与核心模式)
3. [OpenClaw 平台架构概览](#3-openclaw-平台架构概览)
4. [Loop Engineering 在 OpenClaw 中的映射](#4-loop-engineering-在-openclaw-中的映射)
5. [核心循环模式实践方案](#5-核心循环模式实践方案)
6. [高级循环编排模式](#6-高级循环编排模式)
7. [循环治理与安全](#7-循环治理与安全)
8. [性能与可观测性](#8-性能与可观测性)
9. [实施路线图](#9-实施路线图)
10. [参考资源](#10-参考资源)

---

## 1. Loop Engineering 概述

### 1.1 定义

**Loop Engineering** 是一种系统设计方法论，其核心思想是：将 AI Agent 的工作流程构建为显式的、可控的、可组合的**循环结构**（Loops），而非线性的调用链。每个循环代表一个"感知—决策—行动—反馈"的闭环，Agent 在循环中迭代地理解任务、调用工具、评估结果，直到满足终止条件。

这一概念源于控制系统理论中的**反馈控制环**（Feedback Control Loop），以及软件工程中的**事件循环**（Event Loop）思想。在 LLM Agent 领域，Loop Engineering 强调：

- **显式循环结构**：循环的入口、退出条件、迭代上限均明确定义
- **环境反馈驱动**：每一步行动后从环境获取"地面真相"（ground truth）作为下一步决策依据
- **可组合性**：循环可嵌套、可并行、可级联
- **可控性**：支持人工干预（human-in-the-loop）、超时、取消等治理机制

### 1.2 与传统 Agent 架构的区别

| 维度 | 传统线性 Pipeline | Loop Engineering |
|------|-------------------|------------------|
| 控制流 | 固定步骤顺序 | 动态迭代，条件驱动 |
| 错误处理 | 异常抛出/捕获 | 循环内自纠错与重试 |
| 环境交互 | 单次调用 | 持续感知-行动 |
| 终止条件 | 步骤完成 | 目标达成或迭代上限 |
| 可组合性 | 有限（链式） | 高度可组合（嵌套/并行/级联） |

### 1.3 为何重要

Anthropic 在其《Building Effective AI Agents》一文中指出：Agent 本质上就是"LLM 在循环中使用工具，基于环境反馈进行决策"。Loop Engineering 将这一本质显式化、工程化，使 Agent 系统具备：

- **鲁棒性**：单步失败不导致整体崩溃，循环提供自然的重试与修正机会
- **适应性**：Agent 可根据中间结果动态调整策略
- **可观测性**：每次迭代都是可检查的检查点（checkpoint）
- **可治理性**：循环边界天然适合插入审批、限流、安全检查

---

## 2. 理论基础与核心模式

### 2.1 基础控制环模型

Loop Engineering 的核心控制环可以抽象为四个阶段：

```
┌─────────────────────────────────────────┐
│              Agent Loop                 │
│                                         │
│   ┌─────────┐    ┌─────────┐           │
│   │ Observe │───▶│ Orient  │           │
│   │ (感知)  │    │ (判断)  │           │
│   └─────────┘    └────┬────┘           │
│                        │                │
│   ┌─────────┐    ┌────▼────┐           │
│   │  Act    │◀───│ Decide  │           │
│   │ (执行)  │    │ (决策)  │           │
│   └────┬────┘    └─────────┘           │
│        │                                │
│        ▼                                │
│   ┌─────────┐                           │
│   │ Feedback│ (环境反馈 / Ground Truth) │
│   └────┬────┘                           │
│        │                                │
│        └──────────────▶ (回到 Observe)  │
│                                         │
│   终止条件: 目标达成 / 迭代上限 / 人工停止 │
└─────────────────────────────────────────┘
```

这对应了经典的 **OODA Loop**（Observe-Orient-Decide-Act）模型，也是 Anthropic 描述的 Agent 核心运作方式。

### 2.2 Anthropic 的五种工作流模式

根据 Anthropic 的分类，Agent 系统从简单到复杂包含以下模式，每种都是循环工程的一种特化：

#### 2.2.1 Prompt Chaining（提示链）
- **结构**：线性序列，每步 LLM 调用处理上一步输出
- **循环特征**：有限循环（固定步数），中间可插入门控检查
- **适用场景**：可清晰分解为固定子任务的流程

#### 2.2.2 Routing（路由分发）
- **结构**：分类器 → 专用处理分支
- **循环特征**：单次路由决策，分支内可含子循环
- **适用场景**：存在明确类别、需分别优化的场景

#### 2.2.3 Parallelization（并行化）
- **结构**：多 LLM 实例同时工作，结果聚合
- **变体**：Sectioning（分片）与 Voting（投票）
- **循环特征**：同步等待所有并行分支完成
- **适用场景**：子任务独立、或需多视角提高置信度

#### 2.2.4 Orchestrator-Workers（编排者-执行者）
- **结构**：中央 LLM 动态分解任务、分派给工作者、综合结果
- **循环特征**：编排者可在循环中多次分派
- **适用场景**：子任务不可预测（如代码多文件修改）

#### 2.2.5 Evaluator-Optimizer（评估者-优化者）
- **结构**：一个 LLM 生成响应，另一个评估并反馈，形成迭代循环
- **循环特征**：典型的反馈循环，有明确评估标准
- **适用场景**：有清晰评估标准、迭代可提升质量

#### 2.2.6 Autonomous Agent（自主 Agent）
- **结构**：LLM 在循环中自主使用工具，基于环境反馈决策
- **循环特征**：开放式循环，终止条件灵活
- **适用场景**：开放式问题，无法预测所需步骤

### 2.3 循环的属性维度

Loop Engineering 中，每个循环可通过以下维度刻画：

| 属性 | 说明 | 取值示例 |
|------|------|----------|
| **迭代上限** | 最大循环次数 | 1（单次）, 5, ∞（无限） |
| **终止条件** | 退出循环的判定 | 目标达成, 评估通过, 人工停止 |
| **反馈来源** | 环境真相的获取方式 | 工具返回值, 代码执行, 人工审批 |
| **并行度** | 循环内可同时执行的分支数 | 1（串行）, N（并行） |
| **嵌套深度** | 循环内包含的子循环层数 | 0, 1, 2... |
| **人工干预点** | 循环中暂停等待人工的位置 | 每步, 检查点, 仅阻塞时 |
| **状态持久化** | 循环状态是否可跨会话恢复 | 无状态, 快照, 持久化 |

---

## 3. OpenClaw 平台架构概览

### 3.1 核心架构组件

OpenClaw 是一个多 Agent 协作平台，其架构天然支持 Loop Engineering：

```
┌──────────────────────────────────────────────────┐
│                   OpenClaw 平台                    │
│                                                    │
│  ┌──────────┐   ┌──────────┐   ┌──────────────┐  │
│  │ Gateway  │   │  Skills  │   │   ACP Runtime │  │
│  │ (网关)   │   │  (技能)  │   │  (ACP 运行时) │  │
│  └────┬─────┘   └────┬─────┘   └──────┬───────┘  │
│       │              │                 │           │
│  ┌────▼──────────────▼─────────────────▼───────┐  │
│  │              Agent Runtime                   │  │
│  │  (会话管理 / 工具调度 / 子 Agent 编排)       │  │
│  └────┬──────────────┬────────────────────┬────┘  │
│       │              │                    │        │
│  ┌────▼────┐   ┌─────▼─────┐   ┌─────────▼────┐  │
│  │ Subagent│   │ TaskFlow  │   │   Channels    │  │
│  │ Runtime │   │  (任务流) │   │  (通信通道)   │  │
│  └─────────┘   └───────────┘   └──────────────┘  │
│                                                    │
│  ┌─────────────────────────────────────────────┐  │
│  │              MCP 协议层                      │  │
│  │  (工具 / 资源 / 提示 标准化接口)            │  │
│  └─────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

### 3.2 关键子系统与循环的关联

| 子系统 | 在循环中的角色 | 说明 |
|--------|---------------|------|
| **Agent Runtime** | 循环执行引擎 | 管理会话生命周期，每轮对话即一次循环迭代 |
| **Skills 系统** | 循环能力扩展 | 为 Agent 提供工具/流程模板，增强循环内的行动能力 |
| **Subagent 机制** | 嵌套循环 | 主 Agent 可派生子 Agent，形成多级循环 |
| **TaskFlow** | 持久化循环 | 跨会话的任务流，支持等待-恢复的长期循环 |
| **ACP Runtime** | 外部循环接入 | 将外部 Coding Agent（Claude Code, Codex 等）接入循环 |
| **MCP 协议** | 循环接口标准化 | 标准化工具/资源/提示接口，使循环可组合 |
| **Channels** | 循环通信 | 各通信渠道（QQ, Web, Slack 等）作为循环的输入/输出 |

### 3.3 会话模型

OpenClaw 的会话模型本身就是一种循环结构：

```
用户消息 → Agent 感知 → LLM 推理 → 工具调用 → 环境反馈 → Agent 响应 → 用户消息 → ...
```

每一轮对话就是一个循环迭代。Agent 在迭代中：
1. **Observe**：接收用户消息或子 Agent 报告
2. **Orient**：LLM 理解上下文，判断当前状态
3. **Decide**：选择是否调用工具、调用哪个工具
4. **Act**：执行工具调用
5. **Feedback**：工具返回结果，进入下一轮

---

## 4. Loop Engineering 在 OpenClaw 中的映射

### 4.1 对话级循环（Conversation Loop）

**级别**：最外层循环
**映射**：OpenClaw Agent 会话本身

```
┌──────────────────────────────────────────────┐
│            Conversation Loop                 │
│                                              │
│  User Input → Agent Processing → Response    │
│       ▲                            │         │
│       └────────────────────────────┘         │
│                                              │
│  终止: 会话结束 / 超时                        │
│  反馈: 用户对 Agent 响应的后续消息            │
└──────────────────────────────────────────────┘
```

这是最基础的循环。OpenClaw 的 Gateway 接收用户消息，Agent Runtime 调度 LLM 处理，返回响应，等待下一轮输入。

### 4.2 推理级循环（Inference Loop）

**级别**：单次推理内的循环
**映射**：LLM 的多步工具调用

在一次 Agent 推理中，LLM 可能需要多次调用工具：

```
LLM 推理 → 调用工具A → 获取结果 → LLM 再推理 → 调用工具B → ... → 生成最终响应
```

OpenClaw 的 Agent Runtime 原生支持这一循环：LLM 可以在单个对话轮中发起多次工具调用，每次调用后获得环境反馈，驱动下一步决策。

### 4.3 子 Agent 循环（Subagent Loop）

**级别**：嵌套循环
**映射**：`sessions_spawn` 创建的子 Agent

主 Agent 可通过 `sessions_spawn` 派生子 Agent，子 Agent 内部运行自己的对话循环，完成后将结果报告回主 Agent：

```
主 Agent 循环
  ├── 派生子 Agent A → 子 Agent A 的内部循环 → 结果报告
  ├── 派生子 Agent B → 子 Agent B 的内部循环 → 结果报告
  └── 综合子 Agent 结果 → 继续/终止
```

这对应 Anthropic 的 **Orchestrator-Workers** 模式。OpenClaw 的子 Agent 机制使这种嵌套循环天然支持：
- 子 Agent 可并行执行（并行循环）
- 子 Agent 可再派生孙 Agent（多级嵌套）
- 结果自动回报（push-based completion）

### 4.4 TaskFlow 持久循环（Persistent Loop）

**级别**：跨会话循环
**映射**：TaskFlow 机制

TaskFlow 是 OpenClaw 中最强大的循环工程工具，它支持跨会话的持久化循环：

```
创建 TaskFlow → 执行任务步骤 → 设置等待状态 → (外部事件) → 恢复 → ... → 完成/失败/取消
```

TaskFlow 循环的核心特性：
- **状态持久化**：`stateJson` 保存循环状态，支持跨重启恢复
- **等待-恢复**：`setWaiting` → `resume` 模式允许循环暂停等待外部事件
- **子任务链接**：`runTask` 将子任务链接到 Flow，支持循环内分派
- **版本控制**：`revision` 机制确保并发安全的状态更新
- **取消机制**：`requestCancel` / `cancel` 支持循环的优雅终止

### 4.5 ACP 外部循环（External Harness Loop）

**级别**：外部 Agent 循环
**映射**：ACP Runtime + acpx

OpenClaw 通过 ACP（Agent Client Protocol）将外部 Coding Agent（Claude Code, Codex, Gemini CLI 等）接入循环：

```
OpenClaw Agent → ACP 会话 → 外部 Agent 执行 → 结果回流 → OpenClaw Agent 继续
```

这使 OpenClaw 成为一个**循环编排器**，协调多个异构 Agent 的循环：

```
┌───────────────────────────────────────────────────┐
│              OpenClaw 编排循环                      │
│                                                    │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐           │
│  │ Claude  │  │  Codex  │  │  Gemini │  ...      │
│  │  Code   │  │  Loop   │  │  Loop   │           │
│  │  Loop   │  │         │  │         │           │
│  └─────────┘  └─────────┘  └─────────┘           │
│                                                    │
│  结果汇聚 → 综合决策 → 下一轮编排                  │
└───────────────────────────────────────────────────┘
```

### 4.6 技能循环（Skill Loop）

**级别**：能力扩展循环
**映射**：Skills 系统

Skills 为 Agent 循环提供可插拔的能力扩展。当 Agent 遇到特定任务时，可以加载相应 Skill，在循环中按 Skill 定义的模式工作：

```
Agent 循环
  ├── 识别任务类型 → 加载对应 Skill
  ├── 按 Skill 指导调用工具 → 获取反馈
  ├── 评估结果 → 决定是否继续循环
  └── 完成 → 卸载 Skill / 继续下一任务
```

---

## 5. 核心循环模式实践方案

### 5.1 模式一：简单工具循环（Simple Tool Loop）

**场景**：Agent 需要查询信息并回答用户

```yaml
模式: Simple Tool Loop
迭代上限: 3-5
终止条件: 获得足够信息
反馈来源: 工具返回值
```

**实践方案**：

```
用户提问
  → Agent 调用 web_search 工具
  → 获取搜索结果（环境反馈）
  → Agent 判断信息是否充分
    → 充分: 生成回答 → 循环结束
    → 不充分: 调用 web_fetch 获取详情 → 回到判断
```

**OpenClaw 实现**：这是 Agent Runtime 的原生能力。Agent 在单个对话轮中可多次调用工具，LLM 自动决定是否需要更多工具调用来完善答案。

### 5.2 模式二：评估-优化循环（Evaluator-Optimizer Loop）

**场景**：需要高质量产出（如文档翻译、代码审查）

```yaml
模式: Evaluator-Optimizer Loop
迭代上限: 3-5
终止条件: 评估通过 / 达到迭代上限
反馈来源: 评估 LLM 的反馈
并行度: 1（串行迭代）
```

**实践方案**：

```
任务输入
  → Generator LLM 生成初稿
  → Evaluator LLM 评估并给出反馈
  → 判断是否通过
    → 通过: 输出最终结果
    → 未通过: Generator 根据反馈修订 → 回到评估
```

**OpenClaw 实现**：

方案 A — 单 Agent 内循环：
- Agent 先生成内容，再自我评估，根据评估反馈修订
- 利用推理级循环实现

方案 B — 子 Agent 分工循环：
- 主 Agent 作为编排者
- 派生子 Agent A（生成器）和子 Agent B（评估器）
- 主 Agent 在两者间传递结果和反馈，形成循环

```python
# 伪代码
for i in range(max_iterations):
    draft = generator_agent.generate(task, feedback if i > 0 else None)
    evaluation = evaluator_agent.evaluate(draft, criteria)
    if evaluation.passed:
        return draft
    feedback = evaluation.feedback
return draft  # 返回最后一个版本
```

### 5.3 模式三：编排者-执行者循环（Orchestrator-Workers Loop）

**场景**：复杂代码修改、多源信息检索

```yaml
模式: Orchestrator-Workers Loop
迭代上限: 动态
终止条件: 所有子任务完成
反馈来源: 子 Agent 报告
并行度: N（并行子任务）
```

**实践方案**：

```
主 Agent 接收任务
  → 分析并分解为子任务（动态，非预定义）
  → 派生多个子 Agent 并行执行
  → 等待所有子 Agent 完成
  → 综合结果
  → 判断是否需要进一步分解
    → 是: 继续派生子 Agent
    → 否: 返回最终结果
```

**OpenClaw 实现**：

使用 `sessions_spawn` 派生子 Agent：

```
主 Agent (Orchestrator)
  ├── spawn subagent-1: "搜索信息源A"  ──→ 结果1
  ├── spawn subagent-2: "搜索信息源B"  ──→ 结果2
  ├── spawn subagent-3: "分析已有代码"  ──→ 结果3
  │
  └── 综合结果1+2+3 → 如需补充 → 继续spawn → ...
```

关键点：
- 子 Agent 结果自动回报（push-based），无需轮询
- 可设置 `taskName` 便于跟踪
- 子 Agent 可再派生孙 Agent，支持递归分解

### 5.4 模式四：路由循环（Routing Loop）

**场景**：多类型任务分发处理

```yaml
模式: Routing Loop
迭代上限: 1（路由）+ 子循环
终止条件: 路由完成 + 子任务完成
反馈来源: 分类器输出 + 子任务结果
```

**实践方案**：

```
用户输入
  → Router LLM 分类（意图识别）
  → 根据分类路由到专用处理流程
    → 技术问题 → 技术专家 Agent 循环
    → 创意任务 → 创意 Agent 循环
    → 数据分析 → 数据分析 Agent 循环
  → 各流程独立循环完成后返回结果
```

**OpenClaw 实现**：

利用 Skills 系统实现路由：
- 每类任务对应一个 Skill
- Agent 根据输入选择加载对应 Skill
- Skill 内定义该类任务的循环模式

或使用 TaskFlow 实现路由：
- `createManaged` 创建路由 Flow
- `runTask` 分派到对应子 Agent
- `setWaiting` 等待子任务完成
- `resume` 汇总结果

### 5.5 模式五：人机协作循环（Human-in-the-Loop）

**场景**：需要人工审批的关键决策

```yaml
模式: Human-in-the-Loop
迭代上限: 无限（直到人工确认）
终止条件: 人工批准 / 人工拒绝
反馈来源: 人工输入
人工干预点: 关键决策点
```

**实践方案**：

```
Agent 执行到关键决策点
  → 暂停循环，生成审批请求
  → 等待人工输入
    → 人工批准 → 继续执行
    → 人工拒绝 → 终止 / 调整方案
    → 人工提供指导 → 按指导调整后继续
```

**OpenClaw 实现**：

TaskFlow 的 `setWaiting` 机制天然支持人机协作循环：

```typescript
// 伪代码
const flow = taskFlow.createManaged({
  controllerId: "approval-workflow",
  goal: "deploy-with-approval",
  currentStep: "await_approval",
  stateJson: { proposal: generatedPlan },
});

taskFlow.setWaiting({
  flowId: flow.flowId,
  expectedRevision: flow.revision,
  currentStep: "await_approval",
  waitJson: {
    kind: "approval",
    channel: "slack",
    summary: "请审批部署方案",
  },
});

// 人工审批后恢复
taskFlow.resume({
  flowId: flow.flowId,
  expectedRevision: waiting.flow.revision,
  status: "running",
  currentStep: "execute",
});
```

---

## 6. 高级循环编排模式

### 6.1 多 Agent 协作循环（Multi-Agent Collaboration Loop）

**场景**：多个 Agent 协作完成复杂任务，每个 Agent 有不同专长

```
┌─────────────────────────────────────────────────────┐
│              编排 Agent (Orchestrator)               │
│                                                      │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐      │
│  │ Research  │    │  Coding  │    │  Review  │      │
│  │  Agent    │    │  Agent   │    │  Agent   │      │
│  │ (研究)   │    │ (编码)   │    │ (审查)   │      │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘      │
│       │                │                │            │
│       ▼                ▼                ▼            │
│  ┌──────────────────────────────────────────┐       │
│  │         结果汇聚与综合判断                │       │
│  └────────────────────┬─────────────────────┘       │
│                       │                              │
│       ┌───────────────┼───────────────┐              │
│       ▼               ▼               ▼              │
│   需补充研究      需修改代码      审查通过            │
│   → 回到Research  → 回到Coding   → 完成              │
└─────────────────────────────────────────────────────┘
```

**实践方案**：

- 使用 OpenClaw 的 Subagent 机制派生多个专职 Agent
- 每个 Agent 加载对应 Skill（如 healthcheck, browser-automation 等）
- 编排 Agent 收集所有子 Agent 结果后综合决策
- 根据结果决定哪些 Agent 需要再次迭代

### 6.2 ACP 多 Harness 循环（Multi-Harness Loop）

**场景**：利用不同 Coding Agent 的优势协同工作

```
OpenClaw 编排 Agent
  ├── 派生 Claude Code ACP 会话 → 处理架构设计
  ├── 派生 Codex ACP 会话 → 处理算法实现
  ├── 派生 Gemini CLI ACP 会话 → 处理文档生成
  │
  └── 汇聚结果 → 检查一致性 → 如有冲突则协调
```

**实践方案**：

通过 `sessions_spawn` with `runtime: "acp"` 派生不同 Harness 的会话：

```
sessions_spawn:
  - runtime: acp, agentId: claude, task: "设计API架构"
  - runtime: acp, agentId: codex, task: "实现核心算法"
  - runtime: acp, agentId: gemini, task: "生成技术文档"
```

编排 Agent 等待所有 ACP 会话完成，综合结果后决定是否需要额外迭代。

### 6.3 递归分解循环（Recursive Decomposition Loop）

**场景**：超大型任务需要逐级分解

```
任务: "构建完整Web应用"
  → 分解为: 前端 + 后端 + 数据库 + 部署
    → 后端再分解: API设计 + 业务逻辑 + 数据模型
      → API设计再分解: 接口定义 + 验证规则 + 文档
      → ...直到任务足够小
  → 自底向上执行与验证
```

**实践方案**：

利用 Subagent 的递归派生能力：
- 每层 Agent 负责分解当前层任务
- 叶子节点 Agent 执行具体工作
- 结果逐级上报、逐级验证
- 任一层发现问题可触发上层重新分解

### 6.4 竞态循环（Competitive Loop / Voting Loop）

**场景**：需要高置信度答案

```
同一问题
  ├── Agent A (使用 GPT 模型) → 答案A
  ├── Agent B (使用 Claude 模型) → 答案B
  └── Agent C (使用 Gemini 模型) → 答案C
      │
      ▼
  投票/聚合 → 最终答案
```

**实践方案**：

- 使用 `sessions_spawn` 派生多个子 Agent
- 为每个子 Agent 指定不同 `model` 参数
- 收集所有结果后进行投票或聚合
- 如不一致，可触发讨论循环（Agents 互相审视对方的答案）

---

## 7. 循环治理与安全

### 7.1 迭代上限与资源控制

**问题**：无限循环导致资源耗尽

**实践方案**：

| 控制维度 | 策略 | OpenClaw 机制 |
|----------|------|--------------|
| 迭代次数 | 设置最大循环次数 | TaskFlow `stateJson` 跟踪计数 |
| 执行时间 | 设置超时 | Gateway 超时配置 |
| Token 消耗 | 设置 Token 预算 | 模型调用层限流 |
| 并发数 | 限制并行子 Agent 数 | Subagent 数量管理 |
| 工具调用 | 限制单轮工具调用次数 | Agent Runtime 配置 |

### 7.2 人工干预机制

**问题**：Agent 循环可能做出不可逆的错误决策

**实践方案**：

```
循环执行
  ├── 普通步骤: 自动执行
  ├── 关键决策点: 暂停 → 人工审批 → 继续/终止
  ├── 异常检测: 暂停 → 人工确认 → 修正/终止
  └── 定期检查点: 汇报进度 → 人工决定是否继续
```

OpenClaw 机制：
- **TaskFlow `setWaiting`**：暂停循环等待人工输入
- **审批命令**：`/approve` 机制用于需要用户确认的操作
- **Subagent 上下文**：子 Agent 任务可包含"遇到X类决策时暂停并报告"

### 7.3 安全边界

**问题**：循环中的工具调用可能产生安全风险

**实践方案**：

```
每个循环迭代
  ├── 权限检查: Agent 是否有权执行该操作
  ├── 范围检查: 操作是否在允许范围内
  ├── 安全扫描: 工具输入是否包含危险内容
  └── 审计记录: 记录每次工具调用供事后审查
```

OpenClaw 机制：
- **Capabilities**：`capabilities=none` 限制 Agent 能力
- **Policy 过滤**：工具按策略过滤
- **安全提示**：系统提示中明确禁止绕过安全措施
- **沙箱隔离**：`sandbox: "require"` 提供执行隔离

### 7.4 循环取消与回滚

**问题**：需要中途终止循环并处理部分结果

**实践方案**：

TaskFlow 提供两种取消机制：
- **`requestCancel`**：请求停止调度，允许进行中的步骤完成
- **`cancel`**：立即取消，包括进行中的子任务

```typescript
// 优雅取消
taskFlow.requestCancel({ flowId, expectedRevision });

// 立即取消（包括子任务）
taskFlow.cancel({ flowId, expectedRevision });
```

取消后的处理：
- 收集已完成步骤的结果
- 保存当前状态供后续分析
- 通知相关方循环已终止

---

## 8. 性能与可观测性

### 8.1 循环性能优化

#### 8.1.1 减少不必要的迭代

```
优化策略:
  ├── 前置检查: 在循环开始前验证前提条件
  ├── 早退条件: 在循环中尽早检测可终止状态
  ├── 缓存复用: 避免循环中重复计算相同内容
  └── 批量处理: 将多个小操作合并为一次大操作
```

#### 8.1.2 并行化串行循环

```
串行循环 → 分析依赖关系 → 无依赖的步骤并行执行

示例:
  串行: 搜索A → 搜索B → 搜索C → 综合
  并行: 搜索A ┐
        搜索B ├→ 综合
        搜索C ┘
```

OpenClaw 的 `sessions_spawn` 天然支持并行派生多个子 Agent。

#### 8.1.3 上下文管理

```
长循环的上下文膨胀问题:
  ├── 摘要压缩: 每N轮将历史迭代摘要化
  ├── 状态外置: 将中间状态存入 stateJson 而非上下文
  ├── 分段处理: 将长循环拆分为多个短循环
  └── 工具结果裁剪: 只保留关键工具返回
```

### 8.2 可观测性

#### 8.2.1 循环追踪

建议为每个循环维护追踪信息：

```json
{
  "loopId": "loop-xxx",
  "flowId": "flow-xxx",
  "iteration": 3,
  "step": "evaluate",
  "status": "running",
  "startedAt": "2026-07-09T05:10:00Z",
  "lastEventAt": "2026-07-09T05:12:30Z",
  "toolCalls": ["web_search", "web_fetch"],
  "childLoops": ["subagent-1", "subagent-2"],
  "tokenUsage": { "input": 5000, "output": 2000 }
}
```

#### 8.2.2 检查点与调试

TaskFlow 的状态持久化天然提供检查点能力：
- `stateJson` 记录每步状态
- `revision` 提供版本追踪
- `getTaskSummary` 提供紧凑健康视图

调试建议：
- 在 `stateJson` 中记录每次迭代的关键决策
- 使用 `currentStep` 标识当前循环阶段
- 在 `waitJson` 中记录等待原因便于诊断阻塞

#### 8.2.3 指标监控

| 指标 | 说明 | 健康范围 |
|------|------|----------|
| 平均迭代次数 | 循环平均运行多少轮 | 视任务复杂度，通常 1-10 |
| 循环成功率 | 正常终止vs异常终止 | > 95% |
| 平均循环时长 | 从开始到终止的时间 | 视任务类型 |
| 工具调用成功率 | 循环中工具调用成功比例 | > 90% |
| 子 Agent 成功率 | 子 Agent 正常完成比例 | > 95% |
| Token 效率 | 输出token / 总token | > 30% |

---

## 9. 实施路线图

### 9.1 第一阶段：基础循环规范化（1-2 周）

**目标**：建立循环工程的基础实践

- [ ] 梳理现有 Agent 工作流，识别隐式循环
- [ ] 为关键工作流定义显式循环结构（迭代上限、终止条件）
- [ ] 在 TaskFlow 中实现最核心的 2-3 个循环模式
- [ ] 建立基础的循环日志和指标采集

### 9.2 第二阶段：高级模式落地（2-4 周）

**目标**：实现核心高级循环模式

- [ ] 实现 Evaluator-Optimizer 循环（子 Agent 分工版）
- [ ] 实现 Orchestrator-Workers 循环（多子 Agent 并行）
- [ ] 实现 Human-in-the-Loop 审批循环
- [ ] 实现多 ACP Harness 协作循环
- [ ] 建立循环模板库（可复用的循环模式）

### 9.3 第三阶段：治理与优化（2-3 周）

**目标**：建立循环治理体系

- [ ] 实现迭代上限和资源控制
- [ ] 建立循环安全边界（权限、范围、审计）
- [ ] 实现循环取消与回滚机制
- [ ] 建立完整的可观测性体系（追踪、指标、告警）
- [ ] 性能优化（并行化、上下文管理）

### 9.4 第四阶段：自动化与智能化（3-4 周）

**目标**：循环的自适应与自优化

- [ ] 循环模式自动选择（根据任务特征自动选择合适的循环模式）
- [ ] 动态迭代上限（根据任务复杂度自适应调整）
- [ ] 循环质量评估（自动评估循环效果并优化）
- [ ] 循环模板自动生成（根据历史数据生成新的循环模板）

---

## 10. 参考资源

### 10.1 核心文献

1. **Anthropic** —《Building Effective AI Agents》
   - 来源: https://www.anthropic.com/engineering/building-effective-agents
   - 要点: 五种工作流模式（Prompt Chaining, Routing, Parallelization, Orchestrator-Workers, Evaluator-Optimizer）及 Autonomous Agent 定义

2. **Model Context Protocol (MCP)** — 架构规范
   - 来源: https://modelcontextprotocol.io/docs/concepts/architecture
   - 要点: 工具/资源/提示的标准化接口，Client-Server 架构

3. **OODA Loop** — 观察-判断-决策-行动模型
   - 来源: 控制论与军事决策理论
   - 要点: Loop Engineering 的理论原型

### 10.2 OpenClaw 内部资源

4. **TaskFlow SKILL.md** — 持久化任务流机制
   - 位置: `~/.local/share/pnpm/global/5/.pnpm/openclaw@2026.6.10/node_modules/openclaw/skills/taskflow/SKILL.md`
   - 要点: createManaged, runTask, setWaiting, resume, finish 生命周期

5. **ACP Router SKILL.md** — ACP Harness 路由机制
   - 位置: `~/.openclaw/plugin-skills/acp-router/SKILL.md`
   - 要点: 多 Harness 接入、sessions_spawn ACP runtime

6. **TaskFlow Inbox Triage SKILL.md** — 收件箱分类循环示例
   - 位置: `~/.local/share/pnpm/global/5/.pnpm/openclaw@2026.6.10/node_modules/openclaw/skills/taskflow-inbox-triage/SKILL.md`
   - 要点: 路由+等待+恢复的循环实践

### 10.3 延伸阅读

7. **Andrew Ng** — Agentic Design Patterns 系列
   - Reflection, Tool Use, Planning, Multi-Agent Collaboration

8. **LangChain/LangGraph** — Agent 编排框架
   - 对比参考：不同框架对循环的抽象方式

9. **AutoGPT / BabyAGI** — 早期自主 Agent 循环实现
   - 对比参考：开源 Agent 循环的演进

---

## 附录 A：循环模式速查表

| 模式 | 迭代上限 | 并行度 | 适用场景 | OpenClaw 机制 |
|------|----------|--------|----------|--------------|
| Simple Tool Loop | 3-5 | 1 | 信息查询 | Agent Runtime 原生 |
| Evaluator-Optimizer | 3-5 | 1 | 质量优化 | Subagent 分工 |
| Orchestrator-Workers | 动态 | N | 复杂分解 | sessions_spawn |
| Routing | 1+子循环 | 1或N | 分类处理 | Skills / TaskFlow |
| Human-in-the-Loop | ∞ | 1 | 关键决策 | TaskFlow setWaiting |
| Multi-Agent Collab | 动态 | N | 多专长协作 | Subagent + Skills |
| Multi-Harness | 动态 | N | 异构Agent协作 | ACP Runtime |
| Recursive Decomp | 动态 | 递归 | 超大任务 | 递归 sessions_spawn |
| Competitive/Voting | 1 | N | 高置信度 | 多 model spawn |

## 附录 B：TaskFlow 循环生命周期伪代码

```typescript
// 通用循环模式
const flow = taskFlow.createManaged({
  controllerId: "loop-controller",
  goal: taskDescription,
  currentStep: "init",
  stateJson: { iteration: 0, results: [], maxIterations: 10 },
});

while (flow.status === "running") {
  const state = flow.stateJson;

  // 1. Observe: 获取当前状态
  const observation = observe(state);

  // 2. Orient: 判断是否需要继续
  if (shouldTerminate(observation, state)) {
    taskFlow.finish({
      flowId: flow.flowId,
      expectedRevision: flow.revision,
      stateJson: state,
    });
    break;
  }

  // 3. Decide & Act: 执行子任务
  const childTask = taskFlow.runTask({
    flowId: flow.flowId,
    runtime: "subagent",
    childSessionKey: `agent:loop:iter-${state.iteration}`,
    runId: `iteration-${state.iteration}`,
    task: buildTaskFromObservation(observation),
    status: "running",
    startedAt: Date.now(),
    lastEventAt: Date.now(),
  });

  // 4. Feedback: 等待子任务完成
  taskFlow.setWaiting({
    flowId: flow.flowId,
    expectedRevision: flow.revision,
    currentStep: `await-iter-${state.iteration}`,
    stateJson: { ...state, iteration: state.iteration + 1 },
    waitJson: { kind: "child_task", runId: `iteration-${state.iteration}` },
  });

  // 5. Resume: 子任务完成后恢复
  taskFlow.resume({
    flowId: flow.flowId,
    expectedRevision: waiting.flow.revision,
    status: "running",
    currentStep: `iter-${state.iteration + 1}`,
    stateJson: updatedState,
  });
}
```

---

*本文档基于 Anthropic Building Effective Agents、MCP 协议规范、OpenClaw 平台架构及 TaskFlow/ACP/Subagent 机制编写，旨在为 OpenClaw 平台上的 Loop Engineering 实践提供系统性指导。*
