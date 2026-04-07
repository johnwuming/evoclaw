# R-041 GStack 及同类多 Agent 编排产品对比分析

> 调研日期：2026-04-07 | 研究团队：Research Lead + 5 研究搜索员
> 分类：02-AI技术调研

## 一、产品概览

### 1. GStack

**本质揭示：GStack 不是多 Agent 框架。** 它是 Y Combinator CEO Garry Tan 创建的 Claude Code 技能包（Skills），通过 slash commands 在 Claude Code 中切换 23 个专业角色（CEO、Designer、Eng Manager、Release Manager、Doc Engineer、QA 等），实现"人类中介的角色切换"式工作流。

- **定位**：Claude Code 工作流增强工具，非独立 Agent 框架
- **创建者**：Garry Tan（YC CEO）
- **Stars**：~63,500（2026-03-11 创建，一个月内爆发增长）
- **许可证**：MIT，TypeScript
- **支持模型**：仅 Claude Code / Codex 及兼容编码 Agent，锁定 Anthropic 生态
- **部署**：复制文件到 `.claude/` 目录即用
- **定价**：免费开源，仅需付 Anthropic API 费
- **核心局限**：无真正的多 Agent 并行、无持久化、无模型自由、本质是一组 Markdown 技能文件的价值被名人效应放大
- **社区争议**：被批评为"18400 GitHub stars for markdown files"，但有社区 fork 适配其他工具

### 2. AutoGen (Microsoft)

- **定位**：微软开源的多 Agent 编程框架，偏向研究/实验型
- **Stars**：~54,000+
- **架构**：三层（Core、AgentChat、Extensions），对话式/事件驱动
- **支持模型**：多模型（Azure OpenAI、OpenAI 等），不锁定
- **编排方式**：动态多 Agent 对话，非 DAG，基于 Agent 间消息传递
- **持久化**：支持内存管理（细节未深入）
- **工具调用**：代码执行、API 调用、自定义工具
- **部署**：开源免费，本地部署
- **定价**：免费（MIT），按 LLM API 用量付费
- **核心优势**：动态对话编排、强可观测性、灵活模块化
- **核心局限**：学习曲线陡峭、生产稳定性不如 CrewAI、部署复杂度高
- **⚠️ 重要变化**：2025年10月微软宣布将 AutoGen 与 Semantic Kernel 合并为 **Microsoft Agent Framework**，AutoGen 作为独立项目未来走向待定

### 3. CrewAI

- **定位**：基于角色扮演的多 Agent 编排框架，偏向企业级生产
- **Stars**：~45,900
- **架构**：Agent（角色专家）+ Task（任务）+ Crew（团队），层级式/顺序式
- **支持模型**：多模型（通过 LangChain 接入 OpenAI、Anthropic、Gemini 等）
- **编排方式**：Sequential（顺序）+ Hierarchical（层级，Manager Agent 协调），**不支持复杂 DAG/条件分支**
- **持久化**：支持 Memory（短期/长期），细节有限
- **工具调用**：LangChain 生态工具 + 自定义 Python 函数
- **部署**：开源本地 / Docker / CrewAI Enterprise 云平台
- **定价**：Free / Professional $25/月 / Enterprise（定制）
- **核心优势**：上手简单、角色心智模型直观、部署比 AutoGen 快 40%
- **核心局限**：灵活性不足、复杂条件分支支持弱、依赖 LangChain、调试困难
- **宣称数据**：14 亿次 Agentic 执行，60% 财富 500 强使用

### 4. LangGraph

- **定位**：LangChain 生态的低级 Agent 图编排框架，面向生产级有状态工作流
- **Stars**：~10,000+（LangChain 主仓库 126k+）
- **架构**：有状态图（Stateful Graph），支持条件分支、循环、human-in-the-loop
- **支持模型**：完全模型无关（OpenAI、Anthropic、Gemini、Azure、Bedrock、本地模型）
- **编排方式**：图结构（非简单 DAG），条件边、循环边、人机协作节点
- **持久化**：Checkpoint 机制，支持跨交互的有状态持久化
- **工具调用**：支持 MCP（Model Context Protocol）Client 连接外部工具服务 ✅
- **部署**：LangGraph Cloud（托管）/ LangGraph Studio（可视化调试）/ 完全自托管
- **定价**：Developer（免费）/ Plus（$25-50/用户/月）/ Enterprise（定制）
- **核心优势**：图编排灵活性最强、生产级持久化、MCP 支持、模型无关
- **核心局限**：学习曲线最陡、样板代码多、初始设置复杂

### 5. Dify

- **定位**：开源 LLM 应用开发平台，低代码/无代码可视化编排
- **Stars**：~100,000+
- **架构**：前后端分离（Python Flask/FastAPI + Next.js），PostgreSQL + pgvector
- **支持模型**：数百种（OpenAI、Anthropic、Gemini、通义千问、文心一言、智谱 GLM、Ollama 等）
- **编排方式**：ReAct / Function Calling（Agent 模式）+ 可视化 DAG 节点编排（Workflow 模式）
- **持久化**：对话日志、标注数据集、知识库文档、变量记录
- **工具调用**：内置工具（Google Search、Wikipedia）+ OpenAPI schema 自定义工具
- **部署**：Dify Cloud（SaaS）/ Docker Compose 自托管 / Kubernetes
- **定价**：Free / Professional $59/月 / Enterprise（定制）
- **核心优势**：可视化编排门槛低、开箱即用 RAG、中文生态友好、社区最大
- **核心局限**：复杂工作流调试困难、自定义扩展灵活性有限、自托管资源需求较高（最低 2核4G）

---

## 二、六维对比表

| 维度 | GStack | AutoGen | CrewAI | LangGraph | Dify | OpenClaw |
|------|--------|---------|--------|-----------|------|----------|
| **核心定位** | Claude Code 技能包 | 研究型多 Agent 对话框架 | 企业级角色扮演编排 | 低级图编排引擎 | 低代码 AI 应用平台 | 自托管个人 AI Agent 运行时 |
| **架构类型** | 单 Agent 角色切换 | 多 Agent 对话（事件驱动） | 层级式/顺序式团队 | 有状态图（Graph） | Agent + Workflow 双模式 | 层级式多 Agent（main + 子 Agent spawn） |
| **支持模型** | 仅 Claude Code / Anthropic | 多模型（OpenAI/Azure 等） | 多模型（LangChain 生态） | 完全模型无关 | 数百种（含国产模型） | 任意（当前 GLM-5、Kimi、MiniMax） |
| **编排方式** | Slash commands 手动切换 | 动态对话，Agent 间消息传递 | Sequential + Hierarchical | 图结构（条件边/循环） | 可视化 DAG + ReAct | 层级 spawn（run/session 模式），ClawFlow 流编排 |
| **持久化** | ❌ 无 | ✅ 内存管理 | ✅ 短期/长期 Memory | ✅ Checkpoint 机制 | ✅ 对话日志+知识库+数据集 | ✅ 文件系统 + Git 同步 |
| **工具调用** | Claude Code 内置 | 代码执行 + 自定义工具 | LangChain 工具 + 自定义 | MCP Client ✅ + LangChain 工具 | 内置工具 + OpenAPI 自定义 | MCP + Function Calling + exec + browser |
| **部署方式** | 本地 .claude/ 目录 | 本地开源 | 本地/Docker/Enterprise 云 | Cloud/Studio/自托管 | SaaS/Docker/K8s | 自托管 VPS（systemd 守护） |
| **定价** | 免费（付 Anthropic API） | 免费（付 LLM API） | Free / $25月 / Enterprise | Free / $25-50月 / Enterprise | Free / $59月 / Enterprise | 自托管免费（付 LLM API） |
| **GitHub Stars** | ~63,500 | ~54,000 | ~45,900 | ~10,000+ | ~100,000+ | N/A（私有项目） |
| **多通道接入** | ❌ 仅 CLI | ❌ 编程框架 | ❌ 编程框架 | ❌ 编程框架 | ✅ API/Webhook | ✅ 微信/Discord/QQ 等 |
| **中文优先** | ❌ | ❌ | ❌ | ❌ | ✅（国产，中文文档齐全） | ✅ |
| **实时交互** | ✅ Claude Code 内 | ❌ 编程框架 | ❌ 编程框架 | ❌ 编程框架 | ✅ Web UI | ✅ 多通道实时对话 |
| **子 Agent 并行** | ❌ | ✅ 多 Agent 并发 | ✅ Crew 内并行 | ✅ 图节点并行 | ⚠️ 有限 | ✅ 多子 Agent spawn 并行 |

---

## 三、OpenClaw vs 竞品深度对比

### OpenClaw 的独特优势

1. **真正的"活着"的 Agent 系统**：OpenClaw 不是编程框架（AutoGen/CrewAI/LangGraph），也不是开发平台（Dify），而是**持续运行的个人 Agent 运行时**。它有自己的 daemon（systemd）、文件系统记忆、多通道实时交互——这些产品都不具备。

2. **中文优先 + 国产模型**：Dify 虽然中文友好，但它是平台而非运行时。OpenClaw 原生支持微信、QQ 等 IM 通道，使用国产模型（GLM-5），这是所有海外框架不具备的。

3. **文件即记忆**：OpenClaw 的 SOUL.md / IDENTITY.md / USER.md / AGENTS.md 构成了持久的"人格"系统，比 LangGraph 的 checkpoint 更接近真正的"记忆"概念。

4. **多 Agent 真正协同**：9 Agent 系统（main + research 团队 4 人 + dev 团队 4 人）实现了真正的工作分工，比 GStack 的 slash command 切换更接近多 Agent，比 CrewAI 的角色扮演更落地（有实际运行环境）。

5. **完全自托管 + 零 SaaS 依赖**：不依赖任何云服务（除 LLM API），数据完全本地，符合隐私要求。

### OpenClaw 的差距

1. **编排灵活性**：LangGraph 的图结构编排（条件分支、循环、human-in-the-loop）远超 OpenClaw 当前的 spawn 模式。CrewAI 的层级式编排也更成熟。

2. **可视化**：Dify 和 LangGraph Studio 提供可视化工作流设计和调试，OpenClaw 完全依赖代码/配置文件。

3. **MCP 生态**：LangGraph 已原生支持 MCP Client。OpenClaw 支持 MCP 但生态工具集成广度不如 LangChain 生态。

4. **持久化机制**：LangGraph 有生产级 Checkpoint（崩溃恢复、长时间运行），OpenClaw 的文件系统记忆更简单但缺乏事务性保障。

5. **社区与生态**：Dify 100k stars、AutoGen 54k、GStack 63k——OpenClaw 是私有项目，没有开源社区贡献者生态。

6. **RAG 能力**：Dify 开箱即用 RAG 管道，OpenClaw 需要自行实现或通过 Agent 能力完成。

---

## 四、结论与建议

### 产品定位矩阵

```
                    编程框架          运行时/平台
                   ──────────────    ───────────────
  多 Agent 编排    AutoGen          OpenClaw ✅
                   CrewAI
                   LangGraph
                   ──────────────    ───────────────
  单 Agent / 工具  GStack           Dify
```

OpenClaw 在"多 Agent 运行时"这个象限里几乎没有直接竞品。它最接近的是：
- **LangGraph**（如果要更强的编排能力，可借鉴其图结构思路）
- **CrewAI**（如果要更成熟的层级式 Agent 管理）
- **Dify**（如果要可视化 + RAG，但 Dify 不具备"常驻 Agent"概念）

### 建议
- **短期**：借鉴 LangGraph 的 Checkpoint 机制改进 OpenClaw 的持久化
- **中期**：考虑支持可视化工作流编辑（至少生成 AGENTS.md 的可视化）
- **长期**：MCP 生态扩展是关键差异化方向

---

## 五、来源列表

| 来源 | URL |
|------|-----|
| GitHub - garrytan/gstack | https://github.com/garrytan/gstack |
| Star History - gstack | https://star-history.com/garrytan/gstack |
| Agents' Codex - GStack 分析 | https://agentscodex.com/posts/2026-03-20-garry-tan-gstack-agent-teams-claude-code/ |
| Sitepoint - GStack | https://www.sitepoint.com/gstack-garry-tan-claude-code/ |
| GitHub - microsoft/autogen | https://github.com/microsoft/autogen |
| Medium - AutoGen 架构 | https://medium.com/towardsdev/autogen-framework-multi-agent-orchestration-and-complex-task-management-ccf876079bbb |
| The Agent Times - AutoGen Stars | https://theagenttimes.com/articles/autogen-blows-past-54000-github-stars-cementing-its-grip-on-multi-agent-orchestr |
| Medium - AutoGen 合并 Semantic Kernel | https://medium.com/@hieutrantrung.it/the-ai-agent-framework-landscape-in-2025-what-changed-and-what-matters-3cd9b07ef2c3 |
| CrewAI 官方博客 GA | https://crewai.com/blog/crewai-oss-1-0---we-are-going-ga |
| CrewAI 定价 | https://crewai.com/pricing |
| DataCamp - 三框架对比 | https://www.datacamp.com/tutorial/crewai-vs-langgraph-vs-autogen |
| GitHub - langchain-ai/langgraph | https://github.com/langchain-ai/langgraph |
| LangChain Docs - MCP | https://docs.langchain.com/oss/python/langchain/mcp |
| ZenML - LangGraph 定价 | https://www.zenml.io/blog/langgraph-pricing |
| GitHub - langgenius/dify | https://github.com/langgenius/dify |
| Dify 官方文档 | https://docs.dify.ai |
| Dify 定价 | https://dify.ai/pricing |
| SparkCo - 框架对比 | https://sparkco.ai/blog/crewai-vs-autogen-multi-agent-orchestration-2025 |
| LangCopilot - 框架指南 | https://langcopilot.com/posts/2025-11-01-top-multi-agent-ai-frameworks-2024-guide |

---

## 六、方法论反思

### 做得好的
- 5 个并行搜索员高效覆盖了 5 个产品
- GStack 的"非框架"本质被准确识别，避免了误导性对比
- 多源交叉验证（GitHub、官方博客、第三方评测）提高了准确性

### 需改进的
- Dify 搜索员工具全部不可用（rate limit），数据基于训练知识，置信度较低
- LangGraph GitHub stars 精确数字未获取（搜索结果未显示实时数）
- AutoGen 与 Semantic Kernel 合并后的具体迁移时间表未确认
- CrewAI Enterprise 定价存在矛盾信息（$25/月 vs $99-120k/年），需进一步核实
- 缺少实际使用体验的对比（性能基准、延迟、资源占用）
