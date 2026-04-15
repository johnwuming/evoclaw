### 7.7 技术架构

- **自训练模型**：Tongyi DeepResearch-30B-A3B（总参数30B，仅激活3.3B）
- **专为信息搜索设计**：不是通用模型，而是专项优化
- **开源**：完全开源，首个开源达到 OpenAI Deep Research 水平的 Web Agent
- **SOTA 性能**：HLE、BrowseComp、BrowseComp-ZH、WebWalkerQA、SimpleQA 等基准
- **MoE 架构**：混合专家架构，高效推理
- **注**：百度千帆 Deep Research 已登顶 DeepResearch Bench 榜首（来源：中国搜索员数据）

### 7.8 定价和可用性

| 套餐 | 深度研究能力 | 价格 |
|------|------------|------|
| Qwen 助手免费版 | 基础 Deep Research | 免费 |
| Qwen 助手付费版 | 增强配额 | 付费 |
| 开源部署 | Tongyi DeepResearch-30B-A3B | 免费（需自行部署） |
| 阿里云百炼 | 企业级 API | 企业定价 |

### 7.9 来源

1. Qwen DeepResearch 官方介绍 - https://www.alibabacloud.com/blog/qwen-deepresearch-when-inspiration-becomes-its-own-reason_602676
2. GitHub 开源项目 - https://github.com/Alibaba-NLP/DeepResearch
3. HuggingFace 模型 - https://huggingface.co/Alibaba-NLP/Tongyi-DeepResearch-30B-A3B
4. VentureBeat 报道 - https://venturebeat.com/ai/the-deepseek-moment-for-ai-agents-is-here-meet-alibabas-open-source-tongyi
5. Qwen Deep Research 升级 - https://wisdomplexus.com/blogs/alibabas-qwen-deep-research-can-build-webpages-are-chatgpt-and-gemini-in-trouble/

---

## 八、智谱 — AutoGLM 沉思（GLM-Z1-Rumination）

### 8.1 产品概述

智谱 AI（Zhipu AI）于 **2025年3月31日** 上线"AutoGLM 沉思"功能，是国内首个上线的 Deep Research 产品，且**完全免费、不限量**。智谱的独特定位是"边想边干"——将 Deep Research（研究）和 Operator（实际操作）融为一体，基于 GLM-Z1-Rumination 推理模型。

### 8.2 产品形态和入口

- **智谱清言（ChatGLM）**：对话产品中直接使用
- **AutoGLM 沉思**：专门的深度研究模式，与日常对话区分
- **BigModel 开放平台**：API 接口，支持开发者构建研究 Agent
- **免费不限量**：上线即对所有用户免费开放，无次数限制

### 8.3 交互方式

1. 用户在智谱清言中输入研究问题
2. 系统自动判断是否需要深度搜索
3. 多步骤搜索、阅读、分析
4. **AutoGLM 特色**：可自主操作网页浏览器，执行更复杂的研究任务
5. **"边想边干"**：不同于纯研究模式，智谱可以在研究后直接执行操作
6. 实时展示研究进度

### 8.4 搜索和信息收集机制

- **全网搜索**：集成主流搜索引擎
- **AutoGLM 浏览器操作**：可直接访问和操作网页，获取动态内容
- **学术资源**：支持学术论文搜索
- **中文优化**：中文搜索质量高
- **多轮迭代搜索**：根据结果动态调整搜索策略

### 8.5 推理/研究流程

- **GLM-Z1-Rumination**：专为研究场景设计的推理模型，类似 o1/o3 的思考链
- **AutoGLM 原生 Agent**：深度研究 + 操作执行一体化
- **Tool Calling**：丰富的工具调用能力
- **自我反思**：在研究过程中评估信息充分性

### 8.6 输出格式

- **结构化报告**：分节、分段的研究报告
- **来源引用**：标注信息来源
- **多格式支持**：文字、表格、代码等
- **可视化**：支持图表生成

### 8.7 技术架构

- **底层模型**：GLM-Z1-Rumination（推理模型）、GLM-5.1（最新通用模型）
- **AutoGLM**：自主网页操作 Agent
- **Agent 框架**：原生 Agent 能力，Research + Operator 融合
- **开源部分**：部分模型开源（如 GLM-4-9B）
- **关键差异化**：国内首个 Deep Research（2025.3），免费不限量

### 8.8 定价和可用性

| 套餐 | 深度研究能力 | 价格 |
|------|------------|------|
| 智谱清言免费版 | 完整研究能力 | **免费（不限量）** |
| BigModel API | 按 token 计费 | 开发者 |
| 企业版 | 定制方案 | 企业定价 |

### 8.9 来源

1. 中国搜索员数据（searcher-chinese）- 内部数据
2. 智谱清言官网 - https://chatglm.cn/
3. BigModel 开放平台 - https://open.bigmodel.cn/

---

## 九、字节跳动 — 豆包深入研究

### 9.1 产品概述

字节跳动于 **2025年7-8月** 在豆包 App、网页版及电脑版正式上线"**深入研究**"功能。该功能类似 Agent 能力，用户可免费体验。字节跳动的 Agent 模型路线非常激进：从 Seed1.5 到 Seed1.8（2025年12月），再到豆包2.0（2026年2月），每代都在强化 Agent 能力。

### 9.2 产品形态和入口

- **入口方式**：豆包 App、网页版、电脑版中的**独立"深入研究"功能**
- **触发方式**：手动选择"深入研究"模式
- **免费体验**：上线即对所有用户免费开放
- **Agent 模型**：基于 Seed 系列通用 Agent 模型

### 9.3 交互方式

1. 用户选择"深入研究"模式
2. 输入研究指令（可以是详细指令或一句话描述）
3. 系统自动拆解问题、规划搜索策略
4. **多步骤执行**：自动查阅数百篇文献/网页
5. **进度展示**：实时显示研究进展
6. 最终生成专业研报

### 9.4 搜索和信息收集机制

- **全网搜索**：集成搜索引擎进行广泛搜索
- **文献/网页深度挖掘**：可自动查阅数百篇文献
- **多源信息整合**：网页、新闻、学术资源等
- **抖音生态数据**：可访问抖音等内容平台数据（潜在优势）
- **多轮迭代**：根据初步结果动态调整搜索

### 9.5 推理/研究流程

- **Seed 通用 Agent 模型**：专为 Agent 场景设计的模型
- **豆包 2.0 Pro**：面向深度推理与长链路任务执行，对标 GPT 5.2
- **OS Agent 能力**：支持跨应用操作（豆包手机助手）
- **自动任务拆解**：系统自主将复杂问题拆解为子任务
- **"边搜边想"**：基于豆包 1.6/2.0 模型的 Agent 能力

### 9.6 输出格式

- **专业研报**：结构化的深度研究报告
- **多格式**：文字、表格、图表
- **来源引用**：标注信息来源

### 9.7 技术架构

- **底层模型**：豆包 2.0 Pro（通用 Agent 模型）/ Seed 1.8
- **Agent 架构**：原生 Agent 能力，非外挂工具链
- **多模态**：支持图文输入，多模态理解
- **工具调用**：强大的 Tool Calling 能力
- **长链路任务执行**：支持复杂的长时间运行任务
- **闭源**：模型闭源

### 9.8 定价和可用性

| 套餐 | 深度研究能力 | 价格 |
|------|------------|------|
| 豆包免费版 | 深入研究功能 | **免费** |
| 豆包会员 | 增强配额 | 付费 |
| 火山引擎 | 企业级 API | 企业定价 |

### 9.9 来源

1. 豆包深入研究功能上线（财联社）- https://www.cls.cn/detail/2071329
2. Seed1.8 通用Agent模型发布 - https://seed.bytedance.com/zh/blog/official-release-of-seed1-8-a-generalized-agentic-model
3. 豆包2.0发布（亿欧）- https://www.iyiou.com/news/202602141122275
4. 字节AI战略分析（21财经）- https://www.21jingji.com/article/20251225/herald/839a00f59dafd96c26f669f16a16539f.html
5. 2026最全AI工具白皮书 - https://zhuanlan.zhihu.com/p/1992219922361755492
6. 中国搜索员数据（searcher-chinese）- 内部数据

---

## 十、Mistral AI — Le Chat Deep Research

### 10.1 产品概述

Mistral AI 于 **2025年7月19日** 在其 Le Chat 平台推出 "Deep Research" 模式，直接对标 OpenAI 和 Google。以欧洲 AI 公司的隐私优先定位为差异化。Le Chat 被用户评为"目前最快的 AI 应用"之一。

### 10.2 产品形态和入口

- **入口方式**：Le Chat（mistral.ai）对话界面中的**独立功能模式**
- **触发方式**：手动切换到 Deep Research 模式
- **同时推出**：Deep Research + 语音模式 + Projects（知识库）功能
- **定位**：欧洲隐私优先的 AI 研究助手

### 10.3 交互方式

1. 用户切换到 Deep Research 模式
2. 输入研究问题
3. **系统先澄清需求**：主动提问以明确研究方向（类似 Perplexity Pro Search）
4. 制定搜索计划并执行多步骤搜索
5. 生成带引用的研究报告
6. 执行时间：数分钟

### 10.4 搜索和信息收集机制

- **公共网络搜索**：在公共互联网上搜索
- **多步骤执行**：规划 → 搜索 → 阅读 → 综合
- **信息验证**：交叉验证不同来源

### 10.5 推理/研究流程

- **协调研究助手**：Le Chat 变身协调研究助手，可规划、澄清、搜索、综合
- **AI Agent**：自主搜索代表用户执行研究
- **类似人类研究者**：模拟人类研究者的工作流程

### 10.6 输出格式

- **带引用的研究报告**：每项信息标注来源
- **结构化输出**：逻辑清晰的研究报告
- **Projects 支持**：可与知识库项目关联
- **多语言**：支持多语言输出

### 10.7 技术架构

- **底层模型**：Mistral Large 系列
- **Agent 架构**：Le Chat 内置 Agent 能力
- **隐私优先**：欧洲数据保护标准（GDPR）
- **速度优势**：被用户评为"目前最快的 AI 应用"之一
- **开源模型**：部分模型开源（Mistral 7B/8x7B/Mixtral 等）
- **Libraries & Projects**：支持知识库管理和项目组织

### 10.8 定价和可用性

| 套餐 | 深度研究能力 | 价格 |
|------|------------|------|
| Le Chat 免费版 | 有使用次数限制 | 免费 |
| Le Chat Pro | 更多配额 | 付费（约 €15/月） |
| 企业版 | 定制方案 | 企业定价 |
| API | 按 token 计费 | 开发者 |

### 10.9 来源

1. Mistral 官方公告 - https://mistral.ai/news/le-chat-dives-deep
2. VentureBeat 报道 - https://venturebeat.com/ai/mistrals-le-chat-adds-deep-research-agent-and-voice-mode-to-challenge-openais-enterprise-dominance
3. 帮助文档 - https://help.mistral.ai/en/articles/365990-what-is-deep-research-and-how-do-i-use-it-in-le-chat
4. GIGAZINE 报道 - https://gigazine.net/gsc_news/en/20250718-mistral-ai-le-chat-update/
5. Hacker News 讨论 - https://news.ycombinator.com/item?id=44594156

---

## 十一、xAI — Grok DeepSearch

### 11.1 产品概述

xAI（Elon Musk 旗下）于 **2025年2月** 随 Grok 3 发布推出 "DeepSearch" 功能。DeepSearch 可扫描大量信息并生成深度分析报告。Grok 模型迭代极快：Grok 2（2024年8月）→ Grok 3（2025年2月）→ Grok 4（2025年中）→ Grok 4.1 beta（2026年）。

### 11.2 产品形态和入口

- **入口方式**：X（原 Twitter）平台内置 + Grok 独立网页版
- **触发方式**：在 Grok 对话中选择 DeepSearch 功能
- **独特优势**：可访问 X 平台的实时社交媒体数据（Chain of Thought 推理）

### 11.3 交互方式

1. 用户在 Grok 中选择 DeepSearch
2. 输入研究问题
3. 系统执行深度搜索
4. **X 平台数据**：可获取社交媒体上的最新讨论和趋势
5. 生成深度分析报告
6. **实时数据分析**：支持可视化图表

### 11.4 搜索和信息收集机制

- **DeepSearch**：扫描大量网页资源
- **X 平台数据**：独家访问 X 的实时社交媒体数据（独特信息源）
- **实时分析**：支持对实时数据进行分析
- **多源整合**：网页 + 社交媒体 + 新闻
- **Chain of Thought 推理**：深度推理链处理复杂查询

### 11.5 推理/研究流程

- **Grok 推理模型**：Grok 4.1 beta 推理能力
- **Heavy 模式**：支持深度推理
- **自我反思**：在分析过程中评估信息充分性
- **多轮搜索**：根据结果动态调整搜索策略

### 11.6 输出格式

- **深度分析报告**：结构化的研究报告
- **可视化图表**：支持数据可视化
- **实时数据展示**：展示最新的社交媒体趋势
- **来源引用**：标注信息来源

### 11.7 技术架构

- **底层模型**：Grok 4.1 beta（最新）
- **Colossus 超级计算机**：10万 GPU 集群训练
- **X 平台集成**：实时社交媒体数据管道
- **闭源**：所有技术闭源
- **快速迭代**：从 Grok 3 到 Grok 4 仅 5 个月

### 11.8 定价和可用性

| 套餐 | DeepSearch 能力 | 价格 |
|------|----------------|------|
| X Premium（基础） | 有限 DeepSearch | 付费 |
| SuperGrok（$30/月） | 完整 DeepSearch + Heavy 模式 | 付费 |
| 免费版有限 | 有限使用 | 有限 |
| API | 按 token 计费（需Premium+） | 开发者 |

### 11.9 来源

1. Business Insider 报道 - https://www.businessinsider.com/xai-deepsearch-google-gemini-openai-2025-2
2. Grok 发布公告 - https://x.ai/news/grok
3. TechCrunch Grok 3 报道 - https://techcrunch.com/2025/02/17/elon-musks-ai-company-xai-releases-its-latest-flagship-ai-grok-3/
4. Grok 模型概览 - https://www.firstaimovers.com/p/grok-ai-models-supergrok-pricing-2025
5. Grok 技术分析 - https://lifearchitect.substack.com/p/whats-in-grok

---

## 十二、综合对比表格

### 12.1 功能维度对比

| 维度 | OpenAI | Google | Anthropic | Perplexity | Microsoft | 百度 | 阿里 | 智谱 | 字节 | Mistral | xAI |
|------|--------|--------|-----------|------------|-----------|------|------|------|------|---------|-----|
| **功能名称** | Deep Research | Deep Research | Research模式 | Pro/Deep Search | Deep Research | 深度搜索 | Qwen DR | AutoGLM沉思 | 深入研究 | Deep Research | DeepSearch |
| **上线时间** | 2025.02 | 2024.12 | 2025渐进 | 2024渐进 | 2025.03 | 2025.02 | 2025.05 | 2025.03 | 2025.07 | 2025.07 | 2025.02 |
| **独立入口** | ✅ | ✅ | ❌组合 | ❌内置 | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **用户追问** | ✅ | ❌ | ✅ | ✅Pro | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| **执行时间** | 5-73min | 数-数十min | 不定 | 1-3min | 数min-h | 不定 | 数min | 数min | 数min | 数min | 数min |
| **进度展示** | ✅实时 | ✅实时 | ✅过程可见 | ✅ | ✅ | 部分 | ✅ | ✅ | ✅ | ✅ | ❌ |
| **上传文件** | ✅ | ❌Ent✅ | ✅ | ❌ | ✅M365 | ✅ | ✅ | ✅ | ❌ | ✅Projects | ❌ |
| **企业搜索** | ❌ | ✅Ent | ❌MCP | ❌ | ✅Graph | ✅文库 | ✅百炼 | ✅ | ❌ | ❌ | ❌ |
| **引用方式** | 末尾列表 | 行内+列表 | 行内 | [1][2] | 列表 | 标注 | 标注 | 标注 | 标注 | 引用 | 标注 |
| **中文优化** | 一般 | 一般 | 一般 | 一般 | 一般 | ⭐最佳 | ⭐优秀 | ⭐优秀 | ⭐优秀 | 一般 | 一般 |
| **免费可用** | ✅5次/月 | ✅有限 | ✅有限 | ✅有限 | ✅基础 | ✅ | ✅ | ✅不限 | ✅ | ✅有限 | 有限 |

### 12.2 技术架构对比

| 维度 | OpenAI | Google | Anthropic | Perplexity | Microsoft | 百度 | 阿里 | 智谱 | 字节 | Mistral | xAI |
|------|--------|--------|-----------|------------|-----------|------|------|------|------|---------|-----|
| **底层模型** | o3 | Gemini 2.5 | Claude 4 | 多模型 | OpenAI | ERNIE | Tongyi30B | GLM-Z1 | Seed2.0 | Mistral Large | Grok4.1 |
| **推理模型** | ✅ | ✅ | ✅ET | ❌ | ✅ | ❌ | ✅GRPO | ✅ | ✅ | ❌ | ✅Heavy |
| **Agent架构** | 单Agent多线程 | 沙箱Agent | MCP+ToolUse | DAG图编排 | 双Agent编排 | 4阶段闭环 | 单Agent | Research+Op | 原生Agent | LeChatAgent | 单Agent |
| **多Agent** | ❌ | ❌ADK可选 | ✅开发者 | ❌ | ✅R+A | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **自训练模型** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅30B-A3B | ❌ | ❌ | ❌ | ❌ |
| **开源** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅全开源 | 部分 | ❌ | 部分 | ❌ |
| **独特信息源** | — | 150国45语言 | — | 社区Spaces | 企业Graph | 百度生态 | — | — | 抖音 | 隐私GDPR | X平台 |

### 12.3 定价对比

| 厂商 | 免费可用 | 入门付费 | 深度付费 | 备注 |
|------|---------|---------|---------|------|
| OpenAI | ✅5次/月 | Plus $20/月（25次） | Pro $100-200/月（120次） | 最贵但API已开放 |
| Google | ✅有限 | AI Pro $19.99/月 | AI Ultra（更贵） | 免费可用，Ultra有可视化 |
| Anthropic | ✅有限 | Pro $20/月 | Max $100-200/月 | 组合能力，Computer Use预览 |
| Perplexity | ✅有限 | Pro $20/月 | — | DAG架构，20-50次搜索 |
| Microsoft | ✅基础 | Copilot $20/月 | M365企业 | 企业强（Graph+Bing） |
| 百度 | ✅ | 会员 | 千帆企业 | 中文最佳，4阶段闭环 |
| 阿里 | ✅ | — | 百炼企业 | **全开源**，DeepResearch Bench榜首 |
| 智谱 | ✅不限 | — | 企业版 | 国内首发，免费不限量 |
| 字节 | ✅ | — | — | 完全免费，迭代极快 |
| Mistral | ✅有限 | Pro ≈€15/月 | 企业版 | 隐私优先，速度最快 |
| xAI | 有限 | SuperGrok $30/月 | — | X平台独占数据 |

---

## 十三、技术架构深度对比分析

### 13.1 三大技术路线

**路线一：推理模型驱动（Reasoning-First）**
- **代表**：OpenAI（o3）、Anthropic（Extended Thinking）、智谱（GLM-Z1-Rumination）、xAI（Heavy/CoT）
- **特点**：以推理模型为核心，通过深度推理链来规划和执行研究
- **优势**：研究质量高，推理能力强
- **劣势**：成本高、速度慢、token 消耗大

**路线二：Agent 架构驱动（Agent-First）**
- **代表**：Google（ADK/沙箱Agent）、Microsoft（双Agent编排）、Kimi（Agent集群）、百度（4阶段闭环）
- **特点**：以 Agent 框架为核心，通过多步骤规划和工具调用完成研究
- **优势**：灵活性强，可扩展性好
- **劣势**：需要精心设计的编排逻辑

**路线三：搜索增强驱动（Search-First）**
- **代表**：Perplexity（DAG图编排）、百度（搜索生态）
- **特点**：以搜索为核心，AI 生成为辅助
- **优势**：速度快、信息新鲜、引用精准
- **劣势**：深度推理能力有限

### 13.2 自训练 vs 通用模型

| 策略 | 代表 | 优势 | 劣势 |
|------|------|------|------|
| **自训练研究模型** | 阿里 Tongyi 30B-A3B（MoE） | 工具使用能力强、成本极低（仅激活3.3B）、全开源 | 需要大量算力和数据 |
| **通用推理模型** | OpenAI o3、Claude 4、GLM-Z1 | 研究质量高、通用性强 | 成本高、token消耗大 |
| **混合策略** | Google Gemini、字节豆包、百度千帆 | 兼顾质量和成本 | 架构复杂度更高 |

### 13.3 关键技术趋势

1. **Test-time Scaling**：通过增加推理步骤提升研究质量（阿里 IterResearch、OpenAI o3）
2. **Interactive Scaling**：训练模型处理更多工具调用（MiroThinker，300-400次调用）
3. **并行化**：Kimi Agent 集群（100 Agent）代表"用算力换质量"趋势
4. **开源追赶**：阿里 Tongyi 开源模型已达 SOTA，登顶 DeepResearch Bench
5. **Research + Operator 融合**：智谱"边想边干"、OpenAI ChatGPT Agent 合并 DR+Operator
6. **企业搜索**：Microsoft（Graph）和 Google（Gmail/Drive）的企业级研究是差异化方向
7. **实时数据**：xAI 的 X 平台数据是独特信息源
8. **隐私优先**：Mistral 的 GDPR 合规是欧洲市场差异化
9. **DAG 编排**：Perplexity 使用有向无环图编排研究工作流，20-50次定向搜索
10. **中国免费化**：百度、阿里、智谱、字节均免费提供深度研究，与 OpenAI $100-200/月 对比鲜明

---

## 十四、与 OpenClaw 多 Agent 研究团队的对比

### 14.1 能力对比矩阵

| 维度 | 商业产品（最佳） | OpenClaw 多 Agent 团队 |
|------|-----------------|---------------------|
| **研究质量** | ⭐⭐⭐⭐（单次高质量） | ⭐⭐⭐⭐⭐（多轮迭代+双Reviewer） |
| **速度** | ⭐⭐⭐⭐（5-30分钟） | ⭐⭐（数小时，多阶段） |
| **灵活性** | ⭐⭐（固定流程） | ⭐⭐⭐⭐⭐（完全可定制） |
| **可审计性** | ⭐⭐（黑盒） | ⭐⭐⭐⭐⭐（完整JSON轨迹） |
| **准确性** | ⭐⭐⭐（自评偏见） | ⭐⭐⭐⭐⭐（独立Reviewer） |
| **成本** | $20-200/月 | 取决于模型用量 |
| **持续学习** | ❌ | ✅（知识库累积） |
| **定制化** | ❌ | ✅（SOP、自定义流程） |
| **企业数据** | 部分支持 | ✅（MCP工具接入） |
| **操作执行** | 部分支持（智谱） | ✅（可扩展Agent） |

### 14.2 OpenClaw 核心优势

1. **独立审核机制**：双 Reviewer（准确性+完整性）消除自评偏见，所有商业产品不具备
2. **迭代收敛**：支持多轮搜索-审核-补充循环，质量可控
3. **完全可定制**：可自定义 SOP、搜索策略、输出格式
4. **知识累积**：跨研究会话的知识库积累
5. **成本透明**：每步操作有完整审计日志
6. **多模型分工**：不同阶段使用不同能力的模型
7. **领域专用搜索**：可配置不同领域的搜索 Agent（学术/GitHub/LinkedIn）
8. **持久化专家**：跨研究任务积累知识（参考 Deepr 的 persistent expert 模式）

### 14.3 OpenClaw 核心劣势

1. **速度**：多阶段流程需要数小时，远慢于商业产品的 5-30 分钟
2. **易用性**：需要技术知识来配置和维护
3. **搜索质量**：依赖外部搜索 API，可能不如商业产品的自建搜索
4. **用户界面**：纯文本交互，不如商业产品的图形化进度展示
5. **搜索规模**：商业产品（如 Perplexity 20-50次、OpenAI 数百个）的搜索规模更大

### 14.4 差异化定位

| 场景 | 推荐方案 |
|------|---------|
| 快速事实查询 | 商业产品（Perplexity、百度） |
| 日常研究 | 商业产品（OpenAI DR、Google DR） |
| 专业投资研究 | **OpenClaw**（需要独立审核和审计） |
| 企业知识研究 | **OpenClaw + MCP**（企业数据接入） |
| 学术研究 | **OpenClaw**（多轮迭代提升准确性） |
| 中文深度研究 | 百度千帆（Bench榜首）、智谱（免费不限量）或 OpenClaw |
| Research+Action | 智谱 AutoGLM（边想边干）或 OpenClaw Agent |
| 免费/低成本 | 字节豆包、智谱清言、阿里通义（全部免费） |

---

## 十五、趋势观察与判断

### 15.1 行业趋势

1. **Deep Research 成为标配**：2024.12（Google首发）到 2025.07（Mistral），所有主要 AI 厂商在 8 个月内全部推出
2. **中国厂商免费化**：百度、阿里、智谱、字节均免费提供，与 OpenAI $100-200/月形成鲜明对比
3. **Research + Operator 融合**：智谱"边想边干"（2025.3）→ OpenAI ChatGPT Agent（2025.7），研究能力正从纯信息收集走向可执行操作
4. **开源追赶**：阿里 Tongyi 全开源方案登顶 DeepResearch Bench，证明开源可达 SOTA
5. **DAG/图编排**：Perplexity 的 DAG 编排（20-50次定向搜索）代表更精细的研究流程控制
6. **企业场景**：Microsoft（Graph）和 Google（Gmail/Drive）的企业内部搜索是关键差异化
7. **推理模型+搜索融合**：所有主流方案都在将推理模型与搜索能力深度融合
8. **API 开放化**：OpenAI、Google 都已开放 Deep Research API，开发者可集成

### 15.2 对 OpenClaw 的启示

1. **速度优化是关键**：可通过并行搜索员+减少审核轮次缩短时间
2. **开源模型可用**：阿里 Tongyi 30B-A3B 可作为低成本搜索员模型
3. **SOP 模板化**：借鉴百度千帆的 4 阶段闭环和 MiniMax 的研究框架 SOP
4. **DAG 编排**：参考 Perplexity 的图编排思路优化多步骤研究流程
5. **Research+Action**：参考智谱的"边想边干"思路，扩展 OpenClaw Agent 的执行能力
6. **与商业产品互补**：OpenClaw 提供"可控、可审计、可定制"的高级研究能力
7. **Agent 集群化**：参考 Kimi 的 Agent 集群思路，提升并行能力

---

## 十六、来源列表

1. OpenAI Deep Research 官方 - https://openai.com/zh-Hans-CN/index/introducing-deep-research/
2. OpenAI ChatGPT Agent - https://openai.com/index/introducing-chatgpt-agent/
3. OpenAI Deep Research API - https://developers.openai.com/api/docs/guides/deep-research
4. OpenAI 定价更新（PCMag）- https://www.pcmag.com/news/chatgpt-free-users-can-now-run-deep-research-five-times-a-month
5. DeepResearch 技术分析 - https://blog.promptlayer.com/how-deep-research-works/
6. Deep Research 技术综述 - https://modelscope.cn/learn/2107
7. ByteByteGo 对比 - https://blog.bytebytego.com/p/how-openai-gemini-and-claude-use
8. Gemini Deep Research - https://gemini.google/overview/deep-research/
9. Gemini Enterprise - https://docs.cloud.google.com/gemini/enterprise/docs/research-assistant
10. Gemini API Deep Research - https://ai.google.dev/gemini-api/docs/deep-research
11. Google ADK - https://cloud.google.com/blog/products/ai-machine-learning/build-a-deep-research-agent-with-google-adk
12. Gemini 定价 - https://skywork.ai/blog/ai-agent/gemini-pricing-2025/
13. Anthropic Web Search - https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool
14. Anthropic 多Agent系统 - https://www.anthropic.com/engineering/built-multi-agent-research-system
15. Claude Extended Thinking - https://platform.claude.com/docs/en/build-with-claude/extended-thinking
16. Claude Research 指南 - https://support.claude.com/en/articles/11095361
17. Anthropic Computer Use（SiliconANGLE）- https://siliconangle.com/2026/03/23/anthropics-claude-gets-computer-use-capabilities-preview/
18. Perplexity Deep Research - https://www.perplexity.ai/hub/blog/introducing-perplexity-deep-research
19. Perplexity Pro - https://www.perplexity.ai/pro
20. Perplexity 工作原理 - https://www.perplexity.ai/help-center/en/articles/10352895-how-does-perplexity-work
21. Copilot Deep Research - https://www.microsoft.com/en-us/microsoft-copilot/for-individuals/do-more-with-ai/general-ai/copilot-deep-research-expands-learning
22. M365 Copilot Researcher（TechCrunch）- https://techcrunch.com/2025/03/25/microsoft-adds-ai-powered-deep-research-tools-to-copilot/
23. Copilot Search Bing - https://blogs.bing.com/search/April-2025/Introducing-Copilot-Search-in-Bing
24. Qwen DeepResearch - https://www.alibabacloud.com/blog/qwen-deepresearch-when-inspiration-becomes-its-own-reason_602676
25. Alibaba DeepResearch GitHub - https://github.com/Alibaba-NLP/DeepResearch
26. Tongyi HuggingFace - https://huggingface.co/Alibaba-NLP/Tongyi-DeepResearch-30B-A3B
27. 豆包深入研究（财联社）- https://www.cls.cn/detail/2071329
28. Seed1.8 - https://seed.bytedance.com/zh/blog/official-release-of-seed1-8-a-generalized-agentic-model
29. 豆包2.0（亿欧）- https://www.iyiou.com/news/202602141122275
30. Mistral 公告 - https://mistral.ai/news/le-chat-dives-deep
31. Mistral 帮助 - https://help.mistral.ai/en/articles/365990-what-is-deep-research-and-how-do-i-use-it-in-le-chat
32. xAI DeepSearch（Business Insider）- https://www.businessinsider.com/xai-deepsearch-google-gemini-openai-2025-2
33. Grok 发布 - https://x.ai/news/grok
34. Deep Research 产品对比 - https://www.woshipm.com/ai/6201672.html
35. R-004 深度研究Agent全景 - 内部文档
36. R-056 Kimi与MiniMax调研 - 内部文档
37. searcher-western 数据 - 内部数据
38. searcher-chinese 数据 - 内部数据

---

## 十七、知识缺口

- 百度千帆 Deep Research 的具体技术架构（4阶段闭环细节）缺乏公开详细文档
- 智谱 GLM-Z1-Rumination 的模型参数和训练细节未公开
- Microsoft Copilot Deep Research 的具体搜索次数和执行时间缺乏公开数据
- Anthropic Research 模式的具体配额和限制缺乏公开信息
- xAI DeepSearch 的技术架构细节缺乏公开文档
- Mistral Deep Research 的搜索次数和来源类型缺乏详细数据
- 各产品实际用户满意度对比缺乏系统性数据
- 各产品的实际成本结构（单次研究 token 消耗）均未公开
- DeepResearch Bench 排名动态变化，需持续跟踪
