# R-396 · OpenClaw 2.0（v2026.8.1）升级风险评估报告

- **任务**：task-0613（只读评估，未实际升级/重启/安装）
- **日期**：2026-09-01
- **评估对象**：OpenClaw 2026.7.1-2 (0790d9f，pnpm 全局) → 2026.8.1（npm latest，官方口径「OpenClaw 2.0」）
- **分类说明**：任务书建议「07-系统运维」，但 07 前缀已被 07-产品调研 占用；沿现有最大编号顺延建 **20-系统运维**，README 已登记。

---

## 一、结论：**有条件 GO**

可升级，但**不建议立即执行**；推荐在 task-0612 发布窗口关闭后、按本报告 §六 SOP 在低峰窗口执行，并接受「一次性不可逆 schema 迁移」的约束（回滚=恢复备份，非降级二进制）。

核心理由：
1. **无阻断性不兼容**：本机重度依赖面（sessions_spawn 子 agent、微信通道、qqbot、心跳、任务中心）在 2026.8.1 中均为**增能力或修复**，无 API 移除（SDK 子路径废弃是「预告门禁，本版不移除」——官方原话）。
2. **但 2.0 是史上最大更新**（官方自述约 933 贡献者、1.6 万 PR），且官方明确承认 v2026.7.x 升级「not painless」（见 §二）；叠加 schema 前向迁移不可逆，必须以「全量备份 → 升级 → doctor → 验收 → 备份保留」的完整 SOP 执行。
3. **本机 node v22.23.2 满足 2026.8.1 engines 要求**（>=22.22.3 <23），无需动运行时（npm view 实测）。

---

## 二、官方已知升级阻力清单（逐条标注对本机影响）

主要来源：
- [A] v2026.8.1 官方 Release Notes（github.com/openclaw/openclaw/releases/tag/v2026.8.1，全文已抓档 /tmp/openclaw-web-fetch-edb2ec6bd5893b86.log）
- [B] 官方承认升级阻力的公开表述（zread.ai/openclaw/openclaw/4-latest-updates「Known Upgrade Friction」节，原句 *“Real-world upgrades from v2026.7.x have not been painless”*；该页为官方材料的 AI 转述，与 [A] 交叉验证）
- [C] 本机实测（命令输出见过程笔记 work/task-0613-notes.md）

| # | 官方阻力点 | 来源 | 对本机 | 证据 |
|---|---|---|---|---|
| 1 | 前台并发默认值改变：从固定小默认值改为按 CPU 数缩放（bounded 8~16）；[B] 称「未显式设置时静默跳到 10x/18x 并发」 | [A]#114047 + [B] | **YES·高** | 本机 nproc=2，升级后默认并发预计跳至下限 8（具体落值未实测）。必须显式设置 agents 并发上限，否则 2 核 VPS 可能被子 agent 挤占量化采集与网关资源 |
| 2 | SDK 子路径废弃（2026-09-01 起生效的预告门禁）：plugin-sdk/config-runtime、infra-runtime、channel-* 等子路径将迁移到新导入位；官方明示「upcoming gates, not removals in this release」 | [A] | **YES·中** | openclaw-weixin v2.4.6 实测引用废弃子路径 infra-runtime×4 + config-runtime×1（grep src/ 输出在笔记）。8.1 可正常加载，但**下个大版本会坏**，升级后需排期更新该插件 |
| 3 | Named agent setup：legacy main 会话历史迁移、main 复用为普通 agent id，需 doctor 修复 | [A]#123521 等 | **YES·中** | 本机 agents/ = main + claude 两个 agent（实测）。升级后必须跑 `openclaw doctor` 并核对 agents/ 目录与会话归属变化 |
| 4 | Owner-directed ambient heartbeat：环境心跳默认投递到可解析的 owner DM，不可路由则跳过 | [A]#121988 | **YES·中** | 心跳是本机 AGENTS.md 闭环的核心。若 owner 解析失败，环境心跳将**静默不发**。升级后首日必须实测心跳链路 |
| 5 | Active Memory 私聊回忆默认开（个人安装、无 DM 隔离配置时默认检索同 agent 私聊上下文） | [A]#110597 | **YES·中** | 微信私聊是主会话通道。隐私面扩大；如不接受，按官方说明用显式开关关闭 |
| 6 | Session reset 默认变化：无策略时跨空闲/跨天保留会话 | [A]#111140 | **YES·低中** | 本机 session 仅配 dmScope（实测），未配 reset 策略 → 行为由「重置」变「保留」，上下文用量方向性增大 |
| 7 | Automatic self-learning 默认开：自动捕获 lessons 并应用 scanner 批准的技能（用户自建技能仍保持 pending） | [A]#115576 | **YES·低** | workspace/skills/ 可能被自动增改；AGENTS.md 规则文件不受影响 |
| 8 | Grounded dreaming 默认开：模型后台记忆整合 | [A]#114819 | **YES·低** | memory-tdai（60M）可能增长；有显式关闭开关 |
| 9 | 官方 provider 包拆分：部分 provider 改为独立按需安装，缺失时用 `openclaw update repair` / `doctor --fix` 恢复 | [A]#116866 等 | **待验证·低** | 本机 providers 为 glmcode/deepseek 自定义配置；无官方内置 provider 依赖迹象。升级后 doctor 输出核对即可 |
| 10 | OpenProse 移除（breaking）+ codex/*→openai/* 路由迁移（breaking），均需 doctor --fix | [A]#128494 | **NO** | 本机未用 OpenProse；models 配置 grep 无任何 codex 引用（实测 NONE） |
| 11 | macOS App「Legacy device identity sources conflict」需单独 doctor --fix | [B] | **NO** | 无 macOS App |
| 12 | modelPolicy.allow 显式化迁移 | [A]#110888 | **NO** | 本机 config 无 modelPolicy.allow 键（实测） |
| 13 | 插件安装 provenance 警告：任意可执行来源需 --force（ClawHub/官方目录/捆绑豁免） | [A]#102197 | **YES·低** | 影响未来从非官方源更新 weixin 等插件的流程 |

**Schema 与状态迁移（机制层面）**：
- schemaVersions 为 2026.8.1 新增：`{ agent: 19, state: 15 }`（npm view openclaw@2026.8.1 实测）；2026.7.1 / 2026.6.34 的 package.json **均无** openclaw 块（npm view 实测返回空）。
- 官方迁移语义（zread Configuration Reference，转述代码行为）：磁盘 < 支持 → 自动前向迁移；磁盘 > 支持 → **拒绝启动**。即：迁移完成后旧二进制无法启动，「回滚」只能靠升级前全量备份。
- 8.1 对「磁盘更新」场景做了 fences 修复：不再重启循环，改为 unhealthy readiness 拒绝服务（[A]#132916/#133081）。
- 8.1 首次启动自动执行安全 doctor 配置迁移（[A]#132135），并引入 SQLite 状态层（plugin state / credentials / backup sqlite）。

## 三、配置与状态迁移对照

- openclaw.json 现有 17 个顶层键（meta/wizard/browser/auth/models/agents/tools/commands/session/channels/gateway/skills/plugins/mcp/messages/acp/bindings，实测）。8.1 无整键删除类 breaking； doctor 迁移针对的是 OpenProse 残留、codex/* 引用、modelPolicy、suggest_task 引用等**本机均不存在**的键（逐项 grep 实测，见 §二）。
- `update` 键本机未配置 → auto-updater 关闭（默认 off，updating.md 实读），升级窗口完全可控；必要时可设 `OPENCLAW_NO_AUTO_UPDATE=1` 兜底。
- 状态面：~/.openclaw 全量（agents 1.2G + extensions 1.4G + workspace 795M + memory-tdai 60M + credentials + gateway/tls，实测大小）= 升级前备份对象。官方 migrating.md 明示「只备 openclaw.json 不够」：auth-profiles 在 agents/<id>/agent/、通道凭据在 credentials/。

## 四、插件与技能兼容对照（本机 8 个 extensions 实测）

| 插件 | 版本 | compat 声明 | 废弃 SDK 子路径 | 判定 |
|---|---|---|---|---|
| openclaw-weixin（主通道） | 2.4.6 | 无 compat 块 | **infra-runtime×4、config-runtime×1** | 8.1 可加载（废弃≠移除）；**下个大版本高风险**，升级后应尽快跟进插件新版本 |
| qqbot（三件套宿主） | 2026.6.11 | pluginApi>=2026.6.11 | 未检出 | 低风险；8.1 还修复了 qqbot token 获取 30s 停滞问题（[A]#102897），**受益** |
| lightclawbot | 1.2.17 | 无 compat 块 | 未检出 | 低风险（无声明，升级后观察加载日志） |
| memory-tencentdb | 1.0.0 | pluginApi>=2026.3.13 | 未检出 | 中低风险；声明旧但未用废弃路径 |
| openclaw-lark / wecom / dingtalk / yuanbao | — | — | — | enabled=false，不加载，零影响 |

- workspace skills/（含 plugin-skills/ 6 个）：8.1 无技能目录格式 breaking；Skill Workshop 为新增子系统；self-learning 只增改不改格式。
- plugins.allow 8 项与 plugins.entries 启用状态均无 schema 变化迹象（键名实测一致）。

## 五、依赖面行为变化对照（sessions_spawn / 可见性 / 心跳 / 记忆）

| 依赖面 | 8.1 变化 | 性质 |
|---|---|---|
| sessions_spawn 完成回传 | 修复「yielded 子 agent 完成被误报 undelivered」「失败通知泛化」「完成回程绑定 Gateway runtime」（[A] 三处 fix） | **改善**；但属大改区，升级后必测：spawn 一个子 agent 验证完成事件回传 |
| 会话可见性（tree） | 新增 shared-session participation（visibility/membership/owner），向后兼容 | 增能力·低风险 |
| 心跳链路 | 修复 restart-recovery 间隙、支持重启后 one-shot 续投；环境心跳改 owner-DM 路由（见 §二#4） | 改善+行为变化，需实测 |
| MEMORY/上下文注入 | self-learning + dreaming + 私聊回忆三项默认开（§二#5/7/8） | 行为变化，均有显式关闭开关 |
| 独立服务（DSH 3080/账单编辑器/WSS/nginx/任务中心 8055/quant 采集 cron） | 与 openclaw 无进程依赖（crontab 实测：采集/同步/推送均为独立脚本，不经过 openclaw） | **不受升级影响**；网关停机窗口内仅心跳与消息收发暂停 |

## 六、升级时机建议

- **不执行窗口**：task-0612 发布窗口期内；每日 09:00-10:00 与 21:00-23:00（微信/qqbot 消息高峰，实测心跳与消息密集段）；每月 2 日 09:00（gold_mmf_push，实测 crontab）。
- **推荐窗口**：task-0612 完成后的任意工作日 **11:00-14:00**（低峰+用户在线可快速决策）或 **22:30 后**；全程预留 60-90 分钟（其中备份压缩 15-25 分钟为最大头，2.6G 级 ~/.openclaw 实测体量）。
- 升级前确认：无进行中的 spawn 子任务、无 pending_review 任务残留、HP 量化链路当月调仓日（09-01 为调仓日，当日不动）。

## 七、一页升级 SOP（照做版）

```bash
# ===== T-1 备份（网关运行时先做快照类，停机前做最终一致性备份）=====
cd ~ && systemctl --user stop openclaw-gateway.service
tar -czf /root/openclaw-backup-$(date +%Y%m%d-%H%M).tgz -C /root .openclaw --exclude='.openclaw/workspace/logs' --exclude='.openclaw/cache'
sha256sum /root/openclaw-backup-*.tgz | tee /root/openclaw-backup.sha256
# 注：备份=整个 ~/.openclaw（schema 迁移触达 agents/、credentials/、gateway/、memory-tdai/ 及新 SQLite 库）

# ===== T0 升级 =====
pnpm add -g openclaw@2026.8.1            # 或 openclaw update（managed service 路径，自动协调停启）
openclaw --version                        # 确认 2026.8.1
systemctl --user start openclaw-gateway.service
sleep 15 && openclaw doctor               # 自动迁移+修复（Named agent / provider 检查都在这步）
openclaw gateway restart                  # doctor 后按官方流程重启一次

# ===== T+1 验收（全过才算完成）=====
openclaw health
curl -fsS http://127.0.0.1:12145/readyz | head -c 200
openclaw plugins list --json | head -c 2000     # 8 插件 loaded：weixin/qqbot/lightclawbot/memory-tencentdb 必须在列
openclaw gateway status --deep --json | head -c 2000
# 人工验收：①微信收发一条 ②qqbot 收发一条 ③spawn 一个子 agent 验证完成回传 ④心跳跑一轮 ⑤并发确认：查 agents 并发生效值，过高则显式设上限
# 行为开关决策（默认全开，按需关）：self-learning / dreaming / 私聊回忆

# ===== 回滚（仅验收失败时）=====
systemctl --user stop openclaw-gateway.service
pnpm add -g openclaw@2026.7.1-2          # 若启动报 schema 版本高于支持 → 必须走备份恢复，此步跳过
rm -rf /root/.openclaw && tar -xzf /root/openclaw-backup-*.tgz -C /root   # 备份恢复路径（先二次确认 sha256）
systemctl --user start openclaw-gateway.service && openclaw doctor
```

**回滚双路径判据**（升级后未成功启动过新版的场景 vs 已迁移场景）：
- 路径 A「未迁移可降级」：仅替换了二进制、新版从未完成一次成功启动（schema 未落盘 stamp）→ 可直接 `pnpm add -g openclaw@2026.7.1-2` + 重启。
- 路径 B「已迁移必须恢复备份」：新版成功启动过任意一次（自动迁移已写入 agent=19/state=15 与 SQLite 层）→ 旧版会拒绝启动，必须整目录恢复备份。**两者以「新版是否成功启动过一次」为准，不凭感觉。**

## 八、遗留不确定项（如实声明）

1. 2 核 VPS 上 CPU 缩放并发的实际落值未实测（只读约束），以「升级后立即核对并显式设上限」处置。
2. openclaw-weixin 无新版兼容声明可查（非 git 仓库、无 compat 块），其 2.4.6 对 8.1 的兼容结论基于「废弃≠移除」官方表述+SDK gate 时间表推断；升级后若通道异常，第一优先排查该插件加载日志。
3. zread.ai 的「Known Upgrade Friction」节为官方材料的 AI 转述页（原文表述与 release notes 交叉验证一致），未找到独立官方文档页承载该清单原文——已如实标注来源性质。

## 九、来源索引

- [A] v2026.8.1 Release Notes：https://github.com/openclaw/openclaw/releases/tag/v2026.8.1（本地全文档存 /tmp/openclaw-web-fetch-edb2ec6bd5893b86.log）
- [B] Known Upgrade Friction / schemaVersions 迁移语义：https://zread.ai/openclaw/openclaw/4-latest-updates 及 /20-configuration-reference
- [C] updating.md / migrating.md（本机 2026.7.1 包内 docs 实读）：/root/.local/share/pnpm/global/5/.pnpm/openclaw@2026.7.1-2/node_modules/openclaw/docs/install/
- [D] 本机实测：openclaw.json（键名级）、~/.openclaw 目录、extensions/*/package.json、systemd user unit、crontab、npm view（命令与输出见 work/task-0613-notes.md）
