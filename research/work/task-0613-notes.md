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
- schemaVersions 在 2026.7.1 是否存在/版本号多少（npm view 2026.7.1）
- 迁移行为文档 + 升级阻力官方清单（docs.openclaw.ai / releases）

