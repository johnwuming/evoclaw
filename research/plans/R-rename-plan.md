# Agent 重命名变更清单

> 生成时间：2026-04-04 17:43 GMT+8  
> 状态：✅ 审计完成

---

## 一、重命名对照表

| 旧 agentId | 新 agentId | 旧 name | 新 name |
|---|---|---|---|
| main | main | 小朱桑 | **不变** |
| research | research-lead | Research Lead | 研究主管 |
| search | research-searcher | Search Agent | 研究搜索员 |
| reviewer | research-reviewer | Reviewer Agent | 研究审核员 |
| citation | research-citation | Citation Agent | 研究引用员 |
| dev | dev-lead | Dev Lead | 开发主管 |
| dev-init | dev-designer | Dev Init | 开发设计师 |
| dev-coder | dev-coder | Dev Coder | 开发编码员 |
| dev-qa | dev-qa | Dev QA | 开发测试员 |

---

## 二、openclaw.json 变更清单

文件：`/root/.openclaw/openclaw.json`

### 2.1 main agent（不变，无需修改）

### 2.2 research → research-lead

| 行号 | 字段 | 旧值 | 新值 |
|------|------|------|------|
| 96 | `id` | `"research"` | `"research-lead"` |
| 97 | `name` | `"Research Lead"` | `"研究主管"` |
| 106-108 | `allowAgents[]` | `"search"`, `"reviewer"`, `"citation"` | `"research-searcher"`, `"research-reviewer"`, `"research-citation"` |

### 2.3 search → research-searcher

| 行号 | 字段 | 旧值 | 新值 |
|------|------|------|------|
| 114 | `id` | `"search"` | `"research-searcher"` |
| 115 | `name` | `"Search Agent"` | `"研究搜索员"` |

### 2.4 reviewer → research-reviewer

| 行号 | 字段 | 旧值 | 新值 |
|------|------|------|------|
| 124 | `id` | `"reviewer"` | `"research-reviewer"` |
| 125 | `name` | `"Reviewer Agent"` | `"研究审核员"` |

### 2.5 citation → research-citation

| 行号 | 字段 | 旧值 | 新值 |
|------|------|------|------|
| 136 | `id` | `"citation"` | `"research-citation"` |
| 137 | `name` | `"Citation Agent"` | `"研究引用员"` |

### 2.6 dev → dev-lead

| 行号 | 字段 | 旧值 | 新值 |
|------|------|------|------|
| 144 | `id` | `"dev"` | `"dev-lead"` |
| 145 | `name` | `"Dev Lead"` | `"开发主管"` |
| 153-156 | `allowAgents[]` | `"dev-init"`, `"dev-coder"`, `"dev-qa"` | `"dev-designer"`, `"dev-coder"`, `"dev-qa"` |

### 2.7 dev-init → dev-designer

| 行号 | 字段 | 旧值 | 新值 |
|------|------|------|------|
| 162 | `id` | `"dev-init"` | `"dev-designer"` |
| 163 | `name` | `"Dev Init"` | `"开发设计师"` |

### 2.8 dev-coder → dev-coder（id 不变）

| 行号 | 字段 | 旧值 | 新值 |
|------|------|------|------|
| 170 | `id` | `"dev-coder"` | `"dev-coder"`（不变） |
| 171 | `name` | `"Dev Coder"` | `"开发编码员"` |

### 2.9 dev-qa → dev-qa（id 不变）

| 行号 | 字段 | 旧值 | 新值 |
|------|------|------|------|
| 181 | `id` | `"dev-qa"` | `"dev-qa"`（不变） |
| 182 | `name` | `"Dev QA"` | `"开发测试员"` |

---

## 三、workspace 目录重命名清单

| 旧目录 | 新目录 | 状态 |
|--------|--------|------|
| `/root/.openclaw/workspace-search` | `/root/.openclaw/workspace-research-searcher` | 需重命名 |
| `/root/.openclaw/workspace-reviewer` | `/root/.openclaw/workspace-research-reviewer` | 需重命名 |
| `/root/.openclaw/workspace-citation` | `/root/.openclaw/workspace-research-citation` | 需重命名 |
| `/root/.openclaw/workspace-dev-init` | `/root/.openclaw/workspace-dev-designer` | 需重命名 |
| `/root/.openclaw/workspace-dev-coder` | 不变 | 无需修改 |
| `/root/.openclaw/workspace-dev-qa` | 不变 | 无需修改 |
| `/root/.openclaw/workspace-research` | 不变 | 无需修改 |
| `/root/.openclaw/workspace-dev` | 不变 | 无需修改 |

**说明：** workspace 目录名应与新的 agentId 保持一致，便于辨识。

---

## 四、agent 目录重命名清单

| 旧目录 | 新目录 | 状态 |
|--------|--------|------|
| `/root/.openclaw/agents/research/` | `/root/.openclaw/agents/research-lead/` | 需重命名 |
| `/root/.openclaw/agents/search/` | `/root/.openclaw/agents/research-searcher/` | 需重命名 |
| `/root/.openclaw/agents/reviewer/` | `/root/.openclaw/agents/research-reviewer/` | 需重命名 |
| `/root/.openclaw/agents/citation/` | `/root/.openclaw/agents/research-citation/` | 需重命名 |
| `/root/.openclaw/agents/dev/` | `/root/.openclaw/agents/dev-lead/` | 需重命名 |
| `/root/.openclaw/agents/dev-init/` | `/root/.openclaw/agents/dev-designer/` | 需重命名 |
| `/root/.openclaw/agents/dev-coder/` | 不变 | 无需修改 |
| `/root/.openclaw/agents/dev-qa/` | 不变 | 无需修改 |
| `/root/.openclaw/agents/main/` | 不变 | 无需修改 |

**注意：** 重命名 agent 目录后，还需同步更新 openclaw.json 中对应的 `agentDir` 字段路径。

---

## 五、AGENTS.md / SOUL.md 内容变更清单

### 5.1 `/root/.openclaw/workspace-research/AGENTS.md`

| 行号 | 变更类型 | 旧内容 | 新内容 |
|------|----------|--------|--------|
| 1 | 标题 | `# Research Lead（研究主管）— v4` | `# 研究主管 — v4` |
| 5 | 绝对不做什么 | `❌ 不自己搜索（交给 Search Agent）` | `❌ 不自己搜索（交给 研究搜索员）` |
| 6 | 绝对不做什么 | `❌ 不自己审核（交给 Reviewer）` | `❌ 不自己审核（交给 研究审核员）` |
| 7 | 绝对不做什么 | `❌ 不自己处理引用（交给 Citation Agent）` | `❌ 不自己处理引用（交给 研究引用员）` |
| 12 | 团队成员表 | `\| Search Agent \|`search` \|` | `\| 研究搜索员 \|`research-searcher` \|` |
| 13 | 团队成员表 | `\| Reviewer Agent \|`reviewer` \|` | `\| 研究审核员 \|`research-reviewer` \|` |
| 14 | 团队成员表 | `\| Citation Agent \|`citation` \|` | `\| 研究引用员 \|`research-citation` \|` |
| 79 | spawn 调用 | `agentId: "search"` | `agentId: "research-searcher"` |
| 105 | spawn 调用 | `agentId: "reviewer"` | `agentId: "research-reviewer"` |
| 112 | spawn 调用 | `agentId: "reviewer"` | `agentId: "research-reviewer"` |
| 126 | 收敛步骤 | `1. spawn Citation Agent 验证引用` | `1. spawn 研究引用员验证引用` |

### 5.2 `/root/.openclaw/workspace-research/SOUL.md`

Research Lead 的 SOUL.md 内嵌了完整 AGENTS.md 内容，需要同步修改以下位置：

| 行号 | 变更类型 | 旧内容 | 新内容 |
|------|----------|--------|--------|
| 29 | 标题 | `# Research Lead（研究主管）— v4` | `# 研究主管 — v4` |
| 37 | 绝对不做什么 | `❌ 不自己搜索（交给 Search Agent）` | `❌ 不自己搜索（交给 研究搜索员）` |
| 38 | 绝对不做什么 | `❌ 不自己审核（交给 Reviewer）` | `❌ 不自己审核（交给 研究审核员）` |
| 39 | 绝对不做什么 | `❌ 不自己处理引用（交给 Citation Agent）` | `❌ 不自己处理引用（交给 研究引用员）` |
| 42 | 团队成员表 | `\| Search Agent \|`search` \|` | `\| 研究搜索员 \|`research-searcher` \|` |
| 43 | 团队成员表 | `\| Reviewer Agent \|`reviewer` \|` | `\| 研究审核员 \|`research-reviewer` \|` |
| 44 | 团队成员表 | `\| Citation Agent \|`citation` \|` | `\| 研究引用员 \|`research-citation` \|` |
| 74 | spawn 模板 | `你是 Search Agent。执行以下搜索任务：` | `你是研究搜索员。执行以下搜索任务：` |

### 5.3 `/root/.openclaw/workspace-search/AGENTS.md`

| 行号 | 变更类型 | 旧内容 | 新内容 |
|------|----------|--------|--------|
| 1 | 标题 | `# Search Agent（搜索研究员）` | `# 研究搜索员` |

### 5.4 `/root/.openclaw/workspace-reviewer/AGENTS.md`

| 行号 | 变更类型 | 旧内容 | 新内容 |
|------|----------|--------|--------|
| 1 | 标题 | `# Reviewer Agent（审核员）` | `# 研究审核员` |

### 5.5 `/root/.openclaw/workspace-citation/AGENTS.md`

| 行号 | 变更类型 | 旧内容 | 新内容 |
|------|----------|--------|--------|
| 1 | 标题 | `# Citation Agent（引用处理员）` | `# 研究引用员` |

### 5.6 `/root/.openclaw/workspace-dev/AGENTS.md`

文件内容不直接引用旧 agentId（引用的是 dev-init、dev-coder、dev-qa 这些还未被重命名的 id），但标题需确认：

| 行号 | 变更类型 | 旧内容 | 新内容 |
|------|----------|--------|--------|
| 1 | 标题 | `# Dev Lead（开发编排者）— v4 (Quality-First)` | `# 开发主管（开发编排者）— v4 (Quality-First)` |

**注意：** workspace-dev/AGENTS.md 中多处提到 `spawn dev-coder`、`spawn dev-qa`、`spawn dev-init`、`dev-lead` 等，当前 `dev` → `dev-lead`，`dev-init` → `dev-designer`，需要逐一代换：

| 行号 | 旧内容 | 新内容 |
|------|--------|--------|
| 19 | `（由 dev-qa 执行）` | `（由 dev-qa 执行）`（不变） |
| 22 | `回退给 dev-coder` | `回退给 dev-coder`（不变） |
| 35 | `spawn dev-coder 修复` | `spawn dev-coder 修复`（不变） |
| 40-42 | `dev-init`、`dev-lead`、`dev-coder` | `dev-designer`、`dev-lead`、`dev-coder` |
| 62 | `spawn dev-init` | `spawn dev-designer` |
| 72 | `spawn dev-coder` | `spawn dev-coder`（不变） |
| 73 | `spawn dev-qa` | `spawn dev-qa`（不变） |
| 81-83 | `dev-coder`、`dev-qa` | `dev-coder`、`dev-qa`（不变） |
| 86-88 | `dev-qa`、`dev-coder` | `dev-qa`、`dev-coder`（不变） |
| 97-98 | `dev-coder` | `dev-coder`（不变） |

### 5.7 `/root/.openclaw/workspace-dev-init/AGENTS.md`

| 行号 | 变更类型 | 旧内容 | 新内容 |
|------|----------|--------|--------|
| 1 | 标题 | `# Dev Init（Initializer Agent）— v3 (Quality-First)` | `# 开发设计师（Initializer Agent）— v3 (Quality-First)` |
| 36 | spawn | `spawn dev-init` | `spawn dev-designer` |

### 5.8 `/root/.openclaw/workspace-dev-coder/AGENTS.md`

| 行号 | 变更类型 | 旧内容 | 新内容 |
|------|----------|--------|--------|
| 1 | 标题 | `# Dev Coder（Coding Agent）— v3 (Quality-First)` | `# 开发编码员（Coding Agent）— v3 (Quality-First)` |
| 11 | 内容 | `dev-coder` | `dev-coder`（不变，id 未改） |
| 23,48,49,50,51,73,74 | 内容 | `dev-coder` | `dev-coder`（不变，id 未改） |

### 5.9 `/root/.openclaw/workspace-dev-qa/AGENTS.md`

| 行号 | 变更类型 | 旧内容 | 新内容 |
|------|----------|--------|--------|
| 1 | 标题 | `# Dev QA（质量验证 Agent）— v3` | `# 开发测试员（质量验证 Agent）— v3` |
| 8 | 内容 | `dev-coder` | `dev-coder`（不变） |
| 47-49,60-73,85,93-96 | 内容 | `dev-coder` | `dev-coder`（不变，id 未改） |

### 5.10 `/root/.openclaw/agents/dev/AGENTS.md`

| 行号 | 变更类型 | 旧内容 | 新内容 |
|------|----------|--------|--------|
| 1 | 标题 | `# Dev Lead（开发编排者）— v3 (Quality-First)` | `# 开发主管（开发编排者）— v3 (Quality-First)` |
| 19,20,22 | 内容 | `dev-qa` | `dev-qa`（不变） |
| 27,35 | 内容 | `dev-coder` | `dev-coder`（不变） |
| 40-42 | 内容 | `dev-init` → `dev-designer`，`dev-lead`（新增），`dev-coder` |
| 61,62 | 内容 | `spawn dev-init` → `spawn dev-designer` |
| 72,73,74,75,76,77 | 内容 | `dev-coder`（不变） |
| 79 | 内容 | `dev-qa`（不变） |
| 81,82,83 | 内容 | `dev-coder`（不变） |
| 86,87,88 | 内容 | `dev-qa`、`dev-coder`（不变） |
| 97,98,102 | 内容 | `dev-coder`（不变） |

### 5.11 `/root/.openclaw/agents/dev-init/AGENTS.md`

| 行号 | 变更类型 | 旧内容 | 新内容 |
|------|----------|--------|--------|
| 1 | 标题 | `# Dev Init（Initializer Agent）— v3 (Quality-First)` | `# 开发设计师（Initializer Agent）— v3 (Quality-First)` |
| 36 | 内容 | `spawn dev-init` | `spawn dev-designer` |

### 5.12 `/root/.openclaw/agents/dev-coder/AGENTS.md`

| 行号 | 变更类型 | 旧内容 | 新内容 |
|------|----------|--------|--------|
| 1 | 标题 | `# Dev Coder（Coding Agent）— v3 (Quality-First)` | `# 开发编码员（Coding Agent）— v3 (Quality-First)` |
| 11,23,48,49,50,51,73,74 | 内容 | `dev-coder` | `dev-coder`（id 不变，仅更新标题 name 展示） |

### 5.13 `/root/.openclaw/agents/dev-qa/AGENTS.md`

| 行号 | 变更类型 | 旧内容 | 新内容 |
|------|----------|--------|--------|
| 1 | 标题 | `# Dev QA（质量验证 Agent）— v3` | `# 开发测试员（质量验证 Agent）— v3` |
| 8,13,47-49,60-73,85,93-96 | 内容 | `dev-coder`（id 不变） | `dev-coder`（不变） |

---

## 六、主 Workspace AGENTS.md 变更清单

文件：`/root/.openclaw/workspace/AGENTS.md`

该文件在"Agent 编排纪律"章节中引用了旧的 spawn 格式，需要更新：

| 行号 | 变更类型 | 旧内容 | 新内容 |
|------|----------|--------|--------|
| ~79 | spawn research | `sessions_spawn({ agentId: "research" })` | `sessions_spawn({ agentId: "research-lead" })` |
| ~79 | spawn dev | `sessions_spawn({ agentId: "dev" })` | `sessions_spawn({ agentId: "dev-lead" })` |
| ~79 | spawn dev-qa | `sessions_spawn({ agentId: "dev-qa" })` | `sessions_spawn({ agentId: "dev-qa" })`（不变） |

---

## 七、openclaw.json 中 agentDir 字段同步

重命名 agent 目录后，需同步更新 openclaw.json 中对应的 `agentDir` 字段：

| agentId | 旧 agentDir | 新 agentDir |
|---------|-------------|-------------|
| research-lead | `/root/.openclaw/agents/research/agent` | `/root/.openclaw/agents/research-lead/agent` |
| research-searcher | `/root/.openclaw/agents/search/agent` | `/root/.openclaw/agents/research-searcher/agent` |
| research-reviewer | `/root/.openclaw/agents/reviewer/agent` | `/root/.openclaw/agents/research-reviewer/agent` |
| research-citation | `/root/.openclaw/agents/citation/agent` | `/root/.openclaw/agents/research-citation/agent` |
| dev-lead | `/root/.openclaw/agents/dev/agent` | `/root/.openclaw/agents/dev-lead/agent` |
| dev-designer | `/root/.openclaw/agents/dev-init` | `/root/.openclaw/agents/dev-designer` |
| dev-coder | `/root/.openclaw/agents/dev-coder` | 不变 |
| dev-qa | `/root/.openclaw/agents/dev-qa` | 不变 |
| main | `/root/.openclaw/agents/main/agent` | 不变 |

---

## 八、执行顺序建议

1. **Phase 1：** 重命名 agent 目录（`/root/.openclaw/agents/` 下各目录）
2. **Phase 2：** 重命名 workspace 目录（`/root/.openclaw/workspace-*`）
3. **Phase 3：** 更新 `openclaw.json`（agent id、name、allowAgents、agentDir 全部字段）
4. **Phase 4：** 更新所有 AGENTS.md 和 SOUL.md 文件中的 agentId 引用和标题 name
5. **Phase 5：** 重启 openclaw gateway 使配置生效

---

## 九、未发现引用的区域（已审计，确认干净）

- `/root/.openclaw/extensions/lightclawbot/skills/*` — 无旧 agent 引用
- `/root/.openclaw/workspace-research/` 下 `IDENTITY.md`、`USER.md`、`TOOLS.md` — 无旧 agent 引用
- `/root/.openclaw/workspace-dev/` 下 `SOUL.md`、`IDENTITY.md`、`USER.md`、`TOOLS.md` — 无旧 agent 引用
- `/root/.openclaw/workspace/` 下 `SOUL.md`、`IDENTITY.md`、`USER.md`、`TOOLS.md` — 无旧 agent 引用
- 任何 `.yaml` / `.yml` 配置文件 — 无旧 agent 引用
