notes dir ready 2026-08-18T05:34:30Z

## 基线（修复前）
- metrics.db MAX(timestamp): hp=2026-08-17T01:08:01Z（冻结，符合根因），vps=2026-08-18T05:35:01Z（正常）
- dashboard 服务名：agent-dashboard.service，当前 active running
- pull-hp-metrics.sh 共 1792B：scp 命令在 L13-14，`2>/dev/null || exit 0` 静默吞错
- server.js renderSmCurrent() 在 L12819，卡片渲染 smCard() 在 L12795，头部时间戳用 smFmtTime（HH:MM 无秒、无过期标记）

## 修复点
1. 脚本：scp 加 -O；失败时写日志 scripts/pull-hp-metrics.log（时间戳+错误摘要，密码替换为 ***，日志>100KB 截断保留后半 50KB）
2. 前端：smCard 头部改用新 helper smUpdatedBadge(iso)：显示"更新于 HH:MM:SS"（CST），>10 分钟显示 ⚠ + 红色 + "（过期）"
