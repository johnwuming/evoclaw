# R-134 多Agent强制接地与共享黑板模式评估

> 报告状态：baseline（待引用验证）
> 生成日期：2026-07-06

## 一、核心发现

### 1.1 强制接地（Grounding）

1. **Self-RAG反思Token机制**（Asai et al., 2023）是学术界最成熟的检索接地方案之一：模型训练时学习生成 Retrieve/IsRel/IsSup/IsUse 四个反思token，推理时自动判断是否需要检索、检索内容是否相关、生成内容是否被检索支持。这是"模型内在接地"的最高标准。（F001，准确性 9/10）

2. **Chain-of-Noting**（Yu et al., EMNLP 2024）针对无关检索文档场景：通过为每个检索文档生成阅读笔记来评估相关性，噪声文档下 EM 提升 +7.9，超出预训练知识范围的问题拒绝率提升 +10.5。这意味着 prompt 中要求模型"先评估检索内容相关性再回答"是有效的接地策略。（F002，准确性 10/10）

3. **基础RAG接地策略**（Gao et al., 2023-2024）已成熟：将检索文档作为上下文注入 prompt，明确指示"仅基于提供的上下文回答，如果上下文不包含答案就说不知道"。这是 LangChain、LlamaIndex 等框架的默认实践。（F003，准确性 8/10）

4. **ChatQA两阶段指令微调**（NVIDIA, NeurIPS 2024）证明：通过在检索数据集上进行对比指令训练 + 混合非检索任务增强，Llama3-ChatQA-1.5-70B 在 ChatRAG Bench 上超越 GPT-4-Turbo 4.4%。对于无法微调模型的生产环境，指令微调路径不可行，但其 prompt 设计模式可借鉴。（F004，准确性 10/10）

5. **ReaLMistake错误检测基准**（Kamoi et al., COLM 2024）发现：GPT-4 和 Claude 3 等顶级 LLM 在检测 LLM 自身错误时召回率极低，self-consistency 和多数投票不能改善错误检测。这直接证明了多 Agent 系统中引入**独立验证器（Reviewer）**的必要性——当前架构中 Reviewer 角色是正确设计。（F006，准确性 7/10，Claude3数据需全文验证）

### 1.2 共享黑板模式（Blackboard Pattern）

6. **LLM黑板架构首次引入**（Han & Zhang, 2025, arXiv:2507.01701）：Agent 通过共享黑板交换所有信息，基于黑板当前内容动态选择执行 Agent，循环直到黑板达成共识。在常识推理和数学任务上达到 SOTA 水平且 token 消耗更少。这是黑板模式在 LLM Agent 场景的学术验证。（F009，准确性 9/10）

7. **去中心化黑板系统**（Salemi et al., 2025, arXiv:2510.01285）：中央 Agent 向共享黑板发布请求，自治子 Agent 基于自身能力自愿响应，无需中央协调器了解各 Agent 专长。相比 master-slave 架构，端到端成功率提升 13%-57%，数据发现 F1 提升 9%。（F010，准确性 10/10）

8. **Token Coherence Theorem**（Parakhin, 2026, arXiv:2603.15183）：将 MESI 缓存一致性协议映射到多 Agent 上下文同步，惰性失效策略将同步成本从 O(n×S×|D|) 降至 O((n+W)×|D|)，不同 workload 下 token 节省 84%-95%。已提供 LangGraph/CrewAI/AutoGen 适配层实现。这是黑板模式 token 效率的理论证明。（F011，准确性 10/10）

9. **上下文压缩三层策略可组合**：底层 Token Coherence 惰性同步（84-95% 节省）→ 中层 ACON 失败分析驱动压缩（26-54% 峰值减少）→ 上层 PAACE 计划感知压缩（97% 性能保留/10x 成本降低）。三层优化方向互补，理论上可叠加。（F012-F013, F021，准确性 5-10/10，叠加声明需实验验证）

10. **当前架构已是黑板雏形**：research-state.json 和 findings 文件的读写模式本质上就是 file-based blackboard。升级路径清晰：(1) 增加写入粒度从文件级到字段级；(2) 支持增量更新而非全量覆写；(3) 引入版本控制和并发写入合并策略；(4) Agent 间通过黑板轮询获取最新状态而非线性传递。（F020，准确性 4/10，无实验来源支撑）

### 1.3 框架对比

11. **OpenAI Swarm context_variables**：Agent 间通过字典传递共享上下文，handoff 时自动传递。Agents SDK 进一步引入 Sandbox Agent，通过容器化文件系统工作区实现持久化状态共享。（F015，准确性 6/10）

12. **LangGraph StateGraph**：TypedDict State Schema 作为图的共享状态，子图继承父图 state，reducer 控制更新策略。与黑板模式的区别：LangGraph 在编译时定义 schema，黑板模式支持运行时动态扩展内容类型。（F016，准确性 9/10）

13. **CrewAI/AutoGen 无显式接地机制**（经 Reviewer web_fetch 验证）：CrewAI 的 Knowledge 系统仅提供 RAG 向量存储（ChromaDB/Qdrant），无引用强制或接地约束；AutoGen AgentChat 关注 Agent 协调模式（Selector Group Chat/Swarm/GraphFlow），无接地机制文档。这一发现对选型决策有重要意义。

## 二、强制接地（Grounding）具体方案

### 2.1 Prompt 修改方案

#### 2.1.1 Searcher（研究搜索员）Prompt 接地强化

**当前问题**：Searcher 的 AGENTS.md 和 task prompt 中缺少强制接地约束，模型可能用预训练数据（如 DeepSeek 过期的小爱开放平台方案）回答。

**修改方案**：在 Searcher 的 system prompt 和 task prompt 中增加以下约束层：

```
## 🔴 强制接地规则（最高优先级）

1. **检索优先**：所有技术方案、数据、API 文档必须来自本次搜索获取的网页内容，严禁使用预训练知识补全。
2. **来源绑定**：每条 finding 必须标注至少 1 个可追溯的 URL 来源。无来源的声明必须在 findings 中标记为"未验证/基于模型知识"。
3. **时效性检查**：当前日期为 {CURRENT_DATE}。所有信息需评估时效性。对于 API 文档、价格、版本号等动态信息，优先使用近 6 个月内的来源。
4. **不知道就说不知道**：如果多次搜索（≥3 次不同关键词）后仍未找到相关信息，在 findings 中明确标注"未找到"，不要编造。
5. **反幻觉自检**：生成每条 finding 后，自问："这个信息来自搜索结果还是我的预训练知识？"如果答案是后者且无来源支持，删除该 finding 或标注为推测。
```

**设计依据**：
- 规则 1-2：来自 RAG 基础接地策略（F003）+ 26 条提示原则中的"基于事实回答"（F007）
- 规则 3：时间戳注入策略（gaps 中标注为待补充，此处为最小可行方案）
- 规则 4：Chain-of-Noting 的"拒绝回答"精神（F002）的 prompt 层实现
- 规则 5：Self-RAG 反思 token（F001）的 prompt 层面模拟——模型无法生成反思 token，但可以在 prompt 中要求自检

#### 2.1.2 Reviewer（研究审核员）Prompt 接地强化

**修改方案**：在 Reviewer 的 system prompt 中增加：

```
## 🔴 审核接地规则

1. **事实核查优先于推理**：对关键数据点（数字、百分比、API 端点、版本号）优先用 web_search 交叉验证，而非依赖自身知识判断对错。
2. **交叉验证要求**：高置信度（confidence: high）的 finding 至少需要 2 个独立来源支持。单一来源的 finding 降级为 medium。
3. **来源可追溯**：所有验证操作需记录验证方法和验证结果。若使用 web_search，需保留搜索查询和结果 URL。
4. **不推测缺口**：标注"数据缺失"而非推测缺失原因。例如：标注"F006 中 Claude3 声明在摘要中未出现"，而非"可能因为 Claude3 表现与 GPT-4 相似"。
```

**设计依据**：
- 规则 1-2：ReaLMistake（F006）的"LLM 自我错误检测召回率极低"结论的直接应用——Reviewer 不能只靠模型能力判断，必须搜索验证
- 规则 3：当前 Reviewer 已通过 accuracy-review.json 实现了此模式（verification_method 字段）
- 规则 4：防止 Reviewer 引入新的幻觉

#### 2.1.3 全局时间戳注入

**方案**：在所有 Agent 的 system prompt 开头注入：

```
## 当前时间上下文
- 当前日期：{YYYY-MM-DD}（周{X}）
- 模型知识截止日期：请以检索到的信息为准，特别是近 2 年内发布的 API、产品和政策信息
- 时效性要求：涉及技术方案选型时，优先使用近 12 个月内的来源
```

**重要性**：当前 Searcher 的 task 中已有 `{CURRENT_DATE}` 变量，但未在所有 Agent 中统一注入。时间戳注入是防止模型使用过期预训练知识的关键前置条件——模型需要知道"现在是什么时候"才能判断自己的知识是否过期。

### 2.2 接地策略分层总结

| 层级 | 策略 | 实现方式 | 学术支撑 | 实施难度 |
|------|------|----------|----------|----------|
| L1 基础 | 检索文档注入 + "仅基于上下文回答" | Prompt 模板 | RAG 基础（F003） | 低 |
| L2 增强 | 来源绑定 + 时效性检查 + 不知道就说不知道 | System prompt 规则 | CoN（F002）+ RAG 实践 | 低 |
| L3 反思 | 自检指令（"这个信息来自搜索还是预训练"） | Prompt 自检 | Self-RAG 模拟（F001） | 低 |
| L4 微调 | 指令微调增强检索接地 | 模型训练 | ChatQA（F004） | 高（不可行） |
| L5 独立验证 | Reviewer 交叉验证 + 多来源要求 | 多 Agent 协作 | ReaLMistake（F006） | 中（已实现） |

**建议实施**：L1+L2+L3 立即实施（纯 prompt 修改，零成本），L5 已部分实现需强化（Reviewer prompt 增加接地规则），L4 不实施（需要微调模型，不在当前架构能力范围内）。

## 三、共享黑板模式评估

### 3.1 当前架构分析

当前上下文传递方式：
- **对话上下文传递**：Agent 间通过对话消息传递精炼摘要（AGENTS.md 规定搜索员返回 ≤200 token 摘要）
- **文件共享**：通过 research-state.json、findings/*.json、gaps.json 等文件传递结构化数据
- **单向流动**：Lead → Searcher → Lead → Reviewer → Lead → Citation → Lead

这种混合模式（消息 + 文件）实际上是**黑板模式的早期形态**，但与完整黑板模式的关键区别：

| 维度 | 当前模式 | 完整黑板模式 |
|------|----------|--------------|
| 写入粒度 | 文件级（全量覆写 research-state.json） | 字段级（类似 MESI cache line） |
| 更新方式 | 全量覆写 | 增量更新 + 合并策略 |
| 版本控制 | 无 | 版本号 + 冲突解决 |
| 并发控制 | 无（串行工作流） | 读写锁 / 乐观并发 |
| 状态发现 | 显式读取（Lead 主动读文件） | 黑板轮询 / 事件通知 |
| Token 效率 | 消息传递 O(n) 开销 | 惰性同步节省 84-95%（F011） |

### 3.2 是否值得引入完整黑板模式

**结论：暂不建议引入完整的共享黑板基础设施。当前混合模式（文件共享 + 精炼消息传递）已满足当前需求，但可以做渐进式优化。**

**理由**：

1. **并发需求低**：当前工作流是串行的（搜索→审核→引用），不存在多个 Agent 同时写入同一状态文件的场景。黑板模式的最大优势（并发协作、去中心化）在当前场景中无法发挥。

2. **复杂度收益不成正比**：引入 MESI 协议、版本控制、并发合并策略等基础设施，需要额外的存储层和同步机制，但当前 4 个研究 Agent 的协作规模太小，Token Coherence 的 84-95% 节省是在大规模 Agent 场景下测得的。

3. **文件共享已足够**：当前 research-state.json + findings 文件的模式已经实现了黑板的核心价值（共享状态、持久化、可追溯），且无需额外基础设施。

4. **现有约束已控制冗余**：AGENTS.md 中对搜索员返回 ≤200 token 摘要的规定、Phase 3 中"不在上下文中累积大型 JSON 输出"的规则，已经有效控制了上下文膨胀。

### 3.3 渐进式优化建议

在不引入完整黑板基础设施的前提下，可以对当前文件共享模式做以下优化：

1. **增量更新 research-state.json**：当前 Phase 3 全量覆写。改为：新 findings 以追加模式写入，保留已有 findings 不变，避免 I/O 竞争。

2. **统一 findings 命名规范**：当前 findings 文件名由 taskName 决定，建议增加时间戳后缀（如 `grounding-research-20260706.json`）支持多次迭代的追溯。

3. **引入轻量状态标记**：在 research-state.json 中增加 `last_modified_by` 和 `version` 字段，便于调试和追溯。

4. **压缩摘要格式**：当前搜索员摘要为自由文本，可改为结构化格式（`{findings_count, key_numbers, gaps, file_path}`），进一步减少消息传递中的 token 消耗。

## 四、具体落地方案

### 4.1 需要修改的文件

| 文件 | 修改内容 | 优先级 |
|------|----------|--------|
| `workspace-search/AGENTS.md` | 增加"强制接地规则"部分（见 2.1.1） | P0 |
| `workspace-reviewer/AGENTS.md` | 增加"审核接地规则"部分（见 2.1.2） | P0 |
| `workspace/AGENTS.md` (Main Agent) | 增加时间戳注入模板（见 2.1.3） | P1 |
| `workspace-research/AGENTS.md` (Research Lead) | Phase 3 改为增量更新模式（见 3.3.1） | P2 |

### 4.2 修改优先级与风险评估

**P0（立即实施，低风险）**：
- Searcher 和 Reviewer 的 prompt 修改：纯文本修改，不涉及架构变更，可立即生效
- 风险：过于严格的约束可能导致模型拒绝回答边界情况（如"找不到信息"频率增加）→ 缓解：在 prompt 中保留"如果找不到信息，请标注并给出最接近的推测"作为兜底

**P1（短期实施，低风险）**：
- 时间戳注入：当前已有 CURRENT_DATE 变量在部分 task 中使用，统一到所有 Agent 即可

**P2（中期评估，中风险）**：
- 增量更新 research-state.json：需要修改 Phase 3 的写入逻辑，需确保向后兼容
- 统一 findings 命名：需要修改搜索员的 task prompt

### 4.3 不建议实施的方案

- ❌ 引入完整 MESI 协议或 Token Coherence 框架：当前 Agent 规模太小，基础设施成本 > 收益
- ❌ 为 Searcher/Reviewer 做指令微调（ChatQA 方案）：不可行，当前模型非自托管
- ❌ 引入 OpenAI Swarm context_variables 或 LangGraph StateGraph：与 OpenClaw 架构不兼容，引入新框架成本过高

## 五、知识缺口

### 5.1 已识别但未解决的缺口

1. **时间戳注入最佳实践**：学术界缺乏专门讨论 Agent 场景下时间戳注入策略的论文。当前方案（2.1.3）基于工程经验，缺乏实验验证。
2. **DeepSeek 模型特有 Hallucination**：DeepSeek-R1 论文关注推理能力而非知识时效性。缺乏针对 DeepSeek 模型在检索接地场景下的专项研究。
3. **Prompt 注入防御**：多 Agent 系统中 Agent 间传递的不可信输出可能成为注入载体，当前零覆盖。（Completeness Reviewer P0 缺口）
4. **生产环境 ROI 量化**：所有 findings 均为学术论文，缺乏接地策略在生产环境中的成本效益数据。
5. **中国 AI 生态接地实践**：阿里百炼、字节 Coze、百度千帆等平台的 Agent 接地机制未调研。
6. **黑板并发控制细节**：仅提及"并发控制复杂"，未展开锁机制、竞态处理等具体方案。

### 5.2 建议后续调研方向

- 补充中国主流 Agent 平台（百炼/Coze/千帆）的接地机制文档调研
- 收集生产环境中 grounding 策略的 A/B 测试数据或案例
- 对实施后的 Searcher/Reviewer 进行幻觉率前后对比（A/B 测试）

## 六、来源列表

| ID | 来源 | 类型 | 验证状态 |
|----|------|------|----------|
| S01 | Asai et al., "Self-RAG", arXiv:2310.11511 (2023) | 学术论文 | ✅ 摘要验证 |
| S02 | Yu et al., "Chain-of-Noting", arXiv:2311.09210 (EMNLP 2024) | 学术论文 | ✅ 摘要验证 |
| S03 | Gao et al., "RAG Survey", arXiv:2312.10997 (2023) | 学术论文 | ✅ 摘要验证 |
| S04 | Liu et al., "ChatQA", arXiv:2401.10225 (NeurIPS 2024) | 学术论文 | ✅ 摘要验证 |
| S05 | Ma et al., "Rewrite-Retrieve-Read", arXiv:2305.14283 (EMNLP 2023) | 学术论文 | ✅ 摘要验证 |
| S06 | Kamoi et al., "ReaLMistake", arXiv:2404.03602 (COLM 2024) | 学术论文 | ⚠️ 部分验证 |
| S07 | Bsharat et al., "26 Prompt Principles", arXiv:2312.16171 (2023) | 学术论文 | ⚠️ 关联性弱 |
| S08 | Rackauckas, "RAG-Fusion", arXiv:2402.03367 (2024) | 学术论文 | ✅ 摘要验证 |
| S09 | Han & Zhang, "Blackboard LLM MAS", arXiv:2507.01701 (2025) | 学术论文 | ✅ 摘要验证 |
| S10 | Salemi et al., "Blackboard Data Science", arXiv:2510.01285 (2025) | 学术论文 | ✅ 摘要验证 |
| S11 | Parakhin, "Token Coherence Theorem", arXiv:2603.15183 (2026) | 学术论文 | ✅ 摘要验证 |
| S12 | Kang et al., "ACON", arXiv:2510.00615 (ICML 2026) | 学术论文 | ✅ 摘要验证 |
| S13 | Yuksel, "PAACE", arXiv:2512.16970 (2025) | 学术论文 | ✅ 摘要验证 |
| S14 | Shen & Shen, "DOVA", arXiv:2603.13327 (2026) | 学术论文 | ✅ 摘要验证 |
| S15 | OpenAI Swarm / Agents SDK, github.com/openai | 框架文档 | ⚠️ 需拆分 |
| S16 | LangGraph, github.com/langchain-ai/langgraph | 框架文档 | ✅ 文档验证 |
| S17 | Song et al., "PharmaSwarm", arXiv:2504.17967 (2025) | 学术论文 | ✅ 摘要验证 |
| S18 | Wang et al., "MemMachine", arXiv:2604.04853 (2026) | 学术论文 | ✅ 摘要验证 |
| S19 | Prompt Engineering Guide, promptingguide.ai | 在线文档 | ✅ 文档验证 |

## 七、方法论反思

### 做得好的
- 搜索覆盖度：20 个查询覆盖了接地和黑板两个维度，产出了 21 条 findings，16 篇 arxiv 论文
- 准确性验证：Accuracy Reviewer 对 21 条 findings 逐一验证，14 条有 arxiv 来源的 finding 中 12 条数据精确匹配
- 审查严格：标注了 F019/F020/F021 等弱来源 finding，避免了不可靠信息进入结论

### 需改进的
- 工程实践覆盖不足：偏学术论文，缺少生产环境案例、中文生态、ROI 数据
- 时间戳注入方案依赖工程经验而非实验验证
- F020（黑板雏形评估）和 F021（三层策略叠加）为推测性结论，应标注为设计建议
- Completeness 评分 6.0，主要扣分在 grounding_production（2/10）和 grounding_framework（5/10）

### 对后续任务的建议
- 实施 P0 prompt 修改后，进行幻觉率 A/B 测试对比
- 补充中国 Agent 平台接地机制的专项调研
- 如 Agent 规模扩大（>10 个并发 Agent），重新评估完整黑板模式的引入
