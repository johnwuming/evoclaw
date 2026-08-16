# MEMORY.md — 长期记忆（优化稿）

> 仅主会话加载；群聊/共享会话/子 agent 任务书不得加载。
> 本文件只存**事实、决策、教训**，不定义行为规则。规则见 `AGENTS.md`、`USER.md`。
> 目标体积 ≤5KB；每月整理一次，过时条目删除或归档到 `memory/YYYY-MM-DD.md`。

## 关键决策记录

- **2026-08-15 · v4 极简架构**：固定团队（研究/开发/量化）停用，改为按需 `sessions_spawn`；任务中心降级为登记簿/进度看板。现行规则以 AGENTS.md 为准，本条只是历史事实。
- **2026-08-16 · 上下文纪律**：R-208 评审子 agent 10 分钟烧 151 万 tokens 超时，证据丢失。教训：上下文纪律必须由 spawn 模板强制传导给每个子 agent（已写入 `tools/templates/spawn-task.md`）。
- **2026-08-09 · 验收原则**：审核交付物必须独立验证，不信任完成摘要文字。

## 工具与服务事实

- **账单编辑器**：部署 `https://82.156.124.186:8052`，项目 `/root/.openclaw/workspace/tools/bill-editor/`，Node.js + SQLite，systemd 常驻。详见 `memory/2026-06-08.md`。

## 基础设施事实

- 服务器：腾讯云 VPS（`82.156.124.186`），Nginx 以 root 运行。
- Node.js 通过 nvm 管理：`/root/.nvm/versions/node/v22.22.2/bin/node`。
- npm 镜像源：`https://mirrors.tencent.com/npm/`。
- 模型与 API 配置：以 `/root/.openclaw/openclaw.json` 为准，不在本文件重复。

## 安全事件

- VPS 曾遭 6 次入侵（最近 2026-07-04），攻击向量为 Go 编译的 SSH 蠕虫（暴力破解字典 + TLS 伪装 + 端口扫描），曾篡改 `/etc/shadow`。
- 已关闭公网 SSH。处置流程：删恶意文件 → 从 `/etc/shadow-` 恢复 shadow → 重设密码。详见 `memory/2026-07-04.md`。

## 智能家居状态

- LG 洗烘塔已通过 ThinQ 官方集成接入 HA；可用实体：`select.xi_yi_ji_operation`、`number.xi_yi_ji_delayed_end`、`event.xi_yi_ji_notification`。
- 小爱音箱已通过 Xiaomi Home 官方集成接入 HA，中枢网关虚拟事件实体已确认。
- 目标场景：小爱语音触发「洗衣机早上洗完」→ HA 计算启动时间 → 延时启动 → 洗完 TTS 播报。
- 卡点（7/4）：米家场景虚拟事件未绑定小爱语音触发，手动执行场景后 HA 未收到推送。

## 关联文件

- 私密家庭信息：`USER_PRIVATE.md`（仅主会话）。
- 环境事实与工具：`TOOLS.md`。
- 路径规范：`PATHS.md`。
