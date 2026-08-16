# 腾讯云服务器恢复验证审计报告

**审计时间**: 2026-07-09 00:28 GMT+8  
**审计员**: research-lead (subagent)  
**服务器**: 腾讯云 VPS `82.156.124.186`, Ubuntu 24.04  
**审计方式**: 通过 `read` 工具直接读取文件验证（exec 不可用于当前 subagent 深度）

---

## 1. OpenClaw 配置 (`openclaw.json`)

| 检查项 | 状态 | 详情 |
|--------|------|------|
| 文件存在 | ✅ | `/home/ubuntu/.openclaw/openclaw.json` 可读 |
| 文件大小 | ✅ | 约 9.8KB（完整 JSON） |
| Gateway 端口 | ✅ | 29055, bind: lan, mode: local |
| 认证模式 | ✅ | token 模式 |
| Control UI | ✅ | basePath: `/df0s6p`, allowInsecureAuth: true |
| 主模型 | ✅ | `glmcode/GLM-5.2` (智谱直连, 1M 上下文) |
| 降级模型 | ✅ | `volcengine-agent-plan/glm-5.2` |
| Model Providers | ✅ | 3 个: glmcode, deepseek, volcengine-agent-plan |
| Agent 列表 | ✅ | 5 个: main, research-lead, research-searcher, research-reviewer, research-citation |
| 版本 | ✅ | lastTouchedVersion: 2026.6.10 |

**⚠️ 注意**: 进程状态 (`ps aux`)、端口监听 (`ss -tlnp`) 无法在当前深度验证，需主 agent 确认。

---

## 2. 工作区数据 (`workspace/`)

| 文件 | 状态 | 说明 |
|------|------|------|
| `SOUL.md` | ✅ 存在 | 核心人格文件，内容完整 |
| `USER.md` | ✅ 存在 | 用户信息：无名 |
| `MEMORY.md` | ✅ 存在 | 长期记忆完整（工具、规则、基础设施、模型、架构） |
| `AGENTS.md` | ✅ 存在 | 工作区指南 |
| `IDENTITY.md` | ✅ 存在 | 身份：小朱桑 🏠 |

**MEMORY.md 关键内容验证**:
- 服务器 IP: `82.156.124.186` ✅
- Gateway 端口: 29055 ✅
- Node.js 路径: `/home/ubuntu/.nvm/versions/node/v22.23.1/bin/node` ✅
- VPS 安全: 已关闭公网 SSH，UFW 只开 8051/8052/8060 + ZeroTier ✅

**⚠️ 无法验证项**:
- `memory/` 目录文件数量（read 无法列目录）
- `scripts/*.token` 文件数量

---

## 3. 研究报告 (`shared/results/`)

| 检查项 | 状态 |
|--------|------|
| 目录存在 | ✅ 本报告正写入该目录 |
| 已有报告数量 | ⚠️ 无法通过 read 工具列目录统计 |

**已知**: 测试探测 `R-001-wechat-mini-programs.md` 和 `R-002-claude-skills.md` 均返回 ENOENT，可能文件名不同或目录为空/新创建。

---

## 4. 项目 (`tools/`)

| 项目 | 状态 | 验证详情 |
|------|------|----------|
| `bill-editor/` | ✅ 存在 | `package.json` 可读（bill-editor v1.0.0, ES module）, `server.js` 完整（510+ 行 Express 应用） |

**⚠️ 无法验证**: 是否有其他项目目录（read 无法列目录）

---

## 5. 服务状态

**⚠️ 无法验证** — `systemctl list-units` 需要 exec 权限。

根据 MEMORY.md 记录，应有以下 systemd 服务：
- `agent-dashboard` (端口 8055)
- `bill-editor` (端口 8052)
- `ai-tarot`
- OpenClaw gateway (端口 29055)

需主 agent 执行 `systemctl` 确认。

---

## 6. 数据库 (`tasks.db`)

| 检查项 | 状态 | 详情 |
|--------|------|------|
| 文件存在 | ❌ **不存在** | `/home/ubuntu/.openclaw/workspace/scripts/tasks.db` 返回 ENOENT |
| `.task-completions.jsonl` | ✅ 存在 | 可读（返回为二进制/图片格式） |

**🔴 严重问题**: 任务中心数据库 `tasks.db` 文件缺失。这会影响任务录入和 auto-review cron。

---

## 7. Agents 配置 (`agents/`)

| 检查项 | 状态 |
|--------|------|
| 配置文件中定义 | ✅ 5 个 agent（main, research-lead, research-searcher, research-reviewer, research-citation） |
| Agent 目录 | ⚠️ 无法通过 read 确认目录结构 |

`openclaw.json` 中定义的 agentDir 路径:
- `/home/ubuntu/.openclaw/agents/main/agent`
- `/home/ubuntu/.openclaw/agents/research-lead/agent`
- `/home/ubuntu/.openclaw/agents/research-searcher/agent`
- `/home/ubuntu/.openclaw/agents/research-reviewer/agent`
- `/home/ubuntu/.openclaw/agents/research-citation/agent`

探测 `AGENTS.md` 和 `SOUL.md` 在 agent 目录中均返回 ENOENT，说明 agent 目录可能为空或使用不同的文件名。

---

## 8. 插件 (`plugin-skills/`)

**⚠️ 无法列目录**。根据 `openclaw.json` 配置，已启用的插件：

| 插件 | 状态 |
|------|------|
| browser | ✅ enabled |
| qqbot | ✅ enabled |
| openclaw-weixin | ✅ enabled |
| lightclawbot | ✅ enabled |
| memory-tencentdb | ✅ enabled (hybrid recall, embedding-3) |
| acpx | ✅ enabled |
| parallel | ✅ enabled |

**MCP 服务器**:
- `luckin` (瑞幸咖啡) ✅ 配置存在
- `web-search-prime` (智谱) ✅ enabled
- `zhipu-reader` (智谱) ✅ enabled
- `zread` (智谱) ✅ enabled

---

## 9. 渠道配置

| 渠道 | 状态 | 详情 |
|------|------|------|
| lightclawbot | ✅ enabled | 2 个 API key |
| qqbot | ✅ enabled | appId: 1903765716 + 子账号 1904489355 |
| openclaw-weixin | ⚠️ accounts 为空 | `{}` |
| telegram | ❌ disabled | botToken 存在但未启用 |

---

## 总结

### ✅ 恢复正常
1. **openclaw.json** — 完整可读，配置齐全
2. **核心工作区文件** — SOUL/USER/MEMORY/AGENTS/IDENTITY 全部存在且内容完整
3. **模型配置** — 主模型 + 降级 + 多 provider 就绪
4. **Agent 定义** — 5 个 agent 在配置中完整定义
5. **插件配置** — 7 个插件 + 4 个 MCP 服务器已配置
6. **bill-editor 项目** — 代码文件完整

### 🔴 需要关注
1. **`tasks.db` 数据库缺失** — 任务中心数据库不存在，需恢复或重建
2. **Agent 目录可能为空** — agentDir 下的文件未确认存在

### ⚠️ 需主 Agent 验证（需 exec 权限）
1. OpenClaw 进程是否运行 (`ps aux`)
2. 端口 29055 是否监听 (`ss -tlnp`)
3. systemd 服务状态 (`systemctl`)
4. `memory/` 和 `scripts/` 目录内容
5. `shared/results/` 报告数量
6. `plugin-skills/` 目录内容
7. `tasks.db` 的 sqlite3 表结构

---

**建议下一步**: 主 agent 执行完整 shell 命令清单以覆盖上述 ⚠️ 项。
