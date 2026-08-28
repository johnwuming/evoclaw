# task-0547 部署笔记（quantv6）

## 0. 基线探查
- quant-bff.service 存在（1433B），LEDGER_DIR 当前=fixtures/good，需改 live/events
- live/events/ 含 iteration-ledger-2026-08.jsonl
- vite.config.js 无 base；src/api.js 4469B，fetchEvents 用 new URL('/api/v1/events', origin)

## 1. BFF 服务化（完成）
- 障碍：8180 被旧 dev 实例占（pid 2887844，LEDGER_DIR=live，00:53 由前一 agent 会话 bash 启动）→ kill 后 systemd 接管
- 关键发现：server 代码把 LEDGER_DIR 当作含 events/ 子目录的账本根（scandir LEDGER_DIR/events）→ 正确值=/root/.../quant-bff/live（非 live/events）；fixtures/good 结构印证（内含 events/）
- 安装结果：/etc/systemd/system/quant-bff.service，LEDGER_DIR=/root/.openclaw/workspace/tools/quant-bff/live，enabled+active
- 验证：GET /api/v1/health → status=ok ready=true ledger_tail_ts=2026-08-28T15:50:22+00:00 replay_events=2（真实 vC-0 账本，非夹具；夹具 tail=2026-08-28T03:00:00Z/pending_risks=3 可区分）
- 18180 端口另有一个 /tmp/qbff-tail-fixture 测试实例（pid 2821800），与本任务无关，未动

## 2. 前端重建（完成）
- vite.config.js 加 base: '/quantv6/'；src/api.js 抽 API_BASE=import.meta.env.VITE_API_BASE||'/api/v1'，getJSON 与 fetchEvents 均走前缀（其余 fetch 全部经 getJSON，无漏网硬编码）
- VITE_API_BASE=/quantv6/api 构建：dist/index.html 资源引用 /quantv6/assets/...；bundle 内含 quantv6/api ✓
