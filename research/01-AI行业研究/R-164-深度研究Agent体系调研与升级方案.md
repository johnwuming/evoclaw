# R-164 深度研究Agent体系调研与升级方案

> **调研时间**: 2026-07-20  
> **调研角色**: research-lead  
> **任务编号**: task-0108  
> **交付路径**: shared/results/01-AI行业研究/R-164-深度研究Agent体系调研与升级方案.md

---

## 目录

1. [执行摘要](#1-执行摘要)
2. [行业全景：Deep Research Agent 2025-2026](#2-行业全景deep-research-agent-2025-2026)
3. [大厂方案深度拆解](#3-大厂方案深度拆解)
4. [开源框架对比](#4-开源框架对比)
5. [我们现有架构诊断](#5-我们现有架构诊断)
6. [升级方案](#6-升级方案)
7. [实施路线图](#7-实施路线图)
8. [参考资料](#8-参考资料)

---

## 1. 执行摘要

2025年以来，"深度研究"（Deep Research）已成为AI Agent领域最核心的应用形态之一。OpenAI、Anthropic、Google、Perplexity等大厂纷纷推出产品级Deep Research能力，其核心范式从简单的RAG检索演进为**多Agent协同+迭代式搜索+动态推理**的复杂架构。

本报告系统调研了四大厂方案及主流开源框架，对比我们现有基于OpenClaw的研究团队架构，识别出**五大差距领域**，并提出分三阶段实施的升级方案，目标是构建一个**自规划、可并行、可追溯、可评估**的深度研究Agent体系。

**核心建议**：
- 引入**研究Brief生成+迭代式Supervisor**架构（借鉴LangChain/Anthropic）
- 增加**子Agent并行研究+上下文压缩**机制
- 建立**引用追溯+质量评估**体系
- 构建**可配置研究策略**（广度优先/深度优先/对比分析）
- 集成**浏览器自动化+MCP工具生态**

---

## 2. 行业全景：Deep Research Agent 2025-2026

### 2.1 核心范式转移

| 维度 | 传统RAG (2023-2024) | Deep Research Agent (2025-2026) |
|------|---------------------|-------------------------------|
| **检索方式** | 静态向量相似度检索 | 动态多步搜索，自适应路由 |
| **推理深度** | 单轮检索+生成 | 多轮迭代推理，基于中间发现动态调整策略 |
| **Agent架构** | 单Agent或管道式 | 多Agent协同（Orchestrator-Worker模式） |
| **上下文管理** | 依赖单一上下文窗口 | 子Agent独立上下文+压缩汇总+Memory持久化 |
| **输出质量** | 摘要式回答 | 研究报告级输出，含引用、图表、数据可视化 |
| **工具使用** | 简单搜索API | 浏览器自动化、代码执行、MCP服务器、文件分析 |
| **耗时** | 秒级 | 5-30分钟级 |
| **成本** | 低（~$0.01/查询） | 高（multi-agent约15×聊天成本） |

### 2.2 关键技术趋势

1. **多Agent编排成为标配**：Orchestrator-Worker模式（Anthropic）、Supervisor-SubAgent模式（LangChain）、Planner-Executor模式（GPT Researcher）殊途同归
2. **Token消耗是性能核心驱动**：Anthropic发现token使用量解释了80%的性能方差，多Agent架构本质是"花足够多的token来解决问题"
3. **研究策略分化**：广度优先（并行探索多方向）、深度优先（迭代深挖单一领域）、对比分析（分别研究后综合比较）
4. **可中断+可追踪**：OpenAI 2026年2月更新支持实时进度追踪和中途打断优化
5. **MCP协议集成**：OpenAI Deep Research已支持连接任意MCP服务器和应用
6. **评估基准建立**：Deep Research Bench（100道PhD级研究任务，RACE评分）成为行业标准评估

---

## 3. 大厂方案深度拆解

### 3.1 OpenAI Deep Research

**发布时间**：2025年2月

**核心架构**：
- 基于OpenAI o3模型优化版本，专门针对网页浏览和数据分析进行强化训练
- 使用与o1相同的强化学习方法，在真实世界任务上训练浏览器和Python工具使用
- 推理驱动的搜索、解读和分析大量文本、图片和PDF

**工作流程**：
1. 用户在ChatGPT中选择"deep research"模式并输入查询
2. 系统自主规划研究路径，搜索、分析、综合数百个在线来源
3. 侧边栏实时展示研究步骤和使用的来源
4. 5-30分钟完成，输出带完整引用的研究报告

**关键特性**：
- **MCP集成**（2026年2月）：可连接任意MCP服务器/应用，限制搜索到可信站点
- **可视化浏览器**（2025年7月）：作为ChatGPT agent模式的一部分，具备视觉浏览能力
- **轻量级版本**（2025年4月）：基于o4-mini的降本版本，Pro用户250次/月，Free用户5次/月
- **实时进度追踪**：可查看研究进度并中途打断优化
- **多模态输入**：支持附件文件和电子表格
- **引用文档化**：每个输出都有清晰引用和思维过程摘要

**架构亮点**：
```
用户查询 -> o3推理模型规划 -> 浏览器搜索循环 -> 
Python数据分析 -> 中间结果推理 -> 动态调整策略 -> 
综合报告生成（含引用）
```

**配额体系**：
- Plus/Team/Enterprise: 25次/月（完整版）
- Pro: 250次/月
- Free: 5次/月（轻量版自动降级）

### 3.2 Anthropic Claude Research（多Agent研究系统）

**发布时间**：2025年（Claude Research功能）

**核心架构**：Orchestrator-Worker多Agent模式

**详细工作流**：
1. **LeadResearcher Agent启动**：分析用户查询，制定研究策略
2. **Memory持久化**：将计划保存到Memory（因200K token上下文窗口可能被截断）
3. **创建Subagents**：LeadResearcher分解查询为子任务，创建多个并行子Agent
4. **Subagent独立研究**：每个子Agent独立执行网页搜索，使用interleaved thinking评估工具结果
5. **结果返回与综合**：子Agent返回清洗后的发现给LeadResearcher
6. **迭代决策**：LeadResearcher判断是否需要更多研究，可创建额外子Agent或调整策略
7. **CitationAgent处理**：所有发现交给CitationAgent，为报告中每个声明标注引用来源
8. **最终输出**：带完整引用的研究结果返回用户

**关键设计原则**：

| 原则 | 说明 |
|------|------|
| **教编排者如何委派** | 每个子Agent需要：明确目标、输出格式、工具/来源指导、清晰任务边界 |
| **像Agent一样思考** | 在Console中用精确prompts和工具模拟Agent行为，逐步观察发现故障模式 |
| **工具设计** | 搜索工具返回结构化数据，限制结果数量防止上下文膨胀 |
| **压缩是核心** | 子Agent在独立上下文中并行探索，然后压缩最重要信息返回 |

**性能数据**：
- 多Agent（Opus 4 lead + Sonnet 4 subagents）比单Agent Opus 4在内部研究评估上**高出90.2%**
- Token使用量解释BrowseComp评估**80%的性能方差**
- 多Agent系统使用约**15×聊天token**，单Agent约4×聊天token
- 升级到更好的模型 > 增加token预算（Sonnet 4升级比翻倍token预算增益更大）

**适用场景**：广度优先查询、信息量超单一上下文窗口、大量工具接口。**不适用于**：需共享上下文、Agent间高依赖、实时协调的任务。

### 3.3 Google Gemini Deep Research

**发布时间**：2024年12月（实验性），2025年持续迭代

**核心架构**：
- 基于Gemini 2.0系列模型（Flash/Pro/Flash-Lite）
- 利用超大上下文窗口（Pro: 200万token，Flash: 100万token）
- 结合Google Search的实时信息检索能力

**关键特性**：
- **多步研究规划**：Gemini自动拆解研究问题为子主题
- **大上下文优势**：200万token窗口可一次性处理海量信息，减少分块丢失
- **多模态输入输出**：支持文本、图片、音频输入
- **Google生态集成**：原生集成Google Search、Google Workspace
- **代码执行能力**：内置代码执行工具进行数据分析
- **Agent作为工具**（Agent-as-a-Tool）：Gemini可调用其他Gemini实例作为工具

**架构特点**：
```
用户查询 -> Gemini规划研究大纲 -> 生成子主题列表 ->
并行搜索+信息提取 -> 多轮迭代深入 -> 
综合生成结构化报告（含来源链接）
```

**模型分层策略**：
- Gemini 2.0 Pro：最强编码和复杂推理，200万token上下文
- Gemini 2.0 Flash：高效主力模型，100万token上下文
- Gemini 2.0 Flash-Lite：最具成本效益

### 3.4 Perplexity Deep Research

**发布时间**：2025年初

**核心架构**：
- 基于Perplexity的Answer Engine + 多步推理
- 结合自研搜索索引和LLM推理
- 迭代式搜索-评估-再搜索循环

**关键特性**：
- **数十次搜索循环**：针对复杂问题执行多轮搜索
- **动态查询调整**：基于已有发现调整后续搜索策略
- **来源质量评估**：对搜索结果进行可信度评估
- **结构化输出**：带内联引用的研究报告
- **Pro Search增强**：Deep Research是Pro Search的进一步深化

### 3.5 大厂方案横向对比

| 维度 | OpenAI | Anthropic | Google | Perplexity |
|------|--------|-----------|--------|------------|
| **底层模型** | o3/o4-mini优化版 | Claude Opus 4 + Sonnet 4 | Gemini 2.0 Pro/Flash | 多模型路由 |
| **Agent架构** | 单Agent+工具循环 | Orchestrator-Worker多Agent | Agent-as-a-Tool | 迭代搜索循环 |
| **上下文窗口** | ~200K | 200K（Memory持久化） | 200万（Pro） | 未公开 |
| **并行能力** | 顺序为主 | ✅ 强（多子Agent并行） | ✅ 强 | 中等 |
| **浏览器** | ✅ 可视化浏览器 | ✅ 网页搜索 | ✅ Google搜索 | ✅ 自有搜索索引 |
| **MCP支持** | ✅ | ✅ 集成 | Google生态 | 有限 |
| **引用追溯** | ✅ 完整 | ✅ CitationAgent | ✅ 来源链接 | ✅ 内联引用 |
| **可中断** | ✅ | ❌ 未确认 | ❌ 未确认 | ❌ 未确认 |
| **耗时** | 5-30分钟 | 数分钟 | 数分钟 | 数分钟 |
| **成本** | 高 | 很高（15×聊天） | 中 | 中 |
| **数据可视化** | ✅ 嵌入图表 | ❌ 未确认 | ✅ | ❌ 未确认 |

---

## 4. 开源框架对比

### 4.1 LangChain Open Deep Research

**仓库**：github.com/langchain-ai/open_deep_research  
**排名**：Deep Research Bench第6名（RACE: 0.4344）

**三阶段架构**：

#### Phase 1: Scope（范围界定）
- **User Clarification**：使用chat模型询问用户补充上下文
- **Brief Generation**：将对话交互转化为聚焦的研究Brief，作为整个研究的"北极星"

#### Phase 2: Research（研究执行）
- **Research Supervisor**：Supervisor Agent将研究Brief分解为独立子主题
- **Research Sub-Agents**：每个子Agent专注于特定子主题，在独立上下文中执行工具调用循环
- **上下文压缩**：每个子Agent完成后做最终LLM调用，清洗研究发现后返回Supervisor
- **迭代研究**：Supervisor评估发现是否充分，可继续创建更多子Agent

#### Phase 3: Report Writing（报告写作）
- 单次LLM调用，基于研究Brief和所有子Agent发现生成最终报告
- **关键教训**：不使用多Agent并行写报告（会导致报告不连贯），写作在所有研究完成后统一进行

**配置灵活性**：
- 支持任意模型提供商（通过`init_chat_model()` API）
- 四种模型角色：Summarization、Research、Compression、Final Report
- 支持Tavily、MCP、Anthropic原生搜索、OpenAI原生搜索
- 默认配置：GPT-4.1系列，成本$45.98/100题

**评估结果**：

| 配置 | Research模型 | RACE分数 | 成本 |
|------|-------------|---------|------|
| GPT-5 | openai:gpt-5 | 0.4943 | - |
| 默认 | openai:gpt-4.1 | 0.4309 | $45.98 |

**核心教训**：
1. 多Agent仅用于可并行任务（研究阶段），不用于需协调的任务（写作阶段）
2. 子Agent返回压缩后的清洁信息，而非原始数据
3. 研究Brief是关键创新——将冗长对话转化为聚焦指南

### 4.2 GPT Researcher

**仓库**：github.com/assafelovic/gpt-researcher  
**特点**：最早的开源Deep Research Agent之一

**架构**：Planner-Executor模式
```
研究查询 -> 创建任务专属Agent ->
Planner生成研究问题 ->
Executor Agents并行收集信息 ->
Summarize + Source-track每条资源 ->
Filter + Aggregate -> 最终研究报告
```

**核心特性**：
- Plan-and-Solve + RAG灵感
- 聚合20+来源得出客观结论
- 支持Web和本地文档研究
- JavaScript-enabled网页抓取
- 报告导出为PDF/Word
- AI生成内联图片（Google Gemini Nano Banana）
- 可安装为Claude Skill：`npx skills add assafelovic/gpt-researcher`
- 支持NextJS + Tailwind前端

**优势**：成熟稳定，社区活跃，文档完善，多语言支持（中/英/日/韩）  
**局限**：架构相对简单，无Supervisor迭代循环，缺少MCP支持

### 4.3 其他值得关注的框架

| 框架 | 特点 | 适用场景 |
|------|------|---------|
| **HuggingFace open-deep-research** | 社区驱动的Deep Research实现 | 学习和实验 |
| **Google gemini-fullstack-langgraph-quickstart** | Google官方LangGraph全栈模板 | Gemini生态用户 |
| **DeepResearch-Leaderboard** | 100道PhD级研究任务评测基准 | 评估研究Agent质量 |

### 4.4 Deep Research Bench评估体系

- **任务集**：100道PhD级研究任务（50英文+50中文）
- **领域**：22个领域（科技、商业金融等）
- **评估指标**：RACE分数（LLM-as-a-judge，Gemini评判）
- **对比基线**：与专家编写的golden报告对比

---

## 5. 我们现有架构诊断

### 5.1 现有架构概览

当前研究团队基于OpenClaw平台运行：

```
任务中心(tasks.db) -> 主Agent分配 -> research-lead子Agent ->
  ├── 执行研究（Web搜索/文件读取）
  ├── 产出存入 shared/results/
  └── 写入 .task-completions.jsonl 完成回报
```

**现有能力**：
- ✅ 任务中心驱动的任务分配
- ✅ 子Agent可以spawn下级子Agent（最多4层深度）
- ✅ Web搜索和网页抓取能力
- ✅ 文件读写和结果存储
- ✅ ai-berkshire投资研究框架（19个研究Skill）
- ✅ 多通道消息推送（QQ/微信/Telegram等）
- ✅ MCP工具生态集成
- ✅ 浏览器自动化能力（browser-automation skill）
- ✅ TaskFlow多步任务协调

### 5.2 五大差距诊断

#### 差距1：缺乏研究Brief生成与策略规划
**现状**：收到任务后直接开始搜索执行，无系统性的研究策略规划  
**行业最佳实践**：
- LangChain先生成研究Brief作为"北极星"
- OpenAI通过o3推理模型规划研究路径
- Anthropic的LeadResearcher先制定策略再执行

**影响**：研究方向不够系统化，容易遗漏关键维度，输出质量不稳定

#### 差距2：子Agent并行研究能力未充分运用
**现状**：虽然支持spawn子Agent，但缺少Supervisor-SubAgent编排模式  
**行业最佳实践**：
- Anthropic：LeadResearcher + 多个并行SubAgent + CitationAgent
- LangChain：Supervisor分解Brief -> 并行子Agent -> 迭代补充
- GPT Researcher：Planner生成问题 -> Executor并行收集

**影响**：研究速度慢（顺序执行），信息覆盖面有限，无法处理需要广度探索的复杂任务

#### 差距3：无上下文压缩与Memory持久化
**现状**：子Agent结果直接返回，无压缩机制；上下文截断后无法恢复  
**行业最佳实践**：
- LangChain：子Agent做最终LLM调用清洗发现后返回
- Anthropic：LeadResearcher将计划保存到Memory防止截断丢失
- 所有方案都强调"压缩是搜索的本质"

**影响**：长研究任务中上下文膨胀，重要信息被截断，Supervisor需处理大量原始token

#### 差距4：缺少引用追溯与质量评估
**现状**：产出Markdown报告但无系统化引用标注，无质量评估机制  
**行业最佳实践**：
- OpenAI：每个声明都有引用，含思维过程摘要
- Anthropic：专门的CitationAgent处理引用标注
- LangChain：Deep Research Bench标准化评估（RACE分数）

**影响**：报告可信度不足，无法验证信息来源，无法量化评估研究质量

#### 差距5：研究策略不可配置
**现状**：所有任务使用相同的研究流程  
**行业最佳实践**：
- LangChain：根据查询类型选择不同策略（对比/列举/验证）
- OpenAI：agent模式vs deep research模式可选
- 行业共识：广度优先/深度优先/对比分析需不同策略

**影响**：简单任务过度研究浪费时间，复杂任务深度不够

### 5.3 差距优先级矩阵

| 差距 | 影响程度 | 实现难度 | 优先级 |
|------|---------|---------|--------|
| 1. 研究Brief生成 | 🔴 高 | 🟡 中 | P0 |
| 2. 并行子Agent编排 | 🔴 高 | 🟡 中 | P0 |
| 3. 上下文压缩+Memory | 🟡 中 | 🟢 低 | P1 |
| 4. 引用追溯+评估 | 🔴 高 | 🟡 中 | P1 |
| 5. 可配置研究策略 | 🟡 中 | 🔴 高 | P2 |

---

## 6. 升级方案

### 6.1 目标架构总览

```
用户查询/任务 
    │
    ▼
┌─────────────────────────────────────┐
│  Phase 1: Scope（范围界定）          │
│  ├── 用户澄清（如需要）              │
│  └── 研究Brief生成                  │
│      （研究目标、子主题、策略选择）    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Phase 2: Research（研究执行）        │
│  ├── Research Supervisor             │
│  │   ├── 分解Brief为子任务            │
│  │   ├── 分配并行Sub-Agents           │
│  │   └── 评估发现充分性（迭代）        │
│  │                                   │
│  ├── Sub-Agent 1 (子主题A)           │
│  │   ├── Web搜索 + 浏览器自动化       │
│  │   ├── 文件/PDF分析                │
│  │   └── 发现压缩 -> 返回Supervisor    │
│  │                                   │
│  ├── Sub-Agent 2 (子主题B)           │
│  │   └── ...                         │
│  │                                   │
│  └── Sub-Agent N (子主题N)           │
│      └── ...                         │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Phase 3: Synthesize（综合写作）      │
│  ├── Citation Agent（引用标注）       │
│  ├── Report Writer（报告生成）        │
│  │   ├── 基于Brief + 所有研究发现     │
│  │   └── 统一写作（非并行）           │
│  └── Quality Check（质量检查）        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Phase 4: Deliver（交付）             │
│  ├── 存入 shared/results/            │
│  ├── 写入 .task-completions.jsonl    │
│  └── 通知主Agent                     │
└─────────────────────────────────────┘
```

### 6.2 Phase 1: Scope - 研究Brief生成

#### 6.2.1 用户澄清机制

当任务描述不够具体时，research-lead应主动生成澄清问题：

**澄清触发条件**：
- 研究主题过于宽泛（如"研究AI行业"）
- 缺少明确的研究目标（投资决策？技术评估？竞品分析？）
- 缺少输出格式要求
- 缺少深度/广度偏好

**澄清问题模板**：
1. "这项研究的主要目标是什么？（如：投资决策/技术选型/竞品分析/学术调研）"
2. "期望的研究深度如何？（概览级/分析级/深度报告级）"
3. "有无特定的关注维度或排除范围？"
4. "期望的输出格式？（Markdown报告/对比表格/数据可视化）"

#### 6.2.2 研究Brief模板

```markdown
# 研究Brief

## 研究目标
[一句话描述研究的核心目标]

## 研究范围
- 包含：[列出需要覆盖的领域]
- 排除：[列出不需要覆盖的领域]

## 子主题分解
1. [子主题A] - 关键问题：...
2. [子主题B] - 关键问题：...
3. [子主题C] - 关键问题：...

## 研究策略
[广度优先 / 深度优先 / 对比分析 / 验证型]

## 输出要求
- 格式：[Markdown报告 / 对比表格 / ...]
- 深度：[概览 / 分析 / 深度]
- 引用：[需要/不需要]

## 成功标准
[如何判断研究已完成且质量达标]
```

### 6.3 Phase 2: Research - Supervisor-SubAgent编排

#### 6.3.1 Research Supervisor核心逻辑

```
function research_supervisor(brief):
    findings = []
    max_iterations = 3  // 防止无限循环
    
    for iteration in range(max_iterations):
        // 1. 基于Brief和已有发现，生成本轮子任务
        sub_tasks = plan_sub_tasks(brief, findings)
        
        // 2. 并行spawn子Agent执行子任务
        sub_findings = parallel_spawn_subagents(sub_tasks)
        
        // 3. 合并发现
        findings.extend(sub_findings)
        
        // 4. 评估是否充分
        if is_research_sufficient(brief, findings):
            break
        else:
            // 5. 识别缺口，下一轮针对性补充
            gap_analysis = identify_gaps(brief, findings)
            brief = update_brief_with_gaps(brief, gap_analysis)
    
    return findings
```

**并行spawn子Agent的关键要点**：
- 使用 `sessions_spawn` 创建子Agent，每个子Agent获得独立上下文
- 每个子Agent收到：明确目标、输出格式、工具指导、任务边界
- 子Agent完成后自动announce结果给Supervisor
- Supervisor等待所有子Agent完成后再评估

#### 6.3.2 Sub-Agent工作规范

**输入接收**：
- 明确的子主题和关键问题
- 研究Brief相关部分
- 输出格式要求
- 工具和来源指导

**研究执行**：
1. 基于子主题生成3-5个具体搜索查询
2. 执行Web搜索（web_fetch/web_search）
3. 对关键页面进行深度抓取
4. 必要时使用浏览器自动化处理动态页面
5. 使用interleaved thinking评估每步结果

**结果压缩**：
- 做一次最终LLM调用，将原始研究发现压缩为清洁摘要
- 剔除无关信息、失败搜索、重复内容
- 每条发现格式：`[发现内容] (来源: URL, 访问日期)`
- 返回结构化Markdown，非原始网页文本

**质量要求**：
- 至少引用3个独立来源
- 标注信息的时效性
- 区分事实与观点
- 标注信息不确定性

#### 6.3.3 迭代研究策略

| 策略类型 | 适用场景 | 执行方式 |
|---------|---------|--------|
| **广度优先** | 需要覆盖多维度的问题 | 一次性创建多个子Agent，各负责一个维度 |
| **深度优先** | 需要深入特定领域的问题 | 逐轮深入，每轮基于前轮发现细化查询 |
| **对比分析** | 需要比较多方的问题 | 每方一个子Agent + 一个综合比较Agent |
| **验证型** | 需要验证某说法是否属实 | 多个子Agent从不同角度独立验证 |

### 6.4 Phase 3: Synthesize - 综合写作与引用

#### 6.4.1 Citation Agent

**工作流程**：
1. 接收所有子Agent的压缩发现
2. 为每条声明匹配来源
3. 生成内联引用标记 `[1]`, `[2]`...
4. 构建参考文献列表
5. 检查引用完整性（每条关键声明是否有来源）

**引用格式规范**：
```
内联引用：
> 根据Gartner预测，2026年AI Agent市场规模将达到500亿美元 [1]。

参考文献：
[1] Gartner, "AI Agent Market Forecast 2026", https://..., 2026-01
```

#### 6.4.2 Report Writer规范

**核心原则**：
- **统一写作**：一个Agent完成全文写作，确保连贯性（LangChain教训）
- **Brief对齐**：报告必须回应Brief中的每个子主题
- **证据驱动**：每个结论都有研究发现支撑

**报告结构模板**：
1. 执行摘要（300字以内）
2. 研究背景与范围
3. 核心发现（按子主题组织，每个发现含：结论+证据+来源引用）
4. 分析与洞察
5. 结论与建议
6. 参考文献
7. 附录（数据表、原始数据等）

**质量自检清单**：
- [ ] 每个子主题是否都有覆盖？
- [ ] 每个关键结论是否都有来源引用？
- [ ] 引用来源是否可靠（一手 > 二手）？
- [ ] 是否区分了事实和观点？
- [ ] 是否标注了信息时效性？
- [ ] 报告逻辑是否连贯？

#### 6.4.3 质量评估机制

借鉴Deep Research Bench RACE评估体系：

| 维度 | 权重 | 评分标准 |
|------|------|--------|
| **覆盖度** | 25% | Brief中所有子主题是否充分覆盖 |
| **准确性** | 25% | 事实陈述是否正确，引用是否可靠 |
| **深度** | 20% | 是否超越了表面信息，提供深层洞察 |
| **结构** | 15% | 报告组织是否清晰，逻辑是否连贯 |
| **引用** | 15% | 引用是否完整、格式是否规范 |

评估方式：自评（Report Writer完成后自评打分）+ 互评（spawn独立评估Agent）。总分<70分需返工。

### 6.5 Memory与上下文管理

#### 6.5.1 Memory持久化策略（借鉴Anthropic）

**需要持久化的内容**：
1. 研究Brief - 贯穿整个研究过程的指南
2. 研究计划 - Supervisor的分解策略
3. 已完成子任务 - 避免重复研究
4. 关键发现摘要 - 防止上下文截断丢失
5. 待研究缺口 - 下一轮需补充的内容

**持久化方式**：写入临时文件 `shared/results/.tmp/{task-id}/memory.md`，每轮研究后更新。

#### 6.5.2 上下文压缩规范

子Agent返回格式（压缩后）：
```markdown
### 子主题：[名称]

#### 关键发现
1. **[发现标题]**：[1-2句摘要] (来源: [URL], [日期])
2. **[发现标题]**：[1-2句摘要] (来源: [URL], [日期])

#### 数据点
- [关键数据1]: [数值] (来源: [URL])

#### 不确定性
- [标注信息缺口和不确定之处]

#### 建议后续研究方向
- [如有进一步深挖建议]
```

**压缩原则**：返回结论和证据不返回原始网页文本；每条发现不超过3句话；总返回长度控制在2000 token以内；保留所有来源URL。

### 6.6 工具生态集成

| 层级 | 工具 | 用途 | 优先级 |
|------|------|------|--------|
| 搜索 | web_search | 关键词搜索 | P0（需启用） |
| 搜索 | web_fetch | 网页内容抓取 | P0 |
| 搜索 | browser-automation | 动态页面/登录页 | P1 |
| 搜索 | Tavily API | 专业搜索API | P2 |
| 分析 | Python代码执行 | 数据处理、图表生成 | P1 |
| 分析 | financial_rigor.py | 金融计算 | P1 |
| 分析 | MCP服务器 | 特定领域数据源 | P2 |
| 协作 | sessions_spawn | 创建并行子Agent | P0 |
| 协作 | TaskFlow | 多步任务协调 | P1 |
| 协作 | tmux | 长时间任务管理 | P2 |

### 6.7 配置化研究策略

```yaml
# 研究策略配置模板
research_strategy:
  # 策略类型：breadth | depth | comparison | validation
  type: breadth
  
  # 并行度
  max_parallel_subagents: 5
  
  # 迭代次数
  max_iterations: 3
  
  # 模型配置（可分层）
  models:
    supervisor: "default_model"
    subagent: "default_model"
    compression: "lighter_model"
    writer: "default_model"
  
  # 搜索配置
  search:
    max_sources_per_subagent: 10
    trusted_domains: []  # 可限制搜索域
    language: "zh-CN"
  
  # 输出配置
  output:
    format: "markdown"
    min_length: 2000
    require_citations: true
    require_data_tables: false
```

---

## 7. 实施路线图

### 7.1 Phase 1（第1-2周）：基础架构升级

**目标**：实现研究Brief生成 + 基础并行子Agent

| 任务 | 交付物 | 依赖 |
|------|--------|------|
| 编写研究Brief生成Prompt模板 | `skills/deep-research/brief-template.md` | 无 |
| 实现Supervisor-SubAgent编排逻辑 | 更新AGENTS.md | sessions_spawn |
| 创建Sub-Agent工作规范文档 | `skills/deep-research/subagent-spec.md` | Brief模板 |
| 启用web_search工具 | 配置更新 | 无 |

### 7.2 Phase 2（第3-4周）：质量与引用体系

**目标**：实现引用追溯 + 上下文压缩 + Memory持久化

| 任务 | 交付物 | 依赖 |
|------|--------|------|
| 实现Citation Agent引用标注流程 | `skills/deep-research/citation-spec.md` | Phase 1 |
| 创建上下文压缩规范并集成到Sub-Agent | 更新subagent-spec.md | Phase 1 |
| 实现Memory持久化到临时文件 | `skills/deep-research/memory-spec.md` | Phase 1 |
| 建立质量评估自检清单 | `skills/deep-research/quality-checklist.md` | Citation Agent |
| 编写报告写作规范 | `skills/deep-research/report-template.md` | 压缩规范 |

### 7.3 Phase 3（第5-8周）：高级能力与优化

**目标**：实现可配置策略 + 工具生态完善 + 评估闭环

| 任务 | 交付物 | 依赖 |
|------|--------|------|
| 实现策略路由（广度/深度/对比/验证） | `skills/deep-research/strategy-router.md` | Phase 1+2 |
| 集成browser-automation处理动态页面 | 配置更新 | Phase 1 |
| 集成MCP服务器扩展数据源 | MCP配置 | Phase 2 |
| 引入Deep Research Bench评估 | 评估报告 | Phase 2 |
| 实现迭代研究（缺口识别+补充研究） | 更新Supervisor逻辑 | Phase 1+2 |
| 建立研究进度追踪机制 | 进度文件 | Phase 1 |

### 7.4 里程碑与验收标准

| 里程碑 | 时间 | 验收标准 |
|--------|------|--------|
| M1: Brief + 并行研究 | 第2周末 | 能生成研究Brief，并行spawn 3+子Agent |
| M2: 引用 + 质量评估 | 第4周末 | 报告含完整引用，自评分数≥70 |
| M3: 策略路由 + 评估闭环 | 第8周末 | 4种策略可配置，通过Deep Research Bench测试 |

### 7.5 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|--------|
| Token消耗过高 | 成本超预算 | 分层模型策略（压缩用轻量模型） |
| 子Agent协调失败 | 研究不连贯 | Supervisor统一评估+统一写作 |
| 搜索工具不可用 | 研究中断 | 多搜索源备份（web_search + web_fetch + Tavily） |
| 上下文截断 | 信息丢失 | Memory持久化 + 压缩规范 |
| 评估标准不统一 | 质量不可比 | 采用RACE评估体系标准化 |

---

## 8. 参考资料

### 大厂官方文档
1. OpenAI Deep Research介绍：https://openai.com/index/introducing-deep-research/
2. OpenAI Deep Research（2026年2月更新）：MCP集成、实时进度追踪
3. Anthropic多Agent研究系统：https://www.anthropic.com/engineering/multi-agent-research-system
4. Anthropic Claude Research功能：https://www.anthropic.com/news/research
5. Google Gemini 2.0系列发布：https://blog.google/technology/google-deepmind/gemini-model-updates-february-2025/
6. Perplexity Deep Research介绍

### 开源框架
7. LangChain Open Deep Research：https://github.com/langchain-ai/open_deep_research
8. LangChain Open Deep Research博客：https://blog.langchain.com/open-deep-research/
9. GPT Researcher：https://github.com/assafelovic/gpt-researcher
10. Deep Research Bench排行榜：https://huggingface.co/spaces/Ayanami0730/DeepResearch-Leaderboard
11. HuggingFace open-deep-research
12. Google gemini-fullstack-langgraph-quickstart

### 评估与论文
13. BrowseComp评估基准：https://openai.com/index/browsecomp/
14. Plan-and-Solve论文：https://arxiv.org/abs/2305.04091
15. RAG论文：https://arxiv.org/abs/2005.11401
16. Deep Research Bench评估数据集：https://smith.langchain.com/public/c5e7a6ad-fdba-478c-88e6-3a388459ce8b/d

### 相关分析
17. Cognition AI "Don't Build Multi-Agents"：https://cognition.ai/blog/dont-build-multi-agents
18. LangChain Deep Research课程：https://academy.langchain.com/courses/deep-research-with-langgraph
19. LangChain "Bitter Lesson"博客：https://rlancemartin.github.io/2025/07/30/bitter_lesson/

### 内部资源
20. OpenClaw研究团队AGENTS.md
21. ai-berkshire投资研究框架SKILL.md
22. OpenClaw GitHub仓库：https://github.com/openclaw/openclaw

---

## 附录A：Anthropic多Agent研究系统关键数据点

### Token消耗分析
- 单Agent：约4×聊天token
- 多Agent：约15×聊天token
- Token使用量解释80%的BrowseComp性能方差
- 模型升级（Sonnet 3.7 -> Sonnet 4）比翻倍token预算增益更大

### 性能对比
- 多Agent（Opus 4 lead + Sonnet 4 subagents）vs 单Agent Opus 4：+90.2%
- 三个因素解释95%性能方差：token使用量(80%) + 工具调用次数 + 模型选择

### 架构组件
- LeadResearcher：策略规划+任务分解+迭代决策
- Subagents：独立上下文+并行搜索+interleaved thinking
- Memory：计划持久化防止截断
- CitationAgent：引用标注专用Agent

## 附录B：LangChain Open Deep Research配置详情

### 模型角色分层
| 角色 | 默认模型 | 职责 |
|------|---------|------|
| Summarization | openai:gpt-4.1-mini | 摘要搜索API结果 |
| Research | openai:gpt-4.1 | 驱动搜索Agent |
| Compression | openai:gpt-4.1 | 压缩研究发现 |
| Final Report | openai:gpt-4.1 | 撰写最终报告 |

### 评估结果对比
| 配置 | RACE分数 | 成本/100题 | Token总量 |
|------|---------|----------|----------|
| GPT-5 | 0.4943 | - | 204M |
| GPT-4.1默认 | 0.4309 | $45.98 | 58M |

---

*报告完成。如需进一步细化某个章节或开始实施，请联系research-lead。*