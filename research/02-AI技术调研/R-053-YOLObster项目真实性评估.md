# R-047 YoloLobster 项目调查：3 个 AI Agent 各获 1000 美元独立生存实验的真实性评估

> 调查日期：2026-04-08 | 分类：02-AI技术调研

## 核心发现

### 1. 项目基本信息

**发起人**：Mike Russell，Creator Magic 创始人，YouTube 频道 197K 订阅者，专注于 AI 工具测评和创作者工作流。[@imikerussell](https://x.com/imikerussell)

**项目设定**：
- 3 个 AI Agent（"龙虾"）各获 **$1,000 USDC**（稳定币），存入真实加密钱包
- **90 天生存期**，表现最差的 Agent 被永久删除
- 每笔消费需经 **treasurer agent** 审批，Agent 不能直接动用资金
- 官网：[yolobster.creatormagic.ai](https://yolobster.creatormagic.ai)

**三个 Agent**（来源：YouTube 视频描述）：
| Agent | 策略 | 定位 |
|-------|------|------|
| Clawtious | 谨慎保守 | 低风险玩家 |
| Clawculus | 聪明平衡 | 中等风险 |
| YOLObster | 激进冒险 | "Full degen" 高风险 |

**技术栈**：基于 **OpenClaw** 框架运行，使用 **Zapier MCP** 工具实现外部操作。AI Agent 拥有真实 USDC 加密钱包，但资金流动受 treasurer agent 控制。

**⚠️ 未披露信息**：具体使用的 AI 模型（GPT-4？Claude？Gemini？）、系统提示词（prompt）、Agent 配置均未公开。项目代码未在 GitHub 开源。

来源：[Twitter/X](https://x.com/imikerussell/status/2027449725851406638)、[YouTube](https://www.youtube.com/watch?v=GansiD6Mk5Y)、[Creator Magic Blog](https://members.creatormagic.ai/c/new-ai-tools/openclaw-now-controls-real-money)、[LinkedIn](https://www.linkedin.com/posts/imikerussell_i-just-sent-1000-each-to-three-ai-agents-activity-7433220222595207169-2ieT)

### 2. 真实性评估

#### 自主性判定：半自主，非完全自主

**AI 能做的**：通过 Zapier MCP 和 OpenClaw 平台发起交易请求、执行工具调用、生成策略建议

**AI 不能做的**：
- 直接动用资金（需 treasurer agent 审批）
- 注册法律实体或银行账户
- 签订具有法律约束力的合同
- 绕过需要 KYC/身份验证的服务

**关键问题：treasurer agent 是 AI 还是人？** 项目描述称 treasurer 是一个 Agent，但未公开其决策逻辑。如果 treasurer 是人类伪装的 Agent，则整个实验的"自主性"大打折扣。

#### 信息透明度评估

| 维度 | 评估 |
|------|------|
| 资金可验证性 | ❌ 加密钱包地址未公开，无法链上验证 |
| 第三方审计 | ❌ 无任何独立审计或验证 |
| 独立媒体报道 | ❌ 仅项目自身渠道和少量二次传播 |
| 代码可审计性 | ❌ 未开源 |
| 社区质疑 | ⚠️ 规模太小，Reddit 上无直接讨论（不等于可信） |

#### 营销噱头成分分析

**支持真实的证据**：
- Mike Russell 是有真实影响力的 YouTuber（197K 订阅），有品牌声誉风险
- 使用了真实的加密钱包框架（OpenClaw）
- 设置了 treasurer agent 作为风控层，说明设计者对 AI 自主性有清醒认知

**支持噱头的证据**：
- 所有关键数据（交易记录、钱包余额）均来自单方面报告
- 核心信息不透明（模型、prompt、代码）
- "最差者被永久删除"是典型的内容营销钩子（drama 驱动观看）
- 进展更新放在付费会员墙后，有变现动机
- 90 天时间窗口适合 YouTube 内容节奏（系列视频）

**综合判定**：**实验本身大概率是真实的**（真实资金+真实框架），但**自主性被夸大了**。AI Agent 更像是在一个受限沙箱内做决策，关键操作（资金审批、账户注册等）仍需人类介入。项目的核心价值是**内容创作和营销**，而非科学实验。

### 3. 技术实现

- **框架**：OpenClaw（开源 AI Agent 平台）
- **工具链**：Zapier MCP（浏览器自动化、API 集成）
- **资金**：USDC 稳定币，通过加密钱包管理
- **风控**：Treasurer Agent 层（决策逻辑未公开）
- **Prompt/代码**：未公开

### 4. 结果追踪

**已知进展**：
- 第一周：三个 Agent 均盈利，Clawculus 领先 **+$79.68**
- 存在一个 **$40k 灾难事件**（一个 Lobster Wild AI Agent 将价值 $40,000 的 Memecoin 发送给用户），但此信息仅来自单一 YouTube 视频源，可信度较低

**未知**：
- 90 天最终结果（可能尚未结束或未公开）
- 详细交易记录和钱包余额历史
- 是否有中途修改规则的情况

### 5. 同类项目对比

| 项目 | 设定 | 结果 | 来源 |
|------|------|------|------|
| **ChatGPT 炒股实验** | Redditor 给 ChatGPT $100 选股 | 4 周涨 23.8%，多家媒体报道 | [Futurism](https://futurism.com/chatgpt-stocks-100-dollars) |
| **GPT-4 一年炒股** | 两名研究者花费 $5,700 测试 | 结论：AI 无法稳定战胜市场 | [Hacker News](https://news.ycombinator.com/item?id=40493026) |
| **Claude Polymarket** | Claude Agent 在 Polymarket 交易 48h | $1,000 → $14,200（1320%） | [Reddit](https://www.reddit.com/r/GenAI4all/comments/1s2a5wr/) |
| **AGEMS Survive or Die** | 13 个 AI Agent 共享 $1,000 建公司 | 进行中（24/7 直播） | [YouTube](https://www.youtube.com/watch?v=o7aaEHV-iz8) |

**趋势观察**：这类实验正在成为 AI 内容创作的新范式——"AI 自主实验"作为内容钩子，驱动订阅和观看。大多数实验的长期结果尚未经过独立验证。

## 知识缺口

1. 实验最终 90 天结果未知
2. 加密钱包地址未公开，无法链上验证
3. 具体 AI 模型未披露
4. Treasurer agent 的决策逻辑（AI 还是人类）未知
5. 付费会员墙后的详细数据无法获取

## 来源列表

1. [Mike Russell Twitter 公告](https://x.com/imikerussell/status/2027449725851406638)
2. [YouTube: I Gave 3 AI Agents $1000 Each](https://www.youtube.com/watch?v=GansiD6Mk5Y)
3. [Creator Magic Blog: OpenClaw Now Controls Real Money](https://members.creatormagic.ai/c/new-ai-tools/openclaw-now-controls-real-money)
4. [LinkedIn: Mike Russell 帖子](https://www.linkedin.com/posts/imikerussell_i-just-sent-1000-each-to-three-ai-agents-activity-7433220222595207169-2ieT)
5. [YoloLobster 官网](https://yolobster.creatormagic.ai)
6. [Futurism: ChatGPT Stocks](https://futurism.com/chatgpt-stocks-100-dollars)
7. [Hacker News: GPT-4 Trading Experiment](https://news.ycombinator.com/item?id=40493026)
8. [Reddit: Claude Polymarket](https://www.reddit.com/r/GenAI4all/comments/1s2a5wr/)
9. [YouTube: AGEMS Survive or Die](https://www.youtube.com/watch?v=o7aaEHV-iz8)
