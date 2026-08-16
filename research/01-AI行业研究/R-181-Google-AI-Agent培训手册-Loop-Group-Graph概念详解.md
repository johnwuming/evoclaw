# R-181: Google AI Agent 培训手册 — Loop / Group / Graph 概念详解

> **研究编号**: R-181  
> **分类**: AI行业研究  
> **创建日期**: 2026-08-04  
> **研究范围**: Google AI Agent 设计模式中 Loop、Group（Parallel/Collaborative）、Graph 三大核心编排概念的完整解析  
> **信息来源**: Google Cloud 官方文档、ADK (Agent Development Kit) 官方文档、Google Developers Blog、Google Cloud Blog

---

## 目录

1. [概述：从单体到多Agent编排](#1-概述从单体到多agent编排)
2. [Loop 概念详解](#2-loop-概念详解)
3. [Group 概念详解（Parallel / Collaborative）](#3-group-概念详解parallel--collaborative)
4. [Graph 概念详解](#4-graph-概念详解)
5. [三者对比与演进关系](#5-三者对比与演进关系)
6. [ADK 官方设计模式全景](#6-adk-官方设计模式全景)
7. [实战代码示例](#7-实战代码示例)
8. [学习资源](#8-学习资源)
9. [核心要点总结](#9-核心要点总结)

---

## 1. 概述：从单体到多Agent编排

Google 在 AI Agent 领域提出了一套系统化的编排方法论，其演进路径可以概括为：

```
单体Agent (Single Agent) → Loop循环 → Group并行/协作 → Graph有向图
```

这一演进反映了 Agent 系统从简单到复杂、从确定性到灵活性的渐进式设计哲学。

### Google ADK 的定位

**Agent Development Kit (ADK)** 是 Google 于 Cloud NEXT 2025 发布的开源框架，专为构建多Agent系统设计。它也是 Google 内部产品（Agentspace、Customer Engagement Suite）所使用的同一套框架。

ADK 支持四种工作流架构：

| 架构类型 | 版本要求 | 特点 |
|---------|---------|------|
| **Template Workflows** (模板工作流) | ADK 1.0+ | 预定义的 Sequential / Parallel / Loop 执行模式 |
| **Graph-based Workflows** (图工作流) | ADK 2.0+ | 节点+边的有向图，支持分支和条件路由 |
| **Dynamic Workflows** (动态工作流) | ADK 2.0+ | 使用编程代码逻辑动态编排 |
| **Collaborative Workflows** (协作工作流) | ADK 2.0+ | 单Agent作为动态协调者与子Agent协作 |

---

## 2. Loop 概念详解

### 2.1 定义

**Loop（循环）** 是一种多Agent编排模式，其中一组专门的子Agent按照预定义的顺序**反复执行**，直到满足特定的终止条件。

### 2.2 核心特征

- **迭代执行**：子Agent序列重复运行，非一次性执行
- **终止条件驱动**：通过退出条件（而非固定流程）决定何时停止
- **预定义逻辑**：编排本身不依赖LLM决策（区别于动态协调器模式）
- **状态累积**：每次迭代在共享 `session.state` 中累积结果

### 2.3 终止机制

ADK 的 LoopAgent 提供两种退出方式：

1. **最大迭代次数** (`max_iterations`)：硬性上限，防止无限循环
2. **escalate 机制**：Agent 通过工具调用设置 `tool_context.actions.escalate = True`，主动发出退出信号

```python
# 退出工具示例
def exit_loop(tool_context: ToolContext):
    """当评审通过时调用此工具，终止循环"""
    tool_context.actions.escalate = True
    tool_context.actions.skip_summarization = True
    return {}
```

### 2.4 典型应用场景

| 场景 | 描述 |
|-----|------|
| **生成-评审-修改** | 生成Agent产出内容 → 评审Agent检查 → 修改Agent优化，循环直到达标 |
| **代码生成与验证** | 代码生成Agent → 安全审计Agent → 修复Agent，循环直到无漏洞 |
| **内容创作打磨** | 初稿Agent → 批评Agent → 精炼Agent，循环提升质量 |
| **轮询监控** | 定期检查某条件是否满足，直到满足或超时 |

### 2.5 ADK 中的实现

```python
from google.adk.agents import LoopAgent, LlmAgent

# 生成Agent
generator = LlmAgent(
    name="Generator",
    instruction="生成SQL查询。如有{feedback}，修复错误后重新生成。",
    output_key="draft"
)

# 评审Agent
critic = LlmAgent(
    name="Critic",
    instruction="检查{draft}是否为有效SQL。正确则输出'PASS'，否则输出错误详情。",
    output_key="feedback"
)

# 循环Agent
loop = LoopAgent(
    name="ValidationLoop",
    sub_agents=[generator, critic],
    max_iterations=5  # 限制最大循环次数
)
```

### 2.6 注意事项

- ⚠️ **无限循环风险**：终止条件必须正确定义，否则可能导致系统挂起和过度消耗资源
- ⚠️ **成本累积**：每次迭代都会产生LLM调用，需权衡质量与成本
- ⚠️ **延迟叠加**：多轮迭代增加端到端延迟

---

## 3. Group 概念详解（Parallel / Collaborative）

> **说明**：Google ADK 官方术语中没有直接命名为 "Group" 的概念。业界培训中常说的 "Group" 对应 ADK 中的 **ParallelAgent**（并行Agent组）和 ADK 2.0 引入的 **Collaborative Workflow**（协作工作流），以及设计模式中的 **Swarm Pattern**（群集模式）。本节综合阐述这些"分组协作"概念。

### 3.1 ParallelAgent — 并行执行组

#### 定义

**ParallelAgent** 是一种工作流Agent，它**同时执行**多个子Agent，各子Agent独立工作，最终输出被汇总合成。

#### 核心特征

- **并发执行**：所有子Agent同时运行，而非排队
- **独立任务**：各子Agent处理互不依赖的子任务
- **状态共享但隔离**：各Agent共享 `session.state`，但应写入不同的 `output_key` 以避免竞态
- **预定义逻辑**：编排不依赖LLM决策

#### 典型场景

```
用户反馈分析 → 同时调度：
  ├─ 情感分析Agent → 情感结果
  ├─ 关键词提取Agent → 关键词列表  
  ├─ 分类Agent → 类别标签
  └─ 紧急度检测Agent → 紧急级别
→ 汇总Agent → 综合分析报告
```

#### ADK 实现

```python
from google.adk.agents import ParallelAgent, LlmAgent, SequentialAgent

# 定义并行工作的子Agent
security_scanner = LlmAgent(
    name="SecurityAuditor",
    instruction="检查注入攻击等安全漏洞。",
    output_key="security_report"
)

style_checker = LlmAgent(
    name="StyleEnforcer",
    instruction="检查PEP8合规性和格式问题。",
    output_key="style_report"
)

complexity_analyzer = LlmAgent(
    name="PerformanceAnalyst",
    instruction="分析时间复杂度和资源使用。",
    output_key="performance_report"
)

# Fan-out 并行执行
parallel_reviews = ParallelAgent(
    name="CodeReviewSwarm",
    sub_agents=[security_scanner, style_checker, complexity_analyzer]
)

# Gather 汇总合成
pr_summarizer = LlmAgent(
    name="PRSummarizer",
    instruction="基于{security_report}、{style_report}和{performance_report}创建合并的PR评审报告。"
)

# 组合为顺序流程：先并行再汇总
workflow = SequentialAgent(sub_agents=[parallel_reviews, pr_summarizer])
```

### 3.2 Swarm Pattern — 群集协作模式

#### 定义

**Swarm** 是一种全互通（all-to-all）的协作模式。多个专门化Agent共同工作，通过迭代式优化来解决复杂问题。任何Agent都可以将任务交给更适合的Agent。

#### 核心特征

- **无中央协调器**：dispatcher 负责消息传递而非任务编排
- **全互通通信**：每个Agent都能与其他任何Agent通信
- **动态交接**：Agent可自行决定将任务交给更适合的同伴
- **需显式退出条件**：必须定义最大迭代次数、时间限制或共识达成条件

#### 典型场景

产品设计任务：
```
市场研究Agent ↔ 工程Agent ↔ 财务建模Agent
  - 分享初步想法
  - 辩论功能与成本的权衡
  - 共同收敛到平衡各方需求的设计规范
```

### 3.3 Collaborative Workflow（ADK 2.0+）

ADK 2.0 引入的协作工作流允许**单个Agent作为动态协调者**，与一组指定的子Agent协作完成任务。与模板工作流不同，协调者Agent使用LLM推理来动态决定如何分配和路由任务。

### 3.4 Group/并行模式的权衡

| 优势 | 劣势 |
|-----|------|
| 降低整体延迟（并行执行） | 即时资源利用率高 |
| 收集多样化视角 | token消耗大，成本高 |
| 模块化设计，易维护 | 汇总逻辑复杂（需处理冲突结果） |
| 可扩展（增加/移除子Agent） | Swarm模式可能不收敛 |

---

## 4. Graph 概念详解

### 4.1 定义

**Graph（图工作流）** 是 ADK 2.0 引入的编排模式，允许将Agent逻辑定义为由**执行节点（Node）**和**边（Edge）**组成的有向图，结合AI推理和确定性代码逻辑。

### 4.2 核心概念

#### Node（节点）

图中的节点可以是以下任一类型：
- **AI Agent**：基于LLM的推理Agent
- **Tool**：ADK工具调用
- **Code Function**：用户自定义的Python/JS函数
- **Human Input**：人工输入节点
- **Workflow**：嵌套的另一个工作流

每个节点接受上游节点的输入，通过 `Event` 对象输出数据。

#### Edge（边）

边定义了节点之间的执行顺序和路由逻辑：
- **顺序边**：按数组顺序执行
- **条件边**：根据路由值选择执行路径
- **并行边**：多个START入口实现并行

#### Event（事件）

节点间数据传递的载体：
```python
from google.adk import Event

# 路由事件 — 指定下一步走哪条路
def router(node_input: str):
    if condition(node_input):
        return Event(route="RUN_TASK_C")
    return Event(route="RUN_TASK_B")

# 输出事件 — 传递数据给下游
def my_function_node(node_input: str):
    return Event(output=node_input.upper())
```

### 4.3 Graph 的核心优势

| 优势 | 说明 |
|-----|------|
| **精确逻辑控制** | 显式映射路由逻辑，管理节点间转换 |
| **复杂结构支持** | 支持分支和状态管理 |
| **纯代码执行链** | 无需AI模型即可调用工具和代码 |
| **增强可靠性** | 结构化节点定义比纯prompt更可靠 |
| **Prompt可视化** | 将长prompt中的步骤分解为图结构 |

### 4.4 关键模式

#### 分支路由（Conditional Branching）

```python
from google.adk import Workflow, Event

root_agent = Workflow(
   name="routing_workflow",
   edges=[
       ("START", process_message, router),
       (router, {
           "BUG": response_1_bug,
           "CUSTOMER_SUPPORT": response_2_support,
           "LOGISTICS": response_3_logistics,
       }),
   ],
)
```

#### 并行 + Join 汇聚

```python
from google.adk.workflow import JoinNode

my_join_node = JoinNode(name="my_join_node")

edges=[
    ("START", parallel_task_A, my_join_node),
    ("START", parallel_task_B, my_join_node),
    ("START", parallel_task_C, my_join_node),
    (my_join_node, final_task_D),
]
```

> JoinNode 等待所有上游节点完成后，将输出汇总传递给下一个节点。

#### 嵌套工作流（Nested Workflows）

Workflow可以作为另一个Workflow的节点使用，实现复杂逻辑的封装和复用：

```python
root_agent = Workflow(
    name="parent_workflow",
    edges=[
       ("START", task_A1, router),
       (router, {
            "RUN_WORKFLOW_B": workflow_B,  # 嵌套工作流
            "RUN_WORKFLOW_C": workflow_C,  # 嵌套工作流
       }),
    ],
)
```

### 4.5 从 Prompt 到 Graph 的范式转换

Google 官方文档强调了一个重要的设计理念转变：

```
长Prompt Agent → Graph-based Workflow
```

当一个Agent的instruction越来越长、步骤越来越多时，确保Agent遵循每一步变得困难且不可靠。Graph工作流通过将每个步骤明确定义为图中的节点，将非确定性的prompt推理与确定性的代码执行交替结合，大幅提升了可控性和可靠性。

### 4.6 已知限制

- ❌ 不兼容 Live Streaming 功能
- ❌ 部分第三方 Integrations 可能不兼容
- ⚠️ Workflow 中的 Agent 需设置为单轮任务模式

---

## 5. 三者对比与演进关系

### 5.1 概念对比表

| 维度 | Loop | Group (Parallel/Swarm) | Graph |
|------|------|----------------------|-------|
| **执行方式** | 线性重复 | 并发或全互通 | 有向图（支持分支、循环、并行） |
| **确定性** | 确定编排逻辑 | 确定编排逻辑 | 确定路由 + 可选AI推理 |
| **灵活性** | 中（固定子Agent序列） | 中（固定子Agent集合） | 高（任意拓扑结构） |
| **适用复杂度** | 中等（迭代优化） | 中等（多视角融合） | 高（复杂业务流程） |
| **ADK版本** | 1.0+ | 1.0+ (Parallel) / 2.0+ (Collaborative) | 2.0+ |
| **退出条件** | 必须 | Swarm必须 | 图遍历完成即退出 |
| **成本控制** | max_iterations | 并发数控制 | 节点级别控制 |

### 5.2 演进路线

```
阶段1: Single Agent (单体)
  ↓ 任务变复杂，需要迭代
阶段2: Loop (循环优化)
  ↓ 需要多视角并行处理
阶段3: Group/Parallel (并行协作)
  ↓ 需要复杂分支和精确控制
阶段4: Graph (图工作流)
  ↓ 需要完全灵活的动态编排
阶段5: Composite (混合模式)
```

### 5.3 混合使用

实际上，这三者**并非互斥**，而是可以组合使用：

- Graph 中可以包含 Loop 节点
- Graph 中可以实现 Parallel + Join 模式
- Loop 内部可以包含 Parallel 子流程
- Sequential Pipeline 可以串联 [Parallel Group] → [Loop] → [Graph]

---

## 6. ADK 官方设计模式全景

Google 官方文档定义了 **10+ 种** Agent 设计模式，可按工作流类型分类：

### 确定性工作流模式

| 模式 | 类型 | 说明 |
|-----|------|------|
| Sequential Pipeline | 模板 | 线性顺序执行 |
| Parallel Fan-Out/Gather | 模板 (Group) | 并行执行+汇总 |
| Loop | 模板 | 循环迭代 |
| Iterative Refinement | Loop变体 | 渐进式质量提升 |
| Review & Critique | Loop变体 | 生成-评审循环 |

### 动态编排模式

| 模式 | 类型 | 说明 |
|-----|------|------|
| Coordinator/Dispatcher | 协调器 | LLM驱动的动态路由 |
| Hierarchical Decomposition | 协调器变体 | 多层级任务分解 |
| Swarm | 群集 | 全互通协作 |

### 高级模式

| 模式 | 类型 | 说明 |
|-----|------|------|
| ReAct | 推理循环 | Thought-Action-Observation循环 |
| Human-in-the-Loop | 安全网 | 人工审批检查点 |
| Custom Logic | 自定义 | 条件分支等复杂逻辑 |
| Graph Workflow | 图 | ADK 2.0 有向图编排 |

---

## 7. 实战代码示例

### 7.1 完整的 Loop + Sequential 组合（迭代写作Pipeline）

```python
from google.adk.agents import LoopAgent, LlmAgent, SequentialAgent
from google.adk.tools.tool_context import ToolContext

STATE_CURRENT_DOC = "current_document"
STATE_CRITICISM = "criticism"
COMPLETION_PHRASE = "No major issues found."

def exit_loop(tool_context: ToolContext):
    """当评审认为无需修改时调用，终止循环"""
    tool_context.actions.escalate = True
    tool_context.actions.skip_summarization = True
    return {}

# Step 1: 初始写作Agent（仅执行一次）
initial_writer = LlmAgent(
    name="InitialWriterAgent",
    model="gemini-2.5-flash",
    include_contents='none',
    instruction=f"写一个关于{{{{initial_topic}}}}的简短故事初稿（2-4句）。",
    output_key=STATE_CURRENT_DOC
)

# Step 2a: 评审Agent（循环内）
critic = LlmAgent(
    name="CriticAgent",
    model="gemini-2.5-flash",
    include_contents='none',
    instruction=f"""
    你是评审AI。审查以下文档：
    ```
    {{{{{STATE_CURRENT_DOC}}}}}
    ```
    评审标准：
    1. 至少4句话
    2. 有清晰的开头、中间和结尾
    3. 包含至少一个感官或情感描写
    
    如有不足，提供具体修改建议。
    如全部满足，回复："{COMPLETION_PHRASE}"
    """,
    output_key=STATE_CRITICISM
)

# Step 2b: 修改/退出Agent（循环内）
refiner = LlmAgent(
    name="RefinerAgent",
    model="gemini-2.5-flash",
    include_contents='none',
    instruction=f"""
    当前文档：{{{{{{STATE_CURRENT_DOC}}}}}}
    评审意见：{{{{{{STATE_CRITICISM}}}}}}
    
    如果评审意见是"{COMPLETION_PHRASE}"，调用exit_loop函数。
    否则，根据评审意见修改文档。只输出修改后的文档。
    """,
    tools=[exit_loop],
    output_key=STATE_CURRENT_DOC
)

# Step 2: 循环Agent
refinement_loop = LoopAgent(
    name="RefinementLoop",
    sub_agents=[critic, refiner],
    max_iterations=5
)

# Step 3: 完整Pipeline
root_agent = SequentialAgent(
    name="IterativeWritingPipeline",
    sub_agents=[initial_writer, refinement_loop]
)
```

### 7.2 Graph 工作流（条件路由）

```python
from google.adk import Agent, Workflow, Event

# 分类Agent
process_message = Agent(
    name="process_message",
    model="gemini-flash-latest",
    instruction="""将用户消息分类为"BUG"、"CUSTOMER_SUPPORT"或"LOGISTICS"。
    如多类别适用，用逗号分隔。""",
    output_schema=str,
)

# 路由函数
def router(node_input: str):
    routes = [r.strip() for r in node_input.split(",")]
    return Event(route=routes)

# 响应函数
def response_1_bug():
    return Event(message="处理Bug中...")

def response_2_support():
    return Event(message="处理客户支持中...")

def response_3_logistics():
    return Event(message="处理物流中...")

# 图工作流
root_agent = Workflow(
   name="routing_workflow",
   edges=[
       ("START", process_message, router),
       (router, {
           "BUG": response_1_bug,
           "CUSTOMER_SUPPORT": response_2_support,
           "LOGISTICS": response_3_logistics,
       }),
   ],
)
```

### 7.3 Parallel + Sequential 组合（代码评审系统）

```python
from google.adk.agents import ParallelAgent, SequentialAgent, LlmAgent

# 并行评审Agent们
security = LlmAgent(
    name="SecurityAuditor",
    instruction="检查安全漏洞如注入攻击。",
    output_key="security_report"
)

style = LlmAgent(
    name="StyleEnforcer",
    instruction="检查PEP8合规性。",
    output_key="style_report"
)

performance = LlmAgent(
    name="PerformanceAnalyst",
    instruction="分析时间复杂度和资源使用。",
    output_key="performance_report"
)

# 并行组
parallel_group = ParallelAgent(
    name="CodeReviewGroup",
    sub_agents=[security, style, performance]
)

# 汇总Agent
synthesizer = LlmAgent(
    name="PRSummarizer",
    instruction="""基于以下三份报告创建合并的PR评审：
    安全：{security_report}
    风格：{style_report}  
    性能：{performance_report}"""
)

# 最终流程
workflow = SequentialAgent(
    name="CodeReviewPipeline",
    sub_agents=[parallel_group, synthesizer]
)
```

---

## 8. 学习资源

### 官方文档

| 资源 | 链接 |
|------|------|
| ADK 官方文档站 | https://adk.dev |
| 选择Agent设计模式 | https://docs.cloud.google.com/architecture/choose-design-pattern-agentic-ai-system |
| ADK多Agent设计模式指南 | https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/ |
| ADK Loop Agent 文档 | https://adk.dev/agents/workflow-agents/loop-agents/ |
| ADK Graph 工作流文档 | https://adk.dev/graphs/ |
| ADK Graph 路由文档 | https://adk.dev/graphs/routes/ |
| 工作流概览 | https://adk.dev/workflows/ |

### Google Cloud Blog

| 资源 | 链接 |
|------|------|
| 构建协作AI：多Agent系统开发者指南 | https://cloud.google.com/blog/topics/developers-practitioners/building-collaborative-ai-a-developers-guide-to-multi-agent-systems-with-adk |
| 使用ADK构建多Agent系统 | https://cloud.google.com/blog/products/ai-machine-learning/build-multi-agentic-systems-using-google-adk |
| ADK：让多Agent应用开发更简单 | https://developers.googleblog.com/agent-development-kit-easy-to-build-multi-agent-applications/ |

### 视频/培训资源

| 资源 | 链接 |
|------|------|
| 多Agent系统基础（ADK） | https://www.youtube.com/watch?v=pX0_iIfRilU |
| AI Agent学习系列 EP3 | https://www.youtube.com/watch?v=a3sQ2cgTJJY |
| ADK 2.0 图工作流介绍 | https://www.youtube.com/watch?v=xyhzznb0vtg |
| ADK Crash Course (Codelabs) | https://codelabs.developers.google.com/onramp/instructions |
| 使用ADK构建多Agent系统 (Codelab) | https://codelabs.developers.google.com/codelabs/production-ready-ai-with-gc/3-developing-agents/build-a-multi-agent-system-with-adk |

### 社区/深度分析

| 资源 | 链接 |
|------|------|
| Loop模式实战 (Medium) | https://medium.com/google-cloud/using-the-loop-pattern-to-make-my-multi-agent-solution-more-robust-86f8e9159a2a |
| ADK vs LangGraph对比 | https://www.zenml.io/blog/google-adk-vs-langgraph |
| 从Loop到Graph的范式转变 | https://flowtivity.ai/blog/graph-engineering-2026-guide-openclaw-codex/ |

---

## 9. 核心要点总结

### 📌 Loop 的本质
- **循环执行**子Agent序列直到满足退出条件
- 核心价值：**迭代优化**和**自纠正**
- 关键配置：`max_iterations` + `escalate` 退出机制
- 适合：质量门控、内容打磨、代码审查循环

### 📌 Group 的本质
- **并行执行**多个专门化Agent，汇总各自结果
- 核心价值：**多视角融合**和**延迟降低**
- 关键配置：各Agent独立 `output_key`，JoinNode 汇聚
- 适合：多维度分析、代码评审、多源数据采集
- ADK 2.0 的 Collaborative Workflow 进一步支持 LLM 驱动的动态协调

### 📌 Graph 的本质
- **有向图**定义执行路径，节点（Agent/Tool/代码）通过边连接
- 核心价值：**精确控制**和**复杂分支**
- 关键配置：`edges` 数组定义拓扑，`Event(route=...)` 控制分支
- 适合：复杂业务流程、条件路由、人机协作检查点
- ADK 2.0 的核心创新，代表从 prompt 驱动到代码驱动的范式转变

### 📌 三者关系
- **互补而非替代**：Loop 和 Group 可以作为 Graph 中的节点
- **演进方向**：Loop → Group → Graph 反映了从简单到复杂的编排需求
- **选择原则**：从简单模式开始，当需求超出模板能力时升级到Graph

### 📌 Google 的设计哲学
1. **模块化**：将大任务分解为专门的子Agent
2. **渐进式复杂度**：从单Agent开始，按需增加编排复杂度
3. **确定性优先**：能用代码确定的逻辑就不要依赖LLM推理
4. **状态管理**：`session.state` 是Agent间共享信息的白板
5. **安全第一**：高风险操作必须有人工审批检查点

---

*本报告基于 Google ADK 官方文档和 Google Cloud 架构中心最新发布的内容编写，涵盖 ADK 1.0 至 2.0 的完整概念体系。*
