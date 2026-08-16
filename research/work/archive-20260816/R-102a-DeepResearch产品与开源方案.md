# Deep Research AI：主流产品与开源方案调研

> 报告编号：R-102a | 分类：02-AI技术调研 | 日期：2026-06-22

---

## 一、主流大厂 Deep Research 产品

### 行业时间线

Deep Research 作为产品品类在 2025 年初集中爆发：
- **2024.12** — Google Gemini Deep Research 低调上线
- **2025.02.02** — OpenAI 发布 Deep Research（首个引发广泛关注的同类产品）
- **2025.02.14** — Perplexity 推出 Deep Research（6 周内跟进）
- **2025.03.07** — Perplexity 开放 Sonar Deep Research API
- **2025.05.27** — Anthropic 将 Claude Research 功能正式上线
- **2026.04.21** — Gemini Deep Research Max 上线（基于 Gemini 3.1 Pro）

### 1. OpenAI Deep Research

**架构：四阶段多 Agent 流水线**，基于 o3 推理模型。API 模型为 `o3-deep-research` 和 `o4-mini-deep-research`（2025.06.26 上线 API）。架构包含：
- **Triage Agent**：分析用户查询，判断是否需要补充信息
- **Clarifier Agent**：向用户追问缺失的关键上下文
- **Instruction Builder Agent**：将补全的输入转化为精确研究简报
- **Research Agent**（o3-deep-research）：执行网页搜索 + MCP 内部知识检索，输出研究报告

**性能数据**：Humanity's Last Exam 得分 26.6%（发布时为所有 AI agent 中最高）；引用准确率约 87%（CJR 测试）。单次研究耗时 5–30 分钟，可阅读数百个页面。2026.02 起支持 MCP server 连接和可信站点白名单。

**定价**：API 价格 o3 为 $10/1M 输入 + $40/1M 输出；o4-mini 为 $2/1M + $8/1M。ChatGPT 免费版每月 5 次轻量查询，Plus 每月 25 次，Pro（$200/月）125 次完整 + 125 次轻量。

### 2. Perplexity Deep Research（Sonar Pro）

**核心优势：速度 + 引用精度**。单次研究通常 2–4 分钟完成，引用准确率达 94.3%（CJR 引用测试，为同类最高）。相比 Google Deep Research 引用 50-100+ 来源，Perplexity 通常引用 10-30 个，深度较浅但速度领先。

**架构特点**：Sonar 架构采用"grounded retrieval first"设计——先从源文档构建答案，而非事后附加引用。Sonar-Reasoning-Pro-High 在 Perplexity Search Arena 得分 1,136，与 Gemini-2 统计学上并列第一。

**API 定价**：$2/1M 输入 + $8/1M 输出（唯一提供按量付费研究 API 的主要厂商）。免费版每天 5 次 Pro Search。

### 3. Google Gemini Deep Research

**核心优势：Google 搜索索引 + Workspace 集成**。标准研究任务触发约 80 次搜索查询，阅读 100+ 页面。2026.04 推出 Deep Research Max（基于 Gemini 3.1 Pro），面向长时间异步研究流程。

**差异化**：原生集成 Gmail、Drive、Docs，适合源材料在 Google 生态内的研究场景。引用准确率表现波动，在 Google 索引内容上表现强劲。

### 4. Claude Research（Anthropic）

**定位：深度长跑型**。研究流程可长达 5–45 分钟（使用 Sonnet 4.5 或 Opus 4.5），200K token 上下文（beta 1M），适合大型研究中减少源丢失。2025.05.27 网页搜索功能正式上线，覆盖所有 Claude 4.x 模型（含 Opus 4.7）。在 Claude.ai 应用上免费可用。

### 5. Grok DeepSearch（xAI）

唯一从 X 平台拉取实时数据的 Deep Research 工具，在突发新闻和实时事件上有独特优势。但引用准确率极低（CJR 测试约 6%，即 94% 的引用为幻觉），不适合严肃研究场景。

### 产品对比总览

| 维度 | OpenAI | Perplexity | Google Gemini | Claude | Grok |
|------|--------|------------|---------------|--------|------|
| 典型耗时 | 5-30 min | 2-4 min | 5-10 min | 5-45 min | 1-3 min |
| 引用准确率 | ~87% | ~94% | 波动 | 未公开 | ~6% |
| 来源数量 | 数十-数百 | 10-30 | 50-100+ | 数十 | 少 |
| 核心优势 | 推理深度 | 速度+引用 | 索引+Workspace | 上下文长度 | 实时数据 |
| API 可用性 | ✅ | ✅ | 有限 | ✅ | ❌ |

---

## 二、开源 Deep Research 框架

### 1. GPT Researcher（assafelovic/gpt-researcher）

**最成熟的开源 Deep Research 框架**。2023.05 由 Assaf Elovic 创建，比行业浪潮早近两年。

- **GitHub 数据**：27.8K stars，3.8K forks，241 贡献者（截至 2026.06）
- **版本**：v3.5.0（2026.05.28 发布），Apache-2.0 许可证，Python
- **架构**：Planner + Execution Agent 模式。Planner 生成研究问题，Execution Agent 并行从 20+ 来源采集信息，Publisher 聚合为带引用的报告。受 Plan-and-Solve 和 RAG 论文启发
- **功能**：支持 Web + 本地文档研究、递归 Deep Research 模式（树状探索）、MCP 集成、多格式输出（PDF/Word/Markdown）、自托管无付费层
- **成本**：免费开源，自带 LLM + 搜索 API key 即可，单次研究约 $0.10 API 消耗
- **生态**：可作为 Claude Skill 安装（`npx skills add assafelovic/gpt-researcher`）

### 2. STORM（stanford-oval/storm）

**Stanford OVAL 实验室出品的学术级知识引擎**。专注于生成 Wikipedia 风格的长篇带引用文章。

- **GitHub 数据**：约 28.4K stars，MIT 许可证，Python
- **架构（两阶段）**：
  - **预写作阶段**：互联网研究 → 收集参考 → 生成大纲
  - **写作阶段**：基于大纲和参考生成完整带引用文章
- **核心创新 — 多视角提问**：
  - **视角引导提问**：分析相关 Wikipedia 文章发现不同视角，以此控制提问方向
  - **模拟对话**：模拟 Wikipedia 编辑与领域专家的对话，基于互联网来源深入追问
- **Co-STORM**：协作增强版，支持人机协同知识构建，包含多类型 LLM Agent 和动态思维导图
- **评估结果**：FreshWiki 数据集测试显示，比基线 AI 系统组织性提升 25%，覆盖广度提升 10%
- **模型支持**：通过 litellm 支持所有主流 LLM；搜索引擎支持 You.com、Bing、Tavily、DuckDuckGo、Google 等 10+
- **局限**：仅支持主题研究（不能执行任意指令）；输出较长可能存在冗余

### 3. Local Deep Research（LDR）

**本地优先的隐私方案**。在 SimpleQA benchmark 达到约 95% 准确率（如 Qwen3.6-27B 在 RTX 3090 上运行）。

- **GitHub 数据**：约 8.5K stars
- **特点**：支持 llama.cpp、Ollama 等本地推理；10+ 搜索引擎（含 arXiv、PubMed、私有文档）；全数据本地加密存储
- **适用场景**：隐私敏感型研究、离线环境、学术文献检索

### 4. LangChain DeepAgents（langchain-ai/deepagents）

**LangChain 官方的通用 Agent 框架**，可构建自定义 Deep Research agent。

- **MIT 许可证**，基于 LangGraph 构建，支持流式输出和持久化
- **核心特性**：Planning First（先规划 TODO 再执行）、文件系统后端、子 Agent 生成（隔离上下文）、上下文管理（大输出卸载到文件）、记忆持久化
- **定位**：不是开箱即用的研究工具，而是构建研究 agent 的底层框架
- **安装**：`pip install deepagents`

### 5. 其他值得关注的项目

| 项目 | 说明 |
|------|------|
| **OpenManus** (FoundationAgents) | 通用 AI Agent 框架，含研究能力 |
| **PraisonAI** | 生产级多 Agent 框架，内置 Deep Research |
| **Antgroup Research-Venus** (AtomSearcher) | 蚂蚁集团出品的自动化研究 Agent |
| **Awesome-Deep-Research** (DavidZWZ) | ACL 2026 论文配套，汇总 Deep Research 前沿论文和代码 |

---

## 三、关键趋势

1. **多 Agent 架构成为共识**：OpenAI 四阶段流水线、GPT Researcher 的 Planner/Executor 分离、STORM 的多视角对话——所有成功方案都采用了某种形式的多 Agent 协作，而非单模型端到端
2. **引用准确率是核心战场**：Perplexity 94% vs Grok 6% 的巨大差距表明，"grounded retrieval first"（先检索后生成）比"生成后附加引用"架构有本质优势
3. **API 化加速**：OpenAI 和 Perplexity 都已开放研究 API + Webhook，支持编程式触发和异步任务
4. **MCP 协议整合**：OpenAI Deep Research 2026.02 起支持 MCP，GPT Researcher 也已集成 MCP——协议标准化正在发生
5. **开源与商业差距在缩小**：LDR 在 SimpleQA 上 95% 的表现表明，本地开源方案在事实准确性上已可竞争商业产品

---

## 四、对自建 Deep Research 系统的启示

1. **架构选择**：Planner-Executor 模式（如 GPT Researcher）是最成熟的开源范式，可复用度高
2. **成本控制**：自建方案单次研究成本约 $0.10（GPT Researcher 数据），远低于商业 API
3. **搜索引擎是关键基础设施**：Tavily（93.3% SimpleQA）、Serper 等专用搜索 API 对研究质量影响巨大
4. **参考 STORM 的多视角提问**：模拟多角色对话提问是提升研究深度的有效策略

---

## 来源

- glasp.ai — Deep Research Tools Compared (2026 Guide)
- felloai.com — AI Search and Deep Research Tools Compared 2026
- agentmarketcap.ai — Deep Research Agent Shootout 2026 (2026.04)
- freeacademy.ai — Google Deep Research vs Perplexity vs ChatGPT (2026)
- GitHub — assafelovic/gpt-researcher (27.8K stars, 2026.06)
- GitHub — stanford-oval/storm (~28.4K stars)
- GitHub — DavidZWZ/Awesome-Deep-Research (ACL 2026)
- rywalker.com — GPT Researcher Research Report (2026.06)
- cobusgreyling.medium.com — OpenAI Deep Research AI Agent Architecture
- community.openai.com — Deep research in the API (2025.06.26)
- andrew.ooo — Local Deep Research Review (2026.05)
- morphllm.com — AI Agent Frameworks 2026 Update
- reddit.com/r/LangChain — LangChain DeepAgents 发布
