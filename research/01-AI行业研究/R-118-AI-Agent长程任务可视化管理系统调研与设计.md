# AI Agent 长程任务可视化管理系统 — 需求与设计文档

> **报告编号**: R-118（基于 R-117 方案 + 用户需求直接编写，研究团队3次未能产出）
> **日期**: 2026-06-27
> **分类**: 01-AI行业研究
> **状态**: 需求文档（待开发）

---

## 一、核心痛点

1. **进度不可见** — 任务进度只能与主 agent 对话获取，无可视化面板
2. **多任务盲区** — 多任务并行时无法批量查看状态
3. **子 agent 不透明** — research-lead/searcher/reviewer 的执行状态不可见
4. **失败无感知** — 任务失败后没有直观告警和重试入口
5. **队列不可视** — 夜间批处理模式的任务排期无法管理

## 二、系统架构

```
┌─────────────────────────────────────────────────────┐
│              VPS (82.156.124.186)                     │
│                                                       │
│  ┌─────────────┐    ┌──────────────────────┐        │
│  │   Nginx     │───▶│  Task Dashboard      │        │
│  │  :8052/     │    │  (Node.js + SQLite)  │        │
│  │  dashboard/ │    │  :8055              │        │
│  └─────────────┘    └──────────┬───────────┘        │
│                                │                      │
│  ┌─────────────────────────────▼──────────────┐     │
│  │          OpenClaw Gateway (:12145)          │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐ │     │
│  │  │  HEART   │  │  Cron    │  │ Subagent │ │     │
│  │  │  BEAT.md │  │  Jobs    │  │ Sessions │ │     │
│  │  └──────────┘  └──────────┘  └──────────┘ │     │
│  └────────────────────────────────────────────┘     │
│                                                       │
│  ┌───────────────────────────────────────────┐       │
│  │  Data Sources (文件系统)                    │       │
│  │  - HEARTBEAT.md (任务清单)                  │       │
│  │  - scripts/.task-alerts.md (告警)          │       │
│  │  - research/research-state.json (研究状态)  │       │
│  │  - shared/results/ (产出文件)               │       │
│  └───────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────┘
          ↕ ZeroTier (10.12.192.225 ↔ .174)
┌─────────────────────────────────────────────────────┐
│          本地 HP 800 G1 (10.12.192.174)               │
│                                                       │
│  ┌──────────────┐  ┌──────────────────────┐         │
│  │ OpenClaw     │  │  Claude Code ACP     │         │
│  │ (:18789)     │  │  Sessions            │         │
│  │              │  │  (夜间批处理)         │         │
│  └──────┬───────┘  └──────────────────────┘         │
│         │                                             │
│  ┌──────▼─────────────────────────────────┐         │
│  │  Git Repos + Project Directories       │         │
│  │  - PROGRESS.md per project             │         │
│  │  - feature_list.json per project       │         │
│  └────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────┘
```

## 三、数据流设计

### 3.1 数据采集层

| 数据源 | 采集方式 | 频率 | 内容 |
|--------|----------|------|------|
| HEARTBEAT.md | 文件解析 | 每10分钟 | 任务清单（名称/状态/分派时间/预期产出） |
| .task-alerts.md | 文件解析 | 每10分钟 | 超时告警 |
| OpenClaw sessions API | HTTP 调用 | 每5分钟 | 子 agent 实时状态（active/done/failed） |
| shared/results/ 目录 | 文件扫描 | 每10分钟 | 报告产出记录 |
| research-state.json | 文件解析 | 按需 | 研究进度（findings/gaps） |
| Git log | git 命令 | 每小时 | 代码提交记录（本地机器） |
| 本地 OpenClaw (ZT) | HTTP over ZeroTier | 每5分钟 | 本地 agent/session 状态 |

### 3.2 数据存储

```
SQLite (dashboard.db, <1MB)
├── tasks          -- 任务列表（同步自 HEARTBEAT.md）
├── agents         -- agent 状态历史
├── activity_log   -- 活动日志（spawn/done/fail 事件）
├── reports        -- 研究报告产出记录
└── alerts         -- 告警历史
```

### 3.3 数据流

```
HEARTBEAT.md ──┐
.task-alerts ──┼──▶ collector.js ──▶ SQLite ──▶ API ──▶ Web UI
sessions API ──┤                     │
results/ ──────┤                     │
               └──▶ WebSocket ──▶ 实时更新面板
```

## 四、功能清单

### MVP（P0 — 必须有）

| # | 功能 | 说明 |
|---|------|------|
| 1 | **任务看板** | 任务列表，按状态分组（待办/进行中/完成/失败），显示名称、分派时间、运行时长、预期产出路径 |
| 2 | **Agent 状态面板** | 所有 agent 实时状态（idle/running/failed），token 消耗，运行时长 |
| 3 | **任务详情** | 点击任务查看详情：子 agent 执行链、日志摘要、产出文件链接 |
| 4 | **告警显示** | 超时任务红色高亮，失败任务标记重试按钮 |
| 5 | **自动刷新** | 每30秒自动刷新数据，无需手动 |

### V2（P1 — 应该有）

| # | 功能 | 说明 |
|---|------|------|
| 6 | **任务创建** | 在面板上直接创建任务，写入 HEARTBEAT.md |
| 7 | **任务重试** | 一键重试失败任务（调用 OpenClaw spawn） |
| 8 | **双机视图** | VPS + 本地机器的统一视图，ZeroTier 连接状态 |
| 9 | **历史趋势** | 7天内任务完成率、agent token 消耗趋势图 |
| 10 | **夜间批处理排期** | 任务队列管理，设置优先级和执行时间窗口 |

### V3（P2 — 可以有）

| # | 功能 | 说明 |
|---|------|------|
| 11 | **微信通知** | 任务完成/失败时推送微信消息 |
| 12 | **报告浏览器** | 浏览/搜索 shared/results/ 下的研究报告 |
| 13 | **Git 活动流** | 本地机器的 git commit 时间线 |

## 五、技术选型

### 方案对比

| | 方案A：轻量单体 | 方案B：前后端分离 |
|---|---|---|
| **前端** | 内嵌 HTML（无框架） | Vue 3 + Vite |
| **后端** | Node.js + Express | Node.js + Express |
| **存储** | SQLite (better-sqlite3) | SQLite |
| **实时** | SSE (Server-Sent Events) | WebSocket |
| **样式** | 内联 CSS，暗色主题 | Tailwind CSS |
| **部署** | systemd 单进程 | systemd + 静态文件 |
| **内存** | ~30MB | ~50MB |
| **开发复杂度** | 低（1个文件） | 中（前后端两套） |
| **推荐** | ✅ **MVP 推荐** | 适合 V2 升级 |

### 推荐：方案A（轻量单体）

理由：
- VPS 仅 2C2G，内存紧张，方案A 仅 ~30MB
- 单文件可维护，Claude Code 一次能写完
- 功能验证后可在 V2 升级为前后端分离

## 六、API 设计

### 数据采集 API（内部）

```
GET /api/tasks          -- 任务列表（解析 HEARTBEAT.md）
GET /api/agents         -- agent 状态（调用 OpenClaw sessions API）
GET /api/alerts         -- 告警列表（解析 .task-alerts.md）
GET /api/reports        -- 报告产出（扫描 shared/results/）
GET /api/stats          -- 统计汇总（完成率/token消耗）
GET /api/local-status   -- 本地机器状态（通过 ZeroTier 调用）
```

### 页面路由

```
GET /                   -- 主面板（任务看板 + agent 状态）
GET /task/:id           -- 任务详情
GET /agents             -- agent 全列表
GET /reports            -- 报告列表
GET /settings           -- 设置（刷新频率等）
```

## 七、UI 布局（ASCII 原型）

```
┌──────────────────────────────────────────────────────────┐
│  🏠 小朱桑 Agent 控制台          🔄 自动刷新 30s         │
├──────────────┬───────────────────────────────────────────┤
│              │                                           │
│  📊 总览     │   任务看板                                 │
│  📋 任务     │   ┌─────────┬─────────┬─────────┬──────┐ │
│  🤖 Agents   │   │ 待办(2) │ 进行中(1)│ 完成(15)│ 失败 │ │
│  📄 报告     │   │         │         │         │ (1)  │ │
│  ⚙️ 设置     │   │ Task A  │ R-118   │ R-117   │ R-118│ │
│              │   │ Task B  │ 33min   │ 26KB    │ retry│ │
│  ────────    │   │         │ 🔴3搜索员│         │      │ │
│  💻 双机状态  │   └─────────┴─────────┴─────────┴──────┘ │
│  VPS ✅      │                                           │
│  本地 ✅     │   Agent 状态                               │
│  ZT  ✅      │   ┌───────────┬────────┬────────┬──────┐ │
│              │   │ Agent     │ Status │ Tokens │ Time │ │
│              │   │ research  │ 🟢idle │ 24k    │ 4m   │ │
│              │   │ searcher  │ 🟡run  │ 15k    │ 2m   │ │
│              │   │ reviewer  │ 🟢idle │ 8k     │ 1m   │ │
│              │   │ citation  │ 🟢idle │ 5k     │ 30s  │ │
│              │   └───────────┴────────┴────────┴──────┘ │
└──────────────┴───────────────────────────────────────────┘
```

## 八、部署方案

### 目录结构

```
/root/.openclaw/workspace/tools/agent-dashboard/
├── server.js          # 主服务（Express + SQLite）
├── dashboard.db       # SQLite 数据库（运行时生成）
├── package.json
├── CLAUDE.md          # Claude Code 项目上下文
└── PROGRESS.md        # 开发进度
```

### Nginx 配置

```nginx
location /dashboard/ {
    proxy_pass http://127.0.0.1:8055/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
}
```

### 访问地址

- 外部：`http://82.156.124.186:8052/dashboard/`
- 内部：`http://127.0.0.1:8055`

## 九、MVP 开发计划

| 步骤 | 内容 | 预计工时 |
|------|------|----------|
| 1 | 项目初始化 + Express 骨架 + SQLite | 30min |
| 2 | HEARTBEAT.md 解析器 + tasks API | 30min |
| 3 | OpenClaw sessions API 集成 + agents API | 45min |
| 4 | .task-alerts.md 解析器 + alerts API | 15min |
| 5 | 前端面板（暗色主题，任务卡片+agent表格） | 1h |
| 6 | 自动刷新（SSE 或 polling） | 20min |
| 7 | Nginx 配置 + 部署 | 15min |
| 总计 | | ~3.5h |

## 十、与现有系统的集成点

| 集成点 | 方式 | 说明 |
|--------|------|------|
| HEARTBEAT.md | 文件读取 | 解析 `- [ ]` 和 `- [x]` 行提取任务 |
| .task-alerts.md | 文件读取 | 解析告警 |
| OpenClaw Gateway | HTTP API | `http://localhost:12145/api/sessions` 等 |
| shared/results/ | 文件扫描 | 检测报告产出 |
| 本地机器 | HTTP over ZeroTier | `http://10.12.192.174:18789/api/sessions` |
| Git repos | git log 命令 | 本地机器通过 SSH 执行 |

---

*文档编写: 2026-06-27*
*基于 R-117 方案 + 用户实际架构*
