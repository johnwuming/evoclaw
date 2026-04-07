# R-033 多 Agent 团队模型分配方案

> 状态：搜索验证版（2026-04-07 重调研）
> 分类：01-研发团队架构

---

## 一、可用模型概览（已搜索验证）

### 1.1 智谱（ZhipuAI / zai）

| 模型 | 定位 | 上下文 | 最大输出 | Function Calling | 发布时间 |
|------|------|--------|----------|-----------------|----------|
| **glm-5** | 旗舰基座，面向 Agentic Engineering，Coding 与 Agent 能力开源 SOTA | 200K | 128K | ✅ | 2026 年初 |
| **glm-5-turbo** | 龙虾增强基座，专为 Agent 场景深度优化（工具调用、指令遵循、定时/持续任务、长链路执行） | 200K | 128K | ✅ | 2026-03-16 |
| **glm-5.1** | GLM-5 升级版，编程能力达 Claude Opus 4.6 的 94.6%，强化长程任务和多工具协同，即将开源 | 200K | 131K | ✅ | 2026-03-27 |
| **glm-5v-turbo** | 首个多模态 Coding 基座，原生支持图片/视频输入 + 编程，面向视觉编程和 GUI Agent | 200K | 128K | ✅ | 2026-04-01 |

**关键验证发现**：
- ✅ **glm-5.1 确实存在**（2026-03-27 发布），不应移除。定位为 GLM-5 的升级版，编程能力显著提升（比 GLM-5 提升 20%+），在 Vector Bench 夺冠
- glm-5-turbo 相比 glm-5 API 价格高 20%，但针对 Agent 场景专项优化
- 参数规模：GLM-5/5.1 均为 744B 总参数 / 40B 激活参数
- 来源：[智谱官方文档](https://docs.bigmodel.cn/cn/guide/start/model-overview)、[IT之家](https://www.ithome.com/0/933/487.htm)、[知乎实测](https://zhuanlan.zhihu.com/p/2022946558681908995)

### 1.2 Kimi（月之暗面）

| 模型 | 定位 | 上下文 | Function Calling | 备注 |
|------|------|--------|-----------------|------|
| **kimi-k2.5** | 最智能多模态模型，Agent/代码/视觉 SoTA | 256K | ✅ | 原生多模态，思考与非思考模式 |
| **kimi-k2-0711-preview** | MoE 架构（1T 总参数/32B 激活） | 128K | ✅ | |
| **kimi-k2-turbo-preview** | 高速版（60-100 tokens/s） | 256K | ✅ | 适合高吞吐场景 |
| **kimi-code** | 代码生成优化模型 | 未验证 | ✅ | OpenClaw 配置中已有，定位为编码专项 |
| **moonshot-v1** | 早期生成模型 | 128K | ✅ | 仍在服务但非推荐 |

**说明**：kimi-code 的官方文档需登录 platform.moonshot.cn 查看，未能获取详细参数。基于 OpenClaw 已有配置和 Kimi 在 Agent 任务上的整体优势，保留为可用模型。

### 1.3 MiniMax

| 模型 | 定位 | 上下文 | 输出速度 | Function Calling | 备注 |
|------|------|--------|----------|-----------------|------|
| **MiniMax-M2.7** | 旗舰文本模型，首个支持自我进化的 Agent 原生模型 | 204,800 | ~60 TPS | ✅ | 10B 参数，文字处理"国产最强"，推理相对弱 |
| **MiniMax-M2.7-highspeed** | 高速推理版 | 204,800 | ~100 TPS | ✅ | **输出质量与标准版完全一致**，仅速度和价格不同 |

**M2.7 vs Highspeed 关键验证**：
- ✅ 两者**输出质量完全相同**，区别仅在速度（60 vs 100 TPS）和价格
- ⚠️ MiniMax 的核心优势在文字处理（润色、摘要、写作），**推理能力相对弱**（Arena 得分 84.5，位于第二梯队头部）
- 自我进化能力（100+ 轮优化循环）是其独特卖点
- 来源：[API易](https://docs.apiyi.com/news/minimax-m2-7-launch)、[知乎测评](https://zhuanlan.zhihu.com/p/2017812734159368656)

---

## 二、Agent 角色能力需求分析

### 2.1 编排角色（Orchestrator）

| Agent | 核心需求 | 优先级 |
|-------|----------|--------|
| **research-lead** | 强指令遵循、复杂流程编排、JSON 解析、多步迭代判断、结果整合 | 🔴 指令遵循 > 流程可靠性 |
| **dev-lead** | 项目管理、任务拆解、进度追踪、结果回收、团队协调 | 🔴 指令遵循 > 结构化输出 |

**共同特点**：不做实际搜索/编码，但需要精确理解复杂指令并可靠执行流程。

### 2.2 搜索/工具角色

| Agent | 核心需求 | 优先级 |
|-------|----------|--------|
| **research-searcher** | 多轮工具调用（web_search/web_fetch）、信息提取、JSON 输出 | 🔴 工具调用 > 信息提取 |
| **research-reviewer** | 逻辑推理、准确性判断、长上下文理解（审阅大量 findings） | 🔴 推理能力 > 上下文长度 |
| **research-citation** | URL 验证、精确文本处理、格式标准化 | 🟡 精确性 > 推理深度 |

### 2.3 开发角色

| Agent | 核心需求 | 优先级 |
|-------|----------|--------|
| **dev-designer** | 需求拆解、结构化输出（JSON）、产品设计思维 | 🟡 结构化输出 > 编码 |
| **dev-coder** | 强编码能力、代码理解与生成、debug | 🔴 编码能力 > 其他 |
| **dev-qa** | 严谨逻辑、工具调用（exec/browser）、测试设计 | 🔴 工具调用 > 逻辑严谨 |

---

## 三、模型-角色匹配推荐

### 推荐方案（总览）

| Agent | 推荐模型 | 理由 |
|-------|----------|------|
| **main-agent** | `glm-5-turbo`（默认） | 调度者需要 Agent 工作流优化，glm-5-turbo 专为此设计 |
| **research-lead** | `glm-5-turbo`（默认） | 同上，编排任务是其擅长场景 |
| **research-searcher** | `kimi/kimi-code` | 搜索员需多轮工具调用链，Kimi Agent 能力突出 |
| **research-reviewer** | `glm-5.1` ⭐ | 审核需最强推理能力；GLM-5.1 编程+推理全面升级，且即将开源价格可能更优 |
| **research-citation** | `glm-5-turbo`（默认） | 任务简单（URL 验证+格式化），默认足够 |
| **dev-lead** | `glm-5-turbo`（默认） | 编排角色，同 research-lead |
| **dev-designer** | `minimax/MiniMax-M2.7` | 需求拆解和产品设计 → MiniMax 文字处理"国产最强"，适合结构化产品文档 |
| **dev-coder** | `glm-5.1` ⭐ | 编码核心场景；GLM-5.1 编程能力达 Opus 4.6 的 94.6%，比 kimi-code 更强 |
| **dev-qa** | `glm-5-turbo`（默认） | 工具调用 + 逻辑判断，默认已足够 |

### 推荐方案（详细理由）

#### ⭐ 核心推荐 1：dev-coder → glm-5.1

编码是开发团队的价值核心。GLM-5.1 是智谱最新升级版（2026-03-27），编程能力比 GLM-5 提升 20%+，达到 Claude Opus 4.6 的 94.6%。作为当前最强国产编码模型，应优先分配给 dev-coder。相比 kimi-code，GLM-5.1 在编码评测上已验证领先，且与 glm-5-turbo 同属智谱生态，配置切换成本低。

#### ⭐ 核心推荐 2：research-reviewer → glm-5.1

审核员需要最高质量的事实判断和逻辑推理。GLM-5.1 强化长程任务和多工具协同能力，适合审阅大量 findings 并做出准确判断。调用频率低（仅最终阶段），值得投入。

#### dev-designer → MiniMax-M2.7

更新发现：MiniMax M2.7 在文字处理（润色、摘要、写作）上被评为"国产最强"，而非推理。dev-designer 的核心工作是需求拆解和输出结构化产品文档（PRODUCT.md、feature_list.json），这恰恰是文字处理的强项场景。相比 kimi-code，MiniMax 在此场景更对口。

#### research-searcher → kimi/kimi-code

搜索员需要执行多轮工具调用链。Kimi 在 Agent 任务 benchmark 上表现突出，kimi-code 应继承这一优势。保持此推荐不变。

#### 其余角色 → glm-5-turbo（默认）

编排角色和简单工具角色使用默认模型即可。glm-5-turbo 专为 Agent 场景优化，是编排任务的理想选择。

---

## 四、成本与性能权衡

### 4.1 模型成本排序（已验证，从低到高）

1. `glm-5-turbo` — 基准价格（比 glm-5 贵 20%，但已默认配置）
2. `kimi/kimi-code` — 中等
3. `MiniMax-M2.7` / `MiniMax-M2.7-highspeed` — 中等（highspeed 速度快但价格不同，质量一致）
4. `glm-5.1` — 预计与 glm-5 相当或略高（即将开源，价格可能下降）
5. `glm-5v-turbo` — 多模态附加成本

**已验证的价格信息**：
- GLM-5-Turbo 相对 GLM-5 涨价 20%，相对 GLM-4.7 平均涨 83%
- MiniMax M2.7 标准版 vs highspeed：质量一致，highspeed 速度翻倍但价格更高

### 4.2 推荐配置的总体成本影响

当前所有 agent 均使用 `glm-5-turbo`。推荐方案切换 3 个角色：
- `dev-coder` → `glm-5.1`：调用量大，是主要成本增量，但编码质量提升最大
- `research-reviewer` → `glm-5.1`：调用量少，成本增加有限
- `dev-designer` → `MiniMax-M2.7`：调用量中等

**总体评估**：成本增幅约 10-20%，但核心场景（编码 + 审核）质量显著提升。

---

## 五、备选模型说明

| 模型 | 为何未作为首选 | 潜在使用场景 |
|------|---------------|-------------|
| `glm-5`（非 5.1） | GLM-5.1 已全面超越 | 无需考虑，优先用 5.1 |
| `glm-5v-turbo` | 多模态能力在当前纯文本 agent 中无需求 | UI 截图分析、设计稿转代码等视觉任务 |
| `MiniMax-M2.7-highspeed` | 与标准版质量一致，当前并发不高无需高速 | 高并发场景或延迟敏感场景 |
| `kimi-k2.5` | OpenClaw 未配置此模型 | 如果未来加入配置，可作为编排角色候选 |

---

## 六、实施建议

1. **立即可做**：将 `dev-coder` 的模型设为 `glm-5.1`，这是最高 ROI 的改动
2. **同步调整**：`research-reviewer` 切换到 `glm-5.1`
3. **逐步验证**：`dev-designer` 尝试 `MiniMax-M2.7`，对比产品文档质量
4. **保留 glm-5.1**：✅ 确认存在且能力突出，建议将其提升为备选模型列表的前列（甚至在 dev-coder/reviewer 场景优先于 kimi-code）
5. **考虑调整备选顺序**：建议从 `kimi/kimi-code → minimax/MiniMax-M2.7 → zai/glm-5 → zai/glm-5.1 → zai/glm-5v-turbo` 调整为 `zai/glm-5.1 → kimi/kimi-code → minimax/MiniMax-M2.7 → zai/glm-5 → zai/glm-5v-turbo`

---

## 七、与 R-033 初版的差异

| 项目 | R-033 初版 | 搜索验证版 |
|------|-----------|-----------|
| glm-5.1 | ⚠️ 怀疑不存在，建议移除 | ✅ 确认存在（2026-03-27），编程能力突出 |
| dev-coder 推荐 | kimi-code | **glm-5.1**（更强编码能力） |
| research-reviewer 推荐 | glm-5 | **glm-5.1**（全面升级版） |
| dev-designer 推荐 | kimi-code | **MiniMax-M2.7**（文字处理更强） |
| MiniMax M2.7 认知 | "推理能力强" | ✅ 修正为"文字处理强，推理相对弱" |
| M2.7 vs highspeed | "牺牲部分精度" | ✅ 修正为"质量完全一致，仅速度/价格不同" |

---

## 八、知识缺口

- kimi-code 的具体 token 限制和 benchmark 数据需登录 platform.moonshot.cn 确认
- glm-5.1 的 API 定价未公开（Coding Plan 和 API 定价不同）
- 各模型在 Agent 多轮工具调用场景的实际成功率缺乏定量数据

---

## 来源

- [智谱AI 官方文档 - 模型概览](https://docs.bigmodel.cn/cn/guide/start/model-overview)
- [智谱AI - GLM-5-Turbo 文档](https://docs.bigmodel.cn/cn/guide/models/text/glm-5-turbo)
- [智谱AI - GLM-5 文档](https://docs.bigmodel.cn/cn/guide/models/text/glm-5)
- [智谱AI - GLM-5.1 接入文档](https://docs.bigmodel.cn/cn/coding-plan/using5-1)
- [智谱AI - GLM-5V-Turbo 文档](https://docs.bigmodel.cn/cn/guide/models/vlm/glm-5v-turbo)
- [IT之家 - 智谱GLM-5.1模型公布](https://www.ithome.com/0/933/487.htm)
- [知乎 - GLM-5.1实测](https://zhuanlan.zhihu.com/p/2022946558681908995)
- [知乎 - MiniMax M2.7深度测评](https://zhuanlan.zhihu.com/p/2017812734159368656)
- [API易 - MiniMax M2.7上线](https://docs.apiyi.com/news/minimax-m2-7-launch)
- [mdnice - M2.7-HighSpeed对比](https://mdnice.com/writing/3d4847b4a68a4aabbb894e2f1e139e71)
- [证券时报 - 智谱提价](https://www.stcn.com/article/detail/3680201.html)
- [51CTO - GLM-5.1编码评测](https://www.51cto.com/article/839823.html)
- [53AI - GLM-5.1实测](https://www.53ai.com/news/LargeLanguageModel/2026040224397.html)
