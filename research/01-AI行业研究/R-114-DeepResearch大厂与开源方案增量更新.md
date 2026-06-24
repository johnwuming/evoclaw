# R-114: Deep Research 大厂与开源方案增量更新（2026年6月下旬）

> **报告日期**：2026-06-25
> **增量范围**：2026年5月下旬–6月下旬（相对于 R-057/R-102 系列的更新）
> **前置报告**：R-057（4月15日全球全景）、R-056（Kimi/MiniMax）、R-102/102b（6月22日架构与质量）、R-103（团队升级方案）

---

## 一、核心发现摘要

| 维度 | 关键变化 | 影响等级 |
|------|---------|---------|
| **OpenAI** | 6月无Deep Research专属更新；GPT-5.2退役→GPT-5.5迁移 | 🟡 平稳期 |
| **Google** | 推出 Deep Research Max（Gemini 3.1 Pro），API Preview上线 | 🔴 重大升级 |
| **Perplexity** | Deep Research整合进Computer平台，跨20+模型路由 | 🔴 架构跃迁 |
| **Anthropic** | 推出Dynamic Workflows（1000 agent并发），无独立DR产品 | 🟡 能力增强 |
| **xAI** | Grok 4.3上线Bedrock，DeepSearch/DeeperSearch成熟 | 🟢 稳步迭代 |
| **Kimi** | K2.6/K2.7发布，DeepSearchQA 92.5分领先GPT-5.4 | 🔴 模型升级 |
| **智谱GLM** | GLM-5.2开源（MIT），ZCode 3.0发布 | 🔴 重大升级 |
| **百度** | 千帆DeepResearch商业化（2.5元/次），DuMate登顶DeepResearch Bench | 🔴 产品里程碑 |
| **阿里** | 通义DeepResearch-30B开源，HLE 32.9%全球第一 | 🔴 技术突破 |
| **字节/豆包** | 6月下旬上线付费订阅（68-500元/月），月活3.36亿 | 🟡 商业化 |
| **MiniMax** | M3发布（1M上下文、原生多模态），Agent生态空白 | 🟡 模型升级 |
| **腾讯** | 混元3.0迭代中（256K→512K），元宝完全免费 | 🟢 按计划推进 |
| **开源-STORM** | 近期无重大更新（最新v1.1.0，2025年1月） | 🟡 停滞期 |
| **开源-gpt-researcher** | v3.5.0发布（5月28日），新增图生成、LangSmith集成 | 🟢 活跃迭代 |
| **开源-LangChain ODR** | 11.8K stars，支持MCP，含免费课程 | 🟢 稳步发展 |
| **开源-OpenResearcher** | TIGER-Lab发布，30B-A3B，BrowseComp-Plus 54.8%夺冠 | 🔴 新星出现 |

---

## 二、海外大厂详细更新

### 2.1 OpenAI Deep Research — 6月平稳期

**近期状态**：2026年6月未发布Deep Research专属功能更新。

- **最近重大更新**（2026年2月10日）：
  - 支持MCP连接器（可连接任何MCP或app）
  - 限制web搜索到可信站点
  - 实时进度跟踪和中断后优化
  - 视觉体验更新
  
- **GPT-5.2退役**（6月12日）：
  - GPT-5.2系列（Instant/Thinking/Pro）全部退役
  - 自动迁移到GPT-5.5（4月23日发布的前沿模型）
  - GPT-5.5 Instant健康性能已匹配前沿模型

- **API能力**（已稳定）：
  - `o3-deep-research`（高质量）和`o4-mini-deep-research`（低延迟）
  - 推理web搜索定价 $10/1K calls
  - 支持 background 模式和 webhooks 回调
  - 路线图：数据库连接器、MCP私有文档集成、多模态分析

**结论**：Deep Research功能本身进入稳定优化期，6月更新集中在Codex和企业功能。

> 来源：[OpenAI官方](https://openai.com/index/introducing-deep-research/)、[OpenAI Release Notes](https://help.openai.com/en/articles/6825453-chatgpt-release-notes)、[releases.sh](https://releases.sh/openai/releases)

### 2.2 Google Gemini Deep Research Max — 重大升级

**核心变化**：2026年4月21日推出 **Deep Research Max**，基于 Gemini 3.1 Pro 构建。

- **双版本架构**：
  - **Deep Research（快速版）**：标准深度研究
  - **Deep Research Max（深度版）**：更高深度、更长报告

- **新功能**：
  - **MCP支持**：安全连接私有数据源
  - **原生可视化**：自动生成图表和信息图
  - **可引导的研究计划**：用户可审查和调整研究大纲
  - **多模态输入**：文本/图片/PDF/音频/视频

- **API（Preview）**：
  - 模型ID：`deep-research-preview-04-2026` / `deep-research-max-preview-04-2026`
  - 输入上下文窗口：1,048,576 tokens（1M）
  - 输出限制：65,536 tokens
  - 通过 Interactions API 访问，需 background=true 异步运行

- **性能基准**：
  - Gemini 2.5 Pro Deep Research 用户偏好测试中以 2:1 优势击败竞争对手
  - HLE 从 7.95%（2024.12）提升到 26.9%，高算力下达 32.4%

**结论**：Google成为2026年上半年Deep Research功能升级最积极的大厂。

> 来源：[Google Blog](https://blog.google/innovation-and-ai/models-and-research/gemini-models/next-generation-gemini-deep-research/)、[Google AI for Developers](https://ai.google.dev/gemini-api/docs/models/deep-research-preview-04-2026)、[Interactions API文档](https://ai.google.dev/gemini-api/docs/interactions/deep-research)

### 2.3 Perplexity — 架构跃迁：Deep Research × Computer

**核心变化**：Deep Research 整合进 **Computer**（多模型编排平台）。

- **新架构**：
  - 将复杂问题拆分为子任务
  - 跨 **20+前沿模型** 路由每个子任务
  - 返回可直接使用的报告、PPT、仪表板
  - 基于 Agent Search SDK 和 Search as Code

- **关键能力**：
  - 自动构建研究计划
  - 编写搜索脚本
  - 并行运行数千次检索步骤
  - 生成 presentations、spreadsheets、dashboards、websites

- **定价与接入**：
  - 面向 Perplexity Max 用户
  - 核心推理引擎：Opus 4.6（默认），Sonnet 4.5（备选）
  - 开发者可通过 Agent API 按量付费使用
  - Comet 浏览器已全球上线 iOS/Android/Mac/Windows

- **生态扩展**：
  - 2026年5月集成至 Microsoft Excel/Word/PowerPoint/Outlook
  - 连接 Snowflake 数据仓库

**结论**：Perplexity从单一深度搜索进化为多模型编排研究平台，是架构思路的最大变化。

> 来源：[MarkTechPost](https://www.marktechpost.com/2026/06/11/perplexity-moves-deep-research-into-computer-routing-research-subtasks-across-20-frontier-models-for-reports-decks-and-dashboards)、[BeginnersInAI](https://beginnersinai.org/whats-new-perplexity-2026)、[Toolkitly](https://www.toolkitly.com/latest-updates/perplexity-ai)

### 2.4 Anthropic Claude — Dynamic Workflows 替代独立DR

**核心判断**：截至2026年6月，Anthropic **未推出名为"Deep Research"的独立产品**。

- **替代能力**：
  - **Dynamic Workflows**（研究预览）：可编排数百个并行子agent
  - **Claude Managed Agents**：含 dreaming 功能、self-hosted sandboxes、MCP tunnels
  - **Claude Code Dynamic Workflows**：支持最多 1000 个 agent、16 个并发
  - Claude Opus 4.8（5月28日发布）
  
- **2026年路线图重点**：
  - 增强推理深度（Extended Thinking）
  - 扩展上下文窗口（200K token 非天花板）
  - 实时多模态
  - Project Glasswing（前沿研究模型，邀请制）

**结论**：Anthropic选择用通用agent编排能力覆盖深度研究场景，而非推出独立产品线。

> 来源：[Linas's Newsletter](https://linas.substack.com/p/anthropic-claude-2026-every-launch-guide)、[InKeyBit](https://www.inkeybit.com/blog/future-of-claude-anthropic-roadmap)

### 2.5 xAI Grok — DeepSearch/DeeperSearch 成熟

**核心更新**：Grok 4.3于6月17日上线 Amazon Bedrock，6月推出Word/PowerPoint插件。

- **研究功能**：
  - **DeepSearch**：拆分查询→并行搜索Web+X→迭代检索（最多10步）→7层交叉检查
  - **DeeperSearch**：增强版，更深层次链接遍历
  - 免费层有限使用，SuperGrok 及以上享完整功能

- **Grok 4 性能**：
  - HLE得分：Grok 4（带工具）38.6%，Heavy版本44.4%
  - 原生工具使用：代码解释器、网页浏览、X搜索
  - 128K（App）/ 256K（API）上下文窗口
  - Grok 4 Heavy 为多agent版本（并行运行多个agent后比较结果）

- **6月新动态**：
  - Grok for Microsoft Word（6月18日，免费365插件）
  - Grok for PowerPoint（6月16日）
  - Grok 4.3 上线 Amazon Bedrock（1M token上下文）
  - Imagine Video 1.5 正式发布

**结论**：xAI的DeepSearch走的是社交数据增强路线，与Web+X双源搜索形成差异化。

> 来源：[Suprmind](https://suprmind.ai/hub/grok/grok-features/)、[DataCamp](https://www.datacamp.com/blog/grok-4)、[Releasebot](https://releasebot.io/updates/xai)

---

## 三、国内大厂详细更新

### 3.1 Kimi（月之暗面）— 模型力领先

**核心更新**：K2.6（4月20日）+ K2.7 Code（6月13日）双发。

- **Kimi K2.6**：
  - MoE架构，总参数1万亿/激活320亿，支持256K上下文
  - SWE-Bench Pro 58.6分（超GPT-5.4的57.7）
  - HLE 54.0分
  - **DeepSearchQA 92.5分（领先GPT-5.4超过13分）**
  - 支持300个子Agent并行协作、连续编码13小时

- **Kimi K2.7 Code**（6月13日）：
  - 专用编程模型
  - 推理token消耗减少约30%
  - 多项代码与Agent基准显著提升

- **Kimi深度研究产品**：
  - 由 Kimi-Researcher 模型驱动（端到端Agentic RL训练）
  - 每任务平均：23步推理、规划74个关键词、检索206个网址
  - 筛选前3.2%高质量内容
  - 交付万字报告+可视化动态报告，平均引用26个信源
  - HLE Pass@1 准确率26.9%
  - 红杉中国xBench深度研究任务通过率69%
  - 异步执行（10-25分钟），消耗5-10%月度额度

**结论**：Kimi在DeepSearchQA基准上以92.5分大幅领先，模型力强劲。

> 来源：[AIHub](https://www.aihub.cn/ai-model/kimi-k2-6)、[Kimi官方帮助中心](https://www.kimi.com/zh-cn/help/deep-research/deep-research-overview)、[DataLearner](https://www.datalearner.com/ai-models/pretrained-models/kimi-k2-6)

### 3.2 智谱GLM — GLM-5.2开源 + ZCode 3.0

**核心更新**：2026年6月13日发布GLM-5.2旗舰模型并开源（MIT协议）。

- **GLM-5.2**：
  - MoE架构，约753B参数
  - 1M上下文窗口 + 128K最大输出
  - High/Max两档思考强度
  - Code Arena前端开发评估全球可用模型第一
  - 已在华为昇腾、平头哥等国产算力平台完成适配
  - 三个月内第三个版本（5.0→5.1→5.2），迭代速度极快

- **ZCode 3.0**：
  - 全面切换自研Agent内核
  - 针对GLM深度优化长程推理和工具调用

- **MIT协议开源**：最宽松的开源协议，商业友好

**结论**：智谱以三个月三代的速度迭代，MIT开源策略是国内大厂中最激进的。

> 来源：[AIHub](https://www.aihub.cn/news/glm-5-2-open-source)、[威易网](https://www.weste.net/2026/06-13/GLM-5.2.html)、[kaopu.news](https://kaopu.news/story/2026-06-15/智谱发布旗舰模型glm-52并宣布开源-93f930)

### 3.3 百度 — 千帆DeepResearch商业化 + DuMate登顶

**核心更新**：千帆DeepResearch商业化运营 + 百度搭子DuMate登顶DeepResearch Bench。

- **千帆DeepResearch**（2026年2月商业化）：
  - 定价：2.5元/次，每账户50次免费
  - 自主多步研究、多模态数据整合
  - 深度迭代检索 + 带引用的结构化报告

- **百度搭子DuMate**（2026年3月底推出）：
  - **PinchBench和DeepResearch Bench登顶**
  - 93.3%任务成功率（超Anthropic和OpenAI）

- **平台生态**：
  - 千帆平台已支持构建超140万Agent
  - 服务超46万家企业
  - 提出DAA（Daily Active Agents）指标替代Token消耗衡量AI价值

**结论**：百度在Deep Research商业化落地和企业级服务上走在国内前列。

> 来源：[ITBear](https://m.itbear.com.cn/html/2026-06/1391541.html)、[百度千帆文档](https://cloud.baidu.com/doc/qianfan/s/Mmh8l4qwj)

### 3.4 阿里通义 — DeepResearch-30B开源，HLE全球第一

**核心更新**：通义DeepResearch-30B-A3B开源，HLE榜单登顶。

- **模型参数**：
  - 300亿参数（激活30亿），MoE架构
  - **HLE（Humanity's Last Exam）32.9%准确率，全球第一**
  - 超越DeepSeek-V3.1和OpenAI同类模型

- **生态扩展**：
  - Qwen3.5系列发布，市场份额32.6%领先
  - 千问全面接入淘宝、支付宝等阿里生态

**结论**：通义DeepResearch以30B参数量超越大参数模型，证明了高效架构设计的价值。

> 来源：[腾讯新闻](https://news.qq.com/rain/a/20250918A02T4700)

### 3.5 字节跳动/豆包 — 付费订阅上线

**核心更新**：2026年6月下旬正式上线付费订阅。

- **定价策略**：
  - 基础版：免费
  - 标准版：68元/月
  - 加强版：200元/月
  - 专业版：500元/月
  - 付费功能聚焦：PPT生成、数据分析、影视制作等

- **用户规模**：
  - 月活约3.36亿（2026年4月），全球第二（仅次于ChatGPT）
  - 日均使用10分钟
  - 火山引擎大模型调用量市场份额49.5%（IDC数据）

- **深度研究功能**：
  - 2025年6月推出深度研究功能
  - 2026年2月发布豆包2.0 Pro深度推理模式
  - 6月最新升级细节有限（主要新闻集中在付费订阅）

**结论**：豆包以用户规模和低价策略取胜，深度研究功能本身不是近期焦点。

> 来源：[36氪](https://www.zgeo.com.cn/news/doubao-paid-subscription-douyin-ecommerce-ai-commercialization)

### 3.6 MiniMax — M3发布

**核心更新**：2026年6月1日发布M3模型。

- **M3特点**：
  - 1M上下文窗口 + 原生多模态
  - 聚焦Coding与Agent能力
  - 此前2025年12月发布M2.1（MoE，100B总参/10B激活）

- **市场位置**：
  - 国产大模型市场份额约4.2%
  - 技术优势在多模态和语音合成
  - **Agent生态相对空白**，无独立Deep Research产品

**结论**：MiniMax在Deep Research领域明显缺位，M3重心在通用能力。

> 来源：[AIHub](https://www.aihub.cn/news/minimax-m3-release)

### 3.7 腾讯混元 — 按计划迭代

**核心更新**：混元3.0迭代中，上下文扩展。

- **技术进展**：
  - 混元3.0计划2026年年中完成迭代
  - 上下文窗口从256K扩展至512K（约100万字）
  - 混元图像3.0参数规模80B

- **元宝AI助手**：
  - 混元+DeepSeek双引擎架构
  - 支持8大方言区识别（准确率85%+）
  - 「元宝派」社交功能（AI总结聊天、监督打卡）
  - 截至2026年2月仍完全免费
  - 目标覆盖10亿微信用户

- **基础设施**：
  - 腾讯韶关智算中心2026年6月投产（50亿投资、3万机架）

**结论**：腾讯更侧重元宝AI助手的社交嵌入，而非独立深度研究产品。

> 来源：[i黑马](https://www.iheima.com/article-394305.html)

---

## 四、开源方案更新

### 4.1 Stanford STORM — 停滞期

| 指标 | 数据 |
|------|------|
| GitHub Stars | 29.2K |
| 最新版本 | v1.1.0（2025年1月23日） |
| 最新动态 | 无2026年新更新 |
| 近期论文 | Co-STORM @ EMNLP 2024 |

**状态评估**：STORM项目进入维护期，最后一次重大更新是2025年1月的v1.1.0（添加LiteLLM集成）。项目仍然是最受关注的学术Deep Research系统（70,000+用户体验过live demo），但代码更新放缓。

> 来源：[GitHub stanford-oval/storm](https://github.com/stanford-oval/storm)

### 4.2 GPT Researcher — 活跃迭代

| 指标 | 数据 |
|------|------|
| GitHub Stars | 27.8K |
| 最新版本 | v3.5.0（2026年5月28日） |
| 发布节奏 | 月度稳定迭代 |
| 许可证 | Apache-2.0 |

**近期重要更新**：

- **v3.5.0**（2026年5月28日）：
  - 新增 ModelsLab 图片生成提供器
  - 修复 STRATEGIC_LLM 格式解析问题
  - 修复 detailed report 去重错误
  - 新增 OpenAlex 检索器（学术文献搜索）
  - 新增 Agent Discovery Protocol 支持
  - 新增 Codex CLI 插件清单
  - LLM 生成文件名 + YAML frontmatter

- **v3.4.0**（2026年1月29日）：
  - **内联图片生成**：研究过程中自动生成AI插图（Gemini模型）
  - **LangSmith集成**：原生监控和可观测性
  - 上下文感知的图表选择
  - 暗色模式样式匹配

- **架构特点**：
  - Planner/Executor 模式
  - 20+ web来源并行爬取
  - 多agent研究团队流程
  - 混合 web + 本地文档研究
  - 递归 Deep Research 模式
  - 平均任务耗时约3分钟，成本约$0.10

**结论**：GPT Researcher是开源Deep Research项目中迭代最活跃的，社区贡献活跃。

> 来源：[GitHub assafelovic/gpt-researcher](https://github.com/assafelovic/gpt-researcher/releases)、[ReleaseAlert](https://releasealert.dev/github/assafelovic/gpt-researcher)、[Ry Walker Research](https://rywalker.com/research/gpt-researcher)

### 4.3 LangChain Open Deep Research — 稳步发展

| 指标 | 数据 |
|------|------|
| GitHub Stars | 11.8K |
| Commits | 214 |
| 许可证 | MIT |
| 最近更新 | 活跃但无2026年重大版本 |

**架构特点**：
- 基于 LangGraph 构建
- 三步流程：Scope（澄清范围）→ Research（执行研究）→ Write（生成报告）
- 支持自定义模型、搜索工具、MCP servers
- 在 Deep Research Bench 排行榜上表现接近商业产品
- 提供免费课程（LangChain Academy）

**2026年状态**：项目保持活跃维护，214次commit，但未发布独立版本号。功能持续增强中。

> 来源：[GitHub langchain-ai/open_deep_research](https://github.com/langchain-ai/open_deep_research)、[LangChain Blog](https://www.langchain.com/blog/open-deep-research)

### 4.4 OpenResearcher（TIGER-Lab）— 2026年新星 ⭐

| 指标 | 数据 |
|------|------|
| GitHub | [TIGER-AI-Lab/OpenResearcher](https://github.com/TIGER-AI-Lab/OpenResearcher) |
| 架构 | 30B-A3B MoE（300亿参数，激活30亿） |
| BrowseComp-Plus | **54.8%（开源模型第一）** |
| 论文 | [arXiv:2603.20278](https://arxiv.org/abs/2603.20278) |
| 数据集 | 96K高质量DeepResearch轨迹（11K+ downloads） |

**核心创新**：
- **全离线训练**：使用自建检索器在~11B token语料上生成训练数据，无需实时web API
- **三个浏览器原语**：search、open、find
- **训练轨迹**：97K条，部分超过100+工具调用轮次
- **性能**：超越 GPT-4.1、Claude Opus 4、Gemini 2.5 Pro、DeepSeek-R1、通义DeepResearch
- **行业影响**：NVIDIA已采用此方法训练 Nemotron 3 Ultra
- **HuggingFace**：论文排名第2，数据集前三热门

**里程碑时间线**：
- 2026年2月10日：首发，1.2K+ X点赞
- 2月12日：NVIDIA NeMo Data Designer集成
- 2月14日：Demo视频发布
- 2月18日：训练代码开源
- 2月25日：HuggingFace Top 3热门数据集
- 3月24日：论文发布
- 3月25日：HuggingFace Daily Papers #2
- 5月：Nemotron 3 Ultra采用其数据

**结论**：OpenResearcher代表了2026年上半年开源Deep Research的最大突破——证明了无需实时web访问即可训练出竞争级研究agent。

> 来源：[GitHub TIGER-AI-Lab/OpenResearcher](https://github.com/TIGER-AI-Lab/OpenResearcher)、[ToKnow.ai](https://toknow.ai/posts/openresearcher-offline-deep-research-agent-tiger-lab)

---

## 五、架构与最佳实践进展

### 5.1 多Agent编排模式

**Perplexity Computer 模式**（2026年最重要架构创新）：
- 跨20+前沿模型路由子任务
- 自动构建研究计划 → 编写搜索脚本 → 并行执行数千次检索
- 输出不只是报告，还包括PPT、仪表板、网站

**Anthropic Dynamic Workflows**：
- 支持最多1000个agent、16个并发
- 适用于需要大规模并行研究的场景

**Kimi-Researcher 端到端RL**：
- 端到端Agentic RL训练
- 平均23步推理、74个关键词、206个网页检索
- 筛选前3.2%高质量内容

### 5.2 质量评估基准

| 基准 | 用途 | 当前领先者 |
|------|------|-----------|
| BrowseComp-Plus | 浏览器研究能力 | OpenResearcher 54.8% |
| HLE (Humanity's Last Exam) | PhD级问题 | 通义DeepResearch 32.9%（开源）/ Kimi K2.6 54.0% |
| DeepSearchQA | 深度搜索质量 | Kimi K2.6 92.5% |
| DeepResearch Bench | 综合研究能力 | 百度DuMate 93.3%任务成功率 |
| SWE-Bench Pro | 软件工程 | Kimi K2.6 58.6% |

### 5.3 评测基础设施

- **Deep Research Bench Leaderboard**（HuggingFace）已成为社区标准
- **PinchBench** 作为第三方评测日益受关注
- 百度提出 **DAA（Daily Active Agents）** 新指标替代Token消耗

---

## 六、行业趋势分析

### 6.1 从单模型到多模型编排
Perplexity Computer 代表了新范式：不再依赖单一模型，而是根据子任务特征路由到最适合的模型。这可能是Deep Research架构的下一次范式转移。

### 6.2 开源训练范式转变
OpenResearcher 证明了离线训练路径可行——使用自建语料+轨迹合成，完全不需要实时web API。NVIDIA已采用此方法。这可能降低Deep Research agent的训练门槛。

### 6.3 中国市场的Deep Research差异化
- **百度**：企业级API + 商业化定价
- **Kimi**：模型力驱动 + 端到端RL
- **阿里**：开源模型 + 极致效率（30B参数量夺冠）
- **字节**：用户规模 + 低价订阅
- **智谱**：极速迭代 + MIT开源
- **腾讯**：社交嵌入 + 免费