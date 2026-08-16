# OpenClaw 环境实际状态扫描

> 扫描时间：2026-08-10 02:36  
> 来源：openclaw-capabilities 子 Agent + rdagent-integration 子 Agent

## 关键发现

### OpenClaw 配置（openclaw.json）
- 配置文件：`/root/.openclaw/openclaw.json`（非 YAML）
- 网关端口：12145，模式 local，bind lan
- 控制 UI：basePath `/df0s6p`
- 默认模型：glmcode/glm-5.2
- 备选模型：deepseek-v4-flash/pro, volcengine

### Agent 定义（6 个）
| Agent ID | 名称 | 工作区 |
|----------|------|--------|
| main | 小朱桑 🦞 | /root/.openclaw/workspace |
| research-lead | 研究主管 | /root/.openclaw/workspace-research |
| research-searcher | 研究搜索员 | /root/.openclaw/workspace-search |
| research-reviewer | 研究审核员 | /root/.openclaw/workspace-reviewer |
| research-citation | 研究引用员 | /root/.openclaw/workspace-citation |
| quant-compute | 量化员 | /root/.openclaw/workspace-quant |

### 子 Agent 层级
- main → research-lead, claude, quant-compute
- research-lead → research-searcher, research-reviewer, research-citation, quant-compute

### 通信渠道
- lightclawbot: 已启用
- qqbot: 已启用 (appId=1903765716)
- openclaw-weixin (微信): 已启用
- telegram: 已禁用

### 任务中心
- 独立 Node.js 服务：http://127.0.0.1:8055/api/tasks

### ACP 配置
- 默认 Agent: claude
- 允许: claude, codex, gemini, opencode

### 插件（7 个启用）
browser, acpx, parallel, qqbot, openclaw-weixin, lightclawbot, memory-tencentdb

### 基础设施
- 服务器：腾讯云 VPS 82.156.124.186
- 群晖 NAS：10.12.192.241 (ZeroTier)
- Node.js: v22.23.2
- OpenClaw 版本: 2026.6.11
- 子 Agent 限制：最大 8 并发，深度 4，超时 2400s

### shared/ 工作区状态
- **factor_db.sqlite**: 不存在
- **quant-evolve**: 不存在
- **parquet 文件**: 不存在
- **shared/results/**: 190+ 研究报告（R-001 ~ R-189）
- **shared/projects/**: 空目录
- 量化相关报告在 06-量化投资/ 和 14-投资研究/ 目录

### RD-Agent 集成要点
- 纯 CLI 工具，无原生 REST API（Flask server_ui 提供 API）
- 输出：pickle trace + 因子 .py + 回测 CSV
- 仅支持 Linux，Python 3.10/3.11
- Docker 必需（或 Conda 模式）
- DeepSeek 有官方配置示例
- 高度模块化，所有组件可通过环境变量替换
