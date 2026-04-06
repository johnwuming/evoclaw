# Agent 能力审计报告 — 2026-04-07

## 审计方法
对比每个 agent 的 **AGENTS.md 提示词要求** vs **openclaw.json 实际工具权限**。

---

## 1. Main Agent

| 要求 | 权限 | 状态 |
|------|------|------|
| sessions_spawn（分派研究/开发团队） | ✅ 全部工具可用 | ✅ |
| web_search/web_fetch/browser（简单搜索自己做） | ✅ 全部工具可用 | ✅ |
| read/write（文件操作、记忆管理） | ✅ | ✅ |
| exec（运行命令） | ✅ | ✅ |
| edit（编辑文件） | ✅ | ✅ |

**结论：✅ 全部具备**

---

## 2. Research Lead（研究主管）

| AGENTS.md 要求 | 实际权限 | 状态 |
|----------------|---------|------|
| sessions_spawn（spawn searcher/reviewer/citation） | ✅ tools.allow | ✅ |
| subagents（子agent管理） | ✅ tools.allow | ✅ |
| web_search / webSearchPrime | ✅ tools.allow | ✅ |
| web_fetch（读取URL内容） | ✅ tools.allow | ✅ |
| browser（深度搜索） | ✅ tools.allow | ✅ |
| read/write（读写文件） | ✅ tools.allow | ✅ |
| exec（系统命令） | ❌ tools.deny | ⚠️ 提示词写"不能执行系统命令"，匹配 |
| ❌ 不搜索互联网 | N/A — 但实际有搜索权限 | ⚠️ 矛盾：提示词说"绝对不搜索"但有权限 |

**问题：**
1. ⚠️ 提示词写"❌ 不自己搜索"，但给了 web_search/webSearchPrime 权限。这是设计意图（它有搜索权限作为兜底），但提示词表述矛盾。
2. ❌ **webSearchPrime MCP 当前不可用**（bridge 脚本认证失败，API key 可能不支持）
3. ❌ **DuckDuckGo web_search 在腾讯云不可用**
4. ⚠️ **browser 搜索无搜索引擎可用**（百度需要 JS 渲染，Google 需翻墙）

**实际搜索能力：仅剩 web_fetch（已知 URL）和 browser（但受限）**

---

## 3. Research Searcher（研究搜索员）

| AGENTS.md 要求 | 实际权限 | 状态 |
|----------------|---------|------|
| web_search | ✅ tools.allow | ⚠️ DuckDuckGo 腾讯云不可用 |
| web_fetch | ✅ tools.allow | ✅ |
| browser | ✅ tools.allow | ✅ |
| webSearchPrime | ✅ tools.allow | ❌ 当前不可用（认证失败） |
| read/write | ✅ tools.allow | ✅ |
| sessions_spawn | ❌ tools.deny | ✅ 提示词匹配"不能 spawn 子 agent" |
| exec | ❌ tools.deny | ✅ 提示词匹配"不能执行系统命令" |

**问题：**
1. ❌ **核心能力搜索不可用**：DuckDuckGo 不可用 + webSearchPrime 认证失败 = 搜索员无法搜索
2. 这是最严重的问题——搜索员是研究团队的"眼睛"，眼睛瞎了

---

## 4. Research Reviewer（研究审核员）

| AGENTS.md 要求 | 实际权限 | 状态 |
|----------------|---------|------|
| read | ✅ tools.allow | ✅ |
| write | ✅ tools.allow | ✅ |
| web_search | ❌ tools.deny | ✅ 提示词匹配"不能搜索" |
| web_fetch | ❌ tools.deny | ⚠️ 提示词没要求 web_fetch，但**无法验证 URL** |
| exec | ❌ tools.deny | ✅ |

**问题：**
1. ⚠️ **无法验证引用 URL**：提示词没说它需要 web_fetch，但实际审核引用需要验证 URL 可访问性。当前无 web_fetch 权限。这个看设计意图——如果只做内容审核不需要 web_fetch，但 R-028 报告里 research-citation 才是验证 URL 的角色。

---

## 5. Research Citation（研究引用员）

| AGENTS.md 要求 | 实际权限 | 状态 |
|----------------|---------|------|
| web_fetch（验证URL可访问性） | ✅ tools.allow | ✅ |
| read/write | ✅ tools.allow | ✅ |
| exec | ❌ tools.deny | ✅ |
| web_search | ❌ tools.deny | ✅ 提示词匹配"不能搜索" |

**结论：✅ 全部具备（引用员只需 web_fetch + 读写）**

---

## 6. Dev Lead（开发主管）

| AGENTS.md 要求 | 实际权限 | 状态 |
|----------------|---------|------|
| sessions_spawn（spawn designer/coder/qa） | ✅ tools.allow | ✅ |
| subagents | ✅ tools.allow | ✅ |
| read/write | ✅ tools.allow | ✅ |
| exec（git status/log、init.sh） | ✅ tools.allow | ✅ |
| web_fetch（读取研究文档） | ✅ tools.allow | ✅ |
| web_search | ❌ tools.deny | ✅ 提示词匹配"不能搜索互联网" |

**问题：无**

**结论：✅ 全部具备**

---

## 7. Dev Designer（开发设计师）

| AGENTS.md 要求 | 实际权限 | 状态 |
|----------------|---------|------|
| read/write | ✅ tools.allow | ✅ |
| exec（git操作） | ✅ tools.allow | ✅ |
| sessions_spawn | ❌ tools.deny | ✅ 不需要 |

**问题：无**

**结论：✅ 全部具备**

---

## 8. Dev Coder（开发编码员）

| AGENTS.md 要求 | 实际权限 | 状态 |
|----------------|---------|------|
| read/write | ✅ tools.allow | ✅ |
| exec（运行测试、安装依赖） | ✅ tools.allow | ✅ |
| process（管理后台进程） | ✅ tools.allow | ✅ |
| browser | ❌ tools.deny | ⚠️ 提示词没要求 browser，但某些场景可能需要（如验证前端效果） |

**问题：**
1. ⚠️ **workspace 不一致**：dev-coder workspace 是 `/root/.openclaw/workspace-dev-coder/`，但项目文件在 `/root/.openclaw/workspace-dev/<项目名>/` 下。提示词说 `pwd` 定位项目目录，但 spawn 时 cwd 由 dev-lead 控制，不一定 cd 到项目目录。

---

## 9. Dev QA（开发测试员）

| AGENTS.md 要求 | 实际权限 | 状态 |
|----------------|---------|------|
| exec（curl/dump-dom/init.sh） | ✅ tools.allow | ✅ |
| read/write | ✅ tools.allow | ✅ |
| browser | ✅ tools.allow | ⚠️ 提示词明确说"禁止使用 browser screenshot（无 GPU）" |

**问题：**
1. ⚠️ **browser 权限给了但提示词禁止用**：提示词说"本机器 Chrome 截图不可用（无 GPU），禁止使用 browser screenshot"。但实际 playwright 可以截图（刚才猪周期看板就是用 playwright 截的）。提示词信息过时。
2. ⚠️ **workspace 不一致**：同 dev-coder，workspace 是独立的但项目在 workspace-dev 下。

---

## 汇总

### ❌ 严重问题（功能不可用）

| # | Agent | 问题 | 影响 |
|---|-------|------|------|
| 1 | research-searcher | **搜索能力完全不可用**：DuckDuckGo 不可用 + webSearchPrime 认证失败 | 研究团队核心能力瘫痪 |
| 2 | research-lead | 同上 | 无法兜底 |

### ⚠️ 需要修复

| # | Agent | 问题 | 影响 |
|---|-------|------|------|
| 3 | dev-qa | 提示词禁止 browser screenshot，但实际 playwright 可用 | QA 验证质量受限 |
| 4 | dev-coder/dev-qa | workspace 路径不一致 | 如果 dev-lead 不传 cwd，agent 找不到项目文件 |
| 5 | research-lead | 提示词"不自己搜索"但有搜索权限，表述矛盾 | 可能导致行为不一致 |

### ✅ 正常

| Agent | 状态 |
|-------|------|
| main | ✅ |
| dev-lead | ✅ |
| dev-designer | ✅ |
| research-reviewer | ✅ |
| research-citation | ✅ |
