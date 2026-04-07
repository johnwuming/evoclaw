# R-041: GStack、Superpowers 及同类 AI Agent 编排产品对比调研

> 调研日期：2026-04-08 | 调研员：Research Lead

## 一、调研产品概览

本次共调研 5 个同类产品：GStack、Superpowers、Hermes Agent、ClaudeFlow，以及 Anthropic 官方的 Agent Teams。

---

## 二、逐产品深度分析

### 1. GStack

| 维度 | 详情 |
|------|------|
| **产品全称** | gstack |
| **官网/仓库** | https://github.com/garrytan/gstack |
| **核心定位** | YC CEO Garry Tan 的个人 Claude Code 工作流，模拟 15 人工程团队的 23 个角色化技能 |
| **形态** | Claude Code 技能包（CLAUDE.md + skills 目录） |
| **支持模型** | 锁定 Claude（Claude Code） |
| **GitHub Stars** | ~52,000（2026 年 3 月 12 日开源，16 天内达 20k，后持续增长至 52k+） |
| **定价** | 开源免费 |
| **核心功能** | CEO review、Eng Manager、Release Manager、Doc Engineer 等 23 个角色化 prompt；PR 审查门控；设计→编码→发布流水线 |
| **工作原理** | 在项目根目录放置 CLAUDE.md 和 skills/，Claude Code 启动时自动加载角色化指令，通过 `/` 命令调用不同角色 |
| **核心优势** | 名人效应（Garry Tan）带来巨大曝光；极简安装（复制文件即用）；角色化思维模型成熟 |
| **核心局限** | 本质是 prompt 模板，非真正多 agent；锁死 Claude Code；无持久化、无通道接入、无多用户支持；过度依赖单一场景（代码开发） |

### 2. Superpowers

| 维度 | 详情 |
|------|------|
| **产品全称** | Superpowers |
| **官网/仓库** | https://github.com/obra/superpowers |
| **核心定位** | Agent 技能框架 + 软件开发方法论，让编码 agent 有纪律地工作 |
| **形态** | Claude Code / Gemini CLI / Codex 技能框架（可组合的 SKILL.md 文件） |
| **支持模型** | 不锁定，支持 Claude Code、Gemini CLI、Codex（通过不同配置文件） |
| **GitHub Stars** | ~138,000（全球排名第 51，史上增长最快的开发工具之一） |
| **定价** | 开源免费 |
| **核心功能** | Plan-before-code（先规划后编码）、TDD 工作流、YAGNI 约束、记忆系统、子 agent 编排、技能可组合 |
| **工作原理** | 通过 SKILL.md 文件定义技能，agent 启动时自动加载；支持技能间引用和覆盖；用户指令优先级最高 |
| **核心优势** | 模型无关（最广泛兼容）；社区最大（138k stars）；技能生态丰富；方法论成熟（TDD/YAGNI） |
| **核心局限** | 仍是编码场景为主；无自托管服务器/多通道；无真正并行 agent 调度；技能质量依赖社区贡献 |

### 3. Hermes Agent

| 维度 | 详情 |
|------|------|
| **产品全称** | Hermes Agent |
| **官网/仓库** | https://github.com/NousResearch/hermes-agent / https://hermes-agent.nousresearch.com |
| **核心定位** | 自改进 AI agent，能从经验中学习并自主创建技能 |
| **形态** | 自托管 CLI agent 平台（Docker 部署） |
| **支持模型** | 400+ 模型端点（Nous Portal），包括 Claude、GPT、自家 Hermes/Nomos 系列 |
| **GitHub Stars** | ~22,000（2026 年 2 月发布，2 周达 5.5k） |
| **定价** | 开源免费，自付模型 API 费用 |
| **核心功能** | 持久记忆跨会话、自主技能创建（从经验中学习）、技能市场、多模型支持、集成 Claude Code/Gemini/Codex |
| **工作原理** | 本地 Docker 容器运行，有学习循环：执行任务→提取经验→生成/改进技能→下次应用 |
| **核心优势** | 真正的自学习能力（唯一内置学习循环的 agent）；多模型最广泛（400+）；有持久记忆；自托管可控 |
| **核心局限** | 项目较新（2026.2），稳定性待验证；复杂度高；中文支持一般；学习循环质量不可控 |

### 4. ClaudeFlow

| 维度 | 详情 |
|------|------|
| **产品全称** | ClaudeFlow（后更名为 Ruflo） |
| **官网/仓库** | https://github.com/ruvnet/ruflo |
| **核心定位** | Claude Code 的多 agent 群体编排平台，实现 agent 蜂群式协作 |
| **形态** | CLI 编排框架（基于 tmux 会话管理） |
| **支持模型** | 锁定 Claude（Claude Code） |
| **GitHub Stars** | ~5,000（活跃但社区较小） |
| **定价** | 开源免费 |
| **核心功能** | 多 agent 并行执行、蜂群调度（swarm）、记忆共享、agent 间通信、GitHub/GitLab 集成、代码审查 |
| **工作原理** | 在 tmux 中启动多个 Claude Code 实例，通过编排层协调任务分配和结果收集 |
| **核心优势** | 真正的多 agent 并行执行；蜂群调度理念先进；与 Claude Code 深度集成 |
| **核心局限** | 锁定 Claude Code；依赖 tmux（不适合无头服务器长期运行）；社区小；复杂场景稳定性存疑 |

### 5. Anthropic Agent Teams（官方）

| 维度 | 详情 |
|------|------|
| **产品全称** | Claude Code Agent Teams |
| **官网** | https://code.claude.com/docs/en/agent-teams |
| **核心定位** | Anthropic 官方的多 agent 协作功能，一个 session 作为 team lead 协调其他 session |
| **形态** | Claude Code 内置功能 |
| **支持模型** | Claude |
| **GitHub Stars** | N/A（官方功能） |
| **定价** | 包含在 Claude Code Pro/Max 订阅中（$20-$100/月） |
| **核心功能** | 内置子 agent spawn、任务分配、结果收集 |
| **核心优势** | 官方支持、最稳定、无额外安装 |
| **核心局限** | 仅限 Claude；功能较基础；无自托管；无通道接入 |

---

## 三、综合对比表

| 维度 | OpenClaw | GStack | Superpowers | Hermes Agent | ClaudeFlow |
|------|----------|--------|-------------|--------------|------------|
| **形态** | 自托管平台 | 技能包 | 技能框架 | 自托管 agent 平台 | CLI 编排框架 |
| **模型支持** | 任意（当前 GLM-5） | 仅 Claude | Claude/Gemini/Codex | 400+ | 仅 Claude |
| **多 Agent** | ✅ spawn 并行 | ❌ 单 agent 模拟 | ✅ 子 agent | ✅ 子 agent | ✅ tmux 群体 |
| **通道接入** | ✅ 微信/Discord/QQ | ❌ | ❌ | ❌ | ❌ |
| **持久记忆** | ✅ 文件系统 | ❌ | ✅ 记忆系统 | ✅ 跨会话 | ⚠️ 会话内 |
| **自托管** | ✅ VPS | N/A | N/A | ✅ Docker | ❌ 本地 |
| **自学习能力** | ❌ | ❌ | ❌ | ✅ 学习循环 | ❌ |
| **中文优先** | ✅ | ❌ | ❌ | ⚠️ | ❌ |
| **多用户** | ✅ | ❌ | ❌ | ⚠️ | ❌ |
| **Stars** | 较小 | 52k | 138k | 22k | 5k |
| **定价** | 开源 | 开源 | 开源 | 开源 | 开源 |
| **成熟度** | 生产可用 | prompt 模板 | 成熟框架 | 早期 | 早期 |

---

## 四、核心对比结论

### 相对于 OpenClaw 的定位差异

1. **GStack 和 Superpowers 是技能层，不是平台**——它们只解决"agent 怎么做事更规范"的问题，不解决"agent 在哪里运行、怎么接入用户、怎么多 agent 协调"的问题。OpenClaw 是完整的运行平台，GStack/Superpowers 的理念可以内化为 OpenClaw 的 skill。

2. **Hermes Agent 是最接近的竞品**——同样是自托管、同样支持多模型、同样有持久记忆。但 Hermes 的"自学习"目前在中文场景和团队协作场景下不可靠，而 OpenClaw 的 9 agent 协同系统在多角色分工上更成熟可控。

3. **所有 Claude Code 生态产品都锁定 Claude 模型**——GStack、ClaudeFlow、Agent Teams 全部依赖 Claude。只有 Superpowers（模型无关但仍是本地 CLI）和 Hermes（400+ 模型）不锁定。OpenClaw 使用国产模型 GLM-5 的路线在这组产品中独一无二。

4. **OpenClaw 的独特壁垒是"中文 + 多通道 + 自托管"三位一体**——没有任何一个竞品同时支持微信/Discord/QQ 通道接入、自托管部署、和中文优先体验。这是面向中国用户的核心差异化。

5. **可借鉴之处**——Superpowers 的 SKILL.md 可组合范式、GStack 的角色化 prompt 设计理念、Hermes 的自学习循环，都可以作为 OpenClaw skill 生态的设计参考。

---

## 五、来源

- https://github.com/garrytan/gstack
- https://github.com/obra/superpowers
- https://github.com/NousResearch/hermes-agent
- https://github.com/ruvnet/ruflo
- https://code.claude.com/docs/en/agent-teams
- https://www.mindstudio.ai/blog/gstack-vs-superpowers-vs-hermes-claude-code-frameworks/
- https://ossinsight.io/blog/personal-ai-stacks-2026
- https://thenewstack.io/persistent-ai-agents-compared/
- https://hermes-agent.nousresearch.com/
