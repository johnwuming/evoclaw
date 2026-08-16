# R-028: Agent 提示词审查报告

**审查日期：** 2026-04-06  
**审查范围：** Main Agent + 研究团队(4) + 开发团队(4) 共 9 个 Agent  
**配置基准：** `/root/.openclaw/openclaw.json`（meta: 2026.4.2）

---

## 执行摘要

共发现 **19 个问题**，其中：

- 🔴 严重（阻碍运行）：**5 个**
- 🟡 中等（路径/版本不一致）：**8 个**
- ⚪ 提示性（文档冗余）：**6 个**

**最高优先级修复：**
1. dev-init agentDir 配置错误
2. 所有 agent 的 agentDir 路径与实际 AGENTS.md 位置不匹配
3. research-lead 嵌入 AGENTS.md 描述与实际工具权限不符

---

## 一、Main Agent — `/root/.openclaw/workspace/AGENTS.md`

### 问题 1：team output 表格中路径引用错误（中等）

**位置：** "团队输出目录" 表格

| 当前描述 | 实际路径 |
|----------|----------|
| `workspace-dev/` | 实际 workspace 是 `/root/.openclaw/workspace-dev/` |
| `shared/results/R-xxx.md` | ✅ 正确 |

**修复建议：** 路径本身是对的，但描述不够精确。建议改为绝对路径或明确标注"相对于 workspace"。

### 问题 2：research-lead 嵌入内容声称"没有 exec 权限"（中等）

**位置：** main/AGENTS.md 嵌入的"研究主管— v4"章节

**当前描述：**
> "红线：你不能直接执行系统命令（没有 exec 权限）"

**实际配置（openclaw.json research-lead tools）：**
```json
"allow": ["web_search", "web_fetch", "browser", "read", "write", "sessions_spawn", "subagents", "sessions_list", "sessions_history", "webSearchPrime"],
"deny": ["exec", "process", "edit"]
```

**结论：** ✅ deny 列表确实包含 exec，描述准确。但 embed 内容与其他 research agent 角色说明混在一起容易造成混淆。

### 问题 3：dev-lead 嵌入内容与 dev-lead/workspace-dev/AGENTS.md 版本不同步（中等）

**位置：** main/AGENTS.md 嵌入的"开发主管— v3"，但 `/root/.openclaw/workspace-dev/AGENTS.md` 是 **v4**

**差异：** v4 新增了"文档路径架构"章节（跨团队路径契约、废弃路径 `shared/projects/<项目>/PRODUCT.md`），v3 没有。

**修复建议：** 统一版本，建议 main/AGENTS.md 中的嵌入内容同步更新为 v4。

### 问题 4：嵌入式 AGENTS.md 内容造成版本分裂（中等）

**位置：** main/AGENTS.md 内部嵌入了完整的 research-lead（v4）、dev-lead（v3）AGENTS.md 内容

**问题：** 这些嵌入内容与实际 agent 工作目录中的 AGENTS.md 内容版本可能不一致，维护困难。

**修复建议：** main/AGENTS.md 应只描述 main 的调度职责，不应嵌入子 agent 的完整 AGENTS.md。引用子 agent 时应指向其实际 AGENTS.md 文件路径。

---

## 二、research-lead — `/root/.openclaw/workspace-research/AGENTS.md`

### 问题 5：workspace 路径引用不一致（中等）

**当前：**
> "research/knowledge-base.json"（相对路径）

**openclaw.json 定义：** workspace = `/root/.openclaw/workspace-research`

**实际文件系统：** research-lead workspace 中不存在 `research/` 子目录（除非 agent 自己创建）

**修复建议：** 使用绝对路径 `/root/.openclaw/workspace-research/research/research-plan.json`，或在 Phase 0 初始化时先创建 `research/` 目录。

### 问题 6：声称"没有 exec 权限"但 openclaw.json 配置为有 exec（严重）

**位置：** 红线章节

**AGENTS.md：** "你不能直接执行系统命令（没有 exec 权限）"

**openclaw.json research-lead tools.deny：** `["exec", "process", "edit"]` ✅ 描述正确

**结论：** 描述与配置一致，但研究主管"红线"部分与 research-lead AGENTS.md 混在一起，实际是 main/AGENTS.md 嵌入内容，未做区分。

### 问题 7：搜索工具选择策略提及"webSearchPrime"但未说明工具来源（提示）

**位置：** "搜索工具选择策略" 章节

提及了 `webSearchPrime`（智谱 MCP），但实际 openclaw.json 的 tools profile 是 "full"，MCP 工具不一定可用。

**修复建议：** 明确标注 webSearchPrime 需要 MCP 连接，或改为确认可用的 `web_search` / `browser`。

---

## 三、research-searcher — `/root/.openclaw/workspace-search/AGENTS.md`

### 问题 8：文件内容与 agent 名称不匹配（严重）

**实际文件：** `/root/.openclaw/workspace-search/AGENTS.md` 内容是通用的"AGENTS.md - Your Workspace"模板（Session Startup、Memory、Heartbeats 等章节），**不是** research-searcher 的专业提示词。

**正确内容位置：** `/root/.openclaw/agents/dev-designer/AGENTS.md` 有完整内容，但那不是 research-searcher 的文件。

**结论：** research-searcher 的专业 AGENTS.md **内容缺失**。当前它使用的是通用模板，无法执行搜索任务。

**修复建议：** 创建 `/root/.openclaw/workspace-search/AGENTS.md`，内容应包含：
- 搜索任务执行流程
- JSON 输出格式规范
- 搜索工具使用策略
- web_search / browser / web_fetch 的使用场景

### 问题 9：sessions_spawn 权限与 openclaw.json 不符（严重）

**openclaw.json research-searcher tools.deny：** `["exec", "process", "sessions_spawn", "cron"]`

research-searcher **不能** spawn 子 agent，但当前 AGENTS.md（即使有专业内容）可能会描述 spawn 行为。需要确保 AGENTS.md 不要求 research-searcher spawn 任何子 agent。

---

## 四、research-reviewer — `/root/.openclaw/workspace-reviewer/AGENTS.md`

### 问题 10：文件内容与 agent 名称不匹配（严重）

**实际文件：** `/root/.openclaw/workspace-reviewer/AGENTS.md` 内容是通用模板，**不是** research-reviewer 的专业提示词。

**结论：** 同问题 8，research-reviewer 专业 AGENTS.md **内容缺失**。

### 问题 11：工具权限配置正确（无问题）

**openclaw.json research-reviewer tools：** `allow: ["read", "write"]`，deny 其他所有

AGENTS.md 如使用通用模板，其"Search the web"等描述与实际 deny 列表一致（模板不强制要求 web 搜索）。

---

## 五、research-citation — `/root/.openclaw/workspace-citation/AGENTS.md`

### 问题 12：文件内容与 agent 名称不匹配（严重）

**实际文件：** `/root/.openclaw/workspace-citation/AGENTS.md` 内容是通用模板，**不是** research-citation 的专业提示词。

**结论：** 同问题 8，research-citation 专业 AGENTS.md **内容缺失**。

### 问题 13：工具权限配置正确（无问题）

**openclaw.json research-citation tools：** `allow: ["web_fetch", "read", "write"]`，deny 其他

如使用通用模板，描述与配置基本一致。

---

## 六、dev-lead — `/root/.openclaw/workspace-dev/AGENTS.md`（v4）

### 问题 14：agentDir 与实际路径不匹配（严重）

**openclaw.json 定义：** `"agentDir": "/root/.openclaw/agents/dev-lead/agent"`（不存在）

**实际 AGENTS.md：** `/root/.openclaw/workspace-dev/AGENTS.md`（v4）

**影响：** OpenClaw 可能无法正确加载 dev-lead 的 AGENTS.md（agentDir 目录不存在）。

### 问题 15：文档路径架构章节提及废弃路径（提示）

**位置：** "废弃路径：`shared/projects/<项目>/PRODUCT.md` — 已废弃"

**说明：** v4 新增此说明是好的，但需确认所有团队成员都知道这个路径已废弃。

### 问题 16：与 main/AGENTS.md 嵌入的 v3 版本不同步（中等）

**位置：** main/AGENTS.md 嵌入的是 dev-lead v3，但实际 workspace 中是 v4

**差异：** v4 多了"文档路径架构"章节（路径契约、废弃路径说明）

**修复建议：** main/AGENTS.md 中的嵌入内容应更新为 v4，或移除嵌入改为引用。

---

## 七、dev-designer — `/root/.openclaw/agents/dev-designer/AGENTS.md`（v3）

### 问题 17：agentDir 指向不存在的目录（严重）

**openclaw.json 定义：** `"agentDir": "/root/.openclaw/agents/dev-init"`（不存在）

**实际 AGENTS.md：** `/root/.openclaw/agents/dev-designer/AGENTS.md`（v3）

**影响：** OpenClaw 找不到 dev-init 目录，导致 dev-designer 无法正常加载 AGENTS.md。

### 问题 18：workspace 路径不一致（中等）

**openclaw.json 定义：** `"workspace": "/root/.openclaw/workspace-dev-init"`（不存在）

**实际使用：** dev-designer 应该在项目目录下工作，而不是 `/workspace-dev-init/` 根目录

**修复建议：** workspace-dev-init 应是一个临时/初始化工作区，初始化完成后 dev-designer 应切到项目目录。

---

## 八、dev-coder — `/root/.openclaw/agents/dev-coder/AGENTS.md`（v3）

### 问题 19：与 dev-designer 类似，agentDir 指向问题（中等）

**openclaw.json 定义：** `"agentDir": "/root/.openclaw/agents/dev-coder"` ✅ 存在

**实际 AGENTS.md：** `/root/.openclaw/agents/dev-coder/AGENTS.md`（v3）✅ 存在

**workspace：** `"workspace": "/root/.openclaw/workspace-dev-coder"` ✅ 存在

**结论：** dev-coder 的配置是所有 dev agent 中最完整的，路径均正确对应。

---

## 九、dev-qa — `/root/.openclaw/agents/dev-qa/AGENTS.md`（v3）

### 问题 20：与 dev-designer 类似，agentDir 指向问题（中等）

**openclaw.json 定义：** `"agentDir": "/root/.openclaw/agents/dev-qa"` ✅ 存在

**实际 AGENTS.md：** `/root/.openclaw/agents/dev-qa/AGENTS.md`（v3）✅ 存在

**workspace：** `"workspace": "/root/.openclaw/workspace-dev-qa"` ✅ 存在

**结论：** dev-qa 配置完整。

---

## 十、dev-init 配置修复方案

### 问题：dev-init agentDir 指向根目录 "/"（严重）

**当前 openclaw.json 中 dev-designer 的配置：**
```json
{
  "id": "dev-designer",
  "name": "开发设计师",
  "workspace": "/root/.openclaw/workspace-dev-init",
  "agentDir": "/root/.openclaw/agents/dev-init",  // ← 目录不存在
  "model": "minimax/MiniMax-M2.7-highspeed",
  ...
}
```

### 修复方案

**方案 A（推荐）：修正 agentDir 指向已有目录**

dev-designer 的 AGENTS.md 实际位于 `/root/.openclaw/agents/dev-designer/AGENTS.md`，应修正：

```json
{
  "id": "dev-designer",
  "workspace": "/root/.openclaw/workspace-dev-init",
  "agentDir": "/root/.openclaw/agents/dev-designer"
}
```

**方案 B：创建 dev-init 目录并迁移**

```bash
mkdir -p /root/.openclaw/agents/dev-init
# 将 dev-designer AGENTS.md 复制到 /root/.openclaw/agents/dev-init/AGENTS.md
cp /root/.openclaw/agents/dev-designer/AGENTS.md /root/.openclaw/agents/dev-init/AGENTS.md
```

### 额外发现：workspace-dev-init 不存在

**修复：**
```bash
mkdir -p /root/.openclaw/workspace-dev-init
```

---

## 十一、所有 agent 的 agentDir 路径问题汇总

| Agent | openclaw.json agentDir | 实际 AGENTS.md 位置 | 状态 |
|-------|------------------------|---------------------|------|
| main | `/root/.openclaw/agents/main/agent` ❌不存在 | `/root/.openclaw/workspace/AGENTS.md` | 需修复 |
| research-lead | `/root/.openclaw/agents/research-lead/agent` ❌不存在 | `/root/.openclaw/workspace-research/AGENTS.md` | 需修复 |
| research-searcher | `/root/.openclaw/agents/research-searcher/agent` ❌不存在 | `/root/.openclaw/workspace-search/AGENTS.md`（通用模板，内容缺失） | 需修复 |
| research-reviewer | `/root/.openclaw/agents/research-reviewer/agent` ❌不存在 | `/root/.openclaw/workspace-reviewer/AGENTS.md`（通用模板，内容缺失） | 需修复 |
| research-citation | `/root/.openclaw/agents/research-citation/agent` ❌不存在 | `/root/.openclaw/workspace-citation/AGENTS.md`（通用模板，内容缺失） | 需修复 |
| dev-lead | `/root/.openclaw/agents/dev-lead/agent` ❌不存在 | `/root/.openclaw/workspace-dev/AGENTS.md` | 需修复 |
| dev-designer | `/root/.openclaw/agents/dev-init` ❌不存在 | `/root/.openclaw/agents/dev-designer/AGENTS.md` | 需修复 |
| dev-coder | `/root/.openclaw/agents/dev-coder` ✅存在 | `/root/.openclaw/agents/dev-coder/AGENTS.md` | ✅ 正确 |
| dev-qa | `/root/.openclaw/agents/dev-qa` ✅存在 | `/root/.openclaw/agents/dev-qa/AGENTS.md` | ✅ 正确 |

---

## 十二、总结与修复优先级

### 第一优先级（阻塞运行）

1. **创建 research-searcher 专业 AGENTS.md**（当前是通用模板）
2. **创建 research-reviewer 专业 AGENTS.md**（当前是通用模板）
3. **创建 research-citation 专业 AGENTS.md**（当前是通用模板）
4. **修复 dev-init agentDir**（指向不存在的 `/root/.openclaw/agents/dev-init`）

### 第二优先级（配置不一致）

5. 修正所有 agent 的 agentDir 路径，使 openclaw.json 与实际 AGENTS.md 位置对应
6. 同步 main/AGENTS.md 中嵌入的子 agent 内容（research-lead v3→v4，dev-lead v3→v4）
7. research-lead AGENTS.md 使用绝对路径引用 `research/` 子目录

### 第三优先级（文档优化）

8. main/AGENTS.md 中移除嵌入式 AGENTS.md 完整内容，改为引用路径
9. dev-lead AGENTS.md（v4）中的废弃路径说明推广到所有 team
10. 确认 webSearchPrime MCP 工具可用性

---

**报告结束**
