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

## 3. nginx（完成）
- TLS 终止块定位：/etc/nginx/sites-enabled/www-zhengqiangnan（listen 443 ssl，www.zhengqiangnan.cn）；12145 conf 是独立 SNI 网关不需动
- 备份：/etc/nginx/sites-enabled/www-zhengqiangnan.bak-task0547
- 新增两个 location（只加不改）：^~ /quantv6/api/ → proxy_pass http://127.0.0.1:8180/api/（映射后后端收到 /api/v1/*）；^~ /quantv6/ → alias dist/，try_files 兜底 index.html；两者均 auth_basic + /etc/nginx/.htpasswd_quantv6
- htpasswd：wuming 建好，明文已入 secrets.env（QUANTV6_BASIC_AUTH）
- nginx -t ok（conflicting server name warning 为存量，非本次引入）→ reload
- 回归：/ 200、/df0s6p 302、/triple/ 200 均不受影响；/quantv6/ 无凭据 401

## 4. 前端 API 前缀（返工一次，最终方案）
- 第一版 VITE_API_BASE=/quantv6/api + urlFor 剥 /api/v1 → 实际请求 /quantv6/api/health → 后端 /api/health 404（契约是 /api/v1/*）
- 最终：API_BASE 默认 ''（dev 同源），生产 VITE_API_BASE=/quantv6；urlFor=API_BASE+逻辑路径(/api/v1/...)；fetchEvents 也走 urlFor
- 请求链：/quantv6/api/v1/health → nginx 剥 /quantv6/api/ → BFF /api/v1/health ✓

## 5. 端到端验证（全部通过）
- 无凭据 /quantv6/ → 401；带凭据 → 200；/quantv6/api/v1/health → 真实数据（tail 2026-08-28T15:50:22+00:00，2 events，pending_risks 0）
- 静态资源 200；API 无凭据 401
- 无头浏览器 390x844 + basic auth：status 200，scrollWidth=390 ✓，总览页渲染：账本尾 2026-08-28 23:50、对账✅、风险 0、引擎 2 全部在役、vC-0 paper 权重 58/42 与账本一致；截图 work/task-0547-quantv6-390.png
- 截图视觉复核：暗色主题布局正常，无溢出/错位/报错；"待接入"为信息性占位（NAV 待 HP 产物）
