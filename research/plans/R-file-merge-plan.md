# 文档合并方案

> 生成时间：2026-04-05 | 范围：workspace 根目录 17 个 + shared/results 45 个，共 62 个文件
> 本方案自身（R-file-merge-plan.md）不参与合并

---

## 合并后文件命名规范

- 格式：`三位编号-中文标题.md`
- 编号分段：
  - 001-099：研究设计（Research Team / Agent 设计）
  - 100-199：开发设计（Dev Team）
  - 200-299：投资研究（Pig Cycle / 量化）
  - 300-399：技术方案（Access / Dashboard / MD Viewer）
  - 400-499：工具与基础设施
  - 500-599：知识库与整理

---

## 合并组

---

### 组 1: OpenClaw 研究团队完整设计
- **合并后文件名**: `001-OpenClaw-Research-Team-Config.md`
- **保留主文件**: `research-team-prompts-v4.1.md`（最新最终版提示词，21.8KB，内容最完整）
- **合并来源**:
  - `research-team-design.md` → 第 1-2 节（架构设计 v3 总览、核心思想）
  - `research-team-prompts.md` → 第 2 节（可行性评估部分保留）
  - `research-team-prompts-v4.md` → 技术细节补充（v4 修订版）
  - `research-team-v4-improvements.md` → 改进措施（JSON 稳定性、循环检测等）
  - `research-team-v4.1-review.md` → 审查反馈（Meta-Review 6.5/10 的具体改进点）
  - `research-team-config-audit.md` → 配置审计发现（SOUL.md 不注入等关键问题）
- **删除**: `research-team-design.md`、`research-team-prompts.md`、`research-team-prompts-v4.md`、`research-team-v4-improvements.md`、`research-team-v4.1-review.md`、`research-team-config-audit.md`

---

### 组 2: OpenClaw 架构与配置总览
- **合并后文件名**: `002-OpenClaw-Architecture-Config.md`
- **保留主文件**: `openclaw-agents-config-v4-final.md`（37.6KB，版本最新，含完整冲突解决记录）
- **合并来源**:
  - `agent-config-scheme.md` → 完整提示词 + 冲突清单（38.5KB 内容最全）
  - `agent-architecture-report.md` → 架构总览图、Agent 关系图
- **删除**: `agent-config-scheme.md`、`agent-architecture-report.md`

---

### 组 3: OpenClaw 多团队架构
- **合并后文件名**: `003-OpenClaw-Multi-Team-Architecture.md`
- **保留主文件**: `multi-team-feasibility.md`（多团队架构可行性评估，含完整架构图）
- **合并来源**: （无其他文件重叠，独立保留）
- **删除**: 无

---

### 组 4: Deep Research Agent 全景调研
- **合并后文件名**: `004-Deep-Research-Landscape-2026.md`
- **保留主文件**: `deep-research-landscape-2026.md`（独立调研报告，10 个项目深度分析）
- **合并来源**: （无其他文件重叠）
- **删除**: 无

---

### 组 5: 业界 Prompt 设计最佳实践
- **合并后文件名**: `005-Industry-Prompt-Benchmark.md`
- **保留主文件**: `industry-prompt-benchmark.md`（GPT-Researcher、LangChain ODR、Anthropic 对比）
- **合并来源**: （无其他文件重叠）
- **删除**: 无

---

### 组 6: 语音输入与本地 ASR
- **合并后文件名**: `006-Voice-Input-ASR-Plan.md`
- **保留主文件**: `voice-deep-research-plan.md`（11.1KB，含完整用户旅程和技术架构）
- **合并来源**:
  - `voice-input-plan.md` → 补充技术方案细节（5.7KB）
  - `local-asr-comparison.md` → ASR 方案对比表格（SenseVoice/whisper.cpp 等）
- **删除**: `voice-input-plan.md`、`local-asr-comparison.md`

---

### 组 7: 微信渠道 Bug 报告
- **合并后文件名**: `007-Weixin-Channel-Bug-Report.md`
- **保留主文件**: `bug-report-openclaw-weixin-channel.md`
- **合并来源**: （独立 Bug 报告，单独保留）
- **删除**: 无（Bug 报告独立存在）

---

### 组 8: AI Agent 框架对比
- **合并后文件名**: `008-AI-Agent-Framework-Comparison.md`
- **保留主文件**: `R-002-report.md`
- **合并来源**: （无其他文件重叠）
- **删除**: 无

---

### 组 9: RAG 技术进展
- **合并后文件名**: `009-RAG-Tech-Progress.md`
- **保留主文件**: `R-003-report.md`（RAG 技术最新进展）
- **合并来源**:
  - `R-023-knowledge-base-report.md` → 知识库整理方案（与 RAG 生产实践相关）
- **删除**: `R-023-knowledge-base-report.md`

---

### 组 10: OpenClaw 聊天渠道 + Main Agent
- **合并后文件名**: `010-Chat-Channels-Main-Agent.md`
- **保留主文件**: `R-005-chat-channels-report.md`（24+ 渠道详细对比）
- **合并来源**:
  - `R-008-main-agent-architect.md` → Main Agent 定位优化方案（与 R-005 同属 OpenClaw 核心设计）
- **删除**: `R-008-main-agent-architect.md`

---

### 组 11: 研发团队 vs Claude Code 对比
- **合并后文件名**: `011-Dev-Team-VS-Claude-Code.md`
- **保留主文件**: `R-006-dev-team-comparison.md`
- **合并来源**: （无其他文件重叠）
- **删除**: 无

---

### 组 12: Claude Code 技能调研
- **合并后文件名**: `012-Claude-Code-Skills-Report.md`
- **保留主文件**: `R-007-claude-code-skills-report.md`
- **合并来源**: （无其他文件重叠）
- **删除**: 无

---

### 组 13: OpenClaw 最新功能 + 设计实现差距
- **合并后文件名**: `013-OpenClaw-Features-Design-Gap.md`
- **保留主文件**: `R-001-findings.md`（OpenClaw 2026 功能更新）
- **合并来源**:
  - `R-024-design-implementation-gap.md` → 研究团队做产品设计的最佳实践（方法论研究）
  - `R-012-v4-prompt-revision.md` → v4 Prompt 修订报告（配置同步说明）
- **删除**: `R-024-design-implementation-gap.md`、`R-012-v4-prompt-revision.md`

---

### 组 14: 模型并发限制（智谱 + 多厂商）
- **合并后文件名**: `014-Model-Concurrency-Limits.md`
- **保留主文件**: `R-009-model-concurrency-report.md`（智谱并发限制）
- **合并来源**:
  - `R-009b-multi-provider-concurrency.md` → 腾讯/MiniMax/Kimi 并发评估（姐妹篇）
- **删除**: `R-009b-multi-provider-concurrency.md`

---

### 组 15: 本地 MD 文件外网访问
- **合并后文件名**: `015-MD-External-Access.md`
- **保留主文件**: `R-010b-ios-md-access.md`（iOS 友好方案，内容更丰富 11.4KB）
- **合并来源**:
  - `R-010-md-external-access.md` → 通用访问方案补充（Tailscale + MkDocs 方案）
- **删除**: `R-010-md-external-access.md`

---

### 组 16: 研发团队方案（Dev Team v2）
- **合并后文件名**: `016-Dev-Team-Quality-First-v2.md`
- **保留主文件**: `R-015b-dev-team-quality-first-v2.md`（47.9KB，内容最完整，v2 最终版）
- **合并来源**:
  - `R-013-dev-team-design.md` → Dev Team 架构设计 v1（架构基础，合并第 1 节）
  - `R-014-dev-team-harness-design.md` → Harness Engineering 重设计（第 2 节技术细节）
  - `R-015-dev-team-quality-first-design.md` → 质量优先方案 v1（第 3 节改进历程）
  - `R-015b-meta-review.md` → Meta-Review（评审反馈，并入附录）
  - `R-011-dev-agent-design.md` → Dev Agent 完整设计（旧版，合并第 1 节历史背景）
- **删除**: `R-013-dev-team-design.md`、`R-014-dev-team-harness-design.md`、`R-015-dev-team-quality-first-design.md`、`R-015b-meta-review.md`、`R-011-dev-agent-design.md

---

### 组 17: Model Usage Dashboard + API 限额
- **合并后文件名**: `017-Model-Usage-Dashboard-API-Limits.md`
- **保留主文件**: `R-017-model-usage-dashboard.md`
- **合并来源**:
  - `R-017b-zai-api-reverse.md` → ZAI API 逆向（Dashboard 数据源）
  - `R-017c-usage-limits-detail.md` → 各平台限额详情（MiniMax/腾讯云）
  - `R-017d-api-verification.md` → API 端点验证报告
- **删除**: `R-017b-zai-api-reverse.md`、`R-017c-usage-limits-detail.md`、`R-017d-api-verification.md`

---

### 组 18: AI 变现方案
- **合并后文件名**: `018-Monetization-Strategies.md`
- **保留主文件**: `R-018c-monetization-product.md`（产品/SaaS 方向，内容最全面）
- **合并来源**:
  - `R-018a-monetization-api.md` → 技术/API 类变现方案
  - `R-018b-monetization-content.md` → 内容/知识类变现方案
- **删除**: `R-018a-monetization-api.md`、`R-018b-monetization-content.md`

---

### 组 19: AI 增长策略与营销
- **合并后文件名**: `019-AI-Growth-Strategies.md`
- **保留主文件**: `R-027-ai-growth-strategies.md`（领先 AI 团队 UG 方法论）
- **合并来源**:
  - `R-028-ai-growth-marketing.md` → AI 赋能用户增长营销实战（具体案例和数据）
- **删除**: `R-028-ai-growth-marketing.md`

---

### 组 20: 猪周期研究与跟踪系统
- **合并后文件名**: `020-Pig-Cycle-Research-Tracker.md`
- **保留主文件**: `R-021b-pig-tracker-design.md`（46.9KB，技术设计最完整）
- **合并来源**:
  - `R-021-pig-cycle.md` → 猪周期完整逻辑（核心经济逻辑、历史数据）
- **删除**: `R-021-pig-cycle.md`

---

### 组 21: 巴菲特小资金策略
- **合并后文件名**: `021-Buffett-50percent-Strategy.md`
- **保留主文件**: `R-019-buffett-50percent-strategy.md`
- **合并来源**: （独立投资研究，单独保留）
- **删除**: 无

---

### 组 22: Dev Team 迭代成功率研究
- **合并后文件名**: `022-Dev-Team-Iteration-Failure.md`
- **保留主文件**: `R-026-dev-team-iteration-failure.md`
- **合并来源**: （独立研究，Claude Code Plan Mode + 迭代失败根因）
- **删除**: 无

---

### 组 23: AI Agent 企业落地
- **合并后文件名**: `023-AI-Agent-Enterprise-Adoption.md`
- **保留主文件**: `R-004-report.md`
- **合并来源**: （无其他文件重叠）
- **删除**: 无

---

## 独立保留文件（不参与合并）

以下文件主题独立，无相似/重复文件，单独保留：

| 文件 | 保留路径 | 原因 |
|------|---------|------|
| `R-rename-plan.md` | 原路径保留 | Agent 重命名清单，工具类文档 |
| `R-023b-knowledge-organize.md` | 原路径保留 | 知识库整理执行记录（已执行，内容仅 1.7KB） |
| `model-usage-snapshot.md` | 原路径保留 | 时间点用量快照，与 R-017 系列定位不同 |
| `R-022-data-analysis-agent.md` | 重命名为 `024-Data-Analysis-Agent.md` | 数据分析 Agent 案例，主题独立 |
| `R-025-ruflo-analysis.md` | 重命名为 `025-Ruflo-Open-Source-Analysis.md` | Ruflo 开源项目分析，主题独立 |
| `R-020-joinquant-platform.md` | 重命名为 `200-JoinQuant-Quant-Strategy.md` | 聚宽平台研究，量化投资独立主题 |
| `R-020b-browser-automation-feasibility.md` | 合并到 `200-JoinQuant-Quant-Strategy.md` | 聚宽浏览器自动化，与聚宽强相关 |
| `R-020c-data-sources.md` | 合并到 `200-JoinQuant-Quant-Strategy.md` | A股量化数据源，与量化投资强相关 |
| `R-016-md-web-viewer-design.md` | 重命名为 `300-MD-Web-Viewer-Design.md` | MD 网页实时展示方案，独立产品设计 |

---

## 需归档文件（删除或移入 archive/）

| 文件 | 操作 | 原因 |
|------|------|------|
| `R-001-task.md` | 移入 archive/ | 任务描述文件（0.3KB），无独立知识价值 |
| `R-023b-knowledge-organize.md` | 移入 archive/ | 执行记录，无持续参考价值 |

---

## 汇总统计

| 类别 | 数量 |
|------|------|
| 合并后新文件 | 23 个 |
| 独立保留/重命名文件 | 6 个（R-rename-plan、model-usage-snapshot、R-023b、R-022、R-025、R-016） |
| 合并后新文件（从独立组） | 2 个（200-JoinQuant、300-MD-Viewer） |
| 删除文件 | 31 个 |
| 不参与合并（本方案） | 1 个 |
| **合计** | **62 个（含本方案）** |

---

## 合并冲突说明

### 冲突 1：Dev Team 设计版本链（R-013 → R-014 → R-015 → R-015b）
- **问题**：4 个大文件（25-47KB）代表同一主题的渐进迭代
- **处理**：以最终版 R-015b 为主，将前代设计的核心洞察作为历史背景并入
- **风险**：需人工判断前代设计的哪些细节应保留

### 冲突 2：Pig Cycle 文件（R-021 vs R-021b）
- **问题**：R-021 是逻辑框架，R-021b 是技术设计，但指向同一个系统
- **处理**：合并为 020-Pig-Cycle-Research-Tracker.md，以技术设计为主线

### 冲突 3：Model Usage 相关（R-017 系列 vs model-usage-snapshot）
- **问题**：snapshot 是时间点快照，R-017 系列是系统性调研
- **处理**：snapshot 独立保留，R-017 系列合并

### 冲突 4：知识库整理文件（R-023 vs R-023b）
- **问题**：R-023 是分析报告，R-023b 是执行记录
- **处理**：两者都归档或删除，因为都只是过程文档，无持续知识价值

---

## 执行优先级建议

1. **Phase 1**（立即）：合并简单的一对一/一对多文件（组 6、7、8、11、21、22、23）
2. **Phase 2**（复杂）：合并大型多文件组（组 1、组 16、组 20）
3. **Phase 3**（收尾）：独立文件确认 + archive 迁移
