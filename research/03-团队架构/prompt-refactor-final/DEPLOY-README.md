# 提示词体系重构：最终部署方案（R-213）

> 评审：主 agent（2026-08-16 14:53 用户指示）；原稿：DSH 会话 `/root/dsh-workspace/report/`（13 文件）
> 本目录 = 定稿。原稿声明 8 项抽验全过；主 agent 修正 3 处 + 新增本部署说明。
> **状态：待用户批准部署（未覆盖 workspace 正式文件）**

## 一、定稿清单与处置

| # | 文件 | 处置 | 相对 DSH 原稿的改动 |
|---|------|------|---------------------|
| 1 | `AGENTS.md` | 采纳+改 | §9 按需加载表加「量化任务 spawn → spawn-task.md 量化附加纪律」一行 |
| 2 | `SOUL.md` | 原样 | — |
| 3 | `USER.md` | 原样 | —（含"先方案后实施"偏好，解决旧 MEMORY 规则上移问题） |
| 4 | `USER_PRIVATE.md` | 原样 | —（家庭信息，仅主会话补读） |
| 5 | `MEMORY.md` | 原样 | —（事实/决策/教训已核实无丢失；模型配置改以 openclaw.json 为准） |
| 6 | `TOOLS.md` | 采纳+改 | secrets.env 首次迁移清单（4 变量：NAS_SSH/SUDO/DSH_ACCESS_CODE/QUANT_SSH）+ 轮换提示 |
| 7 | `HEARTBEAT.md` | 原样 | —（1.6KB 纯契约版，量化铁律已迁 spawn-task） |
| 8 | `PATHS.md` | 原样 | —（已核对：零 ubuntu 残留、19 分类与实际一致） |
| 9 | `spawn-task.md` | 采纳+改 | 新增「量化任务附加纪律」段：HP 连接/勿杀进程/PIT 对齐/IC 口径/五门禁 PASS 直接 activate/禁改清单 |
| 10 | `heartbeat.sh.md` | 原样 | —（部署时先跑一次核对 jq 键名再上岗） |
| 11 | `skill-group-chat.md` | 原样 | — |
| 12 | `skill-image-understanding.md` | 原样 | —（视觉模型 glmcode/glm-5v-turbo 细节在此承接） |
| 13 | `skill-dev-task.md` | 原样 | — |

## 二、部署位置与方式

| 定稿文件 | 部署到 | 说明 |
|---|---|---|
| AGENTS/SOUL/USER/USER_PRIVATE/MEMORY/TOOLS/HEARTBEAT/PATHS .md | `/root/.openclaw/workspace/` 同名覆盖 | 8 个常驻文件 |
| spawn-task.md | `/root/.openclaw/workspace/tools/templates/spawn-task.md` | 覆盖（旧 subagent-context-discipline.md 保留但不再是唯一来源） |
| heartbeat.sh.md | 另存为 `/root/.openclaw/workspace/scripts/heartbeat.sh` + chmod +x | 文档稿→脚本 |
| skill-*.md ×3 | `/root/.openclaw/workspace/skills/<名>/SKILL.md` | group-chat / image-understanding / dev-task |

**保留不动**：`IDENTITY.md`（小朱桑身份定义，OpenClaw 标准注入文件，新清单未覆盖它，原文件继续生效）。

## 三、部署顺序（P1/P2 两阶段）

**P1（批准当日，~15 分钟）**
1. 备份：`mkdir -p /root/backups/prompt-bak-20260816 && cd /root/.openclaw/workspace && cp AGENTS.md SOUL.md USER.md MEMORY.md TOOLS.md HEARTBEAT.md PATHS.md IDENTITY.md /root/backups/prompt-bak-20260816/ && cp tools/templates/spawn-task.md /root/backups/prompt-bak-20260816/spawn-task.md`
2. 建 secrets.env（600）并迁移 4 变量，验证 SSH/sudo 可用
3. 覆盖 8 个 workspace 常驻文件 + spawn-task 模板
4. 建议同期轮换已暴露密码（NAS/DSH/sudo——机器有 6 次入侵史；git 仓库未泄露过 TOOLS.md，属加固非急救）

**P2（P1 后观察 1 天）**
5. `bash scripts/heartbeat.sh` 试跑一次，按实际 API 返回核对 jq 键名（脚本头部注释自带此要求）
6. 确认无误 → 部署新 HEARTBEAT.md 契约版 → 观察 2 个心跳周期（每 30min，产出应路由微信）
7. 3 个 skill 文件 + 下次 spawn 任务试点 spawn-task 新模板（验证纪律段传导）

## 四、回归验证（部署后必跑）

1. 简单任务直接做（查状态类）→ 正常
2. 复杂任务：登记带 sourceSession → spawn 任务书含纪律段 → 审核通知带 task-XXXX 且按来源路由
3. 心跳：只跑 heartbeat.sh → 输出契约 JSON → 路由微信
4. 收到图片：先视觉识别再回答
5. 大文件：>30KB 不全读（日志里无全量 cat 痕迹）
6. 新会话冷启动：8 文件注入正常，无重复读取

## 五、回退

任一阶段异常：`cp /root/backups/prompt-bak-20260816/* <原位置>` 即回旧版；secrets.env 独立于提示词，无需回退。P2 的 heartbeat.sh 不满意可保留旧 HEARTBEAT.md（两者不冲突，脚本只是把手工查询固化）。

## 六、遗留决策（部署后择期）

- 旧 `subagent-context-discipline.md` 与新 spawn-task.md 并存 30 天后删除前者
- `USER_PRIVATE.md` 依赖 §4 指令补读（约定层）而非 OpenClaw 机制层——若未来 OpenClaw 支持自定义注入文件再升级
- 17-量化投资 与 04-投资研究 目录合并（PATHS.md 已标注"待合并"）
