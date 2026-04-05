# 文件布局规范 v1

> 最后更新：2026-04-05

---

## 目录结构总览

```
~/.openclaw/
├── workspace/                      # 🏠 主 Agent 工作区（main）
│   ├── AGENTS.md                   # 主 Agent 配置（不可动）
│   ├── SOUL.md / IDENTITY.md / ...  # 系统配置文件
│   ├── FILE-LAYOUT.md              # 本文件
│   ├── memory/                     # 记忆文件
│   ├── shared/                     # 📤 跨团队共享产出
│   │   └── results/                #   研究报告（R-xxx.md）
│   └── archive/                    # 🗄️ 历史归档（已合并的源文件等）
│
├── workspace-research/             # 🔬 研究团队工作区
│   └── research/                   #   研究过程文件（plan.json 等）
│
├── workspace-dev/                  # 🛠️ 开发团队工作区
│   └── <项目名>/                   #   每个项目独立目录
│       ├── PRODUCT.md              #   产品文档（活文档，唯一真相源）
│       ├── feature_list.json       #   功能清单
│       ├── progress.md             #   开发进度
│       ├── init.sh                 #   初始化脚本
│       └── src/                    #   源码
│
├── agents/                         # Agent 配置目录（系统管理）
│   ├── main/                       #   main agent session 存储
│   ├── research-lead/              #   research-lead session 存储
│   ├── dev-lead/                   #   dev-lead session 存储
│   └── ...
│
└── extensions/                     # 插件目录
```

---

## 各目录职责

### `workspace/shared/results/` — 研究报告

**写入者**：研究团队（通过 research-lead）
**性质**：冻结不更新，是立项依据
**命名**：`R-xxx-简短标题.md`（xxx 由 research-lead 分配递增编号）
**内容**：研究报告、调研报告、方案文档

### `workspace/` 根目录 — 主 Agent 产出

**写入者**：main agent
**性质**：main agent 自身产出的分析和方案文档
**注意**：不含 AGENTS.md / SOUL.md 等系统配置文件

### `workspace-dev/<项目>/` — 开发项目

**写入者**：开发团队（通过 dev-lead）
**核心文件**：PRODUCT.md（活文档）、feature_list.json、progress.md
**注意**：PRODUCT.md 是项目的唯一真相源，每次迭代必更新

### `workspace-research/research/` — 研究过程文件

**写入者**：研究团队
**内容**：research-plan.json、knowledge-base.json、gaps.json 等过程数据
**注意**：过程文件，不需要人工查看

### `workspace/archive/` — 历史归档

**用途**：存放已合并的源文件、过期文档
**规则**：可定期清理，不影响任何团队工作

---

## 合并后文件归属（2026-04-05）

以下合并后的文件需要从 `workspace/merged/` 移到正确位置：

### 归入 `shared/results/`（研究报告类）

| 合并后文件 | 新路径 | 分类 |
|-----------|--------|------|
| 001-OpenClaw-Research-Team-Config.md | shared/results/R-001-research-team-config.md | 研究设计 |
| 002-OpenClaw-Architecture-Config.md | shared/results/R-002-architecture-config.md | 研究设计 |
| 003-OpenClaw-Multi-Team-Architecture.md | shared/results/R-003-multi-team-architecture.md | 研究设计 |
| 004-Deep-Research-Landscape-2026.md | shared/results/R-004-deep-research-landscape.md | 研究设计 |
| 005-Industry-Prompt-Benchmark.md | shared/results/R-005-industry-prompt-benchmark.md | 研究设计 |
| 008-AI-Agent-Framework-Comparison.md | shared/results/R-008-agent-framework-comparison.md | 研究报告 |
| 009-RAG-Tech-Progress.md | shared/results/R-009-rag-tech-progress.md | 研究报告 |
| 010-Chat-Channels-Main-Agent.md | shared/results/R-010-chat-channels-main-agent.md | 研究设计 |
| 011-Dev-Team-VS-Claude-Code.md | shared/results/R-011-dev-team-vs-claude-code.md | 研究报告 |
| 012-Claude-Code-Skills-Report.md | shared/results/R-012-claude-code-skills.md | 研究报告 |
| 013-OpenClaw-Features-Design-Gap.md | shared/results/R-013-features-design-gap.md | 研究设计 |
| 016-Dev-Team-Quality-First-v2.md | shared/results/R-016-dev-team-quality-first.md | 研究设计 |
| 017-Model-Usage-Dashboard-API-Limits.md | shared/results/R-017-model-usage-api-limits.md | 研究报告 |
| 024-Design-Implementation-Gap.md | shared/results/R-024-design-implementation-gap.md | 研究设计 |
| 026-Dev-Team-Iteration-Failure.md | shared/results/R-026-dev-team-iteration-failure.md | 研究设计 |

### 归入 `shared/results/`（投资研究类）

| 合并后文件 | 新路径 | 分类 |
|-----------|--------|------|
| 020-Pig-Cycle-Research-Tracker.md | shared/results/R-020-pig-cycle-tracker.md | 投资研究 |
| 021-Buffett-50percent-Strategy.md | shared/results/R-021-buffett-strategy.md | 投资研究 |
| 200-JoinQuant-Quant-Strategy.md | shared/results/R-022-joinquant-quant-strategy.md | 投资研究 |

### 归入 `shared/results/`（技术方案类）

| 合并后文件 | 新路径 | 分类 |
|-----------|--------|------|
| 006-Voice-Input-ASR-Plan.md | shared/results/R-006-voice-input-asr-plan.md | 技术方案 |
| 014-Model-Concurrency-Limits.md | shared/results/R-014-model-concurrency-limits.md | 技术方案 |
| 015-MD-External-Access.md | shared/results/R-015-md-external-access.md | 技术方案 |
| 300-MD-Web-Viewer-Design.md | shared/results/R-018-md-web-viewer-design.md | 技术方案 |

### 归入 `shared/results/`（商业/增长类）

| 合并后文件 | 新路径 | 分类 |
|-----------|--------|------|
| 018-Monetization-Strategies.md | shared/results/R-019-monetization-strategies.md | 商业研究 |
| 019-AI-Growth-Strategies.md | shared/results/R-019b-ai-growth-strategies.md | 商业研究 |

### 归入 `shared/results/`（独立保留）

| 合并后文件 | 新路径 |
|-----------|--------|
| 007-Weixin-Channel-Bug-Report.md | shared/results/R-007-weixin-channel-bug.md |
| 023-AI-Agent-Enterprise-Adoption.md | shared/results/R-023-agent-enterprise-adoption.md |
| 025-Ruflo-Open-Source-Analysis.md | shared/results/R-025-ruflo-analysis.md |
| model-usage-snapshot.md | shared/results/R-model-usage-snapshot.md |
| R-023b-knowledge-organize.md | 保留原名 |
| R-rename-plan.md | 保留原名 |

---

## 命名规范

### 研究报告（shared/results/）
- 格式：`R-xxx-英文短标题.md`
- xxx：三位递增编号，由 research-lead 分配
- 英文短标题：kebab-case，简洁概括主题

### 开发项目（workspace-dev/）
- 项目目录：英文 kebab-case
- PRODUCT.md：项目唯一真相源
- feature_list.json：机器可读的功能清单

### 主 Agent 产出（workspace/）
- 原则上尽量少，分析文档应走研究团队产出到 shared/results/

---

## 规则

1. **研究文档写 `shared/results/`**，不写 workspace 根目录
2. **开发项目写 `workspace-dev/<项目>/`**，PRODUCT.md 是唯一真相源
3. **workspace 根目录只放系统配置文件**（AGENTS.md、SOUL.md 等）和 FILE-LAYOUT.md
4. **archive/ 可随时清理**，不影响任何团队工作
5. **R-xxx 编号不重复使用**，即使文件被删除/合并
