# 业界顶级 AI Agent 项目 Prompt 设计最佳实践对比报告

> 基于 GPT-Researcher、LangChain Open Deep Research (ODR)、Anthropic Building Effective Agents 的实际源码和官方指南分析

---

## 一、项目架构概览

| 项目 | 架构模式 | Agent 数量 | 核心特点 |
|------|----------|-----------|----------|
| **GPT-Researcher** | 线性 Pipeline（搜索→策展→报告） | 单 LLM 多轮调用 | Prompt Family 类，按 ReportType 分派不同 prompt |
| **LangChain ODR** | Supervisor-Workers（Lead Researcher → 多个 Sub-Researchers） | 1 Supervisor + N Researchers | LangGraph 状态机，think_tool 强制反思 |
| **Anthropic 指南** | 理论框架（5 种 workflow + Agent 模式） | N/A | 强调简单优先，渐进增加复杂度 |

---

## 二、搜索 Agent Prompt 设计对比

### GPT-Researcher: `generate_search_queries_prompt`

```python
# 核心结构
f"""Write {max_iterations} google search queries to search online that form an objective opinion from the following task: "{task}"

Assume the current date is {datetime.now(timezone.utc).strftime('%B %d, %Y')} if required.

{context_prompt}  # 可选：包含实时上下文
You must respond with a list of strings in the following format: [{dynamic_example}].
The response should contain ONLY the list.
"""
```

**设计要点：**
- **角色极简**：没有"You are a seasoned research assistant"的前缀（只在 context_prompt 中出现）
- **强制日期注入**：`Assume the current date is ...`
- **输出格式锁定**：用动态示例 `["query 1", "query 2", "query 3"]` 约束输出为纯列表
- **"ONLY" 铁律**：`The response should contain ONLY the list` 防止多余解释
- **父查询拼接**：子话题报告用 `parent_query - question` 构建完整上下文

### LangChain ODR: `research_system_prompt`

```python
# 核心：researcher sub-agent 的 system prompt
"""You are a research assistant conducting research on the user's input topic. For context, today's date is {date}.

<Available Tools>
1. **tavily_search**: For conducting web searches
2. **think_tool**: For reflection and strategic planning
**CRITICAL: Use think_tool after each search to reflect on results.**
</Available Tools>

<Hard Limits>
- Simple queries: 2-3 search tool calls maximum
- Complex queries: up to 5 search tool calls maximum
- Stop when: can answer comprehensively / have 3+ sources / last 2 searches returned similar info
</Hard Limits>

<Show Your Thinking>
After each search, use think_tool to analyze:
- What key information did I find?
- What's missing?
- Should I search more or provide my answer?
</Show Your Thinking>"""
```

**设计要点：**
- **XML 标签分区**：`<Task>` / `<Available Tools>` / `<Hard Limits>` / `<Show Your Thinking>` 清晰隔离
- **Budget 硬限制**：明确数字限制（2-3 / 5 次），防止无限搜索
- **think_tool 强制反思**：每次搜索后必须调用 think_tool，形成 "搜索→反思→决策" 循环
- **三重停止条件**：信息足够 / 3+ 来源 / 信息重复

### 可借鉴技巧总结

| 技巧 | 来源 | 效果 |
|------|------|------|
| 动态示例约束输出格式 | GPT-Researcher | `["q1", "q2", "q3"]` 比描述"请返回列表"可靠 10 倍 |
| XML 标签结构化 prompt | LangChain ODR | LLM 对 `<tag>` 内容理解更精确，解析也更方便 |
| 硬性数字限制 + 停止条件 | LangChain ODR | 防止 agent 陷入无限循环 |
| "ONLY" + 格式示例双重约束 | GPT-Researcher | 几乎消除格式偏离 |
| 日期动态注入 | 两者都有 | 搜索时自动考虑时效性 |

---

## 三、Review/Curate Agent Prompt 设计

### GPT-Researcher: `curate_sources` — 质量把关

```python
"""Your goal is to evaluate and curate the provided scraped content for the research task: "{query}"
while prioritizing the inclusion of relevant and high-quality information, especially sources containing statistics, numbers, or concrete data.

EVALUATION GUIDELINES:
1. Assess each source based on:
   - Relevance: Err on the side of inclusion.
   - Credibility: Favor authoritative sources
   - Currency: Prefer recent information
   - Objectivity: Retain biased sources if they provide unique perspective
   - Quantitative Value: Higher priority for statistics/numbers
2. Source Selection: Include as many as possible up to {max_results}
3. Content Retention: DO NOT rewrite, summarize, or condense any source content.

You MUST return your response in the EXACT sources JSON list format as the original sources.
The response MUST not contain any markdown format or additional text (like ```json), just the JSON list!
"""
```

**设计要点：**
- **5 维评估框架**：Relevance / Credibility / Currency / Objectivity / Quantitative Value
- **"Err on the side of inclusion"**：宁多勿少，保留边际相关内容
- **原样保留指令**：`DO NOT rewrite, summarize, or condense` — 防止信息损失
- **格式铁律**：`EXACT ... JSON list format` + `MUST not contain markdown` — 双重约束

### LangChain ODR: `compress_research_system_prompt` — 压缩整理

```python
"""Your job is to clean up the findings, but preserve all of the relevant statements and information.

<Guidelines>
1. Repeat key information VERBATIM
2. Report can be as long as necessary
3. Return inline citations for each source
4. Include "Sources" section at end
5. Include ALL sources gathered
</Guidelines>

<Output Format>
**List of Queries and Tool Calls Made**
**Fully Comprehensive Findings**
**List of All Relevant Sources (with citations)**
</Output Format>

Critical Reminder: preserve information verbatim (don't rewrite, don't summarize, don't paraphrase)
"""
```

**设计要点：**
- **三段式输出结构**：查询记录 → 完整发现 → 来源列表
- **VERBATIM 强调**：连续三次说"不要改写"，确保信息不损失
- **引用编号规则**：`Number sources sequentially without gaps (1,2,3,4...)` — 具体到编号不能有空隙

---

## 四、保证 Sub-agent 输出格式稳定的核心策略

### 策略 1: 结构化输出 + Pydantic 模型（LangChain ODR 首选）

```python
# deep_researcher.py 中的实际用法
clarification_model = (
    configurable_model
    .with_structured_output(ClarifyWithUser)  # Pydantic class
    .with_retry(stop_after_attempt=configurable.max_structured_output_retries)
)
```

**对应 Prompt 中的 JSON schema 描述：**
```
Respond in valid JSON format with these exact keys:
"need_clarification": boolean,
"question": "<question>",
"verification": "<verification message>"
```

### 策略 2: Prompt Family 类 + 枚举分派（GPT-Researcher）

```python
class PromptFamily:
    """General purpose class for prompt formatting.
    Methods broken into two groups:
    1. Prompt Generators: correlated with ReportType enum
    2. Prompt Methods: situation-specific, accessed directly
    """
    # 可被不同模型的子类覆盖
```

### 策略 3: 格式约束三板斧

| 层级 | 具体做法 | 示例 |
|------|---------|------|
| **描述层** | 明确格式要求 | `Respond in JSON format with these exact keys` |
| **示例层** | 给出完整示例 | `{"need_clarification": false, "question": "", ...}` |
| **禁止层** | 明确禁止什么 | `MUST not contain markdown format or additional text` |

### 策略 4: think_tool 强制中间反思（LangChain ODR 独有）

```python
def think_tool(state, config):
    """A tool for the agent to reflect and plan."""
    # 不是真的执行任何外部操作，只是让 LLM 反思
```

**作用：** 每次搜索后强制调用 think_tool，让 agent 检查自己是否偏航。这相当于在 prompt 层面插入了一个 "checkpoint"。

---

## 五、任务分解 Prompt 的具体写法

### LangChain ODR: `lead_researcher_prompt`（Supervisor 视角）

```python
"""You are a research supervisor.

<Instructions>
1. Read the question carefully
2. Decide how to delegate - Are there multiple independent directions?
3. After each ConductResearch, pause and assess
</Instructions>

<Scaling Rules>
**Simple fact-finding** → single sub-agent
  *Example: Top 10 coffee shops → Use 1 sub-agent*

**Comparisons** → sub-agent for each element
  *Example: OpenAI vs Anthropic vs DeepMind → Use 3 sub-agents*

**Important Reminders:**
- Each ConductResearch spawns a dedicated agent
- Sub-agents can't see other agents' work
- Provide COMPLETE STANDALONE instructions
- Do NOT use acronyms or abbreviations
</Scaling Rules>"""
```

**核心设计原则：**
1. **具体示例驱动**：不是抽象说"并行"，而是给出 "coffee shops → 1 agent" "AI safety → 3 agents" 的具体映射
2. **独立性强调**：`sub-agents can't see other agents' work` — 防止 supervisor 偷懒省略上下文
3. **Standalone 指令**：每个子任务必须包含完整信息，不依赖其他 agent 的输出

### GPT-Researcher: 子话题报告的任务分解

```python
if report_type == ReportType.DetailedReport or report_type == ReportType.SubtopicReport:
    task = f"{parent_query} - {question}"
```

通过 `parent_query + sub_question` 的简单拼接，让每个子 agent 都知道自己在大任务中的位置。

### Anthropic 指南: Orchestrator-Workers 模式

> "A central LLM dynamically breaks down tasks, delegates them to worker LLMs, and synthesizes their results."
> 
> **适用场景：** 复杂任务中子任务不可预测（如代码修改涉及多个文件）
> **与 Parallelization 的区别：** 子任务不是预定义的，而是由 orchestrator 动态决定

---

## 六、报告生成 Prompt 设计

### GPT-Researcher: `generate_report_prompt`

```python
"""Information: "{context}"
---
Using the above information, answer the following query: "{question}" in a detailed report --

- You MUST determine your own concrete and valid opinion. Do NOT defer to general conclusions.
- You MUST write with markdown syntax and {report_format} format.
- Use in-text citations in {report_format} format with markdown hyperlinks
- {reference_prompt}
- Please do your best, this is very important to my career.  # ← 心理操纵技巧
"""
```

**技巧：** `"this is very important to my career"` — 经典的情感激励 prompt 技巧，实际有效

### LangChain ODR: `final_report_generation_prompt`

```python
"""CRITICAL: Make sure the answer is written in the same language as the human messages!
If user's messages are in Chinese, then MAKE SURE you write in Chinese.

Structure examples for different question types:
- Compare two things → intro / overview A / overview B / comparison / conclusion
- List of things → single section with list, OR separate sections per item
- Summarize topic → overview / concept 1 / concept 2 / conclusion

Do NOT refer to yourself as the writer. No self-referential language.
"""
```

**技巧：**
- **语言检测提醒**：`same language as human messages` — 多语言场景必需
- **结构模板**：不是给一个死板结构，而是给出多种结构示例，让 LLM 选择最合适的
- **反自我引用**：`Do NOT refer to yourself` — 消除 "I think" / "In my analysis" 等噪音

---

## 七、Webpage 摘要 Prompt（LangChain ODR 独有）

```python
summarize_webpage_prompt:
- 目标长度：原文 25-30%
- 必须包含：key facts, statistics, data points, quotes from credible sources
- 必须保持：chronological order, lists, step-by-step instructions
- 输出格式：JSON {"summary": "...", "key_excerpts": "..."}
- 按内容类型区分处理方式：新闻 → 5W1H，科学 → 方法/结果/结论，产品 → 特性/参数
- 给出 2 个完整示例（新闻 + 科学）
```

**亮点：** 这是整个 ODR pipeline 中最精细的 prompt，体现了 "摘要也需要分类讨论" 的设计思想。

---

## 八、综合最佳实践清单

### Prompt 结构
1. ✅ 用 XML 标签（`<Task>` `<Instructions>` `<Hard Limits>`）分区，而非纯文本段落
2. ✅ 角色描述极简化 — "You are a research assistant" 一句话足够
3. ✅ 每条指令独立成行，用 `-` 或数字列表，不用长段落

### 输出格式控制
4. ✅ 描述 + 示例 + 禁止 三层约束（缺一不可）
5. ✅ 用 Pydantic / structured output 做强约束（优于纯 prompt）
6. ✅ `Return ONLY the JSON, no additional text` — 永远加上这句
7. ✅ 编号规则要精确到 "without gaps (1,2,3,4...)"

### 任务分解
8. ✅ 给具体示例而非抽象规则（"coffee shops → 1 agent" 比 "simple tasks use 1 agent" 有效）
9. ✅ 强调子 agent 之间的独立性（`can't see other agents' work`）
10. ✅ 子任务指令必须 standalone，不依赖上下文

### 搜索策略
11. ✅ 先宽后窄：broad queries first → narrower as you gather information
12. ✅ 硬性 Budget 限制 + 明确停止条件
13. ✅ 强制中间反思（think_tool 模式）防止偏航

### 质量保证
14. ✅ Review/Curate prompt 中强调 `VERBATIM` / `DO NOT rewrite` 防信息损失
15. ✅ 多维评估框架（5+ 维度）而非单一 "relevant or not"
16. ✅ 动态日期注入确保时效性

### 报告生成
17. ✅ 提供多种结构模板让 LLM 选择，而非固定一种
18. ✅ 语言一致性提醒（多语言场景）
19. ✅ 禁止自我引用语言
20. ✅ 情感激励技巧可适当使用

---

## 九、Anthropic 核心设计原则（补充）

来自 *Building Effective Agents* 文章的三个核心原则：

1. **Maintain simplicity** — 能用简单 prompt 解决就不要用 agent
2. **Prioritize transparency** — 显式展示 agent 的规划步骤
3. **Carefully craft ACI** (Agent-Computer Interface) — 工具文档要清晰、可测试

**五种 Workflow 模式（由简到繁）：**
- Prompt Chaining → Routing → Parallelization → Orchestrator-Workers → Evaluator-Optimizer

**关键洞察：** "The most successful implementations weren't using complex frameworks. Instead, they were building with simple, composable patterns."

---

*报告生成时间：2026-03-28 | 数据来源：GPT-Researcher master 分支 prompts.py, LangChain open_deep_research main 分支 prompts.py + deep_researcher.py, Anthropic engineering blog*
