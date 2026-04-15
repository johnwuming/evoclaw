# R-056 Kimi与MiniMax深度研究系统调研

> 调研时间：2026-04-15 | 研究主题：Kimi（月之暗面）与MiniMax的"深度研究"/Agent产品功能实现方式对比
> 分类：01-AI行业研究

---

## 一、Kimi 深度研究系统

### 1.1 产品概述

Kimi（月之暗面/Moonshot AI）的"深度研究"能力并非一个独立产品，而是其 Agent 能力的核心场景之一。经历了几代模型的演进：

- **K2 Thinking（2025年11月）**：开源思考模型，支持最多 300 步工具调用，"边思考、边使用工具"，是 Agent 能力的基础
- **K2.5 Agent（2026年1月）**：正式推出 Agent 模式和 Agent 集群模式，深度研究成为 Agent 模式的主打场景
- **K2.5 Agent 集群（Beta）**：可调度多达 100 个子 Agent 并行工作，并行处理最高 1500 个步骤

### 1.2 产品入口与交互设计

**入口方式**：
- 网页端 kimi.com，对话框底部提供模式切换按钮
- 四种模式可选：快速模式 → 思考模式 → **Agent 模式** → Agent 集群模式（Beta）
- 侧边栏、对话框底部有文档/表格/PPT 快捷入口
- 也支持通过 Kimi-Researcher 内测入口使用（深度研究专项）

**交互流程**：
1. 用户切换到 Agent 模式（或 Agent 集群模式）
2. 输入研究问题（自然语言描述）
3. 系统自动执行多步骤任务：搜索→分析→生成
4. 过程中有进度展示，用户可观察
5. 最终输出结构化报告

### 1.3 搜索和信息收集机制

- **搜索策略**：Agent 模式下，模型自主决定搜索内容和次数，基于 K2.5 的 Tool Calling 能力自动发起多轮搜索
- **信息收集规模**：Agent 模式适合单线程深度挖掘；Agent 集群模式可同时调度 100 个子 Agent 并行搜索
- **筛选机制**：模型自主评估搜索结果的相关性和可靠性
- **Agent 集群特色**：基于 PARL（并行强化学习）技术，动态生成子 Agent，无需预设角色分工和工作流，用"算力换深度和广度"

### 1.4 推理和写作流程

- **多步骤执行**：非单次生成，而是通过多轮工具调用（搜索→阅读→分析→整合）完成
- **K2 Thinking 基础**：300 步工具调用，持续稳定的深度思考
- **Agent 集群**：1500 步工具调用上限，子 Agent 串行+并行协作
- **写作过程**：在收集完信息后，通过 Agent 模式直接生成最终报告

### 1.5 输出格式

- **结构化报告**：Agent 模式擅长输出格式规范的报告文档
- **多格式交付**：支持 PPT、Excel、Word、PDF、网页生成等多种输出格式
- **Office 三件套**：2026年1月推出，可通过 Agent 模式直接生成 Excel（支持多表联动）、Word、PPT
- **网页生成**：可基于研究结果直接生成可视化网页

### 1.6 技术实现要点

- **底层模型**：K2.5（MoE 架构，总参数 1T，激活参数 32B）
- **Agent 框架**：原生 Agent 能力，非外挂工具链
- **关键创新**：PARL 并行强化学习技术驱动 Agent 集群
- **上下文长度**：256K 超长上下文
- **开源状态**：K2.5 已开源

---

## 二、MiniMax 深度研究系统

### 2.1 产品概述

MiniMax 的深度研究能力主要通过其 **MiniMax Agent** 产品实现，并非一个独立的"深度研究"功能入口。MiniMax 的路线更偏"通用 Agent + 专家子智能体（Expert）"架构：

- **MiniMax M1（2025年6月）**：首个开源大规模混合架构推理模型，集成包括 Deep Research 在内的多种 Agent 能力，上下文输入长度达 1M
- **MiniMax Agent（2025年6月上线）**：通用 Agent 产品，上线一个月完成 12 次功能更新，内部代号"Max"
- **MiniMax M2（2025年9月）**：专为 Coding 和 Agentic 能力而生的模型，秘塔 AI 搜索接入用于深度研究
- **M2.5（2026年2月）**：进一步强化 Agent 能力，推出 MaxClaw 和 Expert 2.0

### 2.2 产品入口与交互设计

**入口方式**：
- 网页端 agent.minimaxi.com
- 桌面端（2026年初推出）
- 对话框中直接输入需求，系统自动识别任务类型
- 专家社区（Experts）：可选用预置的专业智能体执行特定任务

**交互流程**：
1. 用户在 MiniMax Agent 中输入需求（自然语言）
2. 系统自动识别任务类型，选择合适的能力（搜索/编程/分析/创作）
3. 对于深度研究类需求，自动调用搜索、分析、写作等复合能力
4. 过程中有进度反馈，支持用户干预
5. 输出最终报告/文档

**Expert 2.0（专家智能体）**：
- 用自然语言描述即可创建细分领域的专家 Agent
- 覆盖技术开发、商业金融等领域，累计创建超万个
- 社区共享机制：用户可分享/使用他人创建的 Expert

### 2.3 搜索和信息收集机制

- **深度搜索能力**：M2 模型支持深度搜索，能挖掘到常规模型难以定位的信息源
- **来源可追溯**：保持来源 URL 和引用信息
- **自我纠错**：具备自我纠错与任务恢复能力
- **Browser Use**：支持浏览器操作，可直接访问网页获取信息
- **秘塔 AI 搜索集成**：M2 模型被秘塔 AI 搜索接入，用于其深度研究功能
- **1M 上下文**：M1 模型支持 1M（百万 token）上下文输入，远超同侪

### 2.4 推理和写作流程

- **混合模型策略**：根据任务阶段动态切换不同能力的模型
- **分层协作 Agent 框架**：不同层级 Agent 负责不同子任务
- **长程记忆与反思机制**：在多步骤任务中保持上下文一致性
- **预置 SOP 集成**：行业研究等高频场景有成熟的研究框架 SOP，Agent 严格按照既定框架执行
- **自我审查**：Agent 能够在执行过程中主动优化，承认不足，自动测试各种功能

### 2.5 输出格式

- **分析报告**：可输出结构化的市场分析、行业趋势、竞争格局等报告
- **多形式交付**：代码文件、网页小游戏、演讲 PPT 等多种形式
- **格式规范**：将成熟研究框架 SOP 与 Word Skills 融合，输出格式规范的研报文档
- **Expert 专精输出**：如"Global 投研一体 Expert"可一句话生成《2026 年全球贵金属周期报告》

### 2.6 技术实现要点

- **底层模型**：M2.5（闭源），M1（开源，混合架构推理模型）
- **Agent 架构**：分层协作框架 + 混合模型策略
- **MaxClaw**：类似 OpenClaw 的开源工具，支持用户创建自定义工作流
- **MCP 开放协议**：支持 Model Context Protocol，可接入外部工具
- **关键创新**：Expert 2.0 社区化专家智能体生态

---

## 三、与竞品对比

### 3.1 功能矩阵对比

| 维度 | Kimi Agent | MiniMax Agent | OpenAI Deep Research | Perplexity Pro Search |
|------|-----------|---------------|---------------------|----------------------|
| **产品形态** | Agent 模式/集群模式 | 通用 Agent + Expert 子智能体 | 独立 Deep Research 功能 | 搜索增强对话 |
| **触发方式** | 手动切换 Agent 模式 | 自动识别 / 手动选择 Expert | 自动识别或手动选择 | 对话中自动触发 |
| **搜索机制** | 自主多轮搜索 | 深度搜索 + Browser Use | 并行搜索数百个资源 | 并行多源搜索 |
| **执行时间** | 分钟级到数十分钟 | 分钟级 | 5-30分钟 | 秒到分钟级 |
| **并行能力** | 100 Agent 集群 | Expert 分层协作 | 单 Agent 多线程 | 多线程搜索 |
| **上下文** | 256K | 1M（M1） | 取决于模型 | 取决于模型 |
| **输出格式** | 报告/PPT/Excel/Word/PDF/网页 | 报告/代码/网页/PPT | 研究报告（Markdown） | 引用式答案 |
| **引用方式** | 有来源引用 | 来源可追溯 | 完整引用列表 | 行内引用 |
| **开源** | K2.5 开源 | M1 开源 | 闭源 | 闭源 |
| **费用** | 免费使用 | 免费使用 | Plus 25次/月，Pro 250次/月 | Pro 会员 |

### 3.2 核心差异分析

**Kimi 的差异化**：
1. **Agent 集群（蜂群模式）**：全球首个推出 100 Agent 并行集群的商业产品，基于 PARL 技术，是独有的技术亮点
2. **Office 三件套深度集成**：不是简单生成文档，而是支持 Excel 多表联动等专业级操作
3. **开源路线**：K2.5 完全开源，开发者可自由使用和定制
4. **视觉×代码能力**：支持录屏扒代码、截图改网页等视觉理解与代码生成结合能力

**MiniMax 的差异化**：
1. **Expert 社区生态**：用户创建的专家智能体可共享，形成了类似"App Store"的生态
2. **1M 超长上下文**：M1 的百万 token 上下文是 DeepSeek R1（128K）的 8 倍
3. **SOP 预置框架**：行业研究等高频场景有成熟的研究流程模板
4. **MaxClaw 开源工具**：类似 OpenClaw 的自定义工作流能力
5. **自我纠错机制**：Agent 能在过程中主动发现并修正问题

**与 OpenAI/Perplexity 的差异**：
1. **产品定位不同**：Kimi/MiniMax 的深度研究嵌入在更广泛的 Agent 产品中，而非独立功能
2. **并行架构创新**：Kimi 的 Agent 集群比 OpenAI 的单 Agent 多线程更激进
3. **中国生态优势**：在中文搜索质量、国内数据源访问、Office 格式兼容性上有天然优势
4. **商业模式**：Kimi/MiniMax 基础功能免费，而 OpenAI Deep Research 需付费订阅

---

## 四、总结与判断

### 4.1 产品成熟度

- **Kimi Agent**（基于 K2.5）已相当成熟，Agent 集群是其最大亮点，但在专业性内容制作上仍有提升空间（虎嗅评测指出行业报告撰写质量不如预期）
- **MiniMax Agent** 迭代速度极快（上线一个月 12 次更新），Expert 生态正在形成，但在非代码类复杂任务上的稳定性仍需观察

### 4.2 技术路线对比

| 路线 | 代表 | 特点 |
|------|------|------|
| 单 Agent 多步推理 | OpenAI Deep Research | 稳定、可控，但并行能力受限 |
| Agent 集群/蜂群 | Kimi K2.5 | 大规模并行，用算力换质量 |
| 通用 Agent + Expert 子智能体 | MiniMax Agent | 灵活组合，社区生态驱动 |
| 搜索增强 | Perplexity | 以搜索为核心，轻量级研究 |

### 4.3 趋势观察

1. **深度研究正在从独立功能走向 Agent 生态的一部分**：Kimi 和 MiniMax 都没有推出独立的"深度研究"产品，而是将其作为 Agent 的核心场景之一
2. **并行化是核心方向**：Kimi 的 Agent 集群代表了"用算力换研究质量"的趋势
3. **Expert/Skill 生态是护城河**：MiniMax 的 Expert 社区正在形成差异化壁垒
4. **Office 场景成为 Agent 落地主战场**：两家都在深度集成办公文档能力

---

## 五、来源列表

1. Kimi K2.5 发布公告 - https://www.kimi.com/zh
2. Kimi K2.5 Agent 集群深度研究 - https://unifuncs.com/s/abXuVh4Y
3. Kimi K2 Thinking 发布 - https://zhuanlan.zhihu.com/p/1969908447005873171
4. Kimi Agent 模式评测（虎嗅）- https://www.huxiu.com/article/4831317.html
5. MiniMax Agent 官网 - https://agent.minimaxi.com/experts
6. MiniMax M2.5 发布 - https://www.minimaxi.com/news/minimax-m25
7. MiniMax Agent 大升级（极客公园）- https://www.geekpark.net/news/360394
8. MiniMax Agent 团队访谈 - https://www.woshipm.com/ai/6334448.html
9. MiniMax M2 深度搜索能力 - https://cloud.tencent.com/developer/article/2594019
10. MiniMax Agent WAIC 2025 - http://www.news.cn/tech/20250728/2845ebcdf9e24207af195fa2421219af/c.html
11. AI四小强深度研究对比 - https://m.36kr.com/p/3395702384023943
12. Deep Research 产品形态研究 - https://deepseek.csdn.net/67c8fcb7b8d50678a245d710.html
13. Deep Research 技术架构综述 - https://github.com/modelscope/modelscope-classroom/blob/main/Blogs/Articles/Deep-Research-Survey/report.md
14. OpenAI Deep Research 介绍 - https://openai.com/zh-Hans-CN/index/introducing-deep-research/
15. 国内外大模型应用对比（知乎）- https://zhuanlan.zhihu.com/p/1888535008785958517

---

## 六、知识缺口

- Kimi Agent 模式的具体搜索次数上限和单次研究耗时缺乏官方精确数据
- MiniMax Agent 的深度研究在行业报告撰写方面的系统性评测较少
- 两家产品的搜索来源/搜索引擎合作方未公开
- 两家产品的成本结构和单次研究消耗的 token 数量未公开
- 用户留存率和实际使用频次等运营数据缺乏
