# Vibe Coding 最佳实践：如何持续迭代大型项目

> **报告编号**: R-165（文内原误记 R-0122，2026-08-31 编号治理 task-0598 校正） | **日期**: 2026-07-24 | **研究框架**: 概念→工具→工作流→迭代策略→案例与反思→行动指南
> **研究团队**: research-lead + 4×research-searcher | **信息来源**: 20+ 独立来源中英文交叉验证

---

## 核心结论（先读这部分）

1. **Vibe Coding ≠ AI 辅助工程**。Vibe Coding 适用于原型/MVP，大型项目必须转向 AI 辅助工程（AI-Assisted Engineering）——人类保持主导权，AI 作为加速器。
2. **"70% 问题"是社区共识**：AI 能快速生成 70% 可用代码，但最后 30%（可维护性、安全性、架构一致性）决定项目成败。
3. **提出者本人已放弃**：Karpathy 于 2025年10月在 8000 行的 nanochat 项目上承认 AI 工具"完全没有帮助"，亲手完成所有代码。
4. **大型项目中，上下文管理是第一挑战**：200K 的 context window 会快速耗尽，Subagent 隔离和 Path-Scoped Rules 是核心解法。
5. **必须建立"AI 代码防线"**：Spec-Driven Development + 分层 CI 门禁 + 安全左移 + 禁止 "Accept All" + 小步迭代。

---

## 一、概念定基：什么是 Vibe Coding，什么不是

### 1.1 起源

2025年2月6日，Andrej Karpathy 在 X 上提出：

> *"There's a new kind of coding I call 'vibe coding', where you fully give in to the vibes, embrace exponentials, and forget that the code even exists."*

核心特征：**完全放弃对代码的精细控制，不审查 diff，"Accept All"，用自然语言指挥 AI 生成代码。**

### 1.2 关键澄清（Simon Willison）

Django 联合创始人 Simon Willison 在 2025年3月做了重要区分：

| 行为 | 是 Vibe Coding？ |
|------|-----------------|
| 用 AI 生成代码，不审查就提交 | ✅ 是 |
| 用 AI 生成代码，逐行审查、测试、能向他人解释 | ❌ 不是，这是软件工程 |
| 用 AI 做补全和定向编辑，自己主导 | ❌ 不是 |

> **Willison 黄金法则**：*"I won't commit any code to my repository if I couldn't explain exactly what it does to somebody else."*

### 1.3 IBM 的产业定义

IBM 将 Vibe Coding 定义为"意图驱动的软件开发"，并预测核心将从 **Prompt Engineering** 转向 **Context Engineering**——未来的关键不在于如何提问，而在于如何为 AI 提供完整的业务、架构、代码库、安全和运维上下文。

### 1.4 概念演进：Vibe Coding → AI 辅助工程

| 维度 | Vibe Coding | AI 辅助工程 |
|------|------------|------------|
| **主导权** | AI 掌握，人类只提需求 | 人类掌握，AI 辅助 |
| **适用场景** | 原型、MVP、学习 | 生产系统、长期维护 |
| **代码审查** | "Accept All" 不审查 | 逐行审查每次改动 |
| **测试策略** | 可选 | 必须，规范驱动 |
| **安全考量** | 后置 | 前置，安全左移 |

> **本文核心立场：对于需要持续迭代的大型项目，必须采用 AI 辅助工程模式。**

---

## 二、工具全景与选型框架

### 2.1 主流工具速览

| 工具 | 形态 | 核心优势 | 最佳场景 |
|------|------|---------|---------|
| **Cursor** | 独立 IDE | 项目级代码库理解、Autonomy Slider、多模型 | 全栈开发、大型项目 |
| **Claude Code** | CLI Agent | Agentic Search、多文件编辑、终端原生 | 后端、自动化、大型代码库 |
| **GitHub Copilot** | IDE 插件 | 全球最大生态、GitHub 原生集成 | 日常开发辅助 |
| **Windsurf/Devin Desktop** | 独立 IDE | 并行 Agent、云端交接、个人免费 | 快速开发、中小型项目 |
| **Replit** | 浏览器平台 | Parallel Agents、内置托管 | 快速原型、全栈应用 |
| **Bolt.new** | 浏览器平台 | 智能模型路由、Bolt Cloud 托管 | MVP、非工程师构建产品 |
| **Aider** | CLI 开源 | 支持本地模型、开源可控 | 隐私敏感、自托管 |

### 2.2 核心能力差异

| 能力 | 领先者 | 说明 |
|------|--------|------|
| 代码库理解 | Cursor、Claude Code | 专有索引/Agentic Search，无需手选上下文文件 |
| 多文件编辑 | Cursor Composer、Claude Code | 跨文件一致性编辑 |
| Agent 自主性 | Cursor（可调节滑块）、Devin、Replit | 从 Tab 补全到完全自主 |
| 部署/托管 | Replit、Bolt.new | 内置云端，其他工具仅编码 |
| Token 效率 | Claude Code、Aider（CLI 型） | IDE 型工具更 token-hungry |

### 2.3 选型决策树

```
1. 身份？
   ├─ 初学者/非工程师 → Replit, Bolt.new
   ├─ 专业开发者 → Cursor, Claude Code, Copilot
   └─ 团队/企业 → Cursor 企业版, Copilot Enterprise, Devin Desktop

2. 场景？
   ├─ 快速原型 → Bolt.new, Replit, Cursor Agent
   ├─ 生产开发 → Cursor, Claude Code, Copilot
   └─ 大型遗留代码库 → Claude Code, Cursor

3. 交互偏好？
   ├─ 图形 IDE → Cursor, Copilot (VS Code)
   ├─ 终端 CLI → Claude Code, Aider
   └─ 浏览器 → Replit, Bolt.new

4. 安全/隐私？
   ├─ 高（金融/医疗）→ Copilot Enterprise, Tabnine（私有部署）
   ├─ 中 → Cursor 企业版, Claude Code
   └─ 低（个人）→ 任何
```

---

## 三、大型项目工作流：探索→规划→实现→提交

### 3.1 四阶段工作流（Anthropic 官方推荐）

```
┌─────────────────────────────────────────────────────┐
│  Phase 1: EXPLORE（探索）                             │
│  • Plan Mode，AI 只读不写                             │
│  • 理解现有架构、依赖关系、约定                         │
│  • Prompt 示例: "read /src/auth and understand       │
│    how we handle sessions and login."                │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│  Phase 2: PLAN（规划）                                │
│  • 要求 AI 制定详细实现计划                            │
│  • 列出需修改的文件、数据流、步骤                       │
│  • 人类审查计划可行性                                  │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│  Phase 3: IMPLEMENT（实现）                           │
│  • 退出 Plan Mode，AI 按计划编码                      │
│  • 同时编写测试                                       │
│  • 人类逐行审查 diff                                  │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│  Phase 4: COMMIT（提交）                              │
│  • 规范化 commit message                             │
│  • 标注 [AI-assisted]                                │
│  • 创建 PR，CI 自动化检查                             │
└─────────────────────────────────────────────────────┘
```

**关键原则**：小改动可跳过规划直接执行；涉及多文件或不熟悉的代码，规划是必须的。

### 3.2 给 AI 可验证的反馈回路

大型项目中最危险的模式是 AI "看起来完成了"但实际有错。

| 策略 | 差的 Prompt | 好的 Prompt |
|------|------------|------------|
| 验证标准 | "implement email validation" | "write validateEmail. test cases: user@example.com → true, invalid → false. run tests after" |
| 视觉验证 | "make dashboard better" | "[screenshot] implement this. take screenshot, compare, list differences, fix" |
| 根因修复 | "build is failing" | "build fails with: [error]. fix root cause, verify build succeeds" |

验证强度分四级：
1. **单次 Prompt 内**：要求 AI 运行检查并迭代
2. **Session 级**：用 `/goal` 条件让独立评估器每轮检查
3. **确定性门禁**：用 Stop Hook 运行脚本阻止提前结束
4. **二次确认**：用 verification subagent 让新模型反驳结果

---

## 四、上下文管理——大型项目的第一挑战

> *"Most best practices are based on one constraint: Claude's context window fills up fast, and performance degrades as it fills."*
> — Anthropic 官方文档

### 4.1 上下文窗口的消耗模型

一个 200K token 的 context window，启动时已被占用约 8,000 tokens（System Prompt + Memory + 环境 + CLAUDE.md）。之后每次文件读取、grep 搜索、命令输出持续消耗。一个 `auth.ts` 文件约 2,400 tokens，一次 `npm test` 输出约 1,200 tokens。

### 4.2 五大上下文管理策略

**策略 1：精确指定文件范围**
不说 "explore the codebase"，说 "fix the bug in src/api/auth.ts where token refresh fails"。减少 AI 盲目探索。

**策略 2：Subagent 隔离上下文（最重要）**
Subagent 拥有独立 context window，完成后只返回摘要给主 session。
- Explore subagent：只读搜索代码库
- Plan subagent：规划阶段研究
- General-purpose subagent：处理多文件复杂任务

一个研究任务需要读 5-10 个文件时，委派给 subagent 可节省主 session 数千 tokens。

**策略 3：Dynamic Workflows 编排大规模任务**
对于需要数十甚至数百个代理的任务（如全代码库审计、500 文件迁移），将编排逻辑编码为脚本，中间结果存在脚本变量中，不进入 AI context。

**策略 4：定期 /compact 和 /clear**
- `/compact`：压缩对话历史，保留关键信息
- `/clear`：开始全新 session（cost 计数器重置）
- 用 custom status line 持续监控 context 使用量

**策略 5：模型分级**
- 研究性任务用 Haiku（便宜、快速）
- 实现任务用 Sonnet/Opus（更强）
- 企业部署平均成本约 $13/开发者/活跃天

---

## 五、规则文件——项目的"AI 操作手册"

### 5.1 分层规则体系

| 作用域 | Claude Code | Cursor | 共享范围 |
|--------|------------|--------|---------|
| 组织级 | `/etc/claude-code/CLAUDE.md` | 企业策略 | 全组织 |
| 用户级 | `~/.claude/CLAUDE.md` | — | 个人所有项目 |
| 项目级 | `./CLAUDE.md` | `.cursor/rules/*.mdc` | 团队（通过 git） |
| 本地级 | `./CLAUDE.local.md` | — | 个人当前项目 |

### 5.2 Path-Scoped Rules（大型/Monorepo 项目必选）

```
.claude/rules/
├── api-conventions.md       # 匹配 src/api/** 
├── testing.md               # 匹配 *.test.ts
├── frontend-react.md        # 匹配 frontend/**/*.tsx
└── database-migrations.md   # 匹配 migrations/**
```

每个规则文件包含 YAML frontmatter 指定 `paths:` 匹配模式。AI 只在读取匹配文件时加载对应规则，极大节省 context。

### 5.3 规则文件编写要点

```markdown
---
description: API 开发约定
globs: src/api/**/*.ts
---
# API 开发规则
## 架构
- API handlers 放在 src/api/handlers/
- 所有 API 响应遵循 { success, data, error } 格式
## 认证
- 使用 middleware/auth.ts 中的 requireAuth 中间件
- JWT token 通过 Authorization header 传递
## 测试
- 每个 handler 必须有对应的 .test.ts 文件
```

**六条编写原则**：
1. 控制在 200 行以内（越长，遵循率越低）
2. 用 Markdown 结构化
3. 具体可验证（"Use 2-space indentation" 而非 "Format code properly"）
4. 只在 AI 重复犯同一错误时才添加规则
5. 每月审查，清理过时内容
6. 规则变更走 PR review 流程

社区资源 [awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules) 收录了数百个验证过的规则模板，覆盖主流框架。

---

## 六、持续迭代策略——测试、CI/CD、技术债务、安全

### 6.1 Spec-Driven Development（规范驱动开发）

Osmani 提出的核心方法论，是把"模糊需求"转化为"可验证约束"：

1. **先写 Spec**：明确定义输入、输出、边界条件、错误处理
2. **AI 在 Spec 约束下生成代码**
3. **同时生成对应测试用例**
4. **运行测试验证**
5. **人类审查覆盖率和边界**

### 6.2 分层测试策略

| 层级 | 目的 | 工具 | AI 辅助方式 |
|------|------|------|------------|
| 单元测试 | 验证函数正确性 | Jest, PyTest | AI 生成用例，人工审查边界 |
| 集成测试 | 模块间接口一致性 | Supertest | AI 生成框架，人工补场景 |
| E2E 测试 | 用户流程完整可用 | Playwright, Cypress | AI 生成脚本，人工验业务 |
| **回归测试** | **防止"两步退回"** | **CI 自动运行** | **必选项** |

### 6.3 CI/CD 管道——自动化守门人

```
Git Push
  │
  ├─ Stage 1: 预检 ─── Commit 规范 / 分支保护 / 依赖安全扫描
  ├─ Stage 2: 静态分析 ─ Linter / 类型检查 / SonarQube / Snyk 漏洞扫描 / Secret 检测
  ├─ Stage 3: 测试 ──── 单元测试(>80%覆盖) / 集成测试 / E2E / 性能回归
  └─ Stage 4: 构建部署 ─ Docker 镜像 / 蓝绿或金丝雀 / 健康检查 / 自动回滚
```

**关键规则：AI 生成代码绝不允许直接推送到 main 分支。**

### 6.4 技术债务防控

| 策略 | 做法 | 工具 |
|------|------|------|
| 强制代码审查 | 拒绝 "Accept All"，逐行审查 diff | Cursor diff review, GitHub PR |
| 静态分析门禁 | CI 中不通过则拒绝合并 | SonarQube, ESLint, mypy |
| 架构决策记录 (ADR) | 记录重要决策的上下文 | ADR Tools |
| 频繁提交 | 每完成小功能就提交 | Conventional Commits |
| 定期"技术债清偿"迭代 | 每 2-3 个功能迭代后安排重构迭代 | AI 辅助重构 + 人工验证 |
| 代码所有权 | 核心模块指定人工 owner | GitHub CODEOWNERS |

### 6.5 安全审计

AI 生成代码的常见安全漏洞：输入验证缺失、认证/授权薄弱、SQL 注入、XSS、敏感信息硬编码。

**安全左移六层防线**：
1. **IDE 实时检测**：Snyk for IDE, SonarQube for IDE
2. **Pre-commit Hook**：gitleaks/TruffleHog 检测密钥泄露
3. **CI SAST**：SonarQube, CodeQL, Snyk Code
4. **CI SCA**：Snyk Open Source, Dependabot 检测依赖漏洞
5. **审查阶段**：认证/支付/数据处理模块强制专家审查
6. **部署后**：DAST 定期扫描 + 异常监控

### 6.6 代码审查流程

```
Step 1: AI 自动预审 ── Linter / SonarQube / 类型检查 / 自动化测试
Step 2: AI 辅助审查 ── AI 生成"修改摘要" / 标记风险 / 检查兼容性
Step 3: 人工重点审查 ── 架构一致性 / 业务逻辑 / 安全敏感代码 / 隐性上下文验证
Step 4: 合并 ──────── 所有人工审查意见必须解决后才能合并
```

> Osmani 警告：*"如果写代码的是 AI、审代码的也是 AI，而人类并未仔细理解代码内容，那我们就无法确定最终到底上线了什么。"*

### 6.7 版本控制策略

- **Commit 规范**：Conventional Commits + 标注 `[AI-assisted]`，每个 commit 控制在 200 行以内
- **分支保护**：main 禁止 force push，必须 PR + CI + 至少一人审查
- **AI 实验分支**：命名如 `ai/sprint-xxx`，生命周期不超过一周
- **回滚机制**：部署保留至少 3 个历史版本，数据库变更必须可逆

---

## 七、案例与社区经验

### 7.1 Karpathy 的自我否定

2025年10月，Karpathy 在开发 nanochat（约 8000 行代码）时公开承认 AI 工具"完全没有帮助"，最终亲手完成所有代码。nanochat 涉及分词→预训练→微调的复杂依赖链，AI 无法全局把控。

> *"Vibe Coding 对于一次性的周末项目来说还不错，但对复杂项目完全不够用。"*

### 7.2 METR 实验：AI 反而让开发者变慢

- 16 位资深开发者，大型代码库真实任务
- **预期**：AI 工具减少 24% 完成时间
- **实际**：完成时间**增加 19%**
- 时间消耗在：引导 AI、等待回应、修复 AI 错误

### 7.3 Fastly 调查

**95% 的开发者**需要花额外时间修复 AI 生成的代码，有些人表示修复时间比省下的还多。

### 7.4 创业团队教训

某团队用 Vibe Coding 快速做出 MVP 获得融资，后续迭代发现代码无法维护，推倒重来花三个月重写，错过市场窗口。

### 7.5 "两步退回"噩梦

最常见的失败模式：让 AI 加新功能 D，它不仅没做好 D，还把原来能用的 A、B、C 改坏了。因为 AI 每次生成代码不"记住"之前的设计意图。

### 7.6 六大失败模式总览

| # | 失败模式 | 根因 | 解法 |
|---|---------|------|------|
| 1 | 两步退回 | AI 不记住之前设计意图 | 频繁提交 + 回归测试 |
| 2 | 隐性上下文缺失 | AI 不懂代码背后的"为什么" | CLAUDE.md + ADR |
| 3 | 技术债累积 | "Accept All" 不审查 | 强制逐行审查 |
| 4 | 安全漏洞 | AI 不主动考虑安全 | 安全左移六层防线 |
| 5 | 审查瓶颈 | 产出 10 倍但审查者没增加 | 分层 CI + AI 预审 |
| 6 | 心流打断 | 频繁切换角色消耗心理能量 | 探索→规划→实现 四阶段 |

---

## 八、从 MVP 到大型项目的策略演变

```
阶段一：MVP/原型
├── 完全适用 Vibe Coding，快速验证想法
├── 工具：Bolt.new, v0, Cursor
└── ⚠️ 不要在此阶段代码上构建生产系统

阶段二：原型→产品化（危险过渡期）
├── 最常见的失败发生在此
├── 策略：准备推倒重来，将原型视为"需求验证文档"
└── 用专业团队重新设计架构

阶段三：生产级开发
├── AI 辅助工程模式：人类主导，AI 加速
├── Spec-Driven Development
├── 核心功能人工编写，边缘功能 AI 生成 + 审查
└── 完整 CI/CD + 安全审计

阶段四：长期维护
├── 严格代码审查机制
├── 记录所有 AI 相关决策
├── 持续偿还技术债
└── 自动化测试和安全审计常态化
```

---

## 九、Prompt Engineering 速查

### 9.1 精确度对比

| 维度 | 模糊 | 精确 |
|------|------|------|
| 范围 | "add tests" | "add unit tests for src/utils/validator.ts, covering empty input, null, Unicode. use vitest. run tests after." |
| 约束 | "refactor this" | "refactor auth.ts to async/await. keep same API surface. run npm test and fix failures." |
| 参考 | "add endpoint" | "add POST /api/users/follow following pattern in like.ts. include auth middleware." |
| 验证 | "fix bug" | "fix 401 after token refresh. error log: [paste]. write regression test. run full suite." |

### 9.2 委派策略

- **简单任务**：直接描述，一步到位
- **研究任务**：委派给 subagent，避免污染主 context
- **大型重构**：用 Dynamic Workflow 编排多 agent
- **不确定任务**：先用 Plan Mode 探索

---

## 十、行动指南清单

### 个人开发者
- [ ] 创建 `CLAUDE.md`（或 `.cursor/rules/`），用 `/init` 生成初始版本
- [ ] 采用"探索→规划→实现→提交"四阶段工作流
- [ ] 每个 Prompt 包含验证条件（测试、构建、lint）
- [ ] 监控 context 使用量，适时 `/compact` 或 `/clear`
- [ ] 研究性任务委派给 subagent
- [ ] 永远不要 "Accept All"——逐行审查 AI 生成的代码

### 团队
- [ ] 将规则文件纳入版本控制
- [ ] 制定团队编码规范并转化为 AI 规则
- [ ] 使用 Managed Settings 统一安全策略
- [ ] 设置 Spend Limits 和监控
- [ ] 每月 review 规则文件
- [ ] 建立 AI 代码 Code Review 流程（AI 生成必须人审）
- [ ] 每 2-3 个功能迭代安排"技术债清偿"迭代

### 企业/大型项目
- [ ] 采用 Path-Scoped Rules 按模块拆分规则
- [ ] 使用 Dynamic Workflows 处理大规模迁移/审计
- [ ] 配置 Hooks 实现自动化质量门禁
- [ ] 部署完整 CI/CD：静态分析 + SAST + SCA + E2E + 回归
- [ ] 安全左移：IDE 检测 → Pre-commit → CI → 审查 → DAST
- [ ] 用 OpenTelemetry 导入可观测性平台
- [ ] 标注 AI 相关 commit `[AI-assisted]`
- [ ] CODEOWNERS 强制核心模块人工审查

---

## 十一、核心原则总结

1. **永远不要 "Accept All"**——逐行审查，理解每一行在做什么
2. **Spec-Driven Development**——先写规范，再让 AI 在约束下生成
3. **CI 是最后防线**——静态分析 + SAST + SCA + 全量测试 = 不通过不合入
4. **安全左移**——开发阶段就集成安全检测
5. **小步快跑**——频繁提交、小批量迭代、每次改动控制在可审查规模
6. **AI 是副驾驶不是机长**——保持人类主导权
7. **定期清偿技术债**——每 2-3 个功能迭代后安排重构迭代
8. **Context Engineering > Prompt Engineering**——为 AI 提供完整上下文

> **最终结论**：Vibe Coding 适合原型验证和周末项目。对于需要持续迭代的大型项目，必须转向 **AI 辅助工程**——人类保持主导权，AI 作为加速器，配合 Spec-Driven Development、完善的测试/CI/CD/安全审计体系和严格的代码审查流程。

---

## 信息来源

| # | 来源 | URL | 语言 |
|---|------|-----|------|
| 1 | Andrej Karpathy 原始推文 | twitter.com/karpathy/status/1886192184808149383 | EN |
| 2 | Simon Willison — Vibe Coding 澄清 | simonwillison.net/2025/Mar/19/vibe-coding/ | EN |
| 3 | IBM Think — What is Vibe Coding? | ibm.com/think/topics/vibe-coding | EN |
| 4 | Anthropic Claude Code Best Practices | code.claude.com/docs/en/best-practices | EN |
| 5 | Claude Code Memory | code.claude.com/docs/en/memory | EN |
| 6 | Claude Code Context Window | code.claude.com/docs/en/context-window | EN |
| 7 | Claude Code Sub-agents | code.claude.com/docs/en/sub-agents | EN |
| 8 |