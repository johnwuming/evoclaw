### 7.7 技术架构

- **自训练模型**：Tongyi DeepResearch-30B-A3B（总参数30B，仅激活3.3B）
- **专为信息搜索设计**：不是通用模型，而是专项优化
- **开源**：完全开源，首个开源达到 OpenAI Deep Research 水平的 Web Agent
- **SOTA 性能**：HLE、BrowseComp、BrowseComp-ZH、WebWalkerQA、SimpleQA 等基准
- **MoE 架构**：混合专家架构，高效推理

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

## 八、智谱 — GLM 深度研究 / AutoGLM

### 8.1 产品概述

智谱 AI（Zhipu AI）的深度研究能力通过其 GLM 系列模型和**AutoGLM** 产品实现。智谱以学术背景著称，其模型在中文理解和推理上有突出表现。

### 8.2 产品形态和入口

- **智谱清言（ChatGLM）**：对话产品，支持深度搜索和研究
- **AutoGLM**：自动化 Agent 产品，可自主执行网页操作
- **BigModel 开放平台**：API 接口，支持开发者构建研究 Agent
- **触发方式**：对话中自然触发或手动选择研究模式

### 8.3 交互方式

1. 用户在智谱清言中输入研究问题
2. 系统自动判断是否需要深度搜索
3. 多步骤搜索、阅读、分析
4. **AutoGLM 特色**：可自主操作网页浏览器，执行更复杂的研究任务
5. 实时展示研究进度

### 8.4 搜索和信息收集机制

- **全网搜索**：集成主流搜索引擎
- **AutoGLM 浏览器操作**：可直接访问和操作网页，获取动态内容
- **学术资源**：支持学术论文搜索
- **中文优化**：中文搜索质量高
- **多轮迭代搜索**：根据结果动态调整搜索策略

### 8.5 推理/研究流程

- **GLM 系列推理**：GLM-4/GLM-5 系列模型提供推理能力
- **Agent 架构**：AutoGLM 原生 Agent 能力
- **Tool Calling**：丰富的工具调用能力
- **自我反思**：在研究过程中评估信息充分性

### 8.6 输出格式

- **结构化报告**：分节、分段的研究报告
- **来源引用**：标注信息来源
- **多格式支持**：文字、表格、代码等
- **可视化**：支持图表生成

### 8.7 技术架构

- **底层模型**：GLM-5/GLM-5.1 系列
- **AutoGLM**：自主网页操作 Agent
- **Agent 框架**：原生 Agent 能力
- **开源部分**：部分模型开源（如 GLM-4-9B）
- **GLM-5.1**：最新一代模型，推理能力大幅提升

### 8.8 定价和可用性

| 套餐 | 深度研究能力 | 价格 |
|------|------------|------|
| 智谱清言免费版 | 基础研究能力 | 免费 |
| 智谱清言会员 | 增强配额 | 付费 |
| BigModel API | 按 token 计费 | 开发者 |
| 企业版 | 定制方案 | 企业定价 |

---

## 九、字节跳动 — 豆包深入研究

### 9.1 产品概述

字节跳动于 **2025年8月** 在豆包 App、网页版及电脑版正式上线"**深入研究**"功能。该功能类似 Agent 能力，用户可免费体验。字节跳动的 Agent 模型路线非常激进：从 Seed1.5 到 Seed1.8（2025年12月），再到豆包2.0（2026年2月），每代都在强化 Agent 能力。

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
- **豆包 2.0 Pro**：面向深度推理与长链路任务执行
- **OS Agent 能力**：支持跨应用操作（豆包手机助手）
- **自动任务拆解**：系统自主将复杂问题拆解为子任务

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

---

## 十、Mistral AI — Le Chat Deep Research

### 10.1 产品概述

Mistral AI 于 **2025年7月19日** 在其 Le Chat 平台推出 "Deep Research" 模式，直接对标 OpenAI 和 Google。以欧洲 AI 公司的隐私优先定位为差异化。

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
- **隐私优先**：欧洲数据保护标准
- **速度优势**：被用户评为"目前最快的 AI 应用"之一
- **开源模型**：部分模型开源（Mistral 7B/8x7B/Mixtral 等）

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
- **独特优势**：可访问 X 平台的实时社交媒体数据

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
| 免费用户 | 不支持 | — |
| API | 按 token 计费 | 开发者 |

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
| **功能名称** | Deep Research | Deep Research | Research模式 | Pro/Deep Search | Deep Research | 深度搜索 | Qwen DR | AutoGLM | 深入研究 | Deep Research | DeepSearch |
| **上线时间** | 2025.02 | 2024.12 | 2025渐进 | 2024渐进 | 2025.03 | 2025 | 2025 | 2025 | 2025.08 | 2025.07 | 2025.02 |
| **独立入口** | ✅ | ✅ | ❌组合 | ❌内置 | ✅ | ❌ | ✅ | ❌ | ✅ | ✅ | ❌ |
| **用户追问** | ✅ | ❌ | ✅ | ✅Pro | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| **执行时间** | 5-30min | 数-数十min | 不定 | 1-3min | 数min-h | 不定 | 数min | 不定 | 数min | 数min | 数min |
| **进度展示** | ✅ | ✅ | ✅ | ✅ | ✅ | 部分 | ✅ | ✅ | ✅ | ✅ | ❌ |
| **上传文件** | ✅ | ❌Ent✅ | ✅ | ❌ | ✅M365 | ✅ | ✅ | ✅ | ❌ | ✅Projects | ❌ |
| **企业搜索** | ❌ | ✅Ent | ❌MCP | ❌ | ✅Graph | ✅文库 | ✅百炼 | ✅ | ❌ | ❌ | ❌ |
| **引用方式** | 列表 | 行内+列表 | 行内 | [1][2] | 列表 | 标注 | 标注 | 标注 | 标注 | 引用 | 标注 |
| **中文优化** | 一般 | 一般 | 一般 | 一般 | 一般 | ⭐最佳 | ⭐优秀 | ⭐优秀 | ⭐优秀 | 一般 | 一般 |

### 12.2 技术架构对比

| 维度 | OpenAI | Google | Anthropic | Perplexity | Microsoft | 阿里 | 字节 | Mistral | xAI |
|------|--------|--------|-----------|------------|-----------|------|------|---------|-----|
| **底层模型** | o3 | Gemini 2.5 | Claude 4 | 多模型 | OpenAI | Tongyi 30B-A3B | Seed 2.0 | Mistral Large | Grok 4.1 |
| **推理模型** | ✅ | ✅ | ✅ET | ❌ | ✅ | ✅GRPO | ✅ | ❌ | ✅Heavy |
| **Agent架构** | 单Agent多线程 | 沙箱Agent | MCP+ToolUse | 搜索优先 | 双Agent编排 | 单Agent | 原生Agent | LeChat Agent | 单Agent |
| **多Agent** | ❌ | ❌ADK可选 | ✅开发者 | ❌ | ✅R+A | ❌ | ❌ | ❌ | ❌ |
| **自训练模型** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅30B-A3B | ❌ | ❌ | ❌ |
| **开源** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | 部分 | ❌ |

### 12.3 定价对比

| 厂商 | 免费可用 | 入门付费 | 深度付费 | 备注 |
|------|---------|---------|---------|------|
| OpenAI | ❌ | Plus $20/月 | Pro $200/月 | 最贵 |
| Google | ✅有限 | Advanced $20/月 | — | 免费可用 |
| Anthropic | ✅有限 | Pro $20/月 | Max $100-200/月 | 组合能力 |
| Perplexity | ✅有限 | Pro $20/月 | — | 性价比高 |
| Microsoft | ✅基础 | Copilot $20/月 | M365企业 | 企业强 |
| 百度 | ✅ | 会员 | — | 中文最佳 |
| 阿里 | ✅ | — | 百炼 | 开源免费 |
| 智谱 | ✅ | 会员 | 企业版 | — |
| 字节 | ✅ | — | — | **完全免费** |
| Mistral | ✅有限 | Pro ≈€15/月 | 企业版 | 隐私优先 |
| xAI | ❌ | SuperGrok $30/月 | — | X数据 |

---

## 十三、技术架构深度对比分析

### 13.1 三大技术路线

**路线一：推理模型驱动（Reasoning-First）**
- **代表**：OpenAI（o3）、Anthropic（Extended Thinking）、xAI（Heavy 模式）
- **特点**：以推理模型为核心，通过深度推理链来规划和执行研究
- **优势**：研究质量高，推理能力强
- **劣势**：成本高、速度慢、token 消耗大

**路线二：Agent 架构驱动（Agent-First）**
- **代表**：Google（ADK）、Microsoft（双Agent编排）、Kimi（Agent集群）
- **特点**：以 Agent 框架为核心，通过多步骤规划和工具调用完成研究
- **优势**：灵活性强，可扩展性好
- **劣势**：需要精心设计的编排逻辑

**路线三：搜索增强驱动（Search-First）**
- **代表**：Perplexity、百度
- **特点**：以搜索为核心，AI 生成为辅助
- **优势**：速度快、信息新鲜、引用精准
- **劣势**：深度推理能力有限

### 13.2 自训练 vs 通用模型

| 策略 | 代表 | 优势 | 劣势 |
|------|------|------|------|
| **自训练研究模型** | 阿里 Tongyi 30B-A3B | 工具使用能力强、成本极低（仅激活3.3B）、开源 | 需要大量算力和数据 |
| **通用推理模型** | OpenAI o3、Claude 4 | 研究质量高、通用性强 | 成本高、token消耗大 |
| **混合策略** | Google Gemini、字节豆包 | 兼顾质量和成本 | 架构复杂度更高 |

### 13.3 关键技术趋势

1. **Test-time Scaling**：通过增加推理步骤提升研究质量（阿里 IterResearch、OpenAI o3）
2. **Interactive Scaling**：训练模型处理更多工具调用（MiroThinker，300-400次调用）
3. **并行化**：Kimi Agent 集群（100 Agent）代表"用算力换质量"趋势
4. **开源追赶**：阿里 Tongyi 开源模型已达到闭源产品水平
5. **企业搜索**：Microsoft 和 Google 的企业级研究是差异化方向
6. **实时数据**：xAI 的 X 平台数据是独特信息源
7. **隐私优先**：Mistral 的欧洲数据保护是差异化

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

### 14.2 OpenClaw 核心优势

1. **独立审核机制**：双 Reviewer（准确性+完整性）消除自评偏见，所有商业产品不具备
2. **迭代收敛**：支持多轮搜索-审核-补充循环，质量可控
3. **完全可定制**：可自定义 SOP、搜索策略、输出格式
4. **知识累积**：跨研究会话的知识库积累
5. **成本透明**：每步操作有完整审计日志
6. **多模型分工**：不同阶段使用不同能力的模型

### 14.3 OpenClaw 核心劣势

1. **速度**：多阶段流程需要数小时，远慢于商业产品的 5-30 分钟
2. **易用性**：需要技术知识来配置和维护
3. **搜索质量**：依赖外部搜索 API，可能不如商业产品的自建搜索
4. **用户界面**：纯文本交互，不如商业产品的图形化进度展示

### 14.4 差异化定位

| 场景 | 推荐方案 |
|------|---------|
| 快速事实查询 | 商业产品（Perplexity、百度） |
| 日常研究 | 商业产品（OpenAI DR、Google DR） |
| 专业投资研究 | **OpenClaw**（需要独立审核和审计） |
| 企业知识研究 | **OpenClaw + MCP**（企业数据接入） |
| 学术研究 | **OpenClaw**（多轮迭代提升准确性） |
| 中文深度研究 | 商业产品（百度、豆包免费）或 OpenClaw |

---

## 十五、趋势观察与判断

### 15.1 行业趋势

1. **Deep Research 成为标配**：2025年所有主要 AI 厂商都推出了深度研究功能
2. **从独立功能到 Agent 生态**：深度研究正从独立功能融入更广泛的 Agent 生态
3. **中文市场免费化**：字节豆包、百度、智谱都提供免费深度研究，与 OpenAI $200/月形成对比
4. **开源追赶**：阿里 Tongyi 开源模型已达到闭源产品水平
5. **企业场景是下一战场**：Microsoft 和 Google 在企业搜索上的投入加大
6. **自训练研究模型**：阿里证明了"专用研究模型"路线的可行性

### 15.2 对 OpenClaw 的启示

1. **速度优化是关键**：可通过并行搜索员+减少审核轮次缩短时间
2. **开源模型可用**：阿里 Tongyi 30B-A3B 可作为低成本搜索员模型
3. **SOP 模板化**：借鉴 MiniMax 的预置研究框架 SOP 思路
4. **与商业产品互补**：OpenClaw 提供"可控、可审计、可定制"的高级研究能力
5. **Agent 集群化**：参考 Kimi 的 Agent 集群思路，提升并行能力

---

## 十六、来源列表

1. OpenAI Deep Research 官方 - https://openai.com/zh-Hans-CN/index/introducing-deep-research/
2. OpenAI 帮助文档 - https://help.openai.com/zh-hans-cn/articles/10500283-deep-research-in-chatgpt
3. ChatGPT Pro 限制 - https://pinzhanghao.com/tech-tutorials/chatgpt-pro-limits-guide-2025/
4. ChatGPT Agent 架构 - https://cloud.tencent.com/developer/article/2544041
5. DeepResearch 技术分析 - https://zhuanlan.zhihu.com/p/1932033019683771036
6. Deep Research 技术综述 - https://modelscope.cn/learn/2107
7. Gemini Deep Research - https://gemini.google/overview/deep-research/
8. Gemini Enterprise - https://docs.cloud.google.com/gemini/enterprise/docs/research-assistant
9. Google ADK - https://cloud.google.com/blog/products/ai-machine-learning/build-a-deep-research-agent-with-google-adk
10. Gemini Agent 架构 - https://sparkco.ai/blog/in-depth-analysis-of-google-gemini-agents-architecture
11. Anthropic Web Search - https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool
12. Anthropic 多Agent系统 - https://www.anthropic.com/engineering/built-multi-agent-research-system
13. Claude Research 指南 - https://support.claude.com/en/articles/11095361
14. Anthropic Tool Use - https://www.anthropic.com/engineering/advanced-tool-use
15. Long-running Claude - https://www.anthropic.com/research/long-running-Claude
16. Copilot Deep Research - https://www.microsoft.com/en-us/microsoft-copilot/for-individuals/do-more-with-ai/general-ai/copilot-deep-research-expands-learning
17. M365 Copilot Researcher - https://www.microsoft.com/en-us/microsoft-365/blog/2025/03/25/introducing-researcher-and-analyst-in-microsoft-365-copilot/
18. Copilot Search Bing - https://blogs.bing.com/search/April-2025/Introducing-Copilot-Search-in-Bing
19. Qwen DeepResearch - https://www.alibabacloud.com/blog/qwen-deepresearch-when-inspiration-becomes-its-own-reason_602676
20. Alibaba DeepResearch GitHub - https://github.com/Alibaba-NLP/DeepResearch
21. Tongyi HuggingFace - https://huggingface.co/Alibaba-NLP/Tongyi-DeepResearch-30B-A3B
22. VentureBeat Alibaba - https://venturebeat.com/ai/the-deepseek-moment-for-ai-agents-is-here-meet-alibabas-open-source-tongyi
23. 豆包深入研究（财联社）- https://www.cls.cn/detail/2071329
24. Seed1.8 - https://seed.bytedance.com/zh/blog/official-release-of-seed1-8-a-generalized-agentic-model
25. 豆包2.0（亿欧）- https://www.iyiou.com/news/202602141122275
26. Mistral 公告 - https://mistral.ai/news/le-chat-dives-deep
27. VentureBeat Mistral - https://venturebeat.com/ai/mistrals-le-chat-adds-deep-research-agent-and-voice-mode-to-challenge-openais-enterprise-dominance
28. Mistral 帮助 - https://help.mistral.ai/en/articles/365990-what-is-deep-research-and-how-do-i-use-it-in-le-chat
29. xAI DeepSearch - https://www.businessinsider.com/xai-deepsearch-google-gemini-openai-2025-2
30. Grok 发布 - https://x.ai/news/grok
31. TechCrunch Grok3 - https://techcrunch.com/2025/02/17/elon-musks-ai-company-xai-releases-its-latest-flagship-ai-grok-3/
32. Deep Research 对比 - https://www.woshipm.com/ai/6201672.html
33. R-004 深度研究Agent全景 - 内部文档
34. R-056 Kimi与MiniMax调研 - 内部文档

---

## 十七、知识缺口

- 百度深度搜索的具体技术架构和搜索次数缺乏公开详细数据
- 智谱 AutoGLM 的深度研究具体执行流程缺乏官方文档
- Microsoft Copilot Deep Research 的具体搜索次数和时间缺乏公开数据
- Anthropic Research 模式的配额和限制缺乏公开信息
- xAI DeepSearch 的技术架构缺乏公开详细文档
- 各产品实际用户满意度对比缺乏系统性数据
- 各产品的实际成本结构（单次研究 token 消耗）均未公开
