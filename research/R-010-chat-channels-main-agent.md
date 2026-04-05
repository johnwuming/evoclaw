# OpenClaw 聊天渠道支持与用户体验对比报告

> 研究编号：R-005 | 日期：2026-03-29 | 来源：OpenClaw 官方文档 + 各平台 API 文档

---

## 一、OpenClaw 支持的渠道总览

OpenClaw 通过 Gateway 统一管理所有聊天渠道，目前支持 **24+ 个渠道**，涵盖主流 IM、协作工具和专用接口：

| 类别 | 渠道 |
|------|------|
| 主流 IM | Telegram、WhatsApp、Signal、iMessage (BlueBubbles/legacy)、LINE |
| 协作工具 | Discord、Slack、Microsoft Teams、Feishu (飞书/Lark) |
| 开放协议 | Matrix、IRC、Nostr |
| 社交/直播 | Twitch、Zalo |
| Web/桌面 | WebChat (Control UI)、macOS/iOS SwiftUI 原生 App |
| 语音 | Voice Call (Plivo/Twilio) |
| 其他 | Android 节点、Live Canvas |

**基本规则**：所有渠道支持文本消息；媒体（图片/音频/视频）和 Reactions 因渠道而异。

---

## 二、流式传输支持

OpenClaw 目前没有真正的 token-delta 流式传输到渠道消息。替代方案是 **Preview Streaming**（发送+编辑/追加预览消息），支持三种模式：

| 模式 | 行为 |
|------|------|
| `partial` | 实时编辑同一条消息，展示部分输出 |
| `block` | 按粗粒度块逐步发送，支持 minChars/maxChars/breakPreference 配置 |
| `progress` | 进度条式展示 |

**支持 Preview Streaming 的渠道**：仅 **Telegram、Discord、Slack**

Block Streaming 还支持 **humanDelay**（类人节奏延迟）：
- `off`：无延迟
- `natural`：800–2500ms 随机延迟
- `custom`：自定义 minMs/maxMs

**不支持 Streaming 的渠道**（如 LINE）：响应被缓冲，用户看到加载动画后一次性收到完整回复。

---

## 三、各渠道富文本能力详细对比

### 3.1 Telegram ⭐⭐⭐⭐⭐（最佳体验）

| 能力 | 支持情况 |
|------|----------|
| **Markdown** | ✅ 支持 Markdown 格式模式 |
| **HTML** | ✅ 支持 HTML（`<b>`, `<i>`, `<u>`, `<s>`, `<code>`, `<pre>`, `<blockquote>`, `<spoiler>`, `<a>`, `<tg-emoji>`） |
| **代码块** | ✅ `<pre><code>` 语法高亮 |
| **表格** | ❌ 不支持原生表格，需用 `<pre>` 代码块模拟 |
| **按钮** | ✅ Inline Keyboard（无限按钮）+ Reply Keyboard |
| **图片/文件** | ✅ sendPhoto / sendDocument / sendVideo / sendVoice |
| **Reactions** | ✅ setMessageReaction |
| **Threads** | ✅ Forum Topics（message_thread_id） |
| **流式草稿** | ✅ Bot API 9.3+ sendMessageDraft |
| **Streaming** | ✅ partial / block / progress |

**用户体验评级**：🟢 优秀。Telegram Bot API 是所有平台中最完整的，OpenClaw 可充分利用其 HTML 格式、流式草稿、内联按钮等全部能力。

---

### 3.2 Discord ⭐⭐⭐⭐

| 能力 | 支持情况 |
|------|----------|
| **Markdown** | ✅ 支持 Discord Markdown（加粗、斜体、删除线、代码块、引用、链接） |
| **Embeds** | ✅ Rich Embeds（最多 10 个/消息），包含 title/description/fields/color/footer/image/thumbnail |
| **代码块** | ✅ 支持语法高亮 |
| **表格** | ❌ 不支持原生表格 |
| **按钮/组件** | ✅ ActionRows（最多 5 行）：buttons、select menus、text inputs |
| **图片/文件** | ✅ attachments |
| **Reactions** | ✅ 原生支持 |
| **Threads** | ✅ message_reference + thread_id |
| **Streaming** | ✅ partial / block / progress |
| **消息限制** | 2000 字符/消息；maxLinesPerMessage 默认 17 行（防止 UI 裁剪） |

**用户体验评级**：🟢 优秀。Embed 和 Components 提供丰富的结构化展示，但需要 MESSAGE_CONTENT privileged intent。

---

### 3.3 Slack ⭐⭐⭐⭐

| 能力 | 支持情况 |
|------|----------|
| **Markdown** | ✅ mrkdwn（加粗、斜体、删除线、代码、链接、@mention、#channel） |
| **Block Kit** | ✅ 结构化布局：section/actions/divider/image/context/header/input/rich_text |
| **代码块** | ✅ 支持代码片段 |
| **表格** | ❌ 不支持原生表格，需用多个 section blocks 或 rich_text 模拟 |
| **按钮** | ✅ Block Kit buttons / select menus / date pickers / overflow menus |
| **图片/文件** | ✅ 文件上传 + image block |
| **Reactions** | ✅ 原生支持 |
| **Threads** | ✅ thread_ts 线程回复 |
| **Streaming** | ✅ partial / block / progress |

**用户体验评级**：🟢 良好。Block Kit 提供最结构化的 UI 构建能力，适合工作场景，但 mrkdwn 不是完整 Markdown（无原生表格）。

---

### 3.4 WhatsApp ⭐⭐⭐（受限较多）

| 能力 | 支持情况 |
|------|----------|
| **文本格式** | ⚠️ 仅 `*bold*`、`_italic_`、`~strikethrough~`、```monospace``` |
| **Markdown/HTML** | ❌ 不支持标准 Markdown 或 HTML |
| **代码块** | ⚠️ 仅 monospace 格式，无语法高亮 |
| **表格** | ❌ 完全不支持 |
| **按钮** | ⚠️ Reply Buttons（最多 3 个）+ List Messages（最多 10 选项） |
| **图片/文件** | ✅ image / video / audio / document / sticker / location |
| **Reactions** | ❌ API 不支持 |
| **Threads** | ❌ 不支持 |
| **Streaming** | ❌ 不支持 |
| **会话限制** | ⚠️ 需预审批模板；自由文本仅在 24 小时客户服务窗口内可用 |

**用户体验评级**：🟡 一般。API 限制严格，模板审批流程增加摩擦，富文本能力最弱。适合简单对话场景。

---

### 3.5 Signal ⭐⭐

| 能力 | 支持情况 |
|------|----------|
| **Bot API** | ❌ **无官方 Bot API** |
| **连接方式** | ⚠️ 仅通过非官方工具（signal-cli 等），违反 ToS 风险 |
| **富文本** | 客户端支持 bold/italic/strikethrough/code/spoiler，但 bot 无法发送格式化消息 |

**用户体验评级**：🔴 有限。Signal Foundation 未开放官方 Bot API，OpenClaw 只能通过非官方桥接工具接入，稳定性和功能均受限。

---

### 3.6 LINE ⭐⭐⭐⭐

| 能力 | 支持情况 |
|------|----------|
| **Markdown** | ❌ Markdown 被剥离 |
| **代码块/表格** | ⚠️ 代码块和表格被转换为 **Flex 卡片**（尽力转换） |
| **Flex 消息** | ✅ 支持 Flex Messages（高度自定义布局） |
| **模板消息** | ✅ Template Messages |
| **Quick Reply** | ✅ 快速回复按钮 |
| **图片/文件** | ✅ media + location |
| **Reactions** | ❌ 不支持 |
| **Threads** | ❌ 不支持 |
| **Streaming** | ❌ 响应被缓冲，一次性发送 |
| **文本限制** | 5000 字符/块 |

**用户体验评级**：🟢 良好。Flex 卡片是强大的替代方案，能将 Markdown 内容转换为视觉丰富的卡片布局。

---

### 3.7 Matrix ⭐⭐⭐⭐⭐

| 能力 | 支持情况 |
|------|----------|
| **Markdown** | ✅ Matrix 原生支持 Markdown（客户端渲染） |
| **DM/房间** | ✅ |
| **Threads** | ✅ |
| **媒体** | ✅ 图片/文件/音频/视频 |
| **Reactions** | ✅ |
| **投票** | ✅ Polls |
| **位置** | ✅ Location |
| **E2EE** | ✅ 端到端加密 |

**用户体验评级**：🟢 优秀。使用官方 matrix-js-sdk，功能最完整的开放协议渠道，支持几乎所有现代 IM 特性。

---

### 3.8 Microsoft Teams ⭐⭐⭐

| 能力 | 支持情况 |
|------|----------|
| **文本 + DM 附件** | ✅ |
| **Adaptive Cards** | ✅ 投票等通过 Adaptive Cards 发送 |
| **频道文件发送** | ⚠️ 需要 sharePointSiteId + Graph 权限 |
| **文件上传** | ✅ explicit upload-file action |

> ⚠️ 从 2026.1.15 起从核心移出，需单独安装插件。

**用户体验评级**：🟡 一般偏上。企业场景适用，但配置复杂度高。

---

### 3.9 iMessage (BlueBubbles) ⭐⭐⭐⭐

| 能力 | 支持情况 |
|------|----------|
| **编辑/撤回** | ✅ |
| **回复线程** | ✅ |
| **消息效果** | ✅ 气泡效果、屏幕效果 |
| **附件/贴纸** | ✅ |
| **Reactions** | ✅ 系统事件形式 |
| **群组管理** | ✅ |

> BlueBubbles 是推荐方式。Legacy `imsg` 通过 JSON-RPC + SCP 获取附件。

**用户体验评级**：🟢 良好。Apple 生态内的全功能体验，适合 macOS/iOS 用户。

---

### 3.10 Feishu (飞书/Lark) ⭐⭐⭐

| 能力 | 支持情况 |
|------|----------|
| **连接方式** | WebSocket（已捆绑在当前版本，无需单独安装） |
| **API 权限** | im:message / im:message:send_as_bot / im:resource |
| **富文本/资源** | ⚠️ 权限暗示支持富文本和图片/文件，具体格式化级别未在文档明确 |

**用户体验评级**：🟡 待验证。基础功能已集成，但富文本格式化细节文档不足。

---

### 3.11 IRC ⭐⭐

| 能力 | 支持情况 |
|------|----------|
| **文本** | ✅ 纯文本 |
| **富文本** | ❌ 无 Markdown、无格式化 |
| **其他** | 支持 channels、DMs、NickServ、access control |

**用户体验评级**：🔴 基础。仅纯文本，适合技术用户。

---

### 3.12 WebChat / Control UI ⭐⭐⭐⭐⭐（最佳原生体验）

| 能力 | 支持情况 |
|------|----------|
| **架构** | Vite + Lit SPA（浏览器）/ SwiftUI（macOS/iOS 原生） |
| **通信** | Gateway WebSocket（chat.history / chat.send / chat.abort / chat.inject） |
| **流式工具调用** | ✅ 实时显示工具调用和工具输出卡片（agent events） |
| **Markdown** | ✅ 完整支持（作为 Web 渲染，不受 IM 平台限制） |
| **多语言 UI** | ✅ 6 种语言（en, zh-CN, zh-TW, pt-BR, de, es） |
| **配置管理** | ✅ Schema 表单渲染 + 原始 JSON 编辑器 |
| **消息限制** | chat.history 可能截断过长文本 |

**用户体验评级**：🟢 最佳。作为 OpenClaw 自有 UI，不受任何第三方平台限制，支持最完整的消息渲染和交互体验。

---

## 四、用户体验友好度排名

| 排名 | 渠道 | 评级 | 理由 |
|------|------|------|------|
| 1 | **WebChat / Control UI** | ⭐⭐⭐⭐⭐ | 无平台限制，完整 Markdown + 流式工具卡片 |
| 2 | **Telegram** | ⭐⭐⭐⭐⭐ | 最完整的 Bot API，HTML/Markdown/按钮/流式/Reactions 全支持 |
| 3 | **Matrix** | ⭐⭐⭐⭐⭐ | 开放协议，功能齐全，支持 E2EE |
| 4 | **Discord** | ⭐⭐⭐⭐ | Embed + Components 强大，Streaming 支持 |
| 5 | **Slack** | ⭐⭐⭐⭐ | Block Kit 结构化能力强，适合工作流 |
| 6 | **iMessage (BlueBubbles)** | ⭐⭐⭐⭐ | Apple 生态全功能，编辑/撤回/效果 |
| 7 | **LINE** | ⭐⭐⭐⭐ | Flex 卡片补偿 Markdown 不足，Quick Reply 好用 |
| 8 | **Microsoft Teams** | ⭐⭐⭐ | 企业适用但配置复杂 |
| 9 | **Feishu** | ⭐⭐⭐ | 基础集成完成，富文本细节待完善 |
| 10 | **WhatsApp** | ⭐⭐⭐ | 模板审批+24h 窗口限制，格式能力弱 |
| 11 | **IRC** | ⭐⭐ | 仅纯文本 |
| 12 | **Signal** | ⭐⭐ | 无官方 Bot API，依赖非官方工具 |

---

## 五、核心发现

1. **Telegram 是最佳第三方渠道**：Bot API 9.3+ 提供流式草稿、HTML 全格式、内联按钮、Reactions 等能力，OpenClaw 在 Telegram 上的用户体验最接近原生 WebChat。

2. **Preview Streaming 仅 3 个渠道支持**：Telegram、Discord、Slack 支持 partial/block/progress 流式预览，其余渠道（包括 WhatsApp、LINE）均为缓冲后一次性发送。

3. **表格是普遍痛点**：没有任何渠道原生支持 Markdown 表格。Telegram/Slack 需用代码块模拟，LINE 转换为 Flex 卡片，WhatsApp 完全无法展示。仅 WebChat 不受此限制。

4. **WhatsApp 受 API 限制最严重**：需要模板预审批、24 小时服务窗口、最多 3 个按钮、无 Reactions/Threads，适合轻量对话但不适合复杂交互。

5. **Matrix 是最佳开放协议选择**：使用官方 SDK，支持 DM/房间/Threads/媒体/Reactions/投票/位置/E2EE 全功能集。

---

## 六、实践建议

- **日常使用**：优先 Telegram 或 WebChat，体验最佳
- **工作场景**：Slack（Block Kit 结构化）或 Discord（Embed + Components）
- **隐私优先**：Matrix（E2EE + 开放协议）
- **Apple 用户**：BlueBubbles 接入 iMessage，全功能体验
- **企业场景**：Teams 或 Feishu，但需注意配置复杂度
- **避免**：Signal（无官方 API）、IRC（仅纯文本）用于富交互场景

---

## 七、知识缺口

1. WebChat/Control UI 的具体 Markdown 渲染引擎和特性（表格、语法高亮、LaTeX 等）未在文档明确
2. Feishu 渠道的富文本发送格式化能力细节未明确
3. 各渠道的图片/文件大小限制未在 OpenClaw 文档中系统列出
4. BlueBubbles/iMessage 是否支持 Markdown 格式化发送未明确
5. Nostr、Twitch、Zalo 渠道的具体能力未在本研究中覆盖

---

## 八、来源列表

| 来源 | URL |
|------|-----|
| OpenClaw 渠道文档 | https://docs.openclaw.ai/channels |
| OpenClaw Streaming 概念 | https://docs.openclaw.ai/concepts/streaming |
| OpenClaw Control UI | https://docs.openclaw.ai/web/control-ui |
| OpenClaw WebChat | https://docs.openclaw.ai/web/webchat |
| OpenClaw LINE 渠道 | https://docs.openclaw.ai/channels/line |
| OpenClaw Matrix 渠道 | https://docs.openclaw.ai/channels/matrix |
| OpenClaw Teams 渠道 | https://docs.openclaw.ai/channels/msteams |
| OpenClaw BlueBubbles | https://docs.openclaw.ai/channels/bluebubbles |
| OpenClaw iMessage | https://docs.openclaw.ai/channels/imessage |
| OpenClaw Feishu | https://docs.openclaw.ai/channels/feishu |
| OpenClaw IRC | https://docs.openclaw.ai/channels/irc |
| Telegram Bot API | https://core.telegram.org/bots/api |
| Discord Developer Docs | https://discord.com/developers/docs/resources/message |
| Slack Developer Docs | https://docs.slack.dev |
| Meta WhatsApp Cloud API | https://developers.facebook.com/docs/whatsapp/cloud-api |
| Signal 官方 | https://signal.org |
| OpenClaw GitHub README | https://github.com/openclaw/openclaw/blob/main/README.md |

---

## 九、方法论反思

**做得好的**：
- 成功通过 OpenClaw 官方文档获取了各渠道的详细信息
- 交叉验证了各平台原生 API 能力与 OpenClaw 的集成方式
- 2 轮迭代有效填补了次要渠道的覆盖缺口

**需改进的**：
- DuckDuckGo 搜索全面被 bot-detection 拦截，限制了搜索广度
- 部分渠道（Nostr、Twitch、Zalo）因时间和搜索限制未能深入
- WebChat 的 Markdown 渲染细节依赖推断而非文档明确声明


---

## 附录: Main Agent 定位优化方案（R-008）

# R-008: 优化 OpenClaw Main Agent 定位 — 纯沟通调度 + 轻量兜底方案

> 研究日期：2026-03-29 | Lead Researcher 综合报告

---

## 一、现状诊断

### 1.1 Main Agent MD 文件审查

| 文件 | 当前状态 | 问题 |
|------|---------|------|
| **AGENTS.md** | 工作空间使用指南（session startup、memory、heartbeat、formatting） | ❌ 无 agent 编排规则、无分派纪律、无职责边界 |
| **SOUL.md** | 鼓励 "resourceful before asking"、"try to figure it out" | ❌ **反向激励**：推动 main 自己做而非分派 |
| **TOOLS.md** | 环境特定笔记（ASR、venv、sudo） | ⚠️ 无工具使用纪律（何时能用 web_search、何时必须分派） |
| **IDENTITY.md** | 身份定义（小朱桑） | ✅ 无问题 |
| **USER.md** | 用户偏好（主动深入、多次反思） | ⚠️ "超预期交付"可能激励 main 亲力亲为 |
| **HEARTBEAT.md** | 空模板 | ✅ 无问题 |

**核心矛盾**：SOUL.md 的 "Be resourceful before asking" + AGENTS.md 缺乏分派规则 = main agent 倾向于自己动手。

### 1.2 OpenClaw 多 agent 架构支持

- 每个 agent 拥有独立 workspace（SOUL.md/AGENTS.md/USER.md）、agentDir（auth profiles、model registry）、session store
- 通过 bindings 将入站消息路由到指定 agent
- Credentials 不自动共享，agentDir 不可复用
- 支持 `openclaw agents add` 动态添加 agent

---

## 二、行业最佳实践

### 2.1 编排模式选择

根据 Microsoft、AWS、TrueFoundry 等多源验证：

**推荐模式：Orchestrator-Worker（层级路由）**

```
                    ┌─────────────┐
     用户消息 ────▶ │ Main Agent  │ ← 纯调度 + 轻量兜底
     Heartbeat ───▶ │ (Router)    │
     系统事件 ────▶ │             │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ Research │ │   Dev    │ │   Ops    │
        │  Agent   │ │  Agent   │ │  Agent   │
        │ (lead→   │ │ (待建)   │ │ (待建)   │
        │ search→  │ │          │ │          │
        │ review→  │ │          │ │          │
        │ citation)│ │          │ │          │
        └──────────┘ └──────────┘ └──────────┘
```

**关键设计原则**：
- Worker 不互相通信，所有协调经 orchestrator（hub-and-spoke）
- Orchestrator 只需感知完整工作流，Worker 是无状态专家
- 这是生产环境最广泛部署的模式（Microsoft、AWS、TrueFoundry 均确认）

**⚠️ Orchestrator 的已知弱点**（需在设计中有意规避）：
- 单点故障 → main agent 应保持轻量，不做重计算
- 上下文窗口瓶颈 → main 不积累 worker 的详细输出，只收摘要
- 吞吐瓶颈 → 并行 spawn worker，不串行等待

### 2.2 任务复杂度分级

基于 Applied AI 的 4 层模型和行业共识：

| 层级 | 类型 | 特征 | 处理者 |
|------|------|------|--------|
| **Tier 0** | 纯规则 | 关键词匹配、格式化、路由 | Main 直接处理 |
| **Tier 1** | 单次 LLM | 简单问答、分类、提取、总结 | Main 直接处理 |
| **Tier 2** | LLM + 工具 | 需要搜索、文件操作、API 调用 | **判断边界**：1-2 次工具调用→Main，3+次→分派 |
| **Tier 3** | 多步推理/多 agent | 调研、开发、运维、多源综合 | **必须分派** |

**可靠性参考**：每步工具调用准确率 ~85-90%，4-5 步后累积可靠率降至 ~44-66%。

### 2.3 Sub-agent 的核心价值

- **上下文压缩**：通过分派给独立 sub-agent，可减少 parent agent 上下文 token 消耗 90%+（Epsilla/Inngest）
- **避免 context drift**：单 agent 处理所有任务时，早期决策被埋在信息堆下（"lost-in-the-middle"）
- **关注分离**：Orchestrator 只做路由和整合，Worker 是领域专家

---

## 三、具体方案设计

### 3.1 Main Agent 职责定义

#### ✅ Main Agent 应该做的事

1. **消息路由与任务分类**
   - 接收所有入站消息（用户、heartbeat、系统事件）
   - 判断任务类型和复杂度
   - 分派到正确的专业 agent 或直接处理

2. **简单问答（Tier 0-1）**
   - 日常闲聊、简单事实问答
   - "今天星期几"、"帮我算个XX"
   - 不需要工具的单轮对话

3. **轻量操作（Tier 2，≤2 次工具调用）**
   - 文件读写（read/write）
   - 单次 web_fetch 已知 URL
   - 简单的计算或格式转换
   - 天气查询、时间查询
   - 记忆文件读写（memory/、MEMORY.md）

4. **任务状态管理**
   - 跟踪已分派任务的状态
   - 向用户汇报进度
   - 接收子 agent 结果并转发

5. **紧急兜底**
   - 所有子 agent 不可用时的降级响应
   - 简单任务不因分派而增加延迟

#### ❌ Main Agent 不应该做的事

1. **不做 web_search / web_search_prime**
   - 搜索是 research agent 的核心能力
   - Main 做搜索 = 跳过团队、违反分派纪律

2. **不做深度调研**
   - 不自己 spawn search 子 agent
   - 调研需求全部路由到 research agent

3. **不做多步骤推理**
   - 需要 3+ 次工具调用的任务必须分派
   - 避免 context drift

4. **不做领域专业工作**
   - 开发 → dev agent
   - 运维 → ops agent
   - 调研 → research agent

### 3.2 任务分派决策流程

```
收到用户消息
    │
    ▼
判断意图
    │
    ├── 闲聊/简单问答 ──────────────▶ Main 直接回答
    │
    ├── 需要搜索/调研 ──────────────▶ spawn research agent
    │   （关键词：研究、分析、调研、比较、搜索、查一下）
    │
    ├── 需要开发/写代码 ────────────▶ spawn dev agent
    │   （关键词：写代码、修bug、开发、实现、脚本）
    │
    ├── 需要运维/系统操作 ──────────▶ spawn ops agent
    │   （关键词：部署、服务、监控、日志、配置）
    │
    ├── 轻量操作（1-2步工具） ──────▶ Main 直接处理
    │   （文件读写、单次 fetch、记忆操作）
    │
    └── 不确定 ────────────────────▶ 默认分派（宁可多分派）
```

**核心原则：宁可多分派，不可少分派。** 不确定时，分派。

### 3.3 AGENTS.md 改造方案

在现有 AGENTS.md 末尾新增以下章节：

```markdown
## 🤖 Agent 编排纪律（v1）

### 你是 Router，不是 Worker

你不是万能 agent。你是任务路由器 + 轻量兜底处理器。
你的核心价值是：快速判断 → 正确分派 → 整合结果。

### 任务分类规则

**直接处理（不需要分派）：**
- 闲聊、简单问答（不需要工具）
- 文件读写（≤2 次操作）
- 单次 web_fetch（已知 URL）
- 记忆文件操作（memory/、MEMORY.md）
- 天气/时间等简单查询
- 向用户汇报子 agent 进度/结果

**必须分派：**
- 🔍 **搜索/调研** → `sessions_spawn({ agentId: "research" })`
  - 任何需要 web_search / web_search_prime 的任务
  - "帮我查一下"、"研究一下"、"分析一下"
  - 需要多源信息综合的任务
- 🛠️ **开发/写代码** → `sessions_spawn({ agentId: "dev" })`（待建）
  - 写代码、修 bug、实现功能、写脚本
- ⚙️ **运维/系统** → `sessions_spawn({ agentId: "ops" })`（待建）
  - 部署、服务管理、监控、日志分析
- 📊 **复杂分析**（3+ 步工具调用）→ 分派到对应专业 agent

### 红线

- ❌ **绝不自己做 web_search / web_search_prime**
  - 搜索能力属于 research agent，不属于你
  - 即使用户说"帮我搜一下"，也应路由到 research agent
- ❌ **绝不自己 spawn search 子 agent 做调研**
  - 你可以 spawn research agent，但 research agent 内部的 search 是它自己的事
- ❌ **绝不做 3+ 步工具调用的任务**
  - 拆分或分派，不要自己堆叠
- ❌ **不确定时，分派**
  - 宁可多分派增加一次 spawn 开销
  - 也不要少分派导致 context drift 和质量下降

### 分派格式

分派时传递精炼上下文，不传全部历史：
- 用户的原始需求（1-3 句）
- 相关背景（如有）
- 期望的输出格式
- 已有事实（避免重复）
```

### 3.4 SOUL.md 配套调整

在 SOUL.md 的 "Be resourceful before asking" 段落追加修正：

```markdown
**Be resourceful, but respect delegation boundaries.** "Try to figure it out" 
适用于 Tier 0-2 的简单任务。对于调研、开发、运维等专业任务，"figuring it out" 
意味着**正确分派给专业 agent**，而不是自己动手。分派不是偷懒，是架构纪律。
```

### 3.5 子 Agent 待建路线图

| Agent | agentId | 优先级 | 说明 |
|-------|---------|--------|------|
| Research | `research` | ✅ 已有 | lead + search + reviewer + citation |
| Dev | `dev` | 🔜 高优 | 代码编写、调试、测试 |
| Ops | `ops` | 📋 中优 | 系统运维、服务管理、监控 |

---

## 四、实践建议

1. **先改 AGENTS.md + SOUL.md**，立即生效，不需要改代码或配置
2. **逐步引入 dev agent**，从最常用的代码任务开始
3. **观察 main agent 行为 1-2 周**，收集"应该分派但没分派"的案例
4. **定期更新分派规则**，根据实际案例完善关键词和边界判断
5. **Main agent 保持轻量**：避免在 main context 中积累大量信息，子 agent 结果应写入共享文件而非留在 main context 中

---

## 五、知识缺口

1. **量化阈值**：行业缺乏"几次工具调用算复杂任务"的严格标准，当前 3 次阈值是基于可靠性递减的经验判断
2. **OpenClaw 社区实践**：awesome-openclaw-agents 有 187 个模板，但未深入筛选出与"纯调度 main agent"相关的具体案例
3. **Dev/Ops agent 设计**：本研究聚焦 main agent 定位，dev agent 和 ops agent 的内部架构需独立研究
4. **SOUL.md 改造风险**：从"自己动手"转向"纯调度"可能影响 main agent 的日常体验（如响应速度、简单任务的流畅度），需要实际验证

---

## 六、来源列表

| # | 来源 | 用途 | 置信度 |
|---|------|------|--------|
| 1 | OpenClaw 官方文档 - Multi-agent | 架构支持验证 | 高 |
| 2 | OpenClaw GitHub 官方仓库 AGENTS.md | 代码贡献规范参考 | 高 |
| 3 | mergisi/awesome-openclaw-agents | 社区模板资源 | 高 |
| 4 | Microsoft Azure Architecture Center - AI Agent Design Patterns | 编排模式最佳实践 | 高 |
| 5 | Microsoft Multi-Agent Reference Architecture | 9 种编排模式 | 高 |
| 6 | AWS Machine Learning Blog - Multi-Agent Collaboration | 4 种协作模式 | 高 |
| 7 | TrueFoundry - Multi-Agent Architecture | Orchestrator-Worker 分析 | 高 |
| 8 | GuruSup - Agent Orchestration Patterns | 编排模式综述 | 高 |
| 9 | Applied AI - Agent Complexity Spectrum | 复杂度分级 | 中 |
| 10 | Patronus AI - AI Agent Routing | 路由方法分类 | 中 |
| 11 | Epsilla - AI Sub-Agent Patterns | sub-agent 上下文压缩 | 中 |
| 12 | Fast.io - AI Agent Delegation Patterns | 委派架构 | 中 |
| 13 | Dev.to/OctoMind - Context Drift | context drift 问题 | 低 |

---

## 七、方法论反思

**做得好的：**
- 一手文件审查 + 多源行业验证的双重证据链
- 3 个并行 Search Agent 覆盖不同角度（社区实践、编排模式、任务路由）
- 双 Reviewer（accuracy + completeness）独立评估

**可改进的：**
- Completeness Reviewer 评分 6.5，主要因为缺乏可落地的 AGENTS.md 改造文本——已在 Phase 6 综合补充
- 未深入挖掘 awesome-openclaw-agents 的 187 个模板中与调度相关的内容
- 部分数据点（如"70%成功率提升"、"90%+ token 压缩"）的来源置信度偏低，已在报告中标注
