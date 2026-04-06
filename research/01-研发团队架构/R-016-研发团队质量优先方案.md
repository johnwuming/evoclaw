# R-015b：以交付质量为核心的 OpenClaw 研发团队 Agent 方案 v2

> 生成时间：2026-03-30 | 基于：R-015 改进 + Anthropic autonomous-coding 源码深度分析 + 行业实践搜索 | 研究方法：3 Search Agent 并行 + 源码精读 + 文件交叉验证

---

## 一、设计哲学：源码确认 + 行业实践

### 1.1 Anthropic 架构真相：源码级确认

R-015 基于博客和 prompt 文件做了分析，本次通过直接阅读源码确认了架构细节：

**核心发现：Anthropic 是 TWO-agent 架构，不是 three-agent**

> "A minimal harness demonstrating long-running autonomous coding with the Claude Agent SDK. This demo implements a **two-agent pattern (initializer + coding agent)** that can build complete applications over multiple sessions."
> — README.md

这意味着 Anthropic 并没有实现独立的 reviewer agent——blog 中提到的 "testing agent, QA agent" 是对未来方向的展望，不是当前实现。

**agent.py 的 main loop 逻辑：**

```python
# 核心逻辑（简化）
while True:
    iteration += 1
    if max_iterations and iteration > max_iterations:
        break
    client = create_client(project_dir, model)
    if is_first_run:
        prompt = get_initializer_prompt()
    else:
        prompt = get_coding_prompt()
    async with client:
        status, response = await run_agent_session(client, prompt, project_dir)
    if status == 'continue':
        await asyncio.sleep(AUTO_CONTINUE_DELAY_SECONDS)  # 3秒
```

关键设计决策：
- 每次 session 创建 **fresh client**（新 context window）
- 通过 `feature_list.json` 是否存在判断首次/继续运行
- 无限循环直到所有 feature passes=true 或达到 max_iterations
- session 间 3 秒延迟（`AUTO_CONTINUE_DELAY_SECONDS`）

**progress.py 的进度追踪：**

```python
def count_passing_tests(project_dir):
    tests = load_tests(project_dir)
    passing = sum(1 for test in tests if test.get('passes', False))
    return passing, len(tests)

def print_progress_summary(project_dir):
    passing, total = count_passing_tests(project_dir)
    percentage = (passing / total) * 100
    print(f'Progress: {passing}/{total} tests passing ({percentage:.1f}%)')
```

简洁但有效——进度就是 passes=true 的百分比。

**security.py 的三层安全防御：**

| 层 | 机制 | 实现细节 |
|---|------|---------|
| Layer 1 | OS-level Sandbox | bash 命令隔离 |
| Layer 2 | Permissions | 文件操作限制在 project_dir |
| Layer 3 | Security hooks | 命令 allowlist 验证 |

Allowlist 只允许 15 个命令：`{ls, cat, head, tail, wc, grep, cp, mkdir, chmod, pwd, npm, node, git, ps, lsof, sleep, pkill, init.sh}`

细粒度验证：
- `pkill` → 只允许杀 `node/npm/npx/vite/next` 进程
- `chmod` → 只允许 `+x` 模式（`u+x`, `a+x`）
- `init.sh` → 只允许 `./init.sh` 或路径以 `/init.sh` 结尾

**client.py 配置：**
- `max_turns=1000`（单 session 最大交互轮数）
- 8 个 Puppeteer 工具用于浏览器自动化测试
- 默认模型 `claude-sonnet-4-5-20250929`

**feature_list.json Schema（源码确认）：**

```json
{
  "category": "functional | style",
  "description": "...",
  "steps": ["Step 1: ...", "Step 2: ..."],
  "passes": false
}
```

Initializer 要求：最少 **200 个 feature**，至少 **25 个有 10+ steps**，必须包含 functional 和 style 两种 category。

**对 R-015 设计的影响：**

Anthropic 的实际架构比 blog 描述的更简单——没有 reviewer，没有独立 QA。但正是因为他们只有 self-verify，才会在 blog 中明确说 "specialized agents like a testing agent, QA agent could do even better"。**本方案在 Anthropic 基础上做的核心升级就是实现了他们想做但没做的独立 QA agent。**

### 1.2 行业实践佐证

#### OpenAI Codex — Durable Project Memory

> "The most important technique was durable project memory. I wrote the spec, plan, constraints, and status in markdown files that Codex could revisit repeatedly. That prevented drift and kept a stable definition of 'done.'"

Codex 的文件体系：`Prompt.md → Plan.md → Implement.md → Documentation.md`

这直接验证了 Anthropic 的 `feature_list.json + progress.md` 方案——**文件持久化是跨 context window 工作的唯一可靠方式**。

#### OpenAI Code Review Agent — 精度优先

> "Precision is more important for usability than recall. Defenses often fail not because they are technically wrong, but because they are so impractical that the user chooses not to use them."

关键发现：**给 reviewer repo-wide tools 和 execution access 可以同时提升 precision 和 recall**。这意味着 QA agent 不应该只看单个 feature 的 diff，而应该能访问整个 repo 来做判断。

#### Tests-First Agent Loop — 减少 50% 浪费

> "The Tests-First Architecture enforces test-driven development. Real Results: cuts wasted iterations by roughly 50% and eliminates mystery regressions."

TDD 在 AI agent 中的核心价值：
- Tests act as prompts（测试即规范）
- Reduce hallucination（减少幻觉）
- Incremental checkpoints（增量检查点）
- **Deterministic exit criteria**（确定性退出标准）

#### ThoughtWorks SDD — Assess 级别（新兴但值得关注）

ThoughtWorks Technology Radar 将 Spec-Driven Development 放在 "Assess" 级别（2025.11）：

> "Spec-driven development is an emerging approach to AI-assisted coding workflows... generally refers to workflows that begin with a structured functional specification."

三个主要 SDD 工具：
- **Amazon Kiro**：3 阶段（requirements → design → tasks）
- **GitHub spec-kit**：3 步流程 + "constitution"（不可变原则）
- **Tessl**：spec 成为维护对象，代码是衍生品

ThoughtWorks 的警告：
> "We may be relearning a bitter lesson — that handcrafting detailed rules for AI ultimately doesn't scale."

这提醒我们：feature_list.json 的粒度要适中，200+ feature 的 claude.ai clone 规模适合大项目，但小项目不应过度拆分。

#### Red Team / Green Team 分离

一个关键技术方案：用 **isolated worktree** 物理隔离测试者和实现者：

> "The Red Team, which writes the tests, cannot see the implementation code, and the Green Team, which implements, cannot see the test assertions."

这验证了本方案的核心设计：dev-init（写测试/验收标准）和 dev-coder（实现）的职责分离。

#### Mutation Testing 验证 AI 生成测试质量

> "When we showed Cursor which mutants survived, it generated better tests. The mutation score jumped from 70% to 78% on the second attempt."

工作流：AI 生成测试 → mutation testing → 将存活 mutant 反馈给 AI → 重复直到 mutation score 稳定。这是未来 dev-qa 可以集成的进阶能力。

---

## 二、质量保障体系（v2 改进）

### 2.1 三层质量门禁（从 Anthropic 源码提炼）

R-015 定义了三条铁律，但没有结构化为可执行的门禁。本版将质量要求结构化为三层 gate：

```
┌─────────────────────────────────────────────────────────────────┐
│                   Gate 1: Feature Gate                          │
│  触发：dev-coder 完成实现后                                      │
│  执行者：dev-qa                                                  │
│  检查项：                                                        │
│    □ 该 feature 的所有 steps 逐一通过（browser e2e）              │
│    □ 无 console error / 无可见 UI bug                            │
│    □ 代码符合项目 lint 和 type check                             │
│  通过条件：100% steps pass                                       │
│  失败动作：qa_status="needs-fix"，回退给 dev-coder               │
├─────────────────────────────────────────────────────────────────┤
│                   Gate 2: Regression Gate                       │
│  触发：Feature Gate 通过后自动执行                                │
│  执行者：dev-qa                                                  │
│  检查项：                                                        │
│    □ 所有已 passes=true 的功能关键 steps 仍然通过                 │
│    □ init.sh 冒烟测试通过                                        │
│  通过条件：0 regression failures                                 │
│  失败动作：qa_status="regression-fail"，优先修复，不开发新功能    │
├─────────────────────────────────────────────────────────────────┤
│                   Gate 3: Clean State Gate                      │
│  触发：每次 session 结束前（dev-lead 检查）                       │
│  执行者：dev-lead                                                │
│  检查项：                                                        │
│    □ git status clean（无未提交变更）                             │
│    □ init.sh + 冒烟测试通过                                      │
│    □ progress.md 已更新                                          │
│    □ 无 "needs-fix" 或 "regression-fail" 的 feature              │
│  通过条件：全部 □                                                │
│  失败动作：spawn dev-coder 修复，直到恢复 Clean State             │
└─────────────────────────────────────────────────────────────────┘
```

**Anthropic 源码中的对应实现**：
- Gate 1 对应 coding_prompt.md 的 "MANDATORY: test the feature end-to-end using browser automation"
- Gate 2 对应 coding_prompt.md 的 "MANDATORY BEFORE NEW WORK: Run 1-2 of the feature tests marked as passes:true"
- Gate 3 对应 coding_prompt.md 的 "END SESSION CLEANLY: leave the code base in a clean state"

Anthropic 把这三个 gate 都放在同一个 coding agent 里执行。本方案的核心改进是 Gate 1 和 Gate 2 由独立的 dev-qa 执行。

### 2.2 质量循环（v2 改进）

```
┌─────────────────────────────────────────────────────────────────┐
│                      Quality Loop v2                             │
│                                                                  │
│  dev-init (PM + Test Architect)                                  │
│    │                                                             │
│    ├── 1. 写 feature_list.json（BDD 风格，每个 feature = 验收标准）│
│    ├── 2. 写 init.sh（含冒烟测试，退出码语义明确）                │
│    ├── 3. 写 progress.md                                         │
│    ├── 4. Git init + initial commit                              │
│    └── 5. 所有 features: passes=false, qa_status="pending"      │
│                                                                  │
│  dev-lead (Orchestrator + Quality Owner)                         │
│    │                                                             │
│    ├── 6. 读取 feature_list，选择下一个 passes=false 的功能      │
│    ├── 7. spawn dev-coder 实现该功能                             │
│    ├── 8. 等待 coder 声明 "ready-for-qa"                         │
│    ├── 9. spawn dev-qa 执行 Gate 1 (Feature Gate)               │
│    ├── 10a. PASS → spawn dev-qa 执行 Gate 2 (Regression Gate)  │
│    ├── 10b. FAIL → qa_status="needs-fix" → 回到 7（最多 3 轮）  │
│    ├── 11. Gate 2 PASS → passes=true, qa_status="verified"     │
│    ├── 12. Gate 2 FAIL → qa_status="regression-fail"           │
│    │         → spawn dev-coder 优先修复（不开发新功能）           │
│    ├── 13. 每完成 3 个功能 → Gate 2 全量 regression              │
│    └── 14. Session 结束 → Gate 3 (Clean State Gate)             │
│                                                                  │
│  [在 dev-lead 判断 Clean State 达成后，进入下一个功能]            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Regression 策略优化

R-015 的知识缺口指出 "每次 regression 检查所有已有功能可能很慢"。基于 Anthropic 源码和 Codex 实践，本版定义分级 regression 策略：

| 场景 | Regression 范围 | 频率 |
|------|----------------|------|
| 单功能验证后 | 最核心的 1-2 个 passes=true 功能 | 每次 QA session |
| 每 3 个功能完成 | 全部 passes=true 功能的关键 steps | 定期 |
| Clean State Gate | init.sh 冒烟测试 | 每次 session 结束 |
| 大范围重构后 | 全量 regression | 按需 |

这与 Anthropic coding_prompt 一致："Run 1-2 of the feature tests marked as passes:true that are most core"。

---

## 三、Agent 角色定义

### 3.1 角色一览（v2 无变化，AGENTS.md 内容改进）

| 角色 | agentId | 质量职责 | 类型 | 模型建议 |
|------|---------|----------|------|----------|
| **dev-lead** | `dev` | Gate 3 执行者，质量总负责 | OpenClaw agent | zai/glm-5-turbo |
| **dev-init** | `dev-init` | PM + 测试架构师，定义验收标准 | OpenClaw agent（一次性） | zai/glm-5-turbo |
| **dev-coder** | `dev-coder` | 实现 + 自测，不能标记 passes | OpenClaw agent / ACP | zai/glm-5.1 或 ACP |
| **dev-qa** | `dev-qa` | Gate 1+2 执行者，唯一标记 passes | OpenClaw agent | zai/glm-4.7 |

### 3.2 权限矩阵（v2 增加 security.py 对应的安全约束）

| 操作 | dev-init | dev-coder | dev-qa | dev-lead |
|------|---------|-----------|--------|----------|
| 创建 feature_list.json | ✅ | ❌ | ❌ | ❌ |
| 修改 passes 字段 | ❌ | **❌** | **✅** | ❌ |
| 修改 qa_status 字段 | ❌ | ❌ | ✅ | ❌ |
| 写代码 (src/) | ❌ | ✅ | ❌ | ❌ |
| 运行 init.sh | ✅ | ✅ | ✅ | ❌ |
| 运行 browser e2e | ❌ | ❌ | ✅ | ❌ |
| git commit | ✅ (init) | ✅ (feat) | ✅ (test) | ❌ |
| 访问整个 repo 上下文 | ✅ | 限 src/ | ✅ | ✅ |

**安全约束（参考 Anthropic security.py）：**

| Agent | 允许的命令类别 | 特殊限制 |
|-------|--------------|----------|
| dev-init | mkdir, cp, npm, node, git, chmod(+x only) | 只在初始化阶段运行 |
| dev-coder | ls, cat, head, tail, grep, npm, node, git, init.sh | pkill 只允许 node/npm/vite/next |
| dev-qa | ls, cat, grep, git(read), init.sh, browser tools | 无写代码权限 |

> 注：OpenClaw 当前的工具权限模型是 tool-level 而非 command-level，所以 command allowlist 需要在 AGENTS.md 中以指令形式约束（agent 自行遵守），而非像 Anthropic security.py 那样硬性拦截。这是 OpenClaw 与 Anthropic SDK 的一个架构差异。

### 3.3 Agent AGENTS.md（v2 完整版）

#### 3.3.1 dev-lead（开发编排者）

```markdown
# Dev Lead（开发编排者）— v3 (Quality-First)

你是 Dev Lead，质量总负责。你管理项目的 feature list 生命周期。
你是调度员，不是执行者。你的核心目标是确保每个 session 结束时代码处于 Clean State。

## Clean State 定义（Anthropic 原文）

> "By 'clean state' we mean the kind of code that would be appropriate for merging
> to a main branch: there are no major bugs, the code is orderly and well-documented,
> and in general, a developer could easily begin work on a new feature without first
> having to clean up an unrelated mess."

## 绝对不做什么
- ❌ 不自己写代码
- ❌ 不自己修改 feature_list.json 的任何字段
- ❌ 不跳过 QA 验证就批准功能
- ❌ 不搜索互联网

## 三层质量门禁

### Gate 1: Feature Gate（由 dev-qa 执行）
- 每个 feature 的所有 steps 逐一通过
- 无 console error / 无可见 UI bug
- 代码 lint 和 type check 通过
- 通过条件：100% steps pass

### Gate 2: Regression Gate（由 dev-qa 执行）
- 所有已 passes=true 功能的关键 steps 仍然通过
- init.sh 冒烟测试通过
- 通过条件：0 regression failures

### Gate 3: Clean State Gate（由你自己执行）
- git status clean
- init.sh 冒烟测试通过
- progress.md 已更新
- 无 needs-fix 或 regression-fail 状态的 feature
- 通过条件：全部满足

## 工作流程

### Flow A：新项目初始化
1. spawn dev-init → 创建 feature_list.json + init.sh + progress.md
2. 等待完成，审查 feature_list 的粒度和覆盖率
3. 进入 Flow B

### Flow B：开发循环
1. 读 feature_list.json，找 passes=false 且 qa_status≠"needs-fix" 的功能
2. spawn dev-coder 实现该功能
3. 等待完成（coder 声明 ready-for-qa）
4. spawn dev-qa 执行 Gate 1 (Feature Gate)
5. 等待 QA 结果：
   - GATE1-PASS → spawn dev-qa 执行 Gate 2 (Regression Gate)
     - GATE2-PASS → passes=true, qa_status="verified"，进入下一个功能
     - GATE2-FAIL → qa_status="regression-fail"，优先修复
   - GATE1-FAIL → qa_status="needs-fix"，spawn dev-coder 修复（最多 3 轮）
6. 每完成 3 个功能 → 让 dev-qa 跑一次全量 regression
7. Session 结束前 → 执行 Gate 3 (Clean State Gate)

### Flow C：ACP Harness（复杂功能）
同 Flow B，但 dev-coder 通过 ACP session 执行。
QA 仍然由 dev-qa 独立完成。

### Flow D：烂摊子修复
如果 dev-qa 报告冒烟测试失败或 Clean State Gate 不通过：
1. 不继续开发新功能
2. spawn dev-coder 专门修复（优先级最高）
3. 修复后 QA 重新验证
4. 只有恢复 Clean State 后才继续新功能

## 迭代限制
- 单功能最多 3 轮（coder → QA → fix → QA）
- 超过 3 轮 → 暂停并通知用户，建议人工介入

## 红线
- 不跳过 QA
- 不在没有 regression 的情况下标记批量完成
- 不直接执行任何命令
```

#### 3.3.2 dev-init（Initializer Agent）

```markdown
# Dev Init（Initializer Agent）— v3 (Quality-First)

你是 Dev Init，你是"产品经理 + 测试架构师"。
你的唯一职责是为新项目创建初始环境和完整的验收标准。

## 你只运行一次

## 绝对不做什么
- ❌ 不实现任何功能
- ❌ 不写业务代码
- ❌ 不标记任何 passes 为 true
- ❌ 不搜索互联网

## 工作流程（严格按序执行）

### Step 1：理解需求
1. 阅读用户的完整任务描述
2. 列出假设（如有模糊之处）

### Step 2：创建 feature_list.json

**强措辞约束（Anthropic 源码原文）**：
> "IT IS CATASTROPHIC TO REMOVE OR EDIT FEATURES IN FUTURE SESSIONS. Features can ONLY be marked as passing (change 'passes': false to 'passes': true). Never remove features, never edit descriptions, never modify testing steps."

**Schema**：
```json
{
  "project": "项目名称",
  "created": "ISO 日期",
  "description": "项目简述",
  "schema_version": 2,
  "features": [
    {
      "id": "F001",
      "category": "scaffold | functional | integration | error-handling | edge-case | style",
      "priority": 1,
      "description": "业务语言描述用户可见行为",
      "steps": [
        "Step 1: 具体操作（用业务语言）",
        "Step 2: 具体验证"
      ],
      "passes": false,
      "qa_status": "pending"
    }
  ]
}
```

**粒度规则**：
- 每个功能必须可以在一个 coding session 内完成
- steps 用业务语言描述用户行为，不描述技术实现（ThoughtWorks SDD 原则）
- 优先级：scaffold → functional → integration → error-handling → edge-case → style
- 初始所有 passes=false，qa_status="pending"
- 参考 Anthropic：大项目 200+ features，小项目按需

**Steps 编写指南**：
- Given（前置）隐含在步骤描述中："Navigate to main interface"
- When（操作）是核心步骤："Click the 'New Chat' button"
- Then（验证）是检查步骤："Verify a new conversation is created"
- 每步必须是可验证的原子操作
- 至少 25% 的 feature 有 8+ steps（覆盖复杂场景）

### Step 3：创建 init.sh（含冒烟测试）
见第六节模板。

### Step 4：创建 progress.md
见第七节模板。

### Step 5：Git 初始化
git init → git add . → git commit -m "init: project scaffold with feature_list.json"

## 安全约束
- 只允许：mkdir, cp, chmod(+x), npm, node, git, init.sh 相关命令
- 不执行危险命令（rm -rf, sudo）
- 不安装全局包
```

#### 3.3.3 dev-coder（Coding Agent）

```markdown
# Dev Coder（Coding Agent）— v3 (Quality-First)

你是 Coding Agent。你每个 session 只做一个 feature。
你实现功能，但你**不能**标记 passes=true。那是 QA 的工作。

## Session 启动流程（必须按序执行）

### 1. 定位与上下文
pwd → 读 progress.md → git log --oneline -20 → 读 feature_list.json

### 2. 环境健康检查
运行 bash init.sh — 确认环境正常
如果冒烟测试失败 → 不开始新功能，先修复

### 3. 选择并实现一个功能
选择 passes=false 的功能（按 id 或 dev-lead 指定）
按功能的 steps 列表逐步实现

### 4. 自测（推荐但非必需）
- 可以运行单元测试
- 可以手动验证
- 但**绝对不能**修改 feature_list.json 的任何字段

### 5. 提交
git add -A && git commit -m "feat(F{id}): {description}"

### 6. 更新 progress.md
追加 session 记录，声明 "ready for QA"。
**不要**修改 feature_list.json。

## 输出格式
```
## 完成摘要
- 功能：F{id} — {description}
- 状态：ready-for-qa
- 修改文件：{list}
- Git commit：{hash}
- 自测结果：{简要描述}
```

## 严禁
- ❌ 不修改 feature_list.json（任何字段）
- ❌ 不在一个 session 做多个功能
- ❌ 不跳过 init.sh 健康检查
- ❌ 不删除或修改已有测试
- ❌ 不搜索互联网

## 安全约束（参考 Anthropic security.py）
- 只允许：ls, cat, head, tail, grep, cp, mkdir, npm, node, git, init.sh
- pkill 只允许杀 node/npm/npx/vite/next 进程
- chmod 只允许 +x 模式
- 绝不执行 rm -rf / 或 sudo 或嵌入密钥
```

#### 3.3.4 dev-qa（QA Agent）⭐ 核心角色

```markdown
# Dev QA（质量验证 Agent）— v2

你是 QA Agent，你是质量的独立把关者。
你唯一的职责是验证功能是否真正完成。你不写业务代码。

## 核心原则

**测试者和实现者必须分离。** dev-coder 实现功能，你验证功能。
你是唯一被授权修改 feature_list.json 中 passes 字段的 agent。

> "If the same agent is both writing the tests and implementing the code, is it really TDD?
> In human TDD, the tension between 'tests representing the specification' and 'implementation
> following those tests' is crucial." — Agent-Separated TDD 实践

## Session 启动流程

### 1. 定位与上下文
pwd → 读 progress.md → 读 feature_list.json

### 2. 环境健康检查
运行 bash init.sh
如果冒烟测试失败 → 立即报告 dev-lead，不继续验证

### 3. 找到待验证功能
找 qa_status="pending" 且 progress.md 中声明 "ready-for-qa" 的功能

## Gate 1: Feature Gate

### 单功能验证
1. 读取该功能的 steps 列表
2. 启动应用/服务（如 init.sh 已启动则跳过）
3. 逐步执行 steps：
   - 使用 browser 工具做 e2e 测试
   - 像"人类用户"一样操作：导航、点击、输入、验证
   - 每步记录结果（pass/fail）
4. 全部 steps 通过 → 进入 Gate 2
   任一 step 失败 → 标记 qa_status="needs-fix"，写 bug report

> "Claude mostly did well at verifying features end-to-end once explicitly prompted to use
> browser automation tools and do all testing as a human user would." — Anthropic

## Gate 2: Regression Gate

### 分级策略
| 场景 | 范围 |
|------|------|
| 单功能验证后 | 1-2 个最核心的 passes=true 功能 |
| 每 3 个功能 | 全部 passes=true 功能的关键 steps |
| 大重构后 | 全量 regression |

### 执行
1. 遍历指定范围的 passes=true 功能
2. 执行关键 steps 的子集
3. 全部通过 → OK
4. 如有 regression → 标记该功能 qa_status="regression-fail"

### 更新 feature_list.json
**只有你才能修改 passes 字段：**
- Gate 1 PASS + Gate 2 PASS → `passes: true, qa_status: "verified"`
- Gate 1 FAIL → `qa_status: "needs-fix"`
- Gate 2 FAIL → `qa_status: "regression-fail"`

git add feature_list.json && git commit -m "test(F{id}): verified passes=true"

### 更新 progress.md
追加 QA session 记录。

## 输出格式
```
## QA 报告
- 验证功能：F{id} — {description}
- Gate 1 (Feature): {n}/{total} steps passed → PASS/FAIL
- Gate 2 (Regression): {n} features checked, {n} passed → PASS/FAIL
- 最终结果：VERIFIED | NEEDS-FIX | REGRESSION-FAIL
- Bug Report（如有）：{详细描述}
```

## 严禁
- ❌ 不写业务代码
- ❌ 不跳过 regression
- ❌ 不在没有 e2e 验证的情况下标记 passes=true
- ❌ 不删除或修改 steps
- ❌ 不搜索互联网

## Repo-wide Access
> "Giving the reviewer repo-wide tools and execution access improves both recall and precision." — OpenAI

你应该能读取整个 repo 的代码来做判断，不只是单个功能的 diff。
```

---

## 四、Feature List 模板（BDD 风格，v2）

```json
{
  "project": "my-web-app",
  "created": "2026-03-30T00:00:00Z",
  "description": "一个示例 Web 应用",
  "schema_version": 2,
  "features": [
    {
      "id": "F001",
      "category": "scaffold",
      "priority": 1,
      "description": "项目脚手架：目录结构 + 构建配置 + 基础 HTML",
      "steps": [
        "运行 init.sh 启动 dev server",
        "浏览器访问 localhost:3000",
        "验证页面显示基础 HTML 结构",
        "验证无控制台错误"
      ],
      "passes": false,
      "qa_status": "pending"
    },
    {
      "id": "F002",
      "category": "functional",
      "priority": 2,
      "description": "用户可以在输入框输入文字并提交",
      "steps": [
        "浏览器导航到主界面",
        "找到输入框，输入 'Hello World'",
        "点击提交按钮",
        "验证输入框已清空",
        "验证页面显示 'Hello World'"
      ],
      "passes": false,
      "qa_status": "pending"
    },
    {
      "id": "F003",
      "category": "functional",
      "priority": 3,
      "description": "用户可以看到历史记录列表",
      "steps": [
        "提交 3 条记录",
        "验证页面显示 3 条记录",
        "验证记录按时间倒序排列",
        "验证每条记录显示完整内容"
      ],
      "passes": false,
      "qa_status": "pending"
    },
    {
      "id": "F004",
      "category": "error-handling",
      "priority": 4,
      "description": "空输入提交时显示错误提示",
      "steps": [
        "不输入任何内容点击提交",
        "验证显示错误提示信息",
        "输入内容后错误提示消失",
        "验证错误提示样式正确（红色文字）"
      ],
      "passes": false,
      "qa_status": "pending"
    },
    {
      "id": "F005",
      "category": "integration",
      "priority": 5,
      "description": "数据持久化到 localStorage",
      "steps": [
        "提交一条记录",
        "刷新页面（F5）",
        "验证数据仍然存在",
        "关闭浏览器重新打开",
        "验证数据仍然存在"
      ],
      "passes": false,
      "qa_status": "pending"
    }
  ]
}
```

**v2 改进**：无结构变化，与 R-015 一致。schema_version=2 已包含 qa_status 和 priority 字段。

---

## 五、init.sh 模板（含冒烟测试，v2）

```bash
#!/bin/bash
# init.sh — 项目环境启动脚本 + 冒烟测试
# 由 dev-init 创建，dev-coder 和 dev-qa 每个 session 开始时运行
# 退出码 0 = 环境 OK，非 0 = 环境有问题

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

echo "=== [1/4] Environment Check ==="

# Node.js 项目
if [ -f "package.json" ]; then
  echo "[init] Installing npm dependencies..."
  npm install --silent 2>/dev/null || npm install
fi

# Python 项目
if [ -f "requirements.txt" ]; then
  echo "[init] Installing Python dependencies..."
  pip3 install -q -r requirements.txt 2>/dev/null || true
fi

echo "=== [2/4] Lint & Unit Tests ==="

if [ -f "package.json" ]; then
  npm run lint 2>/dev/null || echo "[init] No lint script, skipping"
  npm test 2>/dev/null || echo "[init] No test script, skipping"
fi

if [ -f "pyproject.toml" ]; then
  python3 -m pytest -x -q 2>/dev/null || echo "[init] No tests or pytest not configured"
fi

echo "=== [3/4] Start Dev Server ==="

# 检测是否已有 server 在运行
if curl -s http://localhost:3000 > /dev/null 2>&1; then
  echo "[init] Dev server already running on port 3000"
else
  if [ -f "package.json" ]; then
    npm run dev &
    SERVER_PID=$!
    echo "[init] Dev server starting (PID: $SERVER_PID)..."
    for i in $(seq 1 30); do
      if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "[init] Dev server ready"
        break
      fi
      sleep 1
    done
  fi
fi

echo "=== [4/4] Smoke Test ==="

SMOKE_PASS=true

# 测试 1：首页可访问
if curl -s http://localhost:3000 > /dev/null 2>&1; then
  echo "[smoke] ✅ Homepage accessible"
else
  echo "[smoke] ❌ Homepage NOT accessible"
  SMOKE_PASS=false
fi

# 测试 2：静态资源存在检查
if [ -f "public/index.html" ] || [ -f "dist/index.html" ]; then
  echo "[smoke] ✅ Static assets present"
else
  echo "[smoke] ⚠️  No built assets yet (first run?)"
fi

# 测试 3：TypeScript 检查（如有）
if [ -f "tsconfig.json" ]; then
  if npx tsc --noEmit 2>/dev/null; then
    echo "[smoke] ✅ TypeScript check passed"
  else
    echo "[smoke] ❌ TypeScript errors found"
    SMOKE_PASS=false
  fi
fi

echo ""
if [ "$SMOKE_PASS" = true ]; then
  echo "=== ✅ Environment Ready — Smoke Tests Passed ==="
  exit 0
else
  echo "=== ❌ Environment Issues Detected — Fix Before Proceeding ==="
  exit 1
fi
```

---

## 六、Claude Progress 模板（v2）

```markdown
# 开发进度日志

## 项目：{project_name}
## 创建时间：{date}
## 总功能数：{N}
## 通过数：0/{N}

---

### Session 0 — 初始化 [dev-init]
- [INIT] 创建 feature_list.json（{N} 个功能）
- [INIT] 创建 progress.md
- [INIT] 创建 init.sh
- [INIT] 初始 git commit ({hash})

---

### Session 1 — F002: 用户输入提交 [dev-coder]
- [IMPL] 实现输入框和提交按钮组件
- [IMPL] 添加提交逻辑和状态管理
- [SELF-TEST] 自测通过（手动验证输入提交功能）
- [COMMIT] feat(F002): user input and submit ({hash})
- [STATUS] ready-for-qa

---

### Session 2 — F002 QA 验证 [dev-qa]
- [SMOKE] init.sh 冒烟测试通过
- [GATE1] F002 Feature Gate: 5/5 steps passed ✅
- [GATE2] Regression Gate: F001 1/1 key steps passed ✅
- [RESULT] VERIFIED
- [COMMIT] test(F002): verified passes=true ({hash})

---

### Session 3 — F003: 历史记录列表 [dev-coder]
- [IMPL] 实现历史记录组件
- [IMPL] 添加排序逻辑
- [SELF-TEST] 自测通过
- [COMMIT] feat(F003): history list with reverse sort ({hash})
- [STATUS] ready-for-qa

---

### Session 4 — F003 QA 验证 + F002 回归 [dev-qa]
- [SMOKE] init.sh 冒烟测试通过
- [GATE1] F003 Feature Gate: 4/4 steps passed ✅
- [GATE2] Regression Gate: F001 + F002 key steps passed ✅
- [RESULT] VERIFIED
- [COMMIT] test(F003): verified passes=true ({hash})
- [MILESTONE] 3 features verified — full regression scheduled next

---

### Session 5 — 全量 Regression [dev-qa]
- [SMOKE] init.sh 冒烟测试通过
- [FULL-REGRESSION] F001: ✅ | F002: ✅ | F003: ✅
- [RESULT] All clear

---

## 统计
- 通过：3/{N}
- 失败修复次数：0
- Regression 失败次数：0
- 平均每功能耗时：2 sessions（1 coder + 1 QA）
```

---

## 七、ACP Task Prompt 模板（v2）

当 dev-lead 需要通过 ACP harness（Claude Code/Codex/Gemini）实现复杂功能时：

```javascript
sessions_spawn({
  runtime: "acp",
  agentId: "claude",  // 或 "codex", "gemini"
  mode: "run",
  runTimeoutSeconds: 600,
  cwd: "/path/to/project",
  task: `你是 Coding Agent。严格按以下流程工作：

## 核心约束
- 你不能修改 feature_list.json 中除 passes 以外的任何字段
- 你不能标记 passes=true（那是 QA 的工作）
- 你不能在一个 session 做多个功能

## Session 启动流程（必须按序执行）
1. pwd 确认当前目录
2. 读 progress.md 了解之前做了什么
3. 运行 git log --oneline -20 了解最近变更
4. 读 feature_list.json 了解所有功能
5. 运行 bash init.sh 确认环境正常 — 如果冒烟测试失败，先修复环境
6. 选择功能 ID: ${featureId}（passes: false）

## 实现
7. 按 F${featureId} 的 steps 列表逐步实现该功能
8. 代码要求：正确性 > 优雅性，可读性 > 简洁性
9. 每个函数不超过 50 行

## 自测（推荐）
10. 启动应用，按 steps 逐步验证
11. 运行相关测试套件

## 提交
12. git add -A && git commit -m "feat(F${featureId}): ${description}"
13. 更新 progress.md，声明 "ready-for-qa"
14. **不要修改 feature_list.json**

## 输出
完成后输出：
- 功能：F${featureId}
- 状态：ready-for-qa
- 修改文件列表
- Git commit hash
- 自测结果

## 严禁
- 不修改 feature_list.json 的 passes 或 qa_status 字段
- 不删除或修改已有测试
- 不执行 rm -rf / 或 sudo
- 不嵌入密钥或凭证
- 不搜索互联网

> "IT IS CATASTROPHIC TO REMOVE OR EDIT FEATURES IN FUTURE SESSIONS."
> — Anthropic Initializer Prompt`
})
```

**v2 改进**：
- 明确 coder 不能标记 passes（R-015 中 ACP prompt 允许改 passes，与独立 QA 矛盾）
- 增加冒烟测试失败时的处理
- 增加强措辞约束引用

---

## 八、openclaw.json 配置（v2）

```json5
{
  // ACP 全局配置
  acp: {
    enabled: true,
    dispatch: { enabled: true },
    backend: "acpx",
    defaultAgent: "claude",
    allowedAgents: ["claude", "codex", "gemini", "opencode", "pi", "kimi"],
    maxConcurrentSessions: 8,
    stream: {
      coalesceIdleMs: 300,
      maxChunkChars: 1200,
    },
    runtime: {
      ttlMinutes: 120,
    },
  },

  agents: {
    list: [
      // Dev Lead — 编排调度，质量总负责
      {
        id: "dev",
        identity: "~/.openclaw/agents/dev/AGENTS.md",
        workspace: "~/.openclaw/workspace-dev",
        description: "开发编排者 - 任务拆解、三层质量门禁、feature list 生命周期管理",
        tools: {
          allow: ["read", "write", "web_fetch", "sessions_spawn", "subagents",
                  "sessions_list", "sessions_history"],
          deny: ["exec", "process", "web_search", "web_search_prime", "browser", "cron"]
        },
        subagents: {
          allowAgents: ["dev-init", "dev-coder", "dev-qa", "research"]
        }
      },

      // Dev Init — Initializer Agent（一次性）
      {
        id: "dev-init",
        identity: "~/.openclaw/agents/dev-init/AGENTS.md",
        workspace: "~/.openclaw/workspace-dev",
        description: "Initializer Agent - PM + 测试架构师，创建 feature_list.json + init.sh",
        tools: {
          allow: ["exec", "read", "write"],
          deny: ["web_search", "web_search_prime", "browser", "sessions_spawn", "cron", "subagents"]
        }
      },

      // Dev Coder — Coding Agent（不能标记 passes）
      {
        id: "dev-coder",
        identity: "~/.openclaw/agents/dev-coder/AGENTS.md",
        workspace: "~/.openclaw/workspace-dev",
        description: "Coding Agent - 增量实现功能，不能标记 passes，声明 ready-for-qa",
        tools: {
          allow: ["exec", "read", "write", "process"],
          deny: ["web_search", "web_search_prime", "browser", "sessions_spawn", "cron", "subagents"]
        }
      },

      // Dev QA — 独立验证者（唯一能标记 passes 的角色）
      {
        id: "dev-qa",
        identity: "~/.openclaw/agents/dev-qa/AGENTS.md",
        workspace: "~/.openclaw/workspace-dev",
        description: "QA Agent - Gate 1+2 执行者，独立验证、regression 测试、唯一能标记 passes",
        tools: {
          allow: ["exec", "read", "write", "browser"],
          deny: ["web_search", "web_search_prime", "sessions_spawn", "cron", "subagents"]
        }
      },
    ]
  },

  // ACP 插件
  plugins: {
    entries: {
      acpx: {
        enabled: true,
        config: {
          permissionMode: "approve-all",
          nonInteractivePermissions: "deny"
        }
      }
    }
  }
}
```

**v2 改进**：
- dev-lead 增加 `sessions_list` 和 `sessions_history`（用于检查子 agent 状态）
- dev-lead 的 `allowAgents` 增加 `research`（需要技术调研时）
- dev-qa 有 `browser` 工具（e2e 测试必需）
- ACP task prompt 中 coder 不再被允许改 passes

---

## 九、创建命令 + 部署步骤（v2）

### 9.1 创建命令

```bash
# 1. 创建目录结构
mkdir -p ~/.openclaw/agents/{dev,dev-init,dev-coder,dev-qa}
mkdir -p ~/.openclaw/workspace-dev

# 2. 写入 AGENTS.md（将第三节内容写入对应文件）
# dev: ~/.openclaw/agents/dev/AGENTS.md
# dev-init: ~/.openclaw/agents/dev-init/AGENTS.md
# dev-coder: ~/.openclaw/agents/dev-coder/AGENTS.md
# dev-qa: ~/.openclaw/agents/dev-qa/AGENTS.md

# 3. 注册 agents
openclaw agents add dev \
  --identity ~/.openclaw/agents/dev/AGENTS.md \
  --workspace ~/.openclaw/workspace-dev \
  --description "开发编排者 - 质量总负责"

openclaw agents add dev-init \
  --identity ~/.openclaw/agents/dev-init/AGENTS.md \
  --workspace ~/.openclaw/workspace-dev \
  --description "Initializer Agent - PM + 测试架构师"

openclaw agents add dev-coder \
  --identity ~/.openclaw/agents/dev-coder/AGENTS.md \
  --workspace ~/.openclaw/workspace-dev \
  --description "Coding Agent - 实现功能，不能标记 passes"

openclaw agents add dev-qa \
  --identity ~/.openclaw/agents/dev-qa/AGENTS.md \
  --workspace ~/.openclaw/workspace-dev \
  --description "QA Agent - Gate 1+2 执行者，唯一能标记 passes"

# 4. 编辑 openclaw.json（第八节配置合并到现有配置）

# 5. 安装 ACP 插件（如需 ACP harness）
openclaw plugins install acpx
openclaw config set plugins.entries.acpx.enabled true

# 6. 重启验证
openclaw gateway restart
openclaw agents list
```

### 9.2 部署步骤

#### Phase 0：环境准备（1 天）
- [ ] 确认 OpenClaw 运行正常
- [ ] 确认 browser 工具可用（QA agent 依赖 e2e 测试）
  ```bash
  # 验证 browser 可用：在主 agent 中发送"截个屏"
  # 应该能成功使用 browser snapshot
  ```
- [ ] 安装 acpx 插件（如需 ACP harness）
- [ ] 创建目录和 AGENTS.md
- [ ] 更新 openclaw.json

#### Phase 1：核心循环验证（3-5 天）
**目标**：dev-lead + dev-init + dev-coder + dev-qa，完成一个 5 功能项目

- [ ] 注册所有 4 个 agent
- [ ] 测试 1：dev-lead → dev-init（创建 feature_list + init.sh + progress.md）
- [ ] 测试 2：dev-lead → dev-coder（实现 F001 scaffold，声明 ready-for-qa）
- [ ] 测试 3：dev-lead → dev-qa（Gate 1 验证 F001，Gate 2 无 regression）
- [ ] 测试 4：dev-lead → dev-coder → dev-qa 完整循环（F002-F005）
- [ ] 测试 5：QA 发现 bug → coder 修复 → QA 重新验证（needs-fix 循环）
- [ ] **验收**：5 功能项目，每个功能都经独立 QA 验证，Clean State Gate 通过

#### Phase 2：Regression 和 Clean State 验证（2-3 天）
- [ ] 测试 6：3 个功能后全量 regression
- [ ] 测试 7：故意引入 regression → QA 检测到 → 修复
- [ ] 测试 8：烂摊子场景（冒烟测试失败）→ dev-lead 暂停新功能开发
- [ ] 测试 9：Clean State Gate（session 结束前检查）

#### Phase 3：ACP 集成（1 周）
- [ ] 配置 acpx 插件，`/acp doctor` 确认可用
- [ ] 测试 10：dev-lead 将复杂功能路由到 ACP harness
- [ ] 测试 11：ACP coder 声明 ready-for-qa → dev-qa 独立验证
- [ ] 验证 ACP prompt 中 coder 不能标记 passes

#### Phase 4：生产化（持续）
- [ ] 监控指标：
  - QA Gate 1 通过率（目标 > 80%）
  - Regression 失败率（目标 < 5%）
  - 每功能平均 session 数（目标 ≤ 2：1 coder + 1 QA）
  - needs-fix 循环次数（目标 ≤ 1 轮）
- [ ] AGENTS.md 精简到 100 行以内
- [ ] 安全审计（验证 agent 不违反权限约束）

---

## 十、与 R-014、R-015 的对比

### 10.1 R-014 → R-015 → R-015b 演进

| 维度 | R-014（基础方案） | R-015（质量优先 v1） | R-015b（本方案 v2） |
|------|-----------------|--------------------|--------------------|
| **核心哲学** | Harness Engineering 实现 | Quality-First：交付可合并代码 | Quality-First + 源码验证 |
| **Anthropic 源码分析** | 间接引用 | 博客 + prompt 文件 | **完整源码（agent.py/progress.py/security.py/client.py）** |
| **架构真相** | 未区分 | 未区分 | **确认是 TWO-agent，QA 是我们的创新** |
| **测试者/实现者分离** | ❌ coder 自己测 | ✅ 独立 QA | ✅ + 行业佐证（Red/Green Team） |
| **质量门禁** | ❌ 未结构化 | 三条铁律（叙述式） | **三层 Gate（Feature/Regression/Clean State）** |
| **Regression 策略** | ❌ 未定义 | ✅ 但无分级 | **分级策略（核心1-2/3功能全量/按需全量）** |
| **安全约束** | 基础红线 | 基础红线 | **Anthropic security.py 15 命令 allowlist** |
| **ACP prompt** | 允许改 passes | 允许改 passes（矛盾） | **禁止改 passes（与独立 QA 一致）** |
| **行业对比** | ❌ 无 | Codex/Devin/ThoughtWorks | + OpenAI Reviewer 精度优先、Mutation Testing、Agent-Separated TDD |
| **Progress 模板** | 基础 | 基础 | **含 Gate 1/2 结果、Milestone、统计** |
| **部署步骤** | 4 Phase | 3 Phase | **4 Phase + 具体测试用例编号** |
| **知识缺口处理** | 4 个缺口 | 5 个缺口 | 大部分已通过源码分析解决 |

### 10.2 关键改进总结

**v1→v2 的 6 个核心改进：**

1. **源码级架构确认**：R-015 基于博客推断，R-015b 基于 agent.py/progress.py/security.py/client.py 源码确认。最重要的发现是 Anthropic 只有 TWO-agent，独立 QA 是我们的创新。

2. **三层 Gate 结构化**：R-015 的三条铁律是叙述式的，R-015b 结构化为 Feature Gate → Regression Gate → Clean State Gate，每个 gate 有明确的触发条件、执行者、通过条件、失败动作。

3. **Regression 分级策略**：解决了 R-015 知识缺口中的"regression 太慢"问题，采用 Anthropic coding_prompt 的"1-2 个最核心"策略。

4. **ACP prompt 修正**：R-015 的 ACP prompt 允许 coder 改 passes，与独立 QA 矛盾。v2 修正为 coder 不能改任何 feature_list 字段。

5. **安全约束细化**：参考 Anthropic security.py 的 15 命令 allowlist 和细粒度验证（pkill 白名单、chmod +x only），为每个 agent 定义了安全边界。

6. **行业佐证丰富**：新增 OpenAI code reviewer 精度优先策略、Agent-Separated TDD（Red/Green Team worktree 隔离）、Mutation Testing 验证 AI 测试质量、ThoughtWorks SDD Assess 级别评估。

**v2 仍存在的局限：**

1. **Command-level 安全**：OpenClaw 的工具权限是 tool-level（允许/禁止 exec），不是 command-level（允许/禁止特定命令）。Anthropic security.py 的 allowlist 在 OpenClaw 中只能在 AGENTS.md 以指令形式约束。
2. **Browser e2e 能力**：未实测 OpenClaw browser 工具在 headless 环境下的完整能力。
3. **并发安全**：多个 agent 同时操作 feature_list.json 的并发问题未解决。
4. **QA 模型选择**：QA agent 用 zai/glm-4.7 是否足够可靠需要实测。

---

## 十一、来源

| # | 来源 | URL/路径 | 置信度 | 使用方式 |
|---|------|----------|--------|---------|
| 1 | Anthropic: Effective Harnesses for Long-Running Agents | https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents | — | 设计哲学基础 |
| 2 | Anthropic: agent.py（源码） | https://raw.githubusercontent.com/anthropics/claude-quickstarts/main/autonomous-coding/agent.py | — | 架构确认 |
| 3 | Anthropic: progress.py（源码） | https://raw.githubusercontent.com/anthropics/claude-quickstarts/main/autonomous-coding/progress.py | — | 进度追踪机制 |
| 4 | Anthropic: security.py（源码） | https://raw.githubusercontent.com/anthropics/claude-quickstarts/main/autonomous-coding/security.py | — | 安全约束 |
| 5 | Anthropic: client.py（源码） | https://raw.githubusercontent.com/anthropics/claude-quickstarts/main/autonomous-coding/client.py | — | 三层安全防御 |
| 6 | Anthropic: Initializer Prompt | https://raw.githubusercontent.com/anthropics/claude-quickstarts/main/autonomous-coding/prompts/initializer_prompt.md | — | Feature list schema |
| 7 | Anthropic: Coding Prompt | https://raw.githubusercontent.com/anthropics/claude-quickstarts/main/autonomous-coding/prompts/coding_prompt.md | — | Session 流程 |
| 8 | OpenAI: Run Long-Horizon Tasks with Codex | https://developers.openai.com/blog/run-long-horizon-tasks-with-codex/ | high | Durable project memory |
| 9 | OpenAI: Scaling Code Verification | https://alignment.openai.com/scaling-code-verification/ | high | 精度优先 + repo-wide access |
| 10 | OpenAI: Unrolling the Codex Agent Loop | https://openai.com/index/unrolling-the-codex-agent-loop/ | high | Agent loop 退出条件 |
| 11 | ThoughtWorks: Spec-Driven Development | https://www.thoughtworks.com/en-us/radar/techniques/spec-driven-development | high | Assess 级别 + Kiro/spec-kit/Tessl |
| 12 | ThoughtWorks: SDD Insights | https://www.thoughtworks.com/en-us/insights/blog/agile-engineering-practices/spec-driven-development-unpacking-2025-new-engineering-practices | high | Given/When/Then + ubiquitous language |
| 13 | Agent-Separated TDD | https://zenn.dev/kk225/articles/agent-separated-tdd?locale=en | medium | Red/Green Team worktree 隔离 |
| 14 | Mutation Testing for AI Tests | https://medium.com/@outsightai/the-truth-about-ai-generated-unit-tests-why-coverage-lies-and-mutations-dont-fcd5b5f6a267 | medium | Mutation score 提升 70%→78% |
| 15 | Tests-First Agent Loop | https://medium.com/@Micheal-Lanham/stop-burning-tokens-the-tests-first-agent-loop-that-cuts-thrash-by-50-d66bd62a948e | medium | 减少 50% 浪费 |
| 16 | Tweag: TDD in Agentic Coding | https://tweag.github.io/agentic-coding-handbook/WORKFLOW_TDD/ | medium | Tests as prompts |
| 17 | OpenClaw ACP Agents 文档 | ~/.npm-global/lib/node_modules/openclaw/docs/tools/acp-agents.md | — | ACP 集成 |
| 18 | OpenClaw Delegate Architecture | ~/.npm-global/lib/node_modules/openclaw/docs/concepts/delegate-architecture.md | — | 多 agent 架构 |
| R-014 | 前版设计 v1 | ~/.openclaw/workspace/shared/results/R-014-dev-team-harness-design.md | — | 对比基准 |
| R-015 | 前版设计 v2 | ~/.openclaw/workspace/shared/results/R-015-dev-team-quality-first-design.md | — | 改进基础 |

---

## 十二、知识缺口（v2 更新）

| # | 缺口 | R-015 状态 | R-015b 状态 | 备注 |
|---|------|-----------|------------|------|
| 1 | dev-qa 的 browser 工具能力边界 | 未解决 | **未解决** | 需实测 headless browser |
| 2 | QA 验证耗时 / Regression 策略 | 未解决 | **已解决** | 分级策略：1-2 核心/3功能全量/按需 |
| 3 | 并行 QA 的并发安全 | 未解决 | **未解决** | 建议 dev-lead 串行 spawn dev-qa |
| 4 | QA Agent 模型选择 | 未解决 | **部分解决** | 建议 glm-4.7，需实测 |
| 5 | ACP harness 的 passes 约束 | 未解决 | **已解决** | ACP prompt 明确禁止改 passes |
| 6 | Command-level 安全约束 | 不存在 | **新发现** | OpenClaw 不支持 command allowlist，需在 AGENTS.md 约束 |
| 7 | Anthropic 实际架构 | 不确定 | **已解决** | 源码确认 TWO-agent，无 reviewer |
| 8 | Feature 粒度标准 | R-014 提出 | **已解决** | 参考 Anthropic：一个 session 能完成 |
| 9 | Mutation testing 集成 | 不存在 | **新发现** | 未来可集成到 dev-qa 进阶能力 |


---

## 附录: v1 架构设计

# R-013：OpenClaw Dev Team 架构设计方案

> 生成时间：2026-03-29 | 方法：v4 深度研究流程（3 Search Agent + 双 Reviewer + 1 轮迭代）
> 研究基础：R-007（Claude Code 技能调研）、R-011（单体 dev agent 设计）、R-006（OpenClaw vs Claude Code 对比）

---

## 一、架构总览

### 1.1 设计哲学

**Humans steer. Agents execute.** — 借鉴 OpenAI Harness Engineering 实践 [1]，开发团队的核心理念是：

- **Dev Lead** 是人类工程师的 agent 化身，负责「做什么」（任务拆解、代码审查、质量把关）
- **Harness Worker** 是外部编码 agent（Claude Code/Codex），负责「怎么做」（实现、测试、调试）
- **Dev Lead 不写代码**，正如 Research Lead 不做搜索

### 1.2 架构图

```
                            ┌──────────────────┐
                            │    main agent     │
                            │   (全局路由调度)   │
                            └────────┬─────────┘
                    ┌────────────────┼────────────────┐
                    ▼                                 ▼
         ┌──────────────────┐              ┌──────────────────┐
         │  research (lead) │              │   dev (lead)     │
         │  (调研编排)       │              │  (开发编排)       │
         └────────┬─────────┘              └────────┬─────────┘
                  │                                  │
       ┌──────────┼──────────┐           ┌───────────┼───────────┐
       ▼          ▼          ▼           ▼                       ▼
  ┌────────┐┌────────┐┌────────┐  ┌─────────────┐      ┌──────────────┐
  │ search ││reviewer││citation│  │  dev-coder   │      │ dev-harness  │
  │(搜索)  ││(审核)  ││(引用)  │  │ (轻量编码)   │      │(ACP harness) │
  └────────┘└────────┘└────────┘  │  OpenClaw    │      │ Claude Code  │
                                    │  原生 agent  │      │ /Codex/Gemini│
                                    └─────────────┘      └──────┬───────┘
                                                               │
                                                    ┌──────────┼──────────┐
                                                    ▼          ▼          ▼
                                               ┌────────┐┌────────┐┌────────┐
                                               │claude  ││ codex  ││ gemini │
                                               │ code   ││        ││  CLI   │
                                               └────────┘└────────┘└────────┘
```

### 1.3 角色一览

| 角色 | 类型 | agentId | 职责 | Runtime |
|------|------|---------|------|---------|
| **dev-lead** | OpenClaw agent | `dev` | 任务拆解、代码审查、质量把关、协作编排 | subagent |
| **dev-coder** | OpenClaw agent | `dev-coder` | 轻量编码（脚本、配置、小修改） | subagent |
| **dev-harness** | ACP bridge | `dev-harness` | 重量编码（通过 ACP 调用外部 harness） | acp |

> **设计决策**：不设独立的 dev-tester agent。测试由 dev-coder 或 harness worker 直接执行，dev-lead 审查结果。理由：Azure 建议「只在单 agent 不可靠时才引入 multi-agent」[11]，测试执行可靠性高，不需要独立 agent。

---

## 二、各 Agent 角色详细设计

### 2.1 dev-lead（开发编排者）

**定位**：借鉴 Anthropic 的 planner 角色 [7] 和 OpenAI 的「人类工程师」角色 [2]。不写代码，只做决策和审查。

**核心职责**：
1. 接收开发任务，拆解为子任务
2. 判断子任务复杂度，路由到 dev-coder 或 dev-harness
3. 审查代码变更（diff review），决定是否需要迭代
4. 管理 ACP session 生命周期
5. 与 research team 协作（需要技术调研时 spawn research agent）

**工具权限**：
```
tools.allow: ["read", "write", "web_fetch", "sessions_spawn", "subagents"]
tools.deny:  ["exec", "process", "web_search", "web_search_prime", "browser", "cron"]
```

> dev-lead 不直接执行命令（不做 exec），所有执行委派给 dev-coder 或 dev-harness。

**subagents 配置**：
```json5
subagents: {
  allowAgents: ["dev-coder", "dev-harness", "research"]
}
```

**AGENTS.md**：

```markdown
# Dev Lead（开发编排者）— v1

你是 Dev Lead，负责 orchestrating 开发任务。你是调度员，不是执行者。

## 绝对不做什么
- ❌ 不自己写代码（交给 dev-coder 或 dev-harness）
- ❌ 不自己执行命令（没有 exec 权限）
- ❌ 不自己做调研（交给 research agent）

## 工作流程

### Step 1：任务分析
1. 读取任务描述，理解目标
2. 读取相关文件（read 工具），了解现有代码结构
3. 判断复杂度：
   - **简单**（改配置、写脚本、小 bug fix）→ spawn dev-coder
   - **中等**（新功能、重构、需要外部工具链）→ spawn dev-harness
   - **需要调研**（不确定技术方案）→ 先 spawn research agent

### Step 2：任务拆解
将任务拆成可独立完成的子任务，每个子任务包含：
- 目标（做什么）
- 约束（不做什么）
- 验收标准（怎么算完成）
- 上下文（相关文件路径、已有代码片段）

### Step 3：执行与审查
1. spawn 执行 agent（dev-coder 或 dev-harness）
2. 等待结果
3. 审查代码变更（read diff 文件或 output）
4. 如质量不达标，给出具体修改意见，重新 spawn（最多 3 轮）

### Step 4：验证
1. spawn dev-coder 运行测试和 lint
2. 检查结果
3. 如测试失败，分析原因，决定是修复还是回退

### Step 5：交付
- 总结：做了什么、改了哪些文件
- 测试结果
- 已知问题和后续建议

## ACP Harness 使用指南

### 何时用 dev-harness（ACP）
- 需要完整的 Claude Code / Codex 体验（IDE 级别的代码理解）
- 大规模重构（涉及 10+ 文件）
- 需要 agent 自主探索代码库的任务
- 预计执行时间 > 10 分钟的任务

### spawn 模式选择
- **mode: "run"**（one-shot）：独立子任务，完成后自动关闭
- **mode: "session" + thread: true**：需要多轮交互的复杂任务

### 超时设置
- 简单任务：runTimeoutSeconds: 300（5 分钟）
- 中等任务：runTimeoutSeconds: 600（10 分钟）
- 复杂任务：runTimeoutSeconds: 900（15 分钟，参考 issue #38419）
- 超长任务：使用 fire-and-forget + 轮询结果

### Harness 不可用时回退
1. 检测 ACP 错误（AcpRuntimeError）
2. 回退到 dev-coder（纯 OpenClaw agent）
3. 在结果中标注「harness 不可用，使用降级方案」

## 代码审查标准
- 代码是否符合项目风格
- 是否有明显的 bug 或安全漏洞
- 是否有适当的错误处理
- 是否有必要的测试
- 是否遵循 AGENTS.md 中的红线规则

## 红线
- 不直接执行任何命令
- 不跳过代码审查直接交付
- 最多迭代 3 轮（防止无限循环 [33]）
- 不确定的技术决策标注 [NEEDS_REVIEW]
```

---

### 2.2 dev-coder（轻量编码者）

**定位**：纯 OpenClaw 原生 agent，执行轻量编码任务。继承 R-011 中的单体 dev agent 设计，但定位更窄——只做 dev-lead 委派的子任务。

**核心职责**：
1. 执行代码编写（脚本、配置、小修改）
2. 运行测试、lint、构建
3. Git 操作
4. 读取和分析代码

**工具权限**：
```
tools.allow: ["exec", "read", "write", "edit", "web_fetch", "process"]
tools.deny:  ["web_search", "web_search_prime", "browser", "sessions_spawn", "cron", "subagents"]
```

**AGENTS.md**：

```markdown
# Dev Coder（轻量编码者）— v1

你是 Dev Coder，执行 dev-lead 委派的编码子任务。你是执行者，不是决策者。

## 职责
- 代码编写（Python、Shell、Node.js、TypeScript 等）
- 代码编辑和重构
- 测试编写和执行
- Git 操作
- 依赖管理

## 不做什么
- ❌ 不搜索互联网
- ❌ 不创建子 agent
- ❌ 不做架构决策（由 dev-lead 决定）
- ❌ 不做定时任务

## 工作流程
1. 阅读任务描述和约束
2. 读取相关现有文件
3. 实现（遵循项目代码风格）
4. 自测（运行测试、lint）
5. 输出结构化结果

## 代码质量标准
- 正确性 > 优雅性
- 可读性 > 简洁性
- 不引入新依赖（除非明确要求）
- 函数不超过 50 行
- 错误处理不忽略异常

## 安全红线
- ❌ 绝不执行 rm -rf / 或等效危险命令
- ❌ 绝不修改系统级配置文件
- ❌ 绝不在代码中嵌入密钥或凭证
- ❌ 绝不使用 sudo

## 输出格式
```
## 完成摘要
- 任务：<描述>
- 状态：<已完成 | 部分完成 | 失败>
- 修改文件：<列表>

## 验证结果
- <测试>：<通过/失败>

## 问题
- <如有>
```
```

---

### 2.3 dev-harness（ACP Harness Bridge）

**定位**：不是独立 agent，而是 dev-lead 通过 `sessions_spawn({ runtime: "acp" })` 创建的 ACP session。dev-lead 充当 bridge，将子任务翻译为 ACP prompt。

**支持的 harness**（通过 acpx 后端）[ACP docs]：
- `claude` — Claude Code
- `codex` — OpenAI Codex
- `gemini` — Gemini CLI
- `opencode` — OpenCode
- `pi` — Pi
- `kimi` — Kimi

**spawn 模式**：

```javascript
// 简单子任务（one-shot）
sessions_spawn({
  runtime: "acp",
  agentId: "claude",
  mode: "run",
  runTimeoutSeconds: 600,
  task: "在 src/utils.ts 中添加一个 debounce 函数...",
  cwd: "/path/to/project"
})

// 复杂子任务（persistent + thread）
sessions_spawn({
  runtime: "acp",
  agentId: "codex",
  mode: "session",
  thread: true,
  runTimeoutSeconds: 900,
  task: "重构 src/api/ 目录，将 REST 端点迁移到 tRPC...",
  cwd: "/path/to/project"
})

// 恢复之前的 session
sessions_spawn({
  runtime: "acp",
  agentId: "claude",
  resumeSessionId: "<previous-session-id>",
  task: "继续之前的工作，修复剩余的测试失败..."
})
```

**ACP 生命周期管理**：

| 阶段 | 操作 | 超时 |
|------|------|------|
| 创建 | `sessions_spawn({ runtime: "acp" })` | runTimeoutSeconds |
| 监控 | 结果 auto-announce（push-based） | — |
| 续命 | `resumeSessionId` 恢复 | 新的 timeout |
| 取消 | `/acp cancel <session-key>` | — |
| 关闭 | `/acp close <session-key>` | — |

**权限配置**（openclaw.json）：
```json5
plugins: {
  entries: {
    acpx: {
      enabled: true,
      config: {
        permissionMode: "approve-all",      // ACP session 无 TTY，需自动审批
        nonInteractivePermissions: "deny"   // 权限不足时降级而非崩溃
      }
    }
  }
}
```

---

## 三、与 Research Team 的协作流程

### 3.1 交互模式

```
用户: "帮我实现一个 OAuth2 登录功能"

main agent → 判断需要开发 + 调研
  ├─ spawn research agent → 调研 OAuth2 最佳实践、库选择
  │   └─ 返回调研报告（R-xxx-report.md）
  │
  └─ spawn dev-lead（传入调研结果）
       ├─ 基于调研结果拆解任务
       ├─ spawn dev-harness(claude) → 实现核心逻辑
       ├─ spawn dev-coder → 写测试 + 配置
       └─ 审查 + 验证 → 交付
```

### 3.2 dev-lead 调用 research agent

dev-lead 配置了 `subagents.allowAgents: ["dev-coder", "dev-harness", "research"]`，可直接 spawn research agent：

```javascript
// dev-lead 遇到技术不确定性时
sessions_spawn({
  agentId: "research",
  runTimeoutSeconds: 600,
  task: "调研主题：Node.js 中 tRPC vs GraphQL 的性能对比\n子问题：在高并发场景下哪种方案更适合？\n输出 JSON 格式..."
})
```

### 3.3 协作边界

| 场景 | 谁发起 | 谁执行 |
|------|--------|--------|
| 开发前技术调研 | dev-lead | research team |
| 开发中 API 文档查询 | dev-coder | 自己（web_fetch 已知 URL） |
| 代码审查发现设计问题 | dev-lead | 标注 [NEEDS_RESEARCH]，由 main agent 决定 |
| 开发完成后文档更新 | dev-lead | dev-coder |

---

## 四、失败处理与回退

### 4.1 分级服务能力 [29]

| 级别 | 能力 | 触发条件 |
|------|------|----------|
| **FULL** | dev-lead + dev-coder + ACP harness（全部） | 正常运行 |
| **DEGRADED** | dev-lead + dev-coder（无 harness） | ACP 不可用、acpx 插件故障 |
| **MINIMAL** | dev-lead 仅审查（无执行能力） | dev-coder 和 harness 均不可用 |
| **OFFLINE** | 返回错误，建议人工介入 | 所有 agent 不可用 |

### 4.2 错误传播防控

多 agent 系统的复合错误率极高（10 步流水线 95% 准确率时整体仅 59% [25]）。防控策略：

1. **闭环验证**：每步结果经 dev-lead 审查后再传递（可拦截 96.4% 错误 [27]）
2. **Context reset**：长任务中使用 context reset（清空 + 结构化 handoff）而非 compaction（原地摘要），避免自条件效应 [8][26]
3. **最大迭代次数**：代码审查最多 3 轮，防止无限循环 [33]

### 4.3 Evaluator-Reflect-Refine Loop [30]

代码质量不达标时的迭代机制：

```
dev-harness 产出代码
  → dev-lead 审查（evaluator）
    → 不达标：给出具体修改意见
      → dev-harness 修订（reflect-refine）
        → 重新审查
          → 达标 或 达到 3 轮上限
```

### 4.4 具体失败场景与处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| ACP harness 超时 | runTimeoutSeconds 到期 | 检查是否有部分结果，用 resumeSessionId 续命或降级到 dev-coder |
| ACP 权限错误 | AcpRuntimeError | 调整 permissionMode 或降级 |
| dev-coder 执行失败 | exec 返回非零退出码 | 分析错误，重试一次或升级到 dev-harness |
| 代码审查不通过 | dev-lead 审查判断 | 给修改意见，最多 3 轮 |
| 所有 agent 不可用 | spawn 失败 | 返回 OFFLINE，建议人工介入 |
| harness 限流（429） | API 响应 | 指数退避重试 [32]，最多 3 次 |

---

## 五、openclaw.json 配置片段

```json5
{
  // === ACP 全局配置 ===
  acp: {
    enabled: true,
    dispatch: { enabled: true },
    backend: "acpx",
    defaultAgent: "claude",           // 默认使用 Claude Code
    allowedAgents: ["claude", "codex", "gemini", "opencode", "pi", "kimi"],
    maxConcurrentSessions: 8,
    stream: {
      coalesceIdleMs: 300,
      maxChunkChars: 1200,
    },
    runtime: {
      ttlMinutes: 120,                // ACP session 2 小时 TTL
    },
  },

  // === Agent 列表 ===
  agents: {
    list: [
      // --- Dev Lead ---
      {
        id: "dev",
        identity: "~/.openclaw/agents/dev/AGENTS.md",
        workspace: "~/.openclaw/workspace-dev",
        description: "开发编排者 - 任务拆解、代码审查、质量把关、ACP harness 调度",
        tools: {
          allow: ["read", "write", "web_fetch", "sessions_spawn", "subagents"],
          deny: ["exec", "process", "web_search", "web_search_prime", "browser", "cron"]
        },
        subagents: {
          allowAgents: ["dev-coder", "dev-harness", "research"]
        }
      },

      // --- Dev Coder ---
      {
        id: "dev-coder",
        identity: "~/.openclaw/agents/dev-coder/AGENTS.md",
        workspace: "~/.openclaw/workspace-dev",   // 共享 workspace
        description: "轻量编码者 - 代码编写、测试执行、Git 操作",
        tools: {
          allow: ["exec", "read", "write", "edit", "web_fetch", "process"],
          deny: ["web_search", "web_search_prime", "browser", "sessions_spawn", "cron", "subagents"]
        }
        // 叶节点，不配置 subagents
      },

      // --- Dev Harness（ACP bridge，不需要独立 AGENTS.md）---
      {
        id: "dev-harness",
        description: "ACP Harness Bridge - 由 dev-lead 通过 sessions_spawn 调用",
        runtime: {
          type: "acp",
          acp: {
            backend: "acpx",
            mode: "run",              // 默认 one-shot
            cwd: "~/.openclaw/workspace-dev"
          }
        }
      },

      // --- 更新 main agent ---
      // {
      //   id: "main",
      //   subagents: {
      //     allowAgents: ["research", "dev"]  // 新增 "dev"
      //   }
      // }
    ]
  },

  // === ACP 插件配置 ===
  plugins: {
    entries: {
      acpx: {
        enabled: true,
        config: {
          permissionMode: "approve-all",
          nonInteractivePermissions: "deny"
        }
      }
    }
  }
}
```

---

## 六、创建命令

```bash
# === 1. 创建目录结构 ===
mkdir -p ~/.openclaw/agents/dev
mkdir -p ~/.openclaw/agents/dev-coder
mkdir -p ~/.openclaw/workspace-dev
mkdir -p ~/.openclaw/workspace-dev/docs        # 知识库目录（参考 OpenAI 实践 [4]）

# === 2. 注册 agents ===

# Dev Lead
openclaw agents add dev \
  --identity ~/.openclaw/agents/dev/AGENTS.md \
  --workspace ~/.openclaw/workspace-dev \
  --description "开发编排者 - 任务拆解、代码审查、质量把关"

# Dev Coder
openclaw agents add dev-coder \
  --identity ~/.openclaw/agents/dev-coder/AGENTS.md \
  --workspace ~/.openclaw/workspace-dev \
  --description "轻量编码者 - 代码编写、测试执行、Git 操作"

# Dev Harness（ACP bridge）
openclaw agents add dev-harness \
  --description "ACP Harness Bridge - Claude Code/Codex/Gemini"

# === 3. 手动编辑 openclaw.json ===
# 添加上面的完整配置片段（tools, subagents, acp, plugins）
nano ~/.openclaw/openclaw.json

# === 4. 安装 ACP 插件 ===
openclaw plugins install acpx
openclaw config set plugins.entries.acpx.enabled true

# === 5. 验证 ===
openclaw gateway restart
/acp doctor                                    # 检查 ACP 后端健康
openclaw agents list                           # 确认 agents 注册成功

# === 6. 写入 AGENTS.md 文件 ===
# 将上面 2.1 和 2.2 的 AGENTS.md 内容分别写入对应目录
```

---

## 七、渐进式部署路线图

### Phase 0：准备（1-2 天）

- [x] 安装 acpx 插件
- [x] 配置 ACP 全局设置
- [ ] 创建 workspace 目录结构
- [ ] 写入 AGENTS.md 文件
- [ ] `/acp doctor` 确认 ACP 可用

### Phase 1：最小可用（3-5 天）

**目标**：dev-lead + dev-coder 组合，不依赖 ACP

- [ ] 注册 dev 和 dev-coder agent
- [ ] 更新 main agent 的 `subagents.allowAgents`
- [ ] 测试：让 main agent 将开发任务路由到 dev-lead
- [ ] 测试：dev-lead spawn dev-coder 执行简单编码任务
- [ ] 测试：dev-lead 审查 dev-coder 的输出并决定是否迭代

**验收标准**：能完成一个简单的编码任务（如写一个 Python 脚本）

### Phase 2：ACP 集成（1 周）

**目标**：接入 ACP harness，实现 FULL 级别服务

- [ ] 配置 acpx 插件（permissionMode, nonInteractivePermissions）
- [ ] 测试：dev-lead spawn ACP session（Claude Code）
- [ ] 测试：one-shot 模式（mode: "run"）
- [ ] 测试：超时处理（runTimeoutSeconds: 900）
- [ ] 测试：harness 不可用时降级到 dev-coder

**验收标准**：能通过 ACP harness 完成一个中等复杂度的编码任务

### Phase 3：多 Harness 并行（1 周）

**目标**：同时使用多个 harness，按任务特性选择

- [ ] 配置多个 harness（claude, codex, gemini）
- [ ] 实现智能路由（简单任务→codex，复杂→claude）
- [ ] 测试：并行 spawn 两个 harness 执行不同子任务
- [ ] 测试：resumeSessionId 续命
- [ ] 测试：thread-bound persistent session

**验收标准**：能并行执行 2 个子任务，结果正确

### Phase 4：Research 协作（3-5 天）

**目标**：dev-lead 与 research team 无缝协作

- [ ] 配置 dev-lead 的 `subagents.allowAgents` 包含 "research"
- [ ] 测试：dev-lead spawn research agent 获取技术背景
- [ ] 测试：dev-lead 将调研结果传递给 dev-harness
- [ ] 端到端测试：从调研到实现的完整流程

**验收标准**：能完成一个需要调研+实现的端到端任务

### Phase 5：生产化（持续）

- [ ] 监控指标：任务成功率、平均迭代次数、token 消耗
- [ ] 错误归因：实现简化版 CHIEF 因果图 [31]
- [ ] AGENTS.md 精简：控制在 100 行以内 [4]，详细知识库放 docs/
- [ ] Workspace 隔离：评估是否需要 git worktree 隔离 [5]
- [ ] 安全审计：验证权限边界和红线执行情况

---

## 八、知识缺口

1. **ACP steer 支持**：当前 ACP runtime sessions 不支持 subagents tool 的 steer [19]，无法在任务执行中途调整方向。需关注 issue #43496 的进展。
2. **ACP 默认超时**：没有配置级默认 runTimeoutSeconds，只能在每个 spawn 调用中传参 [20]。建议在 AGENTS.md 中硬编码推荐值。
3. **多 harness 文件冲突**：并行 harness 操作同一仓库时的文件锁机制未找到文档。
4. **Token 消耗预算**：多 agent 架构下的 token 消耗缺乏量化估算，建议 Phase 5 监控。
5. **acpx 并发限制**：8 session 并发限制是否可配置未确认。

---

## 九、来源列表

| # | 来源 | URL |
|---|------|-----|
| 1 | OpenAI Harness Engineering | https://openai.com/index/harness-engineering/ |
| 2 | OpenAI Harness Engineering（角色转变） | https://openai.com/index/harness-engineering/ |
| 3 | OpenAI Agent-to-Agent Review | https://openai.com/index/harness-engineering/ |
| 4 | OpenAI AGENTS.md 实践 | https://openai.com/index/harness-engineering/ |
| 5 | OpenAI Worktree 隔离 | https://openai.com/index/harness-engineering/ |
| 6 | OpenAI Observability Stack | https://openai.com/index/harness-engineering/ |
| 7 | Anthropic 三 Agent 架构 | https://www.anthropic.com/engineering/harness-design-long-running-apps |
| 8 | Anthropic Context Reset | https://www.anthropic.com/engineering/harness-design-long-running-apps |
| 9 | Claude Code Agent Teams | https://dev.to/uenyioha/porting-claude-codes-agent-teams-to-opencode-4hol |
| 10 | OpenCode JSONL Inbox | https://dev.to/uenyioha/porting-claude-codes-agent-teams-to-opencode-4hol |
| 11 | Azure 5 种编排模式 | https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns |
| 12 | Azure Multi-Agent 建议 | https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns |
| 13 | Orchestrator-Worker 模式 | https://arize.com/blog/orchestrator-worker-agents/ |
| 14 | Danau5tin Multi-Agent Coding | https://github.com/Danau5tin/multi-agent-coding-system |
| 15 | Gerred 层级架构 | https://gerred.github.io/building-an-agentic-system/second-edition/part-iv-advanced-patterns/chapter-10-multi-agent-orchestration.html |
| 17 | acpx 命名 Session | https://github.com/openclaw/acpx/blob/main/README.md |
| 18 | acpx 长任务管理 | https://github.com/openclaw/acpx/blob/main/README.md |
| 19 | ACP Steer 不支持 (Issue #43496) | https://github.com/openclaw/openclaw/issues/43496 |
| 20 | Codex 超时问题 (Issue #38419) | https://github.com/openclaw/openclaw/issues/38419 |
| 22 | sessions_send Fire-and-Forget | https://docs.openclaw.ai/concepts/session-tool |
| 23 | Simon Willison 并行 Agent 模式 | https://simonwillison.net/2025/Oct/5/parallel-coding-agents/ |
| 25 | 多 Agent 失败率 | https://www.zartis.com/the-compounding-errors-problem-why-multi-agent-systems-fail-and-the-architecture-that-fixes-it/ |
| 26 | 自条件效应 | https://www.zartis.com/the-compounding-errors-problem-why-multi-agent-systems-fail-and-the-architecture-that-fixes-it/ |
| 27 | 闭环验证 96.4% | https://www.zartis.com/the-compounding-errors-problem-why-multi-agent-systems-fail-and-the-architecture-that-fixes-it/ |
| 28 | Agent 协调成本指数增长 | https://galileo.ai/blog/why-multi-agent-systems-fail |
| 29 | 优雅降级分级 | https://docs.praison.ai/docs/best-practices/graceful-degradation |
| 30 | Evaluator Reflect-Refine Loop | https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-patterns/evaluator-reflect-refine-loop-patterns.html |
| 31 | CHIEF 失败归因框架 | https://arxiv.org/html/2602.23701v1 |
| 33 | Agent 无限循环 | Medium (Komal Baparmar) |
| 34 | AWS 工具冗余 | https://aws.amazon.com/blogs/architecture/build-resilient-generative-ai-agents/ |
| ACP | OpenClaw ACP Agents 文档 | https://docs.openclaw.ai/tools/acp-agents |
| R-007 | Claude Code 技能调研 | /home/noname/.openclaw/workspace/shared/results/R-007-claude-code-skills-report.md |
| R-011 | 单体 Dev Agent 设计 | /home/noname/.openclaw/workspace/shared/results/R-011-dev-agent-design.md |
| R-006 | OpenClaw vs Claude Code 对比 | /home/noname/.openclaw/workspace/shared/results/R-006-dev-team-comparison.md |

---

## 十、方法论反思

**做得好的**：
- 3 个 Search Agent 覆盖了架构模式、ACP 集成、失败处理三个核心维度
- OpenAI Harness Engineering 博客提供了高价值的一手实践参考
- 双 Reviewer 机制发现了 Anthropic 三 agent 架构的表述不准确（原文主要是双 agent）
- 结合已有 R-007/R-011/R-006 成果填补了 Reviewer 指出的 gaps

**需要改进的**：
- 工具权限和配置的深度不足（依赖 R-011 的既有设计，未做独立搜索）
- ACP steer 不支持（issue #43496）是架构设计的硬约束，应该在 Phase 1 就考虑 workaround
- 缺少多 harness 并行的实际测试数据（所有建议基于文档和理论）
- Token 成本估算缺失（影响部署决策）


---

## 附录: Harness Engineering 重设计

# R-014：基于 Anthropic Harness Engineering 3 组件框架的 OpenClaw 开发团队重设计

> 生成时间：2026-03-29 | 基础：Anthropic "Effective Harnesses for Long-Running Agents" | 改进自：R-013

---

## 一、核心洞察：Anthropic 3 组件框架

Anthropic 的长任务 agent 方案解决的是**跨 context window 的连续工作**问题。核心设计：

| 组件 | 职责 | 关键产物 |
|------|------|----------|
| **Initializer Agent** | 首次 session 设置项目环境 | `feature_list.json` + `progress.md` + `init.sh` + 初始 git commit |
| **Coding Agent** | 每个 session 做一个 feature，增量进步 | 代码变更 + git commit + 更新 progress |
| **Feature List** | JSON 格式的功能清单，coding agent 只改 `passes` 字段 | `feature_list.json` |

**4 个失败模式及对策**：

| 问题 | Initializer 对策 | Coding Agent 对策 |
|------|-----------------|-------------------|
| 过早宣布完成 | 写完整 feature list | 每次只做一个功能，测试后才标记 pass |
| 留下 bug | 创建 git repo + progress file | session 开始读 progress + git log + 跑测试 |
| 未验证就标记完成 | 设 feature list | 端到端测试后才标记 pass |
| 不知道怎么启动项目 | 写 init.sh | session 开始读 init.sh |

---

## 二、架构图：3 组件 → OpenClaw Agent 映射

```
┌─────────────────────────────────────────────────────────────────┐
│                      main agent（全局路由）                       │
│  识别开发任务 → spawn dev-lead                                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │       dev-lead           │
              │  (开发编排 = Harness 调度器) │
              │  不写代码，只拆解+审查+调度    │
              │  管理 feature list 生命周期   │
              └───┬─────────┬─────────┬──┘
                  │         │         │
     ┌────────────▼──┐  ┌──▼────────┐ ┌▼──────────────┐
     │ dev-init      │  │ dev-coder │ │ dev-harness   │
     │ (Initializer) │  │ (Coding   │ │ (ACP Coding   │
     │               │  │  Agent)   │ │  Agent)       │
     │ 1次性运行：    │  │ OpenClaw  │ │ Claude Code   │
     │ → feature_list│  │ 原生 agent│ │ /Codex/Gemini │
     │ → progress.md │  │           │ │               │
     │ → init.sh     │  │ exec+read │ │ 通过 ACP 协议  │
     │ → git init    │  │ +write    │ │ 调用          │
     └───────────────┘  └───────────┘ └───────────────┘
                            │                │
                            └───────┬────────┘
                                    ▼
                         ┌────────────────────┐
                         │ 共享 Project Dir    │
                         │ (git repo)         │
                         ├────────────────────┤
                         │ feature_list.json  │ ← Initializer 创建
                         │ progress.md        │ ← Initializer 创建，Coding 更新
                         │ init.sh            │ ← Initializer 创建
                         │ src/               │ ← Coding Agent 修改
                         └────────────────────┘

    可选协作：
    dev-lead → spawn research agent（需要技术调研时）
```

**关键映射关系**：

| Anthropic 组件 | OpenClaw 实现 | 说明 |
|---------------|--------------|------|
| Initializer Agent | `dev-init`（一次性 OpenClaw subagent） | dev-lead 在项目首次启动时 spawn |
| Coding Agent | `dev-coder` 或 `dev-harness`（ACP） | 按任务复杂度选择 |
| Feature List | `feature_list.json`（共享目录） | 文件系统持久化，不依赖 agent 记忆 |
| Progress File | `progress.md`（共享目录） | 同上 |

---

## 三、Agent 角色定义（4 个 Agent）

### 设计决策：为什么是 4 个而不是 R-013 的 3 个？

R-013 方案没有 Initializer Agent，将初始化混在 dev-lead 中。Anthropic 的核心洞察是 **Initializer 必须是独立的、有专门 prompt 的 session**，因为它的职责与后续编码完全不同。因此新增 `dev-init`。

### Agent 角色一览

| 角色 | agentId | 类型 | 职责 |
|------|---------|------|------|
| **dev-lead** | `dev` | OpenClaw agent | 编排调度、代码审查、质量把关 |
| **dev-init** | `dev-init` | OpenClaw agent (一次性) | Initializer Agent — 创建 feature list + progress + init.sh |
| **dev-coder** | `dev-coder` | OpenClaw agent | Coding Agent（轻量）— 脚本、配置、小功能 |
| **dev-harness** | — | ACP session | Coding Agent（重量）— 通过 Claude Code/Codex 执行 |

> **dev-harness 不是注册 agent**，而是 dev-lead 通过 `sessions_spawn({ runtime: "acp" })` 动态创建的 session。

---

## 四、各 Agent 完整 AGENTS.md

### 4.1 dev-lead（开发编排者）

```markdown
# Dev Lead（开发编排者）— v2 (Harness Engineering)

你是 Dev Lead，负责 orchestrating 开发任务。你是调度员，不是执行者。
你管理项目的 feature list 生命周期，决定何时初始化、何时编码、何时验证。

## 绝对不做什么
- ❌ 不自己写代码
- ❌ 不自己执行命令（没有 exec 权限）
- ❌ 不自己修改 feature_list.json 的 passes 字段

## 工作流程

### Flow A：新项目（Initializer 模式）
1. 接收用户的开发任务
2. 判断项目目录中是否存在 `feature_list.json`
3. 如果不存在 → spawn dev-init 创建初始环境
4. 等待 dev-init 完成
5. 进入 Flow B

### Flow B：继续开发（Coding 模式）
1. 读取 `feature_list.json`，统计未完成功能
2. 选择下一个未完成功能（按 category 顺序：functional → integration → edge-case）
3. 判断复杂度：
   - **简单**（< 50 行改动）→ spawn dev-coder
   - **复杂**（多文件/需要深度推理）→ spawn dev-harness (ACP)
4. 等待结果
5. 审查代码变更（read git diff）
6. 如不达标，给修改意见，重新 spawn（最多 3 轮）
7. 验证通过 → 让 coding agent 更新 feature_list.json 的 passes 字段

### Flow C：需要调研
1. spawn research agent 获取技术背景
2. 将调研结果写入 `docs/research/` 目录
3. 基于调研结果回到 Flow B

## Feature List 管理规则
- 只能由 dev-init 创建
- coding agent 只能改 `passes` 字段（false → true）
- dev-lead 不直接修改，只负责读取和调度
- 每次调度前必须重新读取（不缓存）

## Harness 不可用时回退
1. ACP spawn 失败 → 降级到 dev-coder
2. dev-coder 也失败 → 返回 OFFLINE，建议人工介入
3. 结果中标注降级信息

## 与 Research Team 协作
- subagents.allowAgents 包含 "research"
- 需要 API 文档查询时用 web_fetch（已知 URL）
- 不确定技术方案时 spawn research agent

## 代码审查标准
- 是否符合 feature_list.json 中该功能的描述和 steps
- 是否有适当的错误处理
- 是否有必要的测试
- 不确定处标注 [NEEDS_REVIEW]

## 红线
- 不直接执行命令
- 不跳过审查
- 最多迭代 3 轮
- 不确定的技术决策标注 [NEEDS_REVIEW]
```

### 4.2 dev-init（Initializer Agent）

```markdown
# Dev Init（初始化 Agent）— v1

你是 Dev Init，基于 Anthropic Harness Engineering 的 Initializer Agent 设计。
你的唯一职责是为新项目创建初始环境，让后续 Coding Agent 能有效工作。

## 你只运行一次
当项目目录中没有 `feature_list.json` 时，dev-lead 会 spawn 你。
完成后你不会再被调用。

## 绝对不做什么
- ❌ 不实现任何功能（只做环境设置）
- ❌ 不写业务代码
- ❌ 不修改 feature_list.json 中的 passes 为 true

## 工作流程（严格按序执行）

### Step 1：理解需求
1. 阅读用户的完整任务描述
2. 如有模糊之处，在输出中列出假设（dev-lead 会审查）

### Step 2：创建 feature_list.json
在项目根目录创建 `feature_list.json`，格式如下：
```json
{
  "project": "项目名称",
  "created": "ISO 日期",
  "description": "项目简述",
  "features": [
    {
      "id": "F001",
      "category": "functional",
      "description": "用户可以点击新建按钮创建空白对话",
      "steps": [
        "导航到主界面",
        "点击新建对话按钮",
        "验证创建了新对话",
        "验证侧边栏显示新对话"
      ],
      "passes": false
    }
  ]
}
```

**要求**：
- 功能必须细化到可以在一个 session 内完成（避免 agent 试图一次性做太多）
- 初始所有 features 的 passes 必须为 false
- 功能数量至少覆盖核心需求（参考 Anthropic 实践：一个 claude.ai clone 有 200+ features）
- 优先级：functional → integration → error-handling → edge-case → polish

### Step 3：创建 progress.md
```markdown
# 开发进度日志

## 项目：{project_name}
## 创建时间：{date}

### Session 0 — 初始化
- [INIT] 创建 feature_list.json（{N} 个功能）
- [INIT] 创建 progress.md
- [INIT] 创建 init.sh
- [INIT] 初始 git commit
```

### Step 4：创建 init.sh
```bash
#!/bin/bash
# 项目启动脚本 — Coding Agent 在每个 session 开始时运行此脚本

# 1. 安装依赖（如有 package.json/requirements.txt）
# 2. 启动开发服务器（后台）
# 3. 等待服务器就绪
# 4. 运行基础测试确认环境正常

set -e

echo "=== Init: Checking environment ==="

# 示例：Node.js 项目
if [ -f "package.json" ]; then
  npm install --silent 2>/dev/null || true
fi

# 示例：Python 项目
if [ -f "requirements.txt" ]; then
  pip3 install -q -r requirements.txt 2>/dev/null || true
fi

echo "=== Init: Environment ready ==="
```

### Step 5：Git 初始化
1. `git init`（如果还不是 git repo）
2. `git add .`
3. `git commit -m "init: project scaffold with feature_list.json and init.sh"`

## 输出格式
```
## 初始化完成
- 项目：{name}
- 功能数：{N}
- Git commit：{hash}
- 文件创建：feature_list.json, progress.md, init.sh

## 功能概览
- functional: {n} 个
- integration: {n} 个
- error-handling: {n} 个
- edge-case: {n} 个
```

## 安全红线
- 不执行危险命令（rm -rf、sudo 等）
- 不安装全局 npm 包
- 不修改系统配置
```

### 4.3 dev-coder（Coding Agent — OpenClaw 原生）

```markdown
# Dev Coder（Coding Agent）— v2 (Harness Engineering)

你是 Coding Agent，基于 Anthropic Harness Engineering 设计。
你每个 session 只做一个 feature，完成后更新进度文件。

## Session 启动流程（必须按序执行）

### 1. 定位
确认当前工作目录（pwd）

### 2. 读进度文件
读取 `progress.md` — 了解之前做了什么

### 3. 读 Git 日志
运行 `git log --oneline -20` — 了解最近的变更

### 4. 读 Feature List
读取 `feature_list.json` — 了解所有功能和状态

### 5. 选择功能
选择 **一个** passes=false 的功能（按 id 顺序，或 dev-lead 指定的 id）

### 6. 环境健康检查
运行 `bash init.sh` — 确认环境正常

### 7. 实现
按功能的 steps 列表逐步实现

### 8. 端到端验证
**必须端到端验证**，不能只跑单元测试：
- 启动应用/服务
- 按功能描述的 steps 手动验证
- 运行相关测试套件
- 所有验证通过后才标记 passes=true

### 9. 提交
- `git add -A`
- `git commit -m "feat(F{id}): {description}"`
- 更新 `progress.md`

### 10. 更新 Feature List
**只改 passes 字段**：将已完成功能的 passes 改为 true
**严禁**删除功能、修改 steps、修改 description

## Session 结束输出
```
## 完成摘要
- 功能：F{id} — {description}
- 状态：已完成 | 部分完成 | 失败
- 修改文件：{list}
- Git commit：{hash}

## 验证结果
- {step}: ✅/❌
- 测试：{pass}/{total} passed

## 问题
- {如有}
```

## 不做什么
- ❌ 不搜索互联网
- ❌ 不创建子 agent
- ❌ 不做架构决策
- ❌ 不修改 feature_list.json 中除 passes 以外的字段
- ❌ 不在一个 session 做多个功能

## 代码质量标准
- 正确性 > 优雅性
- 可读性 > 简洁性
- 错误处理不忽略异常
- 函数不超过 50 行

## 安全红线
- ❌ 绝不执行 rm -rf / 或等效命令
- ❌ 绝不使用 sudo
- ❌ 绝不在代码中嵌入密钥或凭证
- ❌ 绝不修改系统级配置文件
```

---

## 五、Feature List 管理方案

### 5.1 位置与格式

```
<project-root>/
├── feature_list.json    ← 功能清单（Initializer 创建）
├── progress.md          ← 进度日志（Initializer 创建，Coding 更新）
├── init.sh              ← 环境启动脚本（Initializer 创建）
├── src/                 ← 源代码
└── tests/               ← 测试
```

### 5.2 权限矩阵

| 操作 | dev-init | dev-coder | dev-lead | dev-harness (ACP) |
|------|---------|-----------|----------|-------------------|
| 创建 feature_list.json | ✅ | ❌ | ❌ | ❌ |
| 修改 passes 字段 | ❌ | ✅ | ❌ | ✅ |
| 修改其他字段 | ❌ | ❌ | ❌ | ❌ |
| 读取 | ✅ | ✅ | ✅ | ✅ |
| 创建 progress.md | ✅ | ❌ | ❌ | ❌ |
| 追加 progress.md | ❌ | ✅ | ✅ (审查) | ✅ |
| 创建 init.sh | ✅ | ❌ | ❌ | ❌ |

### 5.3 feature_list.json 模板

```json
{
  "project": "my-web-app",
  "created": "2026-03-29T00:00:00Z",
  "description": "一个示例 Web 应用",
  "features": [
    {
      "id": "F001",
      "category": "scaffold",
      "description": "项目脚手架：目录结构 + 构建配置 + 基础 HTML",
      "steps": [
        "创建 src/, public/, tests/ 目录",
        "配置构建工具（vite/webpack）",
        "创建 index.html 入口",
        "运行 dev server 确认页面加载"
      ],
      "passes": false
    },
    {
      "id": "F002",
      "category": "functional",
      "description": "用户可以在输入框输入文字并提交",
      "steps": [
        "渲染输入框和提交按钮",
        "输入文字后点击提交",
        "验证提交后输入框清空",
        "验证提交的内容显示在页面上"
      ],
      "passes": false
    },
    {
      "id": "F003",
      "category": "functional",
      "description": "用户可以看到历史记录列表",
      "steps": [
        "提交多条记录",
        "验证历史记录按时间倒序显示",
        "验证每条记录显示完整内容"
      ],
      "passes": false
    },
    {
      "id": "F004",
      "category": "error-handling",
      "description": "空输入提交时显示错误提示",
      "steps": [
        "不输入任何内容点击提交",
        "验证显示错误提示信息",
        "输入内容后错误提示消失"
      ],
      "passes": false
    },
    {
      "id": "F005",
      "category": "integration",
      "description": "数据持久化到 localStorage",
      "steps": [
        "提交数据",
        "刷新页面",
        "验证数据仍然存在"
      ],
      "passes": false
    }
  ]
}
```

---

## 六、增量进度管理

### 6.1 progress.md 模板

```markdown
# 开发进度日志

## 项目：my-web-app
## 创建时间：2026-03-29

---

### Session 0 — 初始化 [dev-init]
- [INIT] 创建 feature_list.json（5 个功能）
- [INIT] 创建 progress.md
- [INIT] 创建 init.sh
- [INIT] 初始 git commit (abc1234)

---

### Session 1 — F002: 用户输入提交 [dev-coder]
- [DONE] 实现输入框和提交按钮组件
- [DONE] 添加提交逻辑和状态管理
- [DONE] 端到端验证通过
- [DONE] git commit (def5678): feat(F002): user input and submit
- [PASS] F002 passes: false → true

---

### Session 2 — F003: 历史记录列表 [dev-coder]
- [DONE] 实现历史记录组件
- [DONE] 添加排序逻辑
- [DONE] 端到端验证通过
- [DONE] git commit (ghi9012): feat(F003): history list with reverse sort
- [PASS] F003 passes: false → true
```

### 6.2 Git Commit 策略

| 场景 | 格式 | 示例 |
|------|------|------|
| 初始化 | `init: {描述}` | `init: project scaffold with feature list` |
| 功能完成 | `feat(F{id}): {描述}` | `feat(F002): user input and submit` |
| Bug 修复 | `fix(F{id}): {描述}` | `fix(F003): sort order in history list` |
| 回退 | `revert: {原因}` | `revert: F004 broken by previous commit` |

### 6.3 Session 间上下文传递

**核心原则：不依赖 agent 记忆，所有状态通过文件传递。**

```
Session N 结束时的文件状态：
├── feature_list.json  → 包含 F001..F003 passes=true, F004..F005 passes=false
├── progress.md        → 包含 Session 0..N 的完整日志
├── init.sh            → 不变
├── src/               → 包含 F001..F003 的代码
└── .git/              → 包含所有 commit 历史

Session N+1 开始时：
1. 读 progress.md → 知道上次做到哪了
2. 读 git log → 知道代码变更历史
3. 读 feature_list.json → 知道下一个未完成功能
4. 运行 init.sh → 确认环境
5. 开始工作
```

---

## 七、测试验证机制

### 7.1 端到端验证流程

```
Coding Agent 的验证步骤：
1. 运行 init.sh（环境健康检查）
2. 实现功能代码
3. 运行单元测试（如有）
4. 运行集成测试（如有）
5. 手动/脚本验证（按 feature 的 steps 列表）：
   a. 启动应用
   b. 逐步执行 steps
   c. 每步确认通过
6. 全部通过 → 标记 passes=true
7. 任一失败 → 不标记，在 progress.md 中记录失败原因
```

### 7.2 init.sh 完整模板

```bash
#!/bin/bash
# init.sh — 项目环境启动脚本
# 由 Initializer Agent 创建，Coding Agent 每个 session 开始时运行

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

echo "=== Environment Check ==="

# Node.js 项目
if [ -f "package.json" ]; then
  echo "[init] Installing npm dependencies..."
  npm install --silent 2>/dev/null || npm install
  echo "[init] Running lint..."
  npm run lint 2>/dev/null || echo "[init] No lint script, skipping"
  echo "[init] Running tests..."
  npm test 2>/dev/null || echo "[init] No test script, skipping"
fi

# Python 项目
if [ -f "requirements.txt" ]; then
  echo "[init] Installing Python dependencies..."
  pip3 install -q -r requirements.txt
fi
if [ -f "pyproject.toml" ]; then
  echo "[init] Running pytest..."
  python3 -m pytest -x -q 2>/dev/null || echo "[init] No tests or pytest not configured"
fi

# 通用检查
echo "[init] Git status:"
git status --short

echo "=== Environment Ready ==="
```

---

## 八、ACP Harness 集成方案

### 8.1 任务路由决策

```
dev-lead 收到任务
  │
  ├── 功能简单（< 50行，单文件） → dev-coder (OpenClaw 原生)
  │     优点：快速、低成本、无外部依赖
  │
  ├── 功能复杂（多文件、需要深度推理） → dev-harness (ACP)
  │     优点：Claude Code 有更好的代码理解能力
  │     spawn: sessions_spawn({ runtime: "acp", agentId: "claude", mode: "run" })
  │
  └── 超长任务（20+ 分钟） → dev-harness (ACP, persistent)
        spawn: sessions_spawn({ runtime: "acp", agentId: "claude",
                               mode: "session", thread: true })
```

### 8.2 ACP Coding Agent 的特殊处理

ACP harness（如 Claude Code）不读 OpenClaw 的 AGENTS.md，所以需要通过 task prompt 传递 Harness Engineering 流程：

```javascript
// dev-lead spawn ACP coding agent 时的 task 模板
sessions_spawn({
  runtime: "acp",
  agentId: "claude",    // 或 "codex", "gemini"
  mode: "run",
  runTimeoutSeconds: 600,
  cwd: "/path/to/project",
  task: `你是 Coding Agent。严格按以下流程工作：

## Session 启动流程
1. pwd 确认当前目录
2. 读 progress.md 了解之前做了什么
3. 运行 git log --oneline -20 了解最近变更
4. 读 feature_list.json 了解所有功能
5. 选择功能 ID: ${featureId}（passes: false）
6. 运行 bash init.sh 确认环境正常
7. 按功能的 steps 实现该功能
8. 端到端验证（启动应用，按 steps 逐步验证）
9. 全部通过后，修改 feature_list.json 中 F${featureId} 的 passes 为 true
10. git add -A && git commit -m "feat(F${featureId}): ${description}"
11. 更新 progress.md

## 严禁
- 不要修改 feature_list.json 中除 passes 以外的任何字段
- 不要在一个 session 做多个功能
- 不要跳过端到端验证就标记 passes=true`
})
```

### 8.3 降级方案

| 级别 | 能力 | 触发条件 |
|------|------|----------|
| **FULL** | dev-lead + dev-coder + ACP harness | 正常运行 |
| **DEGRADED** | dev-lead + dev-coder（无 ACP） | ACP 不可用 |
| **MINIMAL** | dev-lead 仅审查 | dev-coder 和 harness 均不可用 |
| **OFFLINE** | 返回错误，建议人工 | 所有 agent 不可用 |

---

## 九、openclaw.json 配置片段

```json5
{
  // ACP 全局配置
  acp: {
    enabled: true,
    dispatch: { enabled: true },
    backend: "acpx",
    defaultAgent: "claude",
    allowedAgents: ["claude", "codex", "gemini", "opencode", "pi", "kimi"],
    maxConcurrentSessions: 8,
    stream: {
      coalesceIdleMs: 300,
      maxChunkChars: 1200,
    },
    runtime: {
      ttlMinutes: 120,
    },
  },

  agents: {
    list: [
      // Dev Lead — 编排调度
      {
        id: "dev",
        identity: "~/.openclaw/agents/dev/AGENTS.md",
        workspace: "~/.openclaw/workspace-dev",
        description: "开发编排者 - 任务拆解、代码审查、feature list 管理、ACP 调度",
        tools: {
          allow: ["read", "write", "web_fetch", "sessions_spawn", "subagents"],
          deny: ["exec", "process", "web_search", "web_search_prime", "browser", "cron"]
        },
        subagents: {
          allowAgents: ["dev-init", "dev-coder", "research"]
        }
      },

      // Dev Init — Initializer Agent
      {
        id: "dev-init",
        identity: "~/.openclaw/agents/dev-init/AGENTS.md",
        workspace: "~/.openclaw/workspace-dev",
        description: "Initializer Agent - 创建 feature_list.json、progress.md、init.sh",
        tools: {
          allow: ["exec", "read", "write"],
          deny: ["web_search", "web_search_prime", "browser", "sessions_spawn", "cron", "subagents"]
        }
        // 一次性 agent，不需要 subagents
      },

      // Dev Coder — Coding Agent (OpenClaw 原生)
      {
        id: "dev-coder",
        identity: "~/.openclaw/agents/dev-coder/AGENTS.md",
        workspace: "~/.openclaw/workspace-dev",
        description: "Coding Agent (OpenClaw) - 增量实现功能、测试、git 操作",
        tools: {
          allow: ["exec", "read", "write", "process"],
          deny: ["web_search", "web_search_prime", "browser", "sessions_spawn", "cron", "subagents"]
        }
      },
    ]
  },

  // ACP 插件
  plugins: {
    entries: {
      acpx: {
        enabled: true,
        config: {
          permissionMode: "approve-all",
          nonInteractivePermissions: "deny"
        }
      }
    }
  }
}
```

---

## 十、创建命令

```bash
# 1. 创建目录结构
mkdir -p ~/.openclaw/agents/dev
mkdir -p ~/.openclaw/agents/dev-init
mkdir -p ~/.openclaw/agents/dev-coder
mkdir -p ~/.openclaw/workspace-dev

# 2. 注册 agents
openclaw agents add dev \
  --identity ~/.openclaw/agents/dev/AGENTS.md \
  --workspace ~/.openclaw/workspace-dev \
  --description "开发编排者"

openclaw agents add dev-init \
  --identity ~/.openclaw/agents/dev-init/AGENTS.md \
  --workspace ~/.openclaw/workspace-dev \
  --description "Initializer Agent"

openclaw agents add dev-coder \
  --identity ~/.openclaw/agents/dev-coder/AGENTS.md \
  --workspace ~/.openclaw/workspace-dev \
  --description "Coding Agent (OpenClaw)"

# 3. 写入 AGENTS.md（将第四节的完整内容写入对应文件）

# 4. 编辑 openclaw.json（添加第九节的配置）

# 5. 安装 ACP 插件
openclaw plugins install acpx
openclaw config set plugins.entries.acpx.enabled true

# 6. 验证
openclaw gateway restart
/acp doctor
openclaw agents list
```

---

## 十一、部署步骤（从零开始）

### Phase 0：环境准备（1 天）
- [ ] 确认 OpenClaw 已安装且运行正常
- [ ] 安装 acpx 插件，`/acp doctor` 确认 ACP 可用
- [ ] 创建目录结构和 AGENTS.md 文件
- [ ] 更新 openclaw.json 配置

### Phase 1：最小可用（3-5 天）
**目标**：dev-lead + dev-init + dev-coder，不依赖 ACP

- [ ] 注册所有 3 个 agent
- [ ] 测试：给 main agent 一个开发任务 → 路由到 dev-lead
- [ ] 测试：dev-lead 检测无 feature_list.json → spawn dev-init
- [ ] 测试：dev-init 创建 feature_list.json + progress.md + init.sh + git init
- [ ] 测试：dev-lead 读 feature_list → spawn dev-coder 做一个功能
- [ ] 测试：dev-coder 按 session 启动流程工作，完成后更新 passes

**验收**：能完成一个 5 功能的小项目的完整初始化→编码→验证循环

### Phase 2：ACP 集成（1 周）
- [ ] 配置 acpx 插件
- [ ] 测试：dev-lead 将复杂功能路由到 ACP harness
- [ ] 测试：ACP harness 的 task prompt 包含完整的 session 启动流程
- [ ] 测试：ACP harness 正确更新 feature_list.json
- [ ] 测试：harness 不可用时降级到 dev-coder

### Phase 3：Research 协作（3-5 天）
- [ ] 配置 dev-lead 的 allowAgents 包含 "research"
- [ ] 测试：dev-lead 在技术不确定时 spawn research agent
- [ ] 端到端测试：调研→初始化→编码→验证

### Phase 4：生产化（持续）
- [ ] 监控：任务成功率、平均每功能耗时、token 消耗
- [ ] AGENTS.md 精简到 100 行以内
- [ ] 安全审计

---

## 十二、与 R-013 方案的对比和改进

| 维度 | R-013（旧方案） | R-014（本方案） | 改进说明 |
|------|---------------|---------------|----------|
| **Initializer** | ❌ 没有，混在 dev-lead 中 | ✅ 独立 dev-init agent | Anthropic 核心洞察：初始化必须是独立 session |
| **Feature List** | ❌ 没有机制 | ✅ feature_list.json + 严格权限 | 解决"过早宣布完成"问题 |
| **Progress File** | ❌ 没有机制 | ✅ progress.md + 结构化日志 | 解决"跨 session 上下文丢失"问题 |
| **Session 启动流程** | ❌ 未定义 | ✅ 6 步标准流程 | 每次开始都读 progress + git log + feature list |
| **增量进度** | ❌ 无约束 | ✅ 每次 session 只做一个功能 | 防止 agent 试图一次性做太多 |
| **端到端验证** | ❌ 只跑测试 | ✅ 按 steps 列表逐步验证 | 必须端到端通过才标记 pass |
| **Agent 数量** | 3（dev-lead + dev-coder + dev-harness） | 4（+ dev-init） | 多 1 个但职责更清晰 |
| **ACP prompt** | 只传任务描述 | 传完整的 session 启动流程 | ACP harness 也能遵循 Harness Engineering 流程 |
| **文件权限** | 未定义 | 明确的权限矩阵 | 防止误操作 feature list |

### 关键改进总结

1. **解决了 Anthropic 识别的 4 个失败模式**：过早完成、留下 bug、未验证标记、不知如何启动
2. **新增 Initializer Agent**：将项目初始化从 dev-lead 中独立出来，与 Anthropic 实践对齐
3. **结构化进度管理**：feature_list.json + progress.md + git history 三重状态追踪
4. **严格的 Coding Agent session 流程**：6 步启动流程确保每个 session 都有完整上下文
5. **ACP harness 兼容**：通过 task prompt 将流程传递给外部 harness，不依赖 OpenClaw AGENTS.md

---

## 十三、知识缺口

1. **ACP harness 的 feature_list.json 操作**：Claude Code 等外部 harness 是否可靠地遵循"只改 passes"的约束？需要实际测试。
2. **并行 Coding Agent**：多个 dev-coder 或 ACP session 同时操作同一个 feature_list.json 时的并发安全未解决。
3. **Feature 粒度**：多大的功能算"一个 feature"？太小会导致过多 session，太大会导致 context 不足。需要 dev-init 的 prompt 中加入粒度指引。
4. **init.sh 适应性**：不同项目类型（前端/后端/全栈/CLI 工具）的 init.sh 模板需要不同，是否需要 dev-init 自动识别项目类型？

---

## 十四、来源

| # | 来源 | URL |
|---|------|-----|
| 1 | Anthropic: Effective Harnesses for Long-Running Agents | https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents |
| 2 | Anthropic: Claude Agent SDK Quickstart (autonomous-coding) | https://github.com/anthropics/claude-quickstarts/tree/main/autonomous-coding |
| 3 | Claude 4 Prompting Guide: Multi-context Window Workflows | https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices |
| 4 | OpenClaw ACP Agents 文档 | /home/noname/.npm-global/lib/node_modules/openclaw/docs/tools/acp-agents.md |
| R-013 | OpenClaw Dev Team 架构设计方案 | /home/noname/.openclaw/workspace/shared/results/R-013-dev-team-design.md |
| R-007 | ClawHub Claude Code 技能调研 | /home/noname/.openclaw/workspace/shared/results/R-007-claude-code-skills-report.md |
| R-006 | OpenClaw vs Claude Code 对比 | /home/noname/.openclaw/workspace/shared/results/R-006-dev-team-comparison.md |


---

## 附录: 质量优先 v1

# R-015：以交付质量为核心的 OpenClaw 研发团队 Agent 方案

> 生成时间：2026-03-30 | 基础：Anthropic "Effective Harnesses for Long-Running Agents" 原文精读 + autonomous-coding quickstart 源码 | 改进自：R-014

---

## 一、设计哲学：从 Anthropic 原文学到什么

### 1.1 核心问题

Anthropic 明确指出长任务 agent 的根本挑战：

> "The core challenge of long-running agents is that they must work in discrete sessions, and each new session begins with no memory of what came before."

这决定了我们的设计必须基于**文件持久化状态**，而非 agent 记忆。

### 1.2 两个失败模式

> "First, the agent tended to try to do too much at once—essentially to attempt to one-shot the app."

> "After some features had already been built, a later agent instance would look around, see that progress had been made, and declare the job done."

**对策**：Feature List（原子化任务） + 增量进度 + 强措辞约束。

### 1.3 Clean State 定义（逐字引用）

> "By 'clean state' we mean the kind of code that would be appropriate for merging to a main branch: there are no major bugs, the code is orderly and well-documented, and in general, a developer could easily begin work on a new feature without first having to clean up an unrelated mess."

**这是本方案的核心验收标准。** 不是"能跑"，是"可合并到 main"。

### 1.4 测试失败的洞察

> "One final major failure mode that we observed was Claude's tendency to mark a feature as complete without proper testing."

> "Claude mostly did well at verifying features end-to-end once explicitly prompted to use browser automation tools and do all testing as a human user would."

**关键**：unit test 不够，必须 e2e browser 测试。

### 1.5 JSON > Markdown

> "After some experimentation, we landed on using JSON for this, as the model is less likely to inappropriately change or overwrite JSON files compared to Markdown files."

### 1.6 强措辞约束（比博客更严厉的实际 prompt）

Anthropic 博客引用了 `"It is unacceptable to remove or edit tests"`，但实际 quickstart 代码中 Initializer prompt 的措辞更严厉：

> **"CRITICAL INSTRUCTION: IT IS CATASTROPHIC TO REMOVE OR EDIT FEATURES IN FUTURE SESSIONS. Features can ONLY be marked as passing (change 'passes': false to 'passes': true). Never remove features, never edit descriptions, never modify testing steps."**

这个措辞选择很有意思——"catastrophic"比"unacceptable"更强烈，说明 Anthropic 在实践中发现温和措辞不够，必须用极端语言约束模型行为。

### 1.7 Coding Agent 的 10 步 Session 流程（源码确认）

Anthropic 的 `coding_prompt.md` 定义了一个精确的 10 步流程：

1. `pwd` 确认工作目录
2. 读 git log + progress 文件获取上下文
3. 运行 `init.sh` 启动服务器
4. **回归测试**：Run 1-2 of the feature tests marked as `passes: true` that are most core
5. 选择一个 `passes: false` 的功能
6. 实现该功能
7. 用浏览器自动化验证（Puppeteer）
8. **只修改 passes 字段**
9. `git commit` + 更新 `claude-progress.txt`
10. 干净地结束 session

**关键发现**：回归测试是 Coding Agent 自己做的（"如发现问题立即标记为 failing 并修复后才做新功能"）。但本方案认为这个回归测试应该由独立 QA 执行——见下文。

### 1.8 Initializer 和 Coding Agent 共享 System Prompt

> "We refer to these as separate agents in this context only because they have different initial user prompts. The system prompt, set of tools, and overall agent harness was otherwise identical."

这意味着 Anthropic 的方案中两个"agent"其实用的是同一个 harness，只是第一次 session 用 initializer prompt，后续 session 用 coding prompt。**在 OpenClaw 中，我们用不同的 agentId + 不同 AGENTS.md 实现同样的效果。**

### 1.9 Multi-Agent 方向

> "It seems reasonable that specialized agents like a testing agent, a quality assurance agent, or a code cleanup agent, could do an even better job at sub-tasks across the software development lifecycle."

**本方案直接回答这个问题：是的，需要独立的 QA Agent。**

---

## 二、行业对比：其他 Agent 如何处理质量

### 2.1 OpenAI Codex — plan→implement→validate→repair 循环

OpenAI Codex 5.3 实现了约 **25 小时不间断运行**（13M tokens，30k 行代码），核心是多步执行循环：

> "It performed well on the parts that matter for long-horizon work: following the spec, staying on task, running verification, and repairing failures as it went."

OpenAI 还训练了专门的 **agentic code reviewer**：
- 每个 PR 自动审查
- 工程师推送前运行 `/review`
- 已保护高价值实验并捕获 launch-blocking 问题
- **优先优化精度而非召回率**：因为防御系统失败往往不是因为技术错误，而是太慢太吵导致用户绕过

**启示**：Codex 的 validate→repair 循环与我们的 dev-qa → fix → re-verify 循环思路一致。OpenAI 的精度优先策略也适用于我们的 QA agent——宁可漏报一些小问题，也不要产生太多误报导致 developer 信任崩塌。

### 2.2 Devin — Testing & Validation 官方用例

Devin 官方明确支持三类质量用例：
- **Test Generation**：自动生成集成测试和单元测试
- **QA Testing**：编写 QA 测试并执行自动化 QA 测试
- **PR Review**：代码审查

**启示**：Devin 将测试生成和 QA 测试分为不同用例，印证了测试者和实现者分离的思路。

### 2.3 ThoughtWorks — Spec-Driven Development (SDD)

ThoughtWorks 2025 年提出将 BDD 经验应用于 AI 辅助开发：

> "Specifications should still use domain-oriented ubiquitous language to describe business intent rather than specific tech-bound implementations. They should also have a clear structure, with a common style to define scenarios using Given/When/Then."

**启示**：我们的 feature_list.json 的 steps 字段应该用业务语言描述用户行为，而非技术实现。已有的 steps 格式（"Navigate to main interface" → "Click the 'New Chat' button"）正好符合这个原则。

### 2.4 BDD 在 AI Agent 中的价值

多个来源指出 BDD 在 AI agent 场景中成为必需品：

> "Agents don't need opinions — they need instructions. Clear, complete, consistent, and auditable instructions."

BDD 的 Given/When/Then 结构提供 agent 兼容的规范格式，作为人类与 agent 之间的契约。更重要的是：

> "Before agents even write a single line of code, we can already validate business logic with pre-implementation tests."

这意味着 dev-init 在写 feature_list.json 时就已经在做"预实现测试设计"——定义验收标准在编码之前。

### 2.5 TDD 的确定性退出标准

> "TDD provides deterministic exit criteria for AI agents. Instead of relying on the AI's judgment about when code is 'done,' tests force agents to iterate until all requirements pass."

这直接支持本方案的核心设计：**passes=false → true 是唯一的"完成"标准**，而非 coder 自己声明完成。

---

## 三、质量保障体系

### 3.1 设计原则：测试者和实现者必须分离

R-014 的根本问题：**dev-coder 既写代码又自己测试又自己标记 passes=true**。这违反了软件工程的基本原则——开发者不能验证自己的代码。

Anthropic 原文的 Coding Agent 确实是"self-verify"（包括回归测试也是 coder 自己做），但 Anthropic 也明确指出：

> "It seems reasonable that specialized agents like a testing agent, a quality assurance agent... could do an even better job."

本方案将 Anthropic 的"self-verify"升级为"independent QA verify"，是对 multi-agent 方向的直接实践。

### 3.2 质量循环（Quality Loop）

```
┌─────────────────────────────────────────────────────────────────┐
│                      Quality Loop                                │
│                                                                  │
│  dev-init (PM + QA Architect)                                    │
│    │                                                             │
│    ├── 1. 写 feature_list.json（每个 feature = BDD 测试用例）     │
│    ├── 2. 写 init.sh（含冒烟测试）                                │
│    ├── 3. git init + initial commit                              │
│    └── 4. 所有 features passes=false, qa_status="pending"       │
│                                                                  │
│  dev-coder (Implementer)                                         │
│    │                                                             │
│    ├── 5. 运行 init.sh（环境健康检查）                            │
│    ├── 6. 选一个 passes=false 的 feature                         │
│    ├── 7. 实现代码                                               │
│    ├── 8. 自测（可选，但不标记 passes）                           │
│    ├── 9. git commit（feat 标记，但 passes 仍为 false）           │
│    └── 10. 更新 progress.md，声明"ready for QA"                  │
│                                                                  │
│  dev-qa (Tester) — 独立验证 ⭐                                   │
│    │                                                             │
│    ├── 11. 运行 init.sh + 冒烟测试                               │
│    ├── 12. 按该 feature 的 steps 做 e2e 验证（browser 工具）     │
│    ├── 13. 运行 regression（已有 passes=true 的功能）            │
│    ├── 14a. 全部通过 → 改 passes=false → true                   │
│    ├── 14b. 新功能失败 → qa_status="needs-fix"                  │
│    ├── 14c. Regression 失败 → qa_status="regression-fail"       │
│    └── 15. git commit（test: 标记）                              │
│                                                                  │
│  dev-lead (Orchestrator)                                         │
│    │                                                             │
│    ├── 16. 审查 QA 结果                                          │
│    ├── 17a. VERIFIED → 选择下一个 feature                        │
│    ├── 17b. NEEDS-FIX → spawn dev-coder 修复（最多 3 轮）       │
│    └── 17c. REGRESSION-FAIL → 优先修复，不开发新功能             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 三条质量铁律

1. **没有独立 QA 通过 = 没有 passes=true**。coding agent 永远不能自己改 passes。
2. **每个 QA session 必须跑 regression**。验证新功能时，同时验证所有已有 passes=true 的功能。
3. **冒烟先行**。任何 agent 开始工作前，先跑 init.sh，确认基础功能没坏。

### 3.4 Feature = BDD 测试用例

每个 feature 的 `steps` 字段就是 BDD 的验收标准：

| BDD 概念 | Feature List 对应 | 示例 |
|----------|-------------------|------|
| **Given** | 前置 steps（隐含在描述中） | "Navigate to main interface" |
| **When** | 操作 steps | "Click the 'New Chat' button" |
| **Then** | 验证 steps | "Verify a new conversation is created" |

这不是形式化的 Given/When/Then 语法，而是 Anthropic 实践验证过的 **自然语言 steps 格式**，对 agent 更友好。

---

## 四、Agent 角色定义

### 4.1 从质量角度重新定义角色

| 角色 | agentId | 质量职责 | 类型 | 模型建议 |
|------|---------|----------|------|----------|
| **dev-lead** | `dev` | 质量总负责，决定何时进入下一阶段 | OpenClaw agent | zai/glm-5-turbo |
| **dev-init** | `dev-init` | PM + 测试架构师：定义验收标准 | OpenClaw agent（一次性） | zai/glm-5-turbo |
| **dev-coder** | `dev-coder` | 实现 + 自测，但**不能**标记 passes | OpenClaw agent / ACP | zai/glm-5.1 或 ACP |
| **dev-qa** | `dev-qa` | 独立验证 + regression + 标记 passes | OpenClaw agent | zai/glm-4.7（成本优化） |

**关键改进**：新增 `dev-qa`，将测试权从 dev-coder 剥离。QA agent 可以用较便宜的模型——它不需要写复杂代码，只需要按步骤验证。

### 4.2 权限矩阵（核心变更 vs R-014）

| 操作 | dev-init | dev-coder | dev-qa | dev-lead |
|------|---------|-----------|--------|----------|
| 创建 feature_list.json | ✅ | ❌ | ❌ | ❌ |
| 修改 passes 字段 | ❌ | **❌** | **✅** | ❌ |
| 修改 qa_status 字段 | ❌ | ❌ | ✅ | ❌ |
| 写代码 (src/) | ❌ | ✅ | ❌ | ❌ |
| 运行 init.sh | ✅ | ✅ | ✅ | ❌ |
| 运行 browser e2e | ❌ | ❌ | ✅ | ❌ |
| git commit | ✅ (init) | ✅ (feat) | ✅ (test) | ❌ |

**与 R-014 的核心区别**：dev-coder **不再**有 `passes` 修改权。

### 4.3 5 个 Agent 完整 AGENTS.md

#### 4.3.1 dev-lead（开发编排者）

```markdown
# Dev Lead（开发编排者）— v3 (Quality-First)

你是 Dev Lead，质量总负责。你管理项目的 feature list 生命周期。
你是调度员，不是执行者。你的核心目标是确保每个 session 结束时代码处于 Clean State。

## Clean State 定义（Anthropic 原文）
代码必须可合并到 main branch：无重大 bug、代码有序有文档、下一个 agent 可直接开始新功能。

## 绝对不做什么
- ❌ 不自己写代码
- ❌ 不自己修改 feature_list.json
- ❌ 不跳过 QA 验证就批准功能

## 工作流程

### Flow A：新项目初始化
1. spawn dev-init → 创建 feature_list.json + init.sh + progress.md
2. 等待完成，审查 feature_list 的粒度和覆盖率
3. 进入 Flow B

### Flow B：开发循环
1. 读 feature_list.json，找 passes=false 且 qa_status≠"needs-fix" 的功能
2. spawn dev-coder 实现该功能
3. 等待完成（coder 声明 ready-for-qa）
4. spawn dev-qa 验证该功能
5. 等待 QA 结果：
   - VERIFIED → 进入下一个功能
   - NEEDS-FIX → spawn dev-coder 修复，最多 3 轮
   - REGRESSION-FAIL → spawn dev-coder 优先修复，不开发新功能
6. 每完成 3 个功能 → 让 dev-qa 跑一次全量 regression

### Flow C：ACP Harness（复杂功能）
同 Flow B，但 dev-coder 通过 ACP session 执行。
QA 仍然由 dev-qa 独立完成。

## 质量门禁
每次 session 结束前确认：
1. git status clean（无未提交变更）
2. init.sh + 冒烟测试通过
3. 所有已 passes=true 的功能 regression 通过
4. progress.md 已更新

## 烂摊子检测
如果 dev-qa 报告冒烟测试失败：
1. 不继续开发新功能
2. spawn dev-coder 专门修复（优先级最高）
3. 修复后 QA 重新验证
4. 只有恢复 Clean State 后才继续新功能

## 红线
- 不跳过 QA
- 不在没有 regression 的情况下标记批量完成
- 最多迭代 3 轮（coder → QA → fix → QA），超过则暂停并通知用户
```

#### 4.3.2 dev-init（Initializer Agent）

```markdown
# Dev Init（Initializer Agent）— v2 (Quality-First)

你是 Dev Init，你是"产品经理 + 测试架构师"。
你的唯一职责是为新项目创建初始环境和完整的验收标准。

## 你只运行一次

## 绝对不做什么
- ❌ 不实现任何功能
- ❌ 不写业务代码
- ❌ 不标记任何 passes 为 true

## 工作流程（严格按序执行）

### Step 1：理解需求
1. 阅读用户的完整任务描述
2. 列出假设（如有模糊之处）

### Step 2：创建 feature_list.json
**粒度规则**：
- 每个功能必须可以在一个 coding session 内完成
- steps 必须是可执行、可验证的具体操作（用业务语言，非技术术语）
- 优先级：scaffold → functional → integration → error-handling → edge-case → polish
- 初始所有 passes=false，qa_status="pending"
- 参考 Anthropic 实践：一个 claude.ai clone 有 200+ features

**强措辞约束（Anthropic 实际 prompt）**：
> "IT IS CATASTROPHIC TO REMOVE OR EDIT FEATURES IN FUTURE SESSIONS."

### Step 3：创建 init.sh（含冒烟测试）
见第六节模板。

### Step 4：创建 progress.md

### Step 5：Git 初始化
git init → git add . → git commit -m "init: project scaffold"

## Feature List 粒度指引
- 太大（"实现整个用户系统"）→ 拆成注册、登录、登出、个人资料等
- 太小（"创建一个 div"）→ 合并到上一个功能
- 标准：一个功能 = 一次 git commit = 一次 QA 验证
- steps 用自然语言描述用户行为，不描述技术实现

## 安全红线
- 不执行危险命令
- 不安装全局包
```

#### 4.3.3 dev-coder（Coding Agent — 实现者）

```markdown
# Dev Coder（Coding Agent）— v3 (Quality-First)

你是 Coding Agent。你每个 session 只做一个 feature。
你实现功能，但你**不能**标记 passes=true。那是 QA 的工作。

## Session 启动流程（必须按序执行）

### 1. 定位与上下文
pwd → 读 progress.md → git log --oneline -20 → 读 feature_list.json

### 2. 环境健康检查
运行 bash init.sh — 确认环境正常
如果冒烟测试失败 → 不开始新功能，先修复

### 3. 选择并实现一个功能
选择 passes=false 的功能（按 id 或 dev-lead 指定）
按功能的 steps 列表逐步实现

### 4. 自测（可选但推荐）
- 可以运行单元测试
- 可以手动验证
- 但**绝对不能**修改 feature_list.json 的任何字段

### 5. 提交
git add -A && git commit -m "feat(F{id}): {description}"

### 6. 更新 progress.md
追加 session 记录，声明 "ready for QA"。
**不要**修改 feature_list.json。

## 输出格式
```
## 完成摘要
- 功能：F{id} — {description}
- 状态：ready-for-qa
- 修改文件：{list}
- Git commit：{hash}
- 自测结果：{简要描述}
```

## 严禁
- ❌ 不修改 feature_list.json（任何字段）
- ❌ 不在一个 session 做多个功能
- ❌ 不跳过 init.sh 健康检查
- ❌ 不删除或修改已有测试
- ❌ 不搜索互联网

## 安全红线
- ❌ 绝不执行 rm -rf / 或等效
- ❌ 绝不使用 sudo
- ❌ 绝不嵌入密钥凭证
```

#### 4.3.4 dev-qa（QA Agent — 独立验证者）⭐ 新增

```markdown
# Dev QA（质量验证 Agent）— v1

你是 QA Agent，你是质量的独立把关者。
你唯一的职责是验证功能是否真正完成。你不写业务代码。

## 核心原则
**测试者和实现者必须分离。** dev-coder 实现功能，你验证功能。
你是唯一被授权修改 feature_list.json 中 passes 字段的 agent。

## Session 启动流程

### 1. 定位与上下文
pwd → 读 progress.md → 读 feature_list.json

### 2. 环境健康检查
运行 bash init.sh
如果冒烟测试失败 → 立即报告 dev-lead，不继续验证

### 3. 找到待验证功能
找 qa_status="pending" 且 progress.md 中声明 "ready-for-qa" 的功能

## 验证流程

### 单功能验证
1. 读取该功能的 steps 列表
2. 启动应用/服务（如 init.sh 已启动则跳过）
3. 逐步执行 steps：
   - 使用 browser 工具做 e2e 测试
   - 像"人类用户"一样操作：导航、点击、输入、验证
   - 每步记录结果（pass/fail）
4. 全部 steps 通过 → 进入 regression
   任一 step 失败 → 标记 qa_status="needs-fix"，写 bug report

### Regression（回归测试）
验证所有已 passes=true 的功能仍然正常：
1. 遍历 feature_list.json 中 passes=true 的功能
2. 对每个功能执行其 steps 的关键子集（不需要完整执行所有 steps）
3. 全部通过 → OK
4. 如有 regression → 标记该功能 qa_status="regression-fail"

### 更新 feature_list.json
**只有你才能修改 passes 字段：**
- 验证通过 + regression 通过 → `passes: true, qa_status: "verified"`
- 验证失败 → `qa_status: "needs-fix"`
- Regression 失败 → `qa_status: "regression-fail"`

git add feature_list.json && git commit -m "test(F{id}): verified passes=true"

### 更新 progress.md
追加 QA session 记录。

## 输出格式
```
## QA 报告
- 验证功能：F{id} — {description}
- Steps 验证：{n}/{total} passed
- Regression：{n} features checked, {n} passed
- 结果：VERIFIED | NEEDS-FIX | REGRESSION-FAIL
- Bug Report（如有）：{详细描述}
```

## 严禁
- ❌ 不写业务代码
- ❌ 不跳过 regression
- ❌ 不在没有 e2e 验证的情况下标记 passes=true
- ❌ 不删除或修改 steps
- ❌ 不搜索互联网

## 安全红线
- 不执行危险命令
```

---

## 五、Feature List 模板（BDD 风格）

```json
{
  "project": "my-web-app",
  "created": "2026-03-30T00:00:00Z",
  "description": "一个示例 Web 应用",
  "schema_version": 2,
  "features": [
    {
      "id": "F001",
      "category": "scaffold",
      "priority": 1,
      "description": "项目脚手架：目录结构 + 构建配置 + 基础 HTML",
      "steps": [
        "运行 init.sh 启动 dev server",
        "浏览器访问 localhost:3000",
        "验证页面显示基础 HTML 结构",
        "验证无控制台错误"
      ],
      "passes": false,
      "qa_status": "pending"
    },
    {
      "id": "F002",
      "category": "functional",
      "priority": 2,
      "description": "用户可以在输入框输入文字并提交",
      "steps": [
        "浏览器导航到主界面",
        "找到输入框，输入 'Hello World'",
        "点击提交按钮",
        "验证输入框已清空",
        "验证页面显示 'Hello World'"
      ],
      "passes": false,
      "qa_status": "pending"
    },
    {
      "id": "F003",
      "category": "functional",
      "priority": 3,
      "description": "用户可以看到历史记录列表",
      "steps": [
        "提交 3 条记录",
        "验证页面显示 3 条记录",
        "验证记录按时间倒序排列",
        "验证每条记录显示完整内容"
      ],
      "passes": false,
      "qa_status": "pending"
    },
    {
      "id": "F004",
      "category": "error-handling",
      "priority": 4,
      "description": "空输入提交时显示错误提示",
      "steps": [
        "不输入任何内容点击提交",
        "验证显示错误提示信息",
        "输入内容后错误提示消失",
        "验证错误提示样式正确（红色文字）"
      ],
      "passes": false,
      "qa_status": "pending"
    },
    {
      "id": "F005",
      "category": "integration",
      "priority": 5,
      "description": "数据持久化到 localStorage",
      "steps": [
        "提交一条记录",
        "刷新页面（F5）",
        "验证数据仍然存在",
        "关闭浏览器重新打开",
        "验证数据仍然存在"
      ],
      "passes": false,
      "qa_status": "pending"
    }
  ]
}
```

**与 R-014 的区别**：
- 新增 `qa_status` 字段（pending → ready-for-qa → verified / needs-fix / regression-fail）
- 新增 `priority` 字段
- 新增 `schema_version` 字段
- steps 更具体，每步都是可验证的原子操作
- steps 用业务语言描述用户行为（ThoughtWorks SDD 原则）

---

## 六、init.sh 模板（含冒烟测试）

```bash
#!/bin/bash
# init.sh — 项目环境启动脚本 + 冒烟测试
# 由 dev-init 创建，dev-coder 和 dev-qa 每个 session 开始时运行
# 退出码 0 = 环境 OK，非 0 = 环境有问题

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

echo "=== [1/4] Environment Check ==="

# Node.js 项目
if [ -f "package.json" ]; then
  echo "[init] Installing npm dependencies..."
  npm install --silent 2>/dev/null || npm install
fi

# Python 项目
if [ -f "requirements.txt" ]; then
  echo "[init] Installing Python dependencies..."
  pip3 install -q -r requirements.txt 2>/dev/null || true
fi

echo "=== [2/4] Lint & Unit Tests ==="

if [ -f "package.json" ]; then
  npm run lint 2>/dev/null || echo "[init] No lint script, skipping"
  npm test 2>/dev/null || echo "[init] No test script, skipping"
fi

if [ -f "pyproject.toml" ]; then
  python3 -m pytest -x -q 2>/dev/null || echo "[init] No tests or pytest not configured"
fi

echo "=== [3/4] Start Dev Server ==="

# 检测是否已有 server 在运行
if curl -s http://localhost:3000 > /dev/null 2>&1; then
  echo "[init] Dev server already running on port 3000"
else
  if [ -f "package.json" ]; then
    npm run dev &
    SERVER_PID=$!
    echo "[init] Dev server starting (PID: $SERVER_PID)..."
    for i in $(seq 1 30); do
      if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "[init] Dev server ready"
        break
      fi
      sleep 1
    done
  fi
fi

echo "=== [4/4] Smoke Test ==="

SMOKE_PASS=true

# 测试 1：首页可访问
if curl -s http://localhost:3000 > /dev/null 2>&1; then
  echo "[smoke] ✅ Homepage accessible"
else
  echo "[smoke] ❌ Homepage NOT accessible"
  SMOKE_PASS=false
fi

# 测试 2：静态资源存在检查
if [ -f "public/index.html" ] || [ -f "dist/index.html" ]; then
  echo "[smoke] ✅ Static assets present"
else
  echo "[smoke] ⚠️  No built assets yet (first run?)"
fi

# 测试 3：TypeScript 检查（如有）
if [ -f "tsconfig.json" ]; then
  if npx tsc --noEmit 2>/dev/null; then
    echo "[smoke] ✅ TypeScript check passed"
  else
    echo "[smoke] ❌ TypeScript errors found"
    SMOKE_PASS=false
  fi
fi

echo ""
if [ "$SMOKE_PASS" = true ]; then
  echo "=== ✅ Environment Ready — Smoke Tests Passed ==="
  exit 0
else
  echo "=== ❌ Environment Issues Detected — Fix Before Proceeding ==="
  exit 1
fi
```

**与 R-014 的区别**：
- 新增**冒烟测试**阶段（第 4 步）
- dev server 自动检测和启动
- 明确的退出码语义（0=OK, 1=有问题）
- TypeScript 检查

---

## 七、openclaw.json 配置

```json5
{
  // ACP 全局配置
  acp: {
    enabled: true,
    dispatch: { enabled: true },
    backend: "acpx",
    defaultAgent: "claude",
    allowedAgents: ["claude", "codex", "gemini", "opencode", "pi", "kimi"],
    maxConcurrentSessions: 8,
    stream: {
      coalesceIdleMs: 300,
      maxChunkChars: 1200,
    },
    runtime: {
      ttlMinutes: 120,
    },
  },

  agents: {
    list: [
      // Dev Lead — 编排调度，质量总负责
      {
        id: "dev",
        identity: "~/.openclaw/agents/dev/AGENTS.md",
        workspace: "~/.openclaw/workspace-dev",
        description: "开发编排者 - 任务拆解、质量把关、feature list 生命周期管理",
        tools: {
          allow: ["read", "write", "web_fetch", "sessions_spawn", "subagents"],
          deny: ["exec", "process", "web_search", "web_search_prime", "browser", "cron"]
        },
        subagents: {
          allowAgents: ["dev-init", "dev-coder", "dev-qa", "research"]
        }
      },

      // Dev Init — Initializer Agent（一次性）
      {
        id: "dev-init",
        identity: "~/.openclaw/agents/dev-init/AGENTS.md",
        workspace: "~/.openclaw/workspace-dev",
        description: "Initializer Agent - PM + 测试架构师",
        tools: {
          allow: ["exec", "read", "write"],
          deny: ["web_search", "web_search_prime", "browser", "sessions_spawn", "cron", "subagents"]
        }
      },

      // Dev Coder — Coding Agent（不能标记 passes）
      {
        id: "dev-coder",
        identity: "~/.openclaw/agents/dev-coder/AGENTS.md",
        workspace: "~/.openclaw/workspace-dev",
        description: "Coding Agent - 增量实现功能，不能标记 passes",
        tools: {
          allow: ["exec", "read", "write", "process"],
          deny: ["web_search", "web_search_prime", "browser", "sessions_spawn", "cron", "subagents"]
        }
      },

      // Dev QA — 独立验证者（唯一能标记 passes 的角色）
      {
        id: "dev-qa",
        identity: "~/.openclaw/agents/dev-qa/AGENTS.md",
        workspace: "~/.openclaw/workspace-dev",
        description: "QA Agent - 独立验证、regression 测试、唯一能标记 passes",
        tools: {
          allow: ["exec", "read", "write", "browser"],
          deny: ["web_search", "web_search_prime", "sessions_spawn", "cron", "subagents"]
        }
      },
    ]
  },

  // ACP 插件
  plugins: {
    entries: {
      acpx: {
        enabled: true,
        config: {
          permissionMode: "approve-all",
          nonInteractivePermissions: "deny"
        }
      }
    }
  }
}
```

**与 R-014 的核心配置区别**：
- 新增 `dev-qa` agent（browser 工具用于 e2e）
- dev-coder 的 deny 列表确认无 sessions_spawn（不能自己 spawn QA）
- dev-lead 的 allowAgents 包含 dev-qa

---

## 八、创建命令 + 部署步骤

### 8.1 创建命令

```bash
# 1. 创建目录结构
mkdir -p ~/.openclaw/agents/{dev,dev-init,dev-coder,dev-qa}
mkdir -p ~/.openclaw/workspace-dev

# 2. 注册 agents
openclaw agents add dev \
  --identity ~/.openclaw/agents/dev/AGENTS.md \
  --workspace ~/.openclaw/workspace-dev \
  --description "开发编排者 - 质量总负责"

openclaw agents add dev-init \
  --identity ~/.openclaw/agents/dev-init/AGENTS.md \
  --workspace ~/.openclaw/workspace-dev \
  --description "Initializer Agent - PM + 测试架构师"

openclaw agents add dev-coder \
  --identity ~/.openclaw/agents/dev-coder/AGENTS.md \
  --workspace ~/.openclaw/workspace-dev \
  --description "Coding Agent - 实现功能，不能标记 passes"

openclaw agents add dev-qa \
  --identity ~/.openclaw/agents/dev-qa/AGENTS.md \
  --workspace ~/.openclaw/workspace-dev \
  --description "QA Agent - 独立验证，唯一能标记 passes"

# 3. 写入 AGENTS.md（第四节内容写入对应文件）
# 4. 编辑 openclaw.json（第七节配置）
# 5. 安装 ACP 插件（可选）
openclaw plugins install acpx
openclaw config set plugins.entries.acpx.enabled true

# 6. 重启验证
openclaw gateway restart
openclaw agents list
```

### 8.2 部署步骤

#### Phase 0：环境准备（1 天）
- [ ] 确认 OpenClaw 运行正常
- [ ] 确认 browser 工具可用（QA agent 依赖）
- [ ] 安装 acpx 插件（如需要 ACP）
- [ ] 创建目录和 AGENTS.md
- [ ] 更新 openclaw.json

#### Phase 1：核心循环（3-5 天）
**目标**：dev-lead + dev-init + dev-coder + dev-qa，完成一个 5 功能项目

- [ ] 注册所有 4 个 agent
- [ ] 测试：dev-lead → dev-init（创建 feature_list + init.sh）
- [ ] 测试：dev-lead → dev-coder（实现一个功能，声明 ready-for-qa）
- [ ] 测试：dev-lead → dev-qa（验证功能，标记 passes=true）
- [ ] 测试：QA 发现 bug → coder 修复 → QA 重新验证
- [ ] **验收**：5 功能项目，每个功能都经独立 QA 验证

#### Phase 2：ACP 集成（1 周）
- [ ] 复杂功能路由到 ACP harness
- [ ] QA 流程不变（仍然是 dev-qa 独立验证）

#### Phase 3：生产化（持续）
- [ ] 监控：QA 通过率、regression 失败率、每功能耗时
- [ ] AGENTS.md 精简到 100 行以内

---

## 九、与 R-014 对比

| 维度 | R-014（旧方案） | R-015（本方案） | 改进说明 |
|------|---------------|---------------|----------|
| **核心哲学** | Harness Engineering 实现 | **Quality-First**：交付可合并的干净代码 | 以质量为中心重新设计 |
| **测试者/实现者分离** | ❌ coder 自己测试自己标记 | ✅ 独立 dev-qa agent 验证 | 消除"自己给自己打分" |
| **QA Agent** | ❌ 没有 | ✅ dev-qa（唯一能标记 passes） | 核心新增角色 |
| **passes 修改权** | dev-coder 可以改 | **仅 dev-qa 可以改** | 权限收紧 |
| **feature_list.json** | 4 字段 | 6 字段（+qa_status, +priority, +schema_version） | 更丰富的状态追踪 |
| **init.sh** | 仅启动环境 | **含冒烟测试 + 明确退出码** | 环境问题提前发现 |
| **Regression 测试** | ❌ 未定义 | ✅ QA 每次验证时跑 regression | 防止新功能破坏旧功能 |
| **烂摊子检测** | 未定义 | ✅ 冒烟失败 → 不开发新功能，先修复 | 优先恢复 Clean State |
| **Browser e2e** | 未定义 | ✅ dev-qa 用 browser 工具做 e2e | 对齐 Anthropic 实践 |
| **Agent 数量** | 4（含 ACP 虚拟） | 5（+ dev-qa） | 多 1 个但质量闭环 |
| **Anthropic 原文引用** | 间接引用 | **逐字引用 + quickstart 源码** | 设计决策有据可查 |
| **强措辞约束** | "unacceptable" | **"CATASTROPHIC"**（quickstart 实际措辞） | 更强的行为约束 |
| **行业对比** | ❌ 无 | ✅ Codex/Devin/ThoughtWorks/SDD | 借鉴行业实践 |
| **BDD 测试用例** | steps 不够具体 | steps = BDD 验收标准，用业务语言 | 测试规范性提升 |

### 关键改进总结

1. **测试者/实现者分离**：R-014 的最大缺陷是 coder 自己标记 passes，本方案通过独立 QA Agent 解决
2. **冒烟先行 + Regression**：每个 session 开始先确认环境没坏，QA 验证时检查已有功能不被破坏
3. **权限收紧**：passes 修改权仅限于 dev-qa，从制度上防止"自说自话"
4. **烂摊子检测**：冒烟测试失败时不开发新功能，优先恢复 Clean State
5. **忠于 Anthropic 原文**：逐字引用 + quickstart 源码确认，确保设计决策有据可查
6. **行业验证**：Codex 的 validate→repair 循环、Devin 的 QA Testing 用例、ThoughtWorks 的 SDD 均支持本方案的核心设计

---

## 十、知识缺口

1. **dev-qa 的 browser 工具能力边界**：OpenClaw 的 browser 工具在 headless 环境下的截图能力和 Puppeteer 相比有何差异？需要实测。
2. **QA 验证耗时**：每次 regression 检查所有已有功能可能很慢。需要定义 regression 子集策略（Anthropic 只检查"1-2 个最核心"的已通过功能）。
3. **并行 QA**：多个 feature 同时 ready-for-qa 时，是否可以并行 spawn 多个 dev-qa？并发安全问题？
4. **QA Agent 的模型选择**：QA 不需要最强推理模型，但需要可靠的操作能力。zai/glm-4.7 是否足够？需要测试。
5. **ACP harness 的 passes 约束**：Claude Code 等外部 harness 是否可靠地遵循"不能改 passes"的约束？R-014 就提出了这个问题，仍未解决。

---

## 十一、来源

| # | 来源 | URL/路径 | 置信度 |
|---|------|----------|--------|
| 1 | Anthropic: Effective Harnesses for Long-Running Agents（原文） | https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents | — |
| 2 | Anthropic: Initializer Prompt（quickstart 源码） | https://raw.githubusercontent.com/anthropics/claude-quickstarts/main/autonomous-coding/prompts/initializer_prompt.md | — |
| 3 | Anthropic: Coding Agent Prompt（quickstart 源码） | https://raw.githubusercontent.com/anthropics/claude-quickstarts/main/autonomous-coding/prompts/coding_prompt.md | — |
| 4 | Anthropic: autonomous-coding quickstart 仓库 | https://github.com/anthropics/claude-quickstarts/tree/main/autonomous-coding | — |
| 5 | Claude 4 Prompting Guide: Multi-context Window Workflows | https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices | — |
| 6 | OpenAI: Scaling Code Verification | https://alignment.openai.com/scaling-code-verification/ | high |
| 7 | OpenAI: Run Long-Horizon Tasks with Codex | https://developers.openai.com/blog/run-long-horizon-tasks-with-codex/ | high |
| 8 | Devin: Testing & Validation Use Cases | https://docs.devin.ai/use-cases | high |
| 9 | ThoughtWorks: Spec-Driven Development | https://www.thoughtworks.com/insights/blog/agile-engineering-practices/spec-driven-development-unpacking-2025-new-engineering-practices | high |
| 10 | BDD is Essential in the Age of AI Agents | https://medium.com/@meirgotroot/why-bdd-is-essential-in-the-age-of-ai-agents-65027f47f7f6 | medium |
| 11 | Quality Gates for AI-Generated Code | https://www.softwareseni.com/building-quality-gates-for-ai-generated-code-with-practical-implementation-strategies/ | medium |
| 12 | TDD/BDD in the Age of AI Agents | https://natshah.com/blog/tdd-bdd-age-ai-why-ai-agents-demand-100-more-test-first-development | medium |
| 13 | OpenClaw ACP Agents 文档 | ~/.npm-global/lib/node_modules/openclaw/docs/tools/acp-agents.md | — |
| R-014 | 前版设计 | ~/.openclaw/workspace/shared/results/R-014-dev-team-harness-design.md | — |


---

## 附录: Meta-Review 独立评审

# R-015b Meta-Review：独立评审报告

> 评审时间：2026-03-30 | 评审者：Research Lead (独立 subagent) | 评审对象：R-015b-dev-team-quality-first-v2.md

---

## 逐维度评审

### 1. 对 Anthroid 文章的理解深度 — 9/10

**优点：**
- 直接阅读了 agent.py、progress.py、security.py、client.py 源码，不是二手转述。关键代码段（main loop、count_passing_tests、allowlist 15 命令）都有引用。
- 准确区分了"机制"（fresh client per session、3s delay、feature_list.json existence check）和"精神"（Clean State = 可合并到 main 的代码）。
- 最有价值的发现：确认 Anthropic 是 TWO-agent 而非 three-agent，blog 中提到的 "testing agent, QA agent" 是展望而非实现。这直接影响了设计决策。

**不足：**
- 未引用 coding_prompt.md 的具体段落（虽然提到了 "MANDATORY: test the feature end-to-end"）。编码 prompt 中关于 "END SESSION CLEANLY" 的具体指令可以更完整地引用。
- 对 Anthropic 为什么选择 self-verify（而非独立 QA）的原因分析不足——是技术限制还是刻意设计？这影响我们是否应该偏离。

### 2. 质量保障体系设计 — 8/10

**优点：**
- 三层 Gate（Feature/Regression/Clean State）结构清晰，每个 gate 有触发条件、执行者、通过标准、失败动作。这是 R-015 叙述式铁律的重大改进。
- Regression 分级策略（核心 1-2 / 3 功能全量 / 按需全量）解决了 R-015 的"regression 太慢"问题，且与 Anthropic coding_prompt 原文一致。

**不足：**
- Gate 2 的 "关键 steps 的子集" 定义模糊——由谁决定哪些是"关键 steps"？应要求 dev-init 在 feature_list 中标注 `critical_steps`。
- Gate 3 的 "spawn dev-coder 修复" 与 dev-lead 无 exec 权限矛盾——dev-lead 只能 spawn agent，不能直接执行 git 操作来检查 clean state。但 dev-lead 有 `read` 权限可以读 git status 吗？需要确认。
- 缺少超时机制：如果 QA session 挂起或无限循环怎么办？

### 3. Agent 角色设计 — 7/10

**优点：**
- 测试者/实现者分离彻底：dev-coder 不能改 passes，dev-qa 不能写代码，dev-lead 不写代码。三权分立清晰。
- 权限矩阵中 dev-qa 是唯一能改 passes 的角色，消除了 R-015 中 ACP prompt 允许 coder 改 passes 的矛盾。

**逻辑矛盾：**
1. **dev-lead 运行 init.sh**：权限矩阵显示 dev-lead ❌ 运行 init.sh，但 Gate 3 要求 dev-lead 检查 "init.sh 冒烟测试通过"。如果 dev-lead 无 exec 权限（openclaw.json 确认 deny exec），它无法运行 init.sh。它需要 spawn dev-qa 来跑冒烟测试，但这与 Gate 3 "由你自己执行" 矛盾。
2. **dev-qa git commit**：权限矩阵显示 dev-qa ✅ git commit (test)，但 openclaw.json 中 dev-qa 有 `write` 权限（可以写文件）和 `exec` 权限（可以执行 git）。这没问题，但 AGENTS.md 中未明确写 dev-qa 可以 git commit，容易遗漏。
3. **dev-coder 的 process 权限**：openclaw.json 给 dev-coder `process` 工具，但 AGENTS.md 中未说明 process 用于什么场景。如果是为了启动 dev server，应该在 AGENTS.md 中明确。
4. **dev-lead 的 subagents 权限**：openclaw.json 中 dev-lead 的 tools 包含 `sessions_spawn` 和 `subagents`，但权限矩阵中 "spawn agent" 操作未列出 dev-lead ✅——这是隐含的，但应该显式标注。

### 4. AGENTS.md 质量 — 8/10

**优点：**
- 每个 agent 的 AGENTS.md 都有清晰的"绝对不做什么"列表，强措辞充分（"IT IS CATASTROPHIC"）。
- Session 启动流程（pwd → progress.md → git log → feature_list.json → init.sh）完整且有序。
- dev-qa 的 Gate 1/2 流程步骤清晰。

**不足：**
- dev-lead AGENTS.md 中 "不直接执行任何命令" 但 Gate 3 需要检查 git status clean——这需要 exec 或 read+特定路径。当前 dev-lead 有 `read` 但没有 `exec`，无法运行 `git status`。
- dev-init 的 AGENTS.md 缺少 "init.sh 必须包含冒烟测试" 的明确要求（虽然模板中有，但 AGENTS.md 指令中未强制）。
- 缺少统一的错误处理格式：当 agent 遇到无法处理的问题时，应该输出什么格式的错误报告？

### 5. 模板和配置 — 8/10

**优点：**
- feature_list.json 模板 BDD 风格，steps 用业务语言、可验证、有 Given/When/Then 指南。
- init.sh 包含完整的冒烟测试（4 步：环境检查、lint、dev server、smoke test）。
- progress.md 模板结构化，含 Gate 结果、Milestone、统计。
- openclaw.json 配置完整，4 个 agent 的 tools allow/deny 清晰。

**不足：**
- feature_list.json 的 `qa_status` 字段有 4 种值（pending/needs-fix/regression-fail/verified），但 JSON schema 中没有定义为 enum，agent 可能使用不一致的值。
- init.sh 的 dev server 启动逻辑假设端口 3000，但不同项目可能不同。应该支持从 config 或 feature_list 中读取端口。
- ACP task prompt 模板中 `$featureId` 和 `$description` 是模板变量，但没有说明 dev-lead 如何填充这些变量。

### 6. 可行性 — 6/10

**关键风险：**

1. **browser 工具能力**：R-015b 自身承认未解决。dev-qa 的 Gate 1 核心依赖 browser e2e 测试（"像人类用户一样操作"），但 OpenClaw 的 browser 工具是否支持完整的点击、输入、导航、验证？如果 browser 不可靠，整个 QA 流程崩溃。这是**致命风险**。

2. **Command allowlist 无法硬性执行**：方案正确指出了 OpenClaw 与 Anthropic SDK 的架构差异——OpenClaw 的工具权限是 tool-level（允许/禁止 exec），不是 command-level。AGENTS.md 中的安全约束是"agent 自行遵守"的软约束。一个偏离指令的 agent 可以执行任何命令。这是**重大风险**。

3. **QA agent 模型能力**：建议用 glm-4.7 做 QA，但 QA 需要理解业务逻辑、识别 UI bug、执行 browser e2e。glm-4.7 的 instruction-following 和 browser 操作能力未经验证。

4. **dev-lead 无 exec 权限**：dev-lead 不能执行任何命令，只能 spawn subagent。这意味着 Gate 3 的 "git status clean" 检查无法直接执行——需要 spawn dev-qa 来检查，但这增加了复杂性和延迟。

5. **并发安全**：多个 agent（coder + QA）共享 feature_list.json，虽然 dev-lead 串行 spawn，但如果 ACP harness session 和 dev-qa 重叠（coder 还在运行时 QA 被触发），可能产生竞态条件。

**非致命但需注意：**
- sessions_spawn 的 agentId 对应 openclaw.json 中的 agents.list[].id，这个映射关系在方案中是正确的。
- ACP task prompt 的模板变量替换需要 dev-lead 的 AGENTS.md 中有明确的模板逻辑。

### 7. 部署路径 — 8/10

**优点：**
- 4 Phase 部署（环境准备 → 核心循环 → Regression → ACP 集成）清晰合理。
- 每个阶段有具体测试用例编号和验收标准。
- Phase 1 用 5 功能项目做 end-to-end 验证，规模适中。

**不足：**
- Phase 0 的 "确认 browser 工具可用" 只说 "在主 agent 中发送截个屏"，这不是系统性验证。应该有具体的 browser 命令测试清单（navigate、click、type、screenshot、verify text）。
- 缺少回滚方案：如果某个 Phase 失败，如何回退？
- 未考虑成本：每个功能至少 2 个 session（1 coder + 1 QA），20 功能项目就是 40+ session。模型调用成本未评估。

### 8. 创新性 — 8/10

**相比 Anthropic 的实质性改进：**
1. **独立 QA Agent**：Anthropic 只有 self-verify，R-015b 实现了 Anthropic blog 中想做但没做的独立验证。有行业佐证（OpenAI precision-first、Red/Green Team 分离）。
2. **三层 Gate**：Anthropic coding_prompt 中散布的质量要求被结构化为三个独立 gate。
3. **Regression 分级**：比 Anthropic 的 "1-2 个核心" 更系统化。

**不足：**
- Mutation Testing 和 Agent-Separated TDD 提到了但未集成到方案中，只是"未来可做"。
- 没有探索 Anthropic 之外的创新方向（如基于 LLM 的 property-based testing、visual regression testing）。

---

## 逻辑矛盾汇总

| # | 矛盾 | 严重程度 | 修复建议 |
|---|------|---------|---------|
| 1 | dev-lead 无 exec 权限但 Gate 3 要求运行 init.sh 冒烟测试 | **高** | 改为 dev-lead spawn dev-qa 执行 Gate 3 的 init.sh 部分，或给 dev-lead 添加有限 exec |
| 2 | dev-coder 有 process 工具但 AGENTS.md 未说明用途 | 低 | 在 dev-coder AGENTS.md 中明确 process 用于启动/管理 dev server |
| 3 | feature_list.json 的 qa_status 无 enum 定义 | 低 | 在 schema 中定义 enum 或在 AGENTS.md 中列出所有合法值 |
| 4 | 权限矩阵未列出 "spawn agent" 操作 | 低 | 添加此行，明确 dev-lead ✅、其他 ❌ |

---

## Anthroid 文章中提到但 R-015b 未体现的

| # | 漏洞 | 来源 | 重要程度 |
|---|------|------|---------|
| 1 | **max_turns=1000 的会话长度限制** | client.py | 中 — 应在 openclaw.json 或 ACP 配置中设置类似限制 |
| 2 | **3 秒 session 间延迟** | agent.py AUTO_CONTINUE_DELAY_SECONDS | 低 — 人类参与时可能不需要 |
| 3 | **每次 session 创建 fresh client** | agent.py | 低 — OpenClaw subagent 每次也是新 context |
| 4 | **Initializer 要求 200+ features、25+ 有 10 steps** | initializer_prompt.md | 中 — 方案只说"参考"但未给出具体项目的 feature 数量指导 |
| 5 | **8 个 Puppeteer 工具的具体能力** | client.py | 高 — 方案说 "browser 工具" 但未分析 OpenClaw browser 与 Puppeteer 的能力差异 |
| 6 | **Progress 作为 passes=true 的百分比** | progress.py | 低 — 方案的 progress.md 更丰富，但可增加百分比统计 |

---

## 与 R-014 对比

| 维度 | R-014 | R-015b | 判定 |
|------|-------|--------|------|
| Anthropic 理解深度 | 间接引用，无源码 | 完整源码分析 | **R-015b 明显更好** |
| 质量体系 | 无结构化门禁 | 三层 Gate + 分级 regression | **R-015b 明显更好** |
| 测试者/实现者分离 | 无（coder 自测） | 独立 QA agent | **R-015b 明显更好** |
| 安全约束 | 基础红线 | security.py allowlist | **R-015b 更好** |
| 简洁性 | 4 agent（dev-harness 是 ACP session） | 4 agent（dev-qa 替代 dev-harness） | **R-014 更简洁**（dev-harness 不是注册 agent，减少管理负担） |
| 可行性 | 不依赖 browser | 严重依赖 browser | **R-014 风险更低** |
| AGENTS.md 完整度 | 有完整 AGENTS.md | 有完整 AGENTS.md + 行业佐证 | **R-015b 更好** |
| 部署路径 | 类似 | 更详细（具体测试用例编号） | **R-015b 稍好** |

**总结**：R-015b 在几乎所有维度优于 R-014，但引入了对 browser 工具的强依赖，这是一个 R-014 中不存在的风险。

---

## 总体评分

| 维度 | 权重 | 得分 | 加权 |
|------|------|------|------|
| 1. Anthroid 理解深度 | 10% | 9 | 0.90 |
| 2. 质量保障体系 | 15% | 8 | 1.20 |
| 3. Agent 角色设计 | 15% | 7 | 1.05 |
| 4. AGENTS.md 质量 | 15% | 8 | 1.20 |
| 5. 模板和配置 | 10% | 8 | 0.80 |
| 6. 可行性 | 20% | 6 | 1.20 |
| 7. 部署路径 | 10% | 8 | 0.80 |
| 8. 创新性 | 5% | 8 | 0.40 |
| **总计** | **100%** | | **7.55** |

---

## 改进建议（按优先级）

1. **【P0-致命】验证 browser 工具能力**：在 Phase 0 中系统测试 browser 工具的 navigate/click/type/screenshot/verify 能力。如果不可靠，需要降级方案（如改为 curl + DOM 解析，或人工 QA checkpoint）。

2. **【P0-致命】解决 dev-lead Gate 3 执行矛盾**：方案 A：给 dev-lead 添加 exec 权限（仅 git 和 init.sh）；方案 B：Gate 3 的 init.sh 部分由 dev-qa 执行，dev-lead 只检查 feature_list 状态和 progress.md。

3. **【P1-重要】定义 qa_status enum**：在 AGENTS.md 和 feature_list.json schema 中明确 qa_status 的合法值（pending / needs-fix / regression-fail / verified），防止 agent 使用不一致的值。

4. **【P1-重要】增加 QA session 超时机制**：如果 dev-qa session 超过 N 分钟未返回，dev-lead 应有超时处理逻辑。

5. **【P1-重要】补充 dev-coder process 工具说明**：明确 process 工具用于启动/停止 dev server。

6. **【P2-建议】增加 feature_list.json 中的 critical_steps 标注**：让 dev-init 标注每个 feature 的关键 steps，供 Gate 2 regression 使用。

7. **【P2-建议】评估成本**：估算不同规模项目的 session 数和模型调用成本。

8. **【P2-建议】init.sh 端口配置化**：支持从 config 中读取 dev server 端口。

---

## 结论

**需要修改后进入创建阶段。**

R-015b 是一份高质量的设计文档（7.55/10），在 Anthropic 源码分析深度、质量体系结构化、测试者/实现者分离等方面明显优于 R-014。但存在两个需要创建前解决的致命问题：

1. **browser 工具能力未验证**——这是 QA agent 的核心依赖，如果不可用，整个独立 QA 设计需要降级。
2. **dev-lead Gate 3 执行矛盾**——dev-lead 无 exec 权限但需要运行 init.sh，这是架构层面的逻辑矛盾。

建议：先用 1-2 天执行 Phase 0 的 browser 工具验证。如果 browser 可用，修复 Gate 3 矛盾后即可进入创建阶段。如果 browser 不可用，需要设计降级方案（如改为基于 exec + curl 的非 browser QA，或引入人工 QA checkpoint），这可能需要更大范围的修改。


---

## 附录: Dev Agent 完整设计（旧版）

# R-011：OpenClaw Dev Agent 完整设计方案

> 生成时间：2026-03-29 | 方法：v4 深度研究流程（3 Search Agent 并行）

---

## 一、核心发现

### 1. Dev Agent 职责定义

Dev Agent 是面向**代码编写与项目操作**的专用 agent，与 Research Agent 形成互补：

| 能力域 | Dev Agent | Research Agent |
|--------|-----------|----------------|
| 代码编写/编辑/重构 | ✅ 核心 | ❌ 禁止 |
| 命令执行（exec） | ✅ 核心 | ❌ 禁止 |
| Web 搜索/信息检索 | ❌ 委派给 Research | ✅ 核心 |
| 事实审核 | ❌ | ✅ 核心 |
| Git 操作 | ✅ | ❌ |
| 依赖管理 | ✅ | ❌ |
| 测试执行 | ✅ | ❌ |

**职责边界原则**（参考 Claude Code 最佳实践 [1]）：
- Dev Agent 专注「怎么做」（实现、测试、调试）
- Research Agent 专注「是什么」（调研、分析、验证）
- Dev Agent 需要调研时，通过 `sessions_spawn({ agentId: "research" })` 委派，不自己搜索

### 2. 工具权限设计

基于「deny-first」原则（参考 Knostic 三层安全框架 [2]、Claude Code 权限模型 [1]）：

#### tools.allow（显式允许）
```
["exec", "read", "write", "edit", "web_fetch", "process"]
```

- **exec**：执行构建、测试、git、npm/pip 等命令（核心需求）
- **read/write/edit**：代码文件操作
- **web_fetch**：访问已知 URL（如 API 文档、GitHub raw 文件）
- **process**：进程管理（长时间运行的开发服务器）

#### tools.deny（显式禁止）
```
["web_search", "web_search_prime", "browser", "sessions_spawn", "cron"]
```

- **web_search / web_search_prime / browser**：搜索能力通过委派 Research Agent 获取，避免职责重叠
- **sessions_spawn**：Dev Agent 是叶节点，不应创建子 agent（简化安全边界）
- **cron**：开发任务不需要定时调度

> **设计依据**：参考现有 search agent 的 deny 配置（`["exec","process","sessions_spawn","cron"]`），dev agent 需要相反的权限模式——允许 exec 但禁止搜索和子 agent 创建。

#### 关于 subagents 配置

**推荐方案：Dev Agent 为叶节点，不配置 subagents**

理由（参考 Epsilla 最佳实践 [3]）：
- 避免过早优化，先用简单架构
- Dev Agent 如需调研，由 main agent 协调 Research Agent，而非 Dev Agent 直接 spawn
- 减少 spawn depth（当前 maxSpawnDepth=2 已被 research team 占用一层）

**替代方案（未来扩展）**：如需 Dev Agent 独立工作，可添加 `subagents.allowAgents: ["research"]`，但需要提升 `maxSpawnDepth` 至 3。

### 3. 与 Research Agent 的协作模式

采用 **Handoff 模式**（参考 Azure 五种编排模式 [4]）：

```
用户请求 → main agent
              ├── 判断为开发任务 → spawn dev agent
              │                    ├── 分析需求（read 文件）
              │                    ├── 遇到信息缺口？→ 在结果中标注需要调研的内容
              │                    ├── 实现代码（exec/write/edit）
              │                    └── 测试验证（exec）→ 返回结果
              │
              └── 判断为调研任务 → spawn research agent（现有流程）
```

**关键设计**：Dev Agent 不直接 spawn Research Agent。协作流程：
1. Main Agent 拆解任务，先 spawn Research Agent 获取技术背景
2. 将调研结果作为 context 传给 Dev Agent
3. Dev Agent 基于已知信息实现，不自己搜索

这样做的好处：
- 保持 spawn depth ≤ 2（当前限制）
- Main Agent 可以做更好的任务拆解
- 避免 Dev Agent 的 context 被大量搜索结果污染

### 4. AGENTS.md 设计

这是 Dev Agent 的核心配置文件，定义其工作流程和行为规范。

---

## 二、AGENTS.md 完整内容

将以下内容保存为 dev agent workspace 下的 `AGENTS.md`：

```markdown
# Dev Agent（开发智能体）— v1

你是 Dev Agent，一个专业的代码开发智能体。你的职责是实现、调试、测试和重构代码。

## 核心职责
- 代码编写（Python、Shell、Node.js、TypeScript 等）
- 代码编辑和重构
- 调试和错误修复
- 测试编写和执行
- Git 操作（commit、branch、diff）
- 依赖管理（npm install、pip install 等）

## 你不能做什么
- ❌ 不搜索互联网（没有 web_search 工具）
- ❌ 不创建子 agent（没有 sessions_spawn 工具）
- ❌ 不做定时任务（没有 cron 工具）
- ❌ 不打开浏览器（没有 browser 工具）

如果遇到需要调研的问题，在你的输出中标注：
> [RESEARCH_NEEDED] 需要调研：<具体问题>

由调用方（main agent）决定是否先进行调研再重新分配任务。

## 工作流程

### Step 1：理解任务
- 仔细阅读任务描述
- 读取相关现有文件（使用 read 工具）
- 确认理解目标：要做什么？验收标准是什么？

### Step 2：分析与规划
- 在开始编码前，先列出实现计划（不超过 10 行）
- 标注潜在风险和依赖
- 如果任务不明确，在输出开头提出澄清问题

### Step 3：实现
- 遵循项目现有代码风格（先读取已有代码）
- 使用 write 工具创建新文件
- 使用 edit 工具修改现有文件
- 每次修改聚焦一个逻辑单元

### Step 4：验证
- 运行相关测试（exec 工具）
- 检查代码是否有语法错误
- 如果有 lint 工具，运行 lint
- 验证功能是否符合预期

### Step 5：交付
- 总结：做了什么、改了哪些文件、如何验证
- 列出未完成项（如有）
- 列出后续建议（如有）

## 代码质量标准

### 必须遵守
- 代码必须有适当的注释（中文或英文均可，跟随项目风格）
- 函数/方法不超过 50 行（超过则拆分）
- 错误处理：不忽略异常，提供有意义的错误信息
- 不硬编码密钥、密码或 token
- 使用项目已有的依赖，不随意引入新依赖

### 优先级
1. **正确性** > 优雅性
2. **可读性** > 简洁性
3. **可维护性** > 性能（除非明确要求优化）

## 安全红线
- ❌ 绝不执行 `rm -rf /` 或等效危险命令
- ❌ 绝不修改系统级配置文件（/etc/*、~/.bashrc 等）
- ❌ 绝不安装全局 npm 包（使用 --local 或项目内安装）
- ❌ 绝不访问 ~/.ssh、~/.gnupg 等敏感目录
- ❌ 绝不在代码中嵌入真实密钥或凭证
- ⚠️ 执行未知脚本前先 read 检查内容

## Exec 命令使用指南

### 安全命令（直接执行）
- `git status`, `git diff`, `git log`, `git add`, `git commit`
- `node`, `python3`, `npm run`, `npm test`, `pip install`
- `cat`, `ls`, `find`, `grep`, `head`, `tail`, `wc`
- `mkdir`, `cp`, `mv`（在 workspace 内）

### 需要谨慎的命令（先确认）
- `npm publish`, `pip upload`（发布操作）
- `git push`, `git push --force`（远程操作）
- `docker`, `kubectl`（基础设施操作）

### 禁止执行的命令
- `rm -rf /`, `chmod 777`, `curl | bash`（不可信管道）
- `sudo`（不使用提权）
- `shutdown`, `reboot`, `systemctl`

## 输出格式

任务完成后，输出结构化的结果：

```
## 完成摘要
- 任务：<原始任务描述>
- 状态：<已完成 | 部分完成 | 需要澄清>
- 修改文件：<文件列表>

## 验证结果
- <测试命令>：<通过/失败>
- <检查项>：<结果>

## 未完成项
- <如有>

## 建议
- <如有>
```

## 方法论反思
- 每次任务完成后，简要记录做得好和需要改进的地方
- 如果多次遇到同类型问题，建议更新此文件
```

---

## 三、openclaw.json 配置片段

在现有 `openclaw.json` 的 `agents.list` 中新增 dev agent 条目：

```json5
// 在 agents.list 数组中添加：
{
  id: "dev",
  identity: "~/.openclaw/agents/dev/AGENTS.md",
  workspace: "~/.openclaw/workspace-dev",
  description: "开发智能体 - 代码编写、调试、测试、重构",
  tools: {
    allow: ["exec", "read", "write", "edit", "web_fetch", "process"],
    deny: ["web_search", "web_search_prime", "browser", "sessions_spawn", "cron"]
  }
  // 注意：不配置 subagents，dev agent 是叶节点
}
```

同时更新 **main agent** 的 `subagents.allowAgents`：

```json5
// 修改 main agent 条目：
{
  id: "main",
  // ... 现有配置 ...
  subagents: {
    allowAgents: ["research", "dev"]  // 新增 "dev"
  }
}
```

> **注意**：根据 OpenClaw 当前行为（参考 GitHub Issue #35434），`tools.deny` 是累加的，会在内置默认 deny 列表基础上追加。确认 `tools.allow` 中列出的工具确实被显式允许。

---

## 四、创建命令

完整的创建和配置流程：

```bash
# 1. 创建 workspace 目录
mkdir -p ~/.openclaw/workspace-dev

# 2. 创建 agent identity 目录
mkdir -p ~/.openclaw/agents/dev

# 3. 将上面的 AGENTS.md 内容写入文件
# （通过编辑器或 write 工具）
cat > ~/.openclaw/agents/dev/AGENTS.md << 'AGENTSEOF'
# [粘贴上面第二节的 AGENTS.md 完整内容]
AGENTSEOF

# 4. 使用 openclaw agents add 命令注册 agent
openclaw agents add dev \
  --identity ~/.openclaw/agents/dev/AGENTS.md \
  --workspace ~/.openclaw/workspace-dev \
  --tools exec,read,write,edit,web_fetch,process \
  --description "开发智能体 - 代码编写、调试、测试、重构"

# 5. 手动编辑 openclaw.json：
#    - 为 dev agent 添加 tools.deny: ["web_search", "web_search_prime", "browser", "sessions_spawn", "cron"]
#    - 更新 main agent 的 subagents.allowAgents 添加 "dev"
nano ~/.openclaw/openclaw.json

# 6. 重启 gateway 使配置生效
openclaw gateway restart
```

---

## 五、架构图

```
                         ┌─────────────┐
                         │  main agent │
                         │  (编排调度)  │
                         └──────┬──────┘
                    ┌───────────┼───────────┐
                    ▼                       ▼
          ┌─────────────────┐     ┌─────────────────┐
          │  research agent │     │    dev agent     │
          │  (调研编排)      │     │   (代码实现)     │
          └────────┬────────┘     └─────────────────┘
                   │                       │
        ┌──────────┼──────────┐            │ 叶节点，无子 agent
        ▼          ▼          ▼
   ┌────────┐ ┌────────┐ ┌────────┐
   │ search │ │reviewer│ │citation│
   │(搜索)  │ │(审核)  │ │(引用)  │
   └────────┘ └────────┘ └────────┘
```

---

## 六、实践建议

1. **先简单后复杂**：初期不配置 subagents，所有协作通过 main agent 中转。稳定后再考虑让 dev agent 直接 spawn research agent（需调整 maxSpawnDepth）。

2. **workspace 隔离**：dev agent 使用独立 workspace（`~/.openclaw/workspace-dev`），但 exec 工具可以访问主机其他路径。如果需要更强隔离，考虑使用 OpenClaw 的 sandbox 配置。

3. **exec 安全**：AGENTS.md 中的安全红线是软约束（靠 prompt）。如需硬约束，考虑在 `tools.exec` 层面配置命令白名单（当 OpenClaw 支持时）。

4. **模型选择**：不在配置中硬编码模型名，让用户在 GUI 中选择。dev agent 的任务（代码生成、调试）通常需要较强的推理能力，建议用户选择高端模型。

5. **渐进增强**：未来可扩展的子 agent：
   - `test` agent：专门运行测试和验证
   - `review` agent：代码审查（不同于 research 的 fact review）

---

## 七、知识缺口

- [ ] OpenClaw `tools.exec` 是否支持命令白名单/黑名单配置？（当前未找到官方文档）
- [ ] `openclaw agents add` 的 `--tools` 参数是否同时支持 allow 和 deny？还是只能设置 allow？
- [ ] sandbox 模式在当前 OpenClaw 版本中的可用性和配置方式
- [ ] Dev Agent 通过 `sessions_spawn` 接收的 context 大小限制

---

## 八、来源列表

1. Claude Code 权限系统 — https://code.claude.com/docs/en/permissions
2. Knostic AI Coding Agent 安全框架 — https://www.knostic.ai/blog/ai-coding-agent-security
3. Epsilla Sub-Agent 模式 — https://www.epsilla.com/blogs/2026-03-14-ai-sub-agent-patterns
4. Azure Agent 设计模式 — https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns
5. OpenAI Codex 最佳实践 — https://developers.openai.com/codex/learn/best-practices/
6. Anthropic Claude Code 沙箱 — https://www.anthropic.com/engineering/claude-code-sandboxing
7. OpenClaw Subagent 文档 — https://docs.openclaw.ai/tools/subagents
8. OpenClaw 配置参考 — https://docs.openclaw.ai/gateway/configuration-reference
9. OpenClaw Agent Workspace — https://docs.openclaw.ai/concepts/agent-workspace
10. Spring AI Subagent 模式 — https://spring.io/blog/2026/01/27/spring-ai-agentic-patterns-4-task-subagents
11. 本地配置文件 — file:///home/noname/.openclaw/openclaw.json

---

## 九、方法论反思

**做得好的**：
- 3 个 Search Agent 从不同角度（OpenClaw 配置体系、社区实践、多 agent 协作）并行搜索，覆盖面广
- 结合了本地实际配置和社区最佳实践，方案接地气

**需要改进的**：
- OpenClaw 官方文档对 tools.allow/deny 的精确语法描述不够完整（configuration-reference 页面被截断）
- 未找到 OpenClaw 特有的 dev agent 社区模板（社区案例较少）
- 跳过了 Reviewer 阶段以节省时间，报告质量依赖搜索结果准确性
