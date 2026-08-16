# R-121 CLAUDE.md 撰写要点与多Agent架构开发质量提升方案

> 研究日期：2026-06-28 | 分类：06-开发实践 | 复杂度：中等
> 研究员：research-lead | 基于 R-120 延伸调研
> 关联报告：R-120 Claude Code 在 ACP 多 Agent 架构下代码生成质量研究

## 摘要

本报告解决两个问题：(1) 如何撰写高质量的 CLAUDE.md 项目指令文件；(2) 在我们的架构（主 Agent → ACP → Claude Code，不经过 dev-lead）下，如何系统提升开发质量。核心结论：**CLAUDE.md 是 ACP 直连模式下最重要的质量杠杆**——由于绕过了 dev-lead 的三层质量门禁，CLAUDE.md + 自检循环 + 任务原子化是保障代码质量的三大支柱。

---

## 一、架构澄清：主 Agent → ACP → Claude Code

### 1.1 当前实际架构

```
用户需求
  ↓
主 Agent (main)
  ├──→ sessions_spawn({ runtime: "acp" })  ← 直连 Claude Code
  │     ↓
  │    Claude Code (ACP harness)
  │     ↓
  │    代码生成 / 文件编辑 / 命令执行
  │
  └──→ sessions_spawn({ agentId: "dev-lead" })  ← 经过开发主管
        ↓
       dev-lead (编排者，无 write/exec 权限)
         ├──→ dev-designer (设计 + 脚手架)
         ├──→ dev-coder (编码 + 执行)
         └──→ dev-qa (测试 + 验证)
```

**关键区别**：
- **ACP 直连模式**（主 Agent → Claude Code）：主 Agent 直接通过 ACP 协议调度 Claude Code，没有 dev-lead 的质量门禁（Feature Gate / Regression Gate / Clean State Gate）
- **dev-lead 模式**（主 Agent → dev-lead → dev-coder/dev-qa）：三层质量门禁强制执行，但流程更重

### 1.2 ACP 直连模式的质量风险

基于 R-120 的研究发现，ACP 直连模式存在以下质量风险：

| 风险 | 严重程度 | 来源 |
|------|----------|------|
| 无独立 QA 验证 | 🔴 高 | dev-qa 被绕过 |
| 无 Clean State 检查 | 🔴 高 | Gate 3 被绕过 |
| 无 PRODUCT.md 一致性检查 | 🟡 中 | 单一真相源缺失 |
| 10-20% 功能性问题率 | 🔴 高 | R-120 §2.2 |
| 上下文退化（~50K token 后） | 🟡 中 | R-120 §2.3 |
| CLAUDE.md 被忽略（system-reminder 机制） | 🟡 中 | HumanLayer 发现 |

### 1.3 为什么仍然使用 ACP 直连

- **速度**：简单任务无需走完 dev-lead 的 Flow A/B/C 全流程
- **成本**：减少 agent 层级 = 减少 token 重复传递
- **灵活性**：适合原型开发、快速修复、单文件改动
- **并行能力**：ACP harness 内部支持 Coordinator/Worker 模式

---

## 二、CLAUDE.md 撰写要点（核心交付物）

### 2.1 CLAUDE.md 的本质与限制

**CLAUDE.md 是什么**：
- Claude Code 会话启动时自动读取的项目级指令文件
- 作为 system-reminder 注入到 user message 中
- 优先级：project > directory > global > built-in

**关键限制（HumanLayer 发现）**：
Claude Code 注入了以下 system-reminder：
> "IMPORTANT: this context may or may not be relevant to your tasks. You should not respond to this context unless it is highly relevant to your task."

这意味着 **Claude 会自主判断 CLAUDE.md 内容是否相关**。文件中不普遍适用的内容越多，Claude 忽略全部指令的概率越高。

**指令容量限制**：
- 前沿思考 LLM 可靠遵循的指令上限：**~150-200 条**
- Claude Code 系统 prompt 已占用 ~50 条指令
- 意味着 CLAUDE.md 实际可用指令预算：**~100-150 条**
- 指令越多，遵循质量均匀下降（不是只忽略后面的，而是全部一起退化）

### 2.2 撰写七大原则

#### 原则 1：少即是多（Less is More）
- **目标**：60-80 行最佳，绝对不超过 200 行
- HumanLayer 自己的 CLAUDE.md 不到 60 行
- 每一条指令都要问："这对每个会话都普遍适用吗？"
- 不确定是否该写的 → 不写

#### 原则 2：以构建/测试命令开头（最高 ROI）
```markdown
## Commands
npm run dev       # 开发服务器
npm run test      # 运行测试
npm run build     # 生产构建
npm run lint      # 代码检查
```
- 这是 Claude 验证自己工作的基础
- 没有 = Claude 无法自检 = 质量降级

#### 原则 3：不复制 linter 规则
- ❌ "使用 2 空格缩进"、"函数名用 camelCase"
- ✅ 这些交给 ESLint/Prettier/Biome 自动处理
- Claude 是昂贵的推理引擎，不是廉价 linter
- LLM 是上下文学习者——给定代码库搜索能力，它会自动遵循现有模式

#### 原则 4：渐进式披露（Progressive Disclosure）
```
项目根/
├── CLAUDE.md                    # 精简核心指令（<80行）
├── agent_docs/
│   ├── building_the_project.md  # 构建细节
│   ├── running_tests.md         # 测试策略
│   ├── code_conventions.md      # 编码规范
│   ├── service_architecture.md  # 架构决策
│   └── database_schema.md       # 数据模型
```
- CLAUDE.md 中用一句话描述每个文件 + 何时读取
- Claude 按需读取，不污染每次会话的上下文

#### 原则 5：只写非显而易见的规则
- ❌ "写干净的代码"（显然，浪费指令）
- ❌ "使用 TypeScript"（看 tsconfig 就知道）
- ✅ "数据库迁移文件不可手动修改，只通过 prisma migrate 生成"
- ✅ "API 路由必须返回 { success, data, error } 结构"
- ✅ "禁止在 src/lib/server 中导入客户端组件"

#### 原则 6：使用正面指令
- ❌ "不要使用 var" → ✅ "使用 const/let 声明变量"
- ❌ "不要忘记错误处理" → ✅ "所有 async 函数必须使用 try/catch"
- 大模型在否定框架上表现更差

#### 原则 7：标注禁止区域
```markdown
## Forbidden
- IMPORTANT: Never modify the migrations/ directory directly
- YOU MUST NOT commit .env files
- Never touch the generated/ folder (auto-generated)
```
- 用 IMPORTANT/YOU MUST 强调（但只在真正关键的规则上，全部都是 IMPORTANT = 没有重要的）

### 2.3 推荐结构模板（适配我们的项目）

```markdown
# [项目名]

一句话描述项目是什么、用什么技术栈。

## Commands
```bash
npm run dev       # 开发服务器
npm run test      # 运行测试
npm run build     # 生产构建
npm run lint      # 代码检查（自动修复）
```

## Project Structure
```
src/
  routes/         # API 路由
  models/         # 数据模型
  services/       # 业务逻辑
  components/     # UI 组件（无状态）
tests/            # 测试文件
```

## Conventions
- 所有 async 函数必须使用 try/catch
- API 返回格式：{ success: boolean, data: any, error?: string }
- 错误处理：使用 AppError 类（src/lib/errors.ts:12）
- 测试文件与源文件同名：user.ts → user.test.ts

## Forbidden
- IMPORTANT: Never modify migrations/ directly
- Never commit .env or *.local files

## Reference Documents
- 架构决策：@agent_docs/architecture.md（设计新功能时读取）
- 数据模型：@agent_docs/database.md（修改 schema 时读取）
- API 规范：@agent_docs/api-conventions.md（新增端点时读取）

## Verification（自检要求）
- 修改代码后 MUST 运行 npm test，修复所有失败
- 新增 API 端点后 MUST 运行 npm run lint
- 如果测试无法通过，在回复中说明原因，不要跳过
```

### 2.4 维护策略：活文档机制

**反馈循环法**（Builder.io 推荐，Boris Cherny 分享）：
1. Claude 犯错 → 立即纠正
2. 告诉 Claude："把这条规则加入 CLAUDE.md"
3. Claude 自动更新文件并提交
4. 同样的错误不再重复

**规则修剪**：
- 如果 Claude 反复忽略某条规则 → 文件太长，需要修剪
- 如果 Claude 反复问 CLAUDE.md 已回答的问题 → 表述有歧义，需重写
- 每周/每个迭代周期 review 一次，删除过时/冲突的规则

---

## 三、提升开发质量的可行方案（ACP 直连模式）

### 3.1 方案总览

针对 ACP 直连模式（主 Agent → Claude Code，不经 dev-lead），设计三层质量保障：

```
Layer 1: CLAUDE.md 预防层  ← 项目级指令（写在文件里）
Layer 2: Task Prompt 约束层  ← 任务级指令（写在 spawn 的 task 里）
Layer 3: 后验证层          ← 主 Agent 拿到结果后的验证
```

### 3.2 Layer 1：CLAUDE.md 预防层

**行动项**：为每个活跃项目编写/优化 CLAUDE.md

| 项目 | 当前状态 | 行动 |
|------|----------|------|
| agent-dashboard | 已有基础版本 | 补充 Verification 段、Forbidden 段 |
| ai-tarot | 需检查 | 创建或优化 |
| mysticmirror-styles | 需检查 | 创建或优化 |
| 其他项目 | 需检查 | 创建或优化 |

**关键写入内容**（根据 R-120 §5.1）：
1. 构建/测试命令（最高 ROI）
2. 自检要求（"修改后 MUST 运行测试"）
3. 项目架构简述（帮助 Claude 导航）
4. 禁止区域
5. 按需加载的参考文档列表

### 3.3 Layer 2：Task Prompt 约束层

主 Agent spawn ACP 会话时，在 task 中嵌入以下结构化约束：

```
sessions_spawn({
  runtime: "acp",
  task: `
    [任务描述]
    
    ## 项目上下文
    项目路径：/root/.openclaw/workspace/tools/xxx
    技术栈：[简要说明]
    
    ## 质量要求
    1. 修改后运行测试：npm test（或等效命令）
    2. 如果测试失败，修复直到全部通过
    3. 不要修改与任务无关的文件
    4. 完成后输出：修改了哪些文件、测试结果
    
    ## 禁止
    - 不要修改 migrations/ 目录
    - 不要安装新依赖（除非任务明确要求）
  `
})
```

**为什么要这样写**：
- CLAUDE.md 可能被 Claude 判断为"不相关"而忽略
- Task prompt 是最近的消息，位于 LLM 注意力的末端（recency bias），更可能被遵循
- 显式的质量要求 = Claude 自检的 trigger

### 3.4 Layer 3：后验证层

主 Agent 拿到 Claude Code 的输出后，执行轻量验证：

**最小验证清单**：
1. ✅ 检查 Claude Code 是否报告测试通过（不是"应该可以"而是实际运行了）
2. ✅ 如果涉及关键文件，spawn 一个轻量 dev-qa 或直接 exec 检查
3. ✅ 确认修改范围合理（没有 50 个文件被改动）

**何时升级为 dev-lead 模式**：
| 信号 | 行动 |
|------|------|
| 任务涉及 3+ 文件的功能开发 | 改用 dev-lead |
| 涉及数据库 schema 变更 | 改用 dev-lead |
| 涉及认证/安全相关代码 | 改用 dev-lead |
| 需要跨项目协调 | 改用 dev-lead |
| Claude Code 报告测试失败但声称修复 | spawn dev-qa 验证 |

### 3.5 决策树：何时用 ACP 直连 vs dev-lead

```
任务到来
  ↓
是简单 bug 修复 / 单文件改动 / 原型验证？
  ├─ YES → ACP 直连模式
  │         ↓
  │         项目有 CLAUDE.md？
  │         ├─ YES → spawn ACP，task 中嵌入质量约束
  │         └─ NO  → 先写 CLAUDE.md（10分钟），再 spawn ACP
  │
  └─ NO（多文件/复杂功能/需要 QA）
            ↓
            dev-lead 模式（三层质量门禁）
```

---

## 四、自检反馈循环设计（R-120 核心建议的具体实现）

### 4.1 为什么自检循环是 2-3x 质量提升的关键

R-120 §5.2 引述 Boris Cherny（Claude Code 团队）的建议：给 Claude Code 运行测试 → 修复失败的反馈循环，可带来 2-3 倍质量提升。原理：

1. **客观验证**：测试通过/失败是确定性信号，不依赖 LLM 自评
2. **自动纠错**：Claude 看到失败后会自动调整，减少 10-20% 的功能性 bug
3. **上下文锚定**：测试输出让 Claude 聚焦于具体问题，而非泛泛推理

### 4.2 在 CLAUDE.md 中嵌入自检循环

```markdown
## Verification Protocol
1. After ANY code change, run: `npm test`
2. If tests fail:
   a. Read the error message carefully
   b. Fix the root cause (not the symptom)
   c. Re-run tests until ALL pass
3. If a test seems wrong, explain why before modifying it
4. Report final test output in your completion summary
```

### 4.3 在 Task Prompt 中强制执行

```
## 强制要求
完成代码修改后，YOU MUST：
1. 运行 `npm test`（或 `python -m pytest` / `go test ./...`）
2. 粘贴完整测试输出
3. 如果有失败，修复后重新运行
4. 只有全部通过才能报告完成
```

---

## 五、实施路线图

### Phase 1：立即执行（1-2 小时）
- [ ] 为 agent-dashboard 项目优化 CLAUDE.md（已有基础版）
- [ ] 为其他活跃项目（ai-tarot, mysticmirror-styles）创建 CLAUDE.md
- [ ] 建立统一的 CLAUDE.md 模板（基于 §2.3）

### Phase 2：流程改进（本周内）
- [ ] 在主 Agent 的 ACP spawn 模板中加入质量约束段（§3.3）
- [ ] 建立决策树判断逻辑：何时用 ACP 直连 vs dev-lead（§3.5）
- [ ] 为每个新项目初始化时强制创建 CLAUDE.md

### Phase 3：持续优化（持续）
- [ ] 每次 Claude Code 犯错后，将纠正加入 CLAUDE.md
- [ ] 每两周 review CLAUDE.md，删除过时/无效规则
- [ ] 追踪 ACP 直连模式的质量指标（成功率、返工率）

---

## 六、知识缺口

1. **CLAUDE.md 在 ACP 模式下的加载行为**：ACP harness 是否完整加载 CLAUDE.md？是否有额外限制？
2. **Hooks 在 ACP 模式下的可用性**：PreToolUse/PostToolUse hooks 是否在通过 OpenClaw ACP 调度时仍然生效？
3. **ACP 模式下的质量基线数据**：需要积累实际使用数据来对比 ACP 直连 vs dev-lead 的质量差异

---

## 七、来源列表

| ID | 来源 | URL | 关键贡献 |
|----|------|-----|----------|
| S01 | HumanLayer - Writing a good CLAUDE.md | https://www.humanlayer.dev/blog/writing-a-good-claude-md | system-reminder 忽略机制、指令容量限制、渐进式披露 |
| S02 | Builder.io - How to Write a Good CLAUDE.md | https://www.builder.io/blog/claude-md-guide | 活文档维护策略、IMPORTANT 前缀用法 |
| S03 | TurboDocx - CLAUDE.md Best Practices | https://www.turbodocx.com/blog/how-to-write-claude-md-best-practices | 快速参考清单、Starter 模板 |
| S04 | maketocreate.com - 2026 Complete Guide | https://maketocreate.com/claude-md-best-practices-the-complete-2026-guide/ | 12 条实践规则、上下文退化数据 |
| S05 | amitray.com - Ultimate Guide 2026 | https://amitray.com/best-practices-for-claude-md/ | 系统化结构模板 |
| S06 | Avinash Sangle - CLAUDE.md That Actually Work | https://avinashsangle.com/blog/claude-md-guide | 60-80 行最佳、正面指令原则 |
| S07 | gradually.ai - Perfect CLAUDE.md Template | https://www.gradually.ai/en/claude-md | 分层加载机制、活文档理念 |
| S08 | computingforgeeks - .claude Directory Guide | https://computingforgeeks.com/claude-code-dot-claude-directory-guide/ | 完整 .claude 目录结构 |
| S09 | jdhodges.com - Project Instructions | https://www.jdhodges.com/blog/claude-code-claudemd-project-instructions/ | 三层 scope（User/Project/Managed） |
| S10 | Claude Code 官方 Best Practices | https://code.claude.com/docs/en/best-practices | 官方建议：验证优先、上下文管理 |
| S11 | R-120 研究报告（内部） | shared/results/06-开发实践/R-120-ClaudeCode在ACP多Agent架构下代码生成质量研究.md | 基准数据、故障模式、竞品对比 |
| S12 | claude-harness.dev - Multi-Agent Orchestration | https://claude-harness.dev/en/articles/08-multi-agent | Coordinator/Worker 模式源码分析 |
| S13 | Hacker News 讨论 | https://news.ycombinator.com/item?id=46098838 | 社区真实体验：50% 遵循率 |
| S14 | GitHub - Claude Multi-Agent Architecture Template | https://github.com/mnzralee/claude-multi-agent-architecture | 14 agent + 8 skill 生产级模板 |
| S15 | techsy.io - 9 Rules for 2026 | https://techsy.io/en/blog/claude-md-best-practices | 指令预算、AGENTS.md 决策 |

---

## 八、方法论反思

**本研究的优势**：
- 直接基于 R-120 的深度调研成果，数据基础扎实
- 结合了实际架构分析（代码级验证了 main → ACP → Claude Code 的链路）
- 多来源交叉验证（HumanLayer + Builder.io + 官方文档 + 社区讨论）

**局限性**：
- CLAUDE.md 的实际效果缺乏严格对照实验数据（业界普遍缺乏）
- 社区报告的"50% 遵循率"是主观体验，非受控实验
- ACP harness 的 CLAUDE.md 加载行为基于文档推断，未做源码级验证
