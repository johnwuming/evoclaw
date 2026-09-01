# task-0613 过程笔记 — OpenClaw 2026.7.1-2 → 2026.8.1 升级风险评估

开始时间：2026-09-01 15:09 (GMT+8)
原则：只读评估；边查边写；每条结论带来源。

## N0. 任务要点摘录
- 目标：go/no-go + 摩擦清单 + 插件兼容 + 回滚 SOP + 时机建议
- 当前：2026.7.1-2 (0790d9f)，pnpm 全局；latest=2026.8.1（官方口径 2.0）、beta=2026.9.1-beta.1、extended-stable=2026.6.34
- 重度依赖：sessions_spawn 子agent+完成回传、会话可见性=tree、openclaw-weixin、qqbot 三件套、心跳-任务中心(8055)、cron

## N1. 本机盘点（实测输出，2026-09-01 15:2x）
- 网关：systemd **user** 单元 `openclaw-gateway.service`（`systemctl --user`，描述硬编码 v2026.7.1-2），unit 文件 /root/.config/systemd/user/openclaw-gateway.service（另有 .bak）；进程 `node .../openclaw@2026.7.1-2/.../dist/index.js gateway --port 12145`
- 已装插件（extensions/，8 个）：dingtalk-connector、lightclawbot、memory-tencentdb、openclaw-lark、openclaw-plugin-yuanbao、openclaw-weixin、qqbot、wecom-openclaw-plugin
- plugins.entries 启用中：browser/acpx/parallel/qqbot/openclaw-weixin/lightclawbot/memory-tencentdb/deepseek=true；openclaw-lark/wecom/dingtalk/yuanbao=false
- plugin-skills/（6 个）：acp-router、browser-automation、lightclaw-cron、qqbot-channel、qqbot-media、qqbot-remind
- ~/.openclaw 顶层：agents(1.2G: main+claude)、extensions(1.4G)、workspace(795M)、memory-tdai(60M)、credentials(12K)、gateway/(仅 tls/)、agents-disabled-backup、migration-backup-20260801-104819、多个 openclaw.json.bak*
- crontab(root)：agent-dashboard 采集(* * * *)、pull-hp-metrics(*/2)、HP auto-sync(*/30)、full-sync(0 3)、gold_mmf_push(0 9 2)、3am lighthouse backup；/etc/cron.d: certbot/e2scrub/jokehub-backup/sgagenttask/sysstat/yunjing —— 无 openclaw 心跳 cron（心跳为 openclaw 内建）
- 相关 systemd：evolving-claw-sync.service(inotify 同步，active)、openclaw-upgrade-guard.service(oneshot，boot 时把 PROGRESSING 改 FAILED——说明宿主机有 /etc/lighthouse/upgrade_status 升级状态机)
- 当前包 package.json 的 openclaw block = {} （空）；2026.8.1 的 openclaw.schemaVersions = { agent: 19, state: 15 }（npm view 实测）
- 2026.8.1 engines: node >=22.22.3 <23 || >=24.15.0 <25 || >=25.9.0；本机 node v22.23.2 ✅满足
- npm dist-tags 实测：latest=2026.8.1、beta=2026.9.1-beta.1、extended-stable=2026.6.34、alpha=2026.5.19-alpha.1
- agents/main 结构：agent/ chats/ sessions/（sessions 内大量 *.json trajectory-path）；未找到 schema 版本落盘文件（maxdepth 4）
- openclaw.json 顶层键：meta,wizard,browser,auth,models,agents,tools,commands,session,channels,gateway,skills,plugins,mcp,messages,acp,bindings；session 仅 dmScope；gateway: port,mode,bind,controlUi,auth,tailscale,tools,trustedProxies
- 本地 bundled docs（当前版）：docs/announcements/ 仅 bluebubbles-imessage.md；docs/ 含 gateway/ install/ 等

## 待查
（已全部完成）

## N2. Schema 迁移机制（官方）
- 2026.7.1/2026.6.34 的 package.json 无 openclaw block（npm view 实测返回空）→ schemaVersions 为 2026.8.1 新增：agent=19, state=15
- 迁移语义（zread Configuration Reference，转述官方代码）：on-disk < supported → 自动前向迁移；= → 不动；> → 拒绝启动（防止旧二进制读新格式）。「回滚只能靠升级前全量备份」成立
- 8.1 release notes Fixes：'Newer database state: stop restart loops when the installed Gateway encounters a newer schema…fence incompatible cached state with an unhealthy readiness result' (#132916,#133081) → 新版自身处理「磁盘更新」场景改为健康检查 fence 而非重启循环
- 8.1 Fixes：'SQLite maintenance schema validation: reject current-version global and agent databases with missing or drifted canonical tables…while accepting supported additive-migration layouts' (#105583)
- 8.1 Changes：'Safer startup repair: apply safe doctor configuration migrations at Gateway startup before normal operation' (#132135) → 首次启动自动跑安全 doctor 迁移
- 8.1 新增 SQLite 状态层（plugin-state-store.sqlite、backup sqlite、shared credential store SQLite）→ 状态从纯文件向 SQLite 迁移，首次启动写入新库

## N3. 官方摩擦清单（v2026.8.1 release notes 逐条 + zread Known Upgrade Friction）
来源：github.com/openclaw/openclaw releases tag v2026.8.1（已抓全文本 /tmp/openclaw-web-fetch-edb2ec6bd5893b86.log）；zread.ai/openclaw/openclaw/4-latest-updates「Known Upgrade Friction」段（官方承认原句：'Real-world upgrades from v2026.7.x have not been painless'）
1. OpenProse 移除（breaking）：bundled 插件+/prose 命令删除，需 doctor --fix 清理 → 本机未用 OpenProse【不影响】
2. OpenAI 路由迁移（breaking）：codex/*→openai/* 需 doctor --fix → 本机 models 无 codex 引用（grep 实测 NONE）【不影响】
3. CPU 缩放前台并发：默认 top-level 并发从固定小值改为按 CPU 数（bounded 8~16）→ 本机 nproc=2，旧默认≈2，升级后预计跳到下限8（未实测，只读评估）【影响 YES，高】缓解：显式设置 agents.defaults 并发上限
4. SDK 子路径废弃（2026-09-01 起，'upcoming gates, not removals in this release'）：config-runtime/infra-runtime/channel-* 等子路径将移除 → openclaw-weixin v2.4.6 实测引用 infra-runtime×4 + config-runtime×1【8.1 内可加载，下个大版本会坏；影响 YES，中】
5. Named agent setup：legacy main 会话历史迁移+复用 main 为普通 agent id，需 doctor 修复 → 本机 agents/main+claude【影响 YES，中：升级后必须跑 doctor 并核对 agents/ 目录】
6. Owner-directed ambient heartbeat：环境心跳默认发 owner DM，不可路由则跳过 → 本机心跳链路依赖 HEARTBEAT.md+内建心跳【影响 YES，中：需确认 owner 可解析，否则环境心跳静默不发】
7. Session reset 默认变化：无策略时跨空闲/跨天保留会话 → 我们未配 reset 策略，行为从「重置」变「保留」【影响 YES，低-中：上下文膨胀方向变化】
8. Automatic self-learning 默认开：自动捕获 lessons+应用 scanner 批准的技能（用户自建技能仍 pending）【影响 YES，低：skills/ 目录可能被自动增改，需留意】
9. Grounded dreaming 默认开：后台记忆整合【影响 YES，低：memory-tdai 60M 可能增长】
10. Active Memory 私聊回忆默认开（个人安装、无 DM 隔离时）→ 微信私聊通道命中【影响 YES，中：隐私面扩大，可用显式开关关闭】
11. macOS App 'Legacy device identity sources conflict' 需单独 doctor --fix【不影响：无 macOS App】
12. 官方 provider 包拆分：缺配置包用 update repair / doctor --fix 恢复 → 本机 providers 为 glmcode/deepseek 自定义【影响待验证：升级后跑 doctor 看 provider 是否完整】
13. 插件安装 provenance 警告：任意可执行来源需 --force（ClawHub/官方目录/捆绑豁免）【影响 YES，低：影响未来插件更新流程】
14. 明确 model allowlist：modelPolicy.allow 迁移由 doctor 处理 → 本机无 modelPolicy.allow 键【不影响】

## N4. 依赖面行为变化对照（release notes Fixes 定位）
- sessions_spawn 完成回传：8.1 修复 subagent completions（visible session-only replies 不再误报 undelivered，line222）+ 失败通知（line223）+ Gateway/subagents 完成回程绑定（line262）→ 【改善，非回归；但属大改区，升级后必测】
- 会话可见性：新增 shared-session participation（visibility/membership/owner，line98）→ 向后兼容的增能力【低风险】
- 心跳投递：8.1 修复 restart-recovery gaps+重启后 one-shot 续投（line248）【改善】
- qqbot：token 获取 30s guarded-fetch deadline 修复（line312）【改善；qqbot 插件 compat>=2026.6.11 声明良好】
- MEMORY/上下文注入：self-learning/dreaming/recall 三项默认开（见 N3-8/9/10）

## N5. 插件兼容盘点（本机实测）
| 插件 | 版本 | compat 声明 | 废弃 SDK 子路径 | 判定 |
|---|---|---|---|---|
| openclaw-weixin | 2.4.6 | 无 compat 块 | infra-runtime×4, config-runtime×1 | 8.1 可载（deprecation 非移除）；下版本风险最高 |
| qqbot | 2026.6.11 | pluginApi>=2026.6.11 | 未检出 | 低风险 |
| lightclawbot | 1.2.17 | 无 compat 块 | 未检出 | 低风险（无声明） |
| memory-tencentdb | 1.0.0 | pluginApi>=2026.3.13, built@2026.3.13 | 未检出 | 中低（声明旧但未用废弃路径） |
- 禁用插件：openclaw-lark/wecom/dingtalk/yuanbao（enabled=false，不加载，无影响）
- workspace skills/ 格式：8.1 无 skills 目录格式 breaking；self-learning 只增改不改格式；Skill Workshop 为新增子系统

## N6. 升级/回滚机制（官方 updating.md，本地 docs 实读）
- 推荐路径：openclaw update（协调包替换+服务刷新+重启+验证）；手动装需先停网关（'stop the managed Gateway first'）
- pnpm 全局形态：docs 给 npm/pnpm/bun 手动示例；openclaw update 对 managed service 协调——本机 unit 为 user systemd openclaw-gateway.service
- 升级后必须：openclaw doctor → gateway restart → health/plugins list/gateway status --deep
- 自动更新：本机 config 无 update 键 → auto-updater 默认关【好：升级窗口可控】；OPENCLAW_NO_AUTO_UPDATE=1 可兜底
- 官方回滚：'npm i -g openclaw@<version> → doctor → gateway restart'，但 schema 前向迁移后旧版拒绝启动 → 真正回滚=恢复备份
- 备份覆盖（migrating.md：'The config file alone is not enough'）：openclaw.json+auth-profiles.json(agents/<id>/agent/)+credentials/+sessions+workspace——即 ~/.openclaw 全量

## N7. 升级窗口
- 约束：避开量化链路活跃（*/2 pull-hp-metrics、*/30 auto-sync 均为旁路采集，不依赖 openclaw；gold_mmf_push 每月2日 9:00）、避开 task-0612 发布窗口（用户口令，时间未定）、微信主会话低峰
- cron 中依赖 openclaw 的：无（心跳为 openclaw 内建，随网关停机暂停）
- 建议：任一天 11:00-14:00 或 22:00 后（避开早盘/收盘推送与心跳高峰）；全程预估 30-60 分钟（备份15-25G级压缩时间为主）

