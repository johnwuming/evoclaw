# R-350 · 新看板部署 quantv6（task-0547）

- 日期：2026-08-29
- 目标：以 `https://www.zhengqiangnan.cn/quantv6/`（Basic Auth，只读）挂出 quant-dashboard v6 看板，数据来自 quant-bff systemd 服务（真实 vC-0 账本）。
- 状态：**完成，端到端验证通过**

## 1. BFF 服务化

- 安装 `/etc/systemd/system/quant-bff.service`（源自 `tools/quant-bff/deploy/quant-bff.service`），`enabled + active`。
- 关键修正：server 代码把 `LEDGER_DIR` 当作含 `events/` 子目录的账本根（内部扫描 `LEDGER_DIR/events`），故设为 `/root/.openclaw/workspace/tools/quant-bff/live`（任务书原写 `live/events` 会导致启动后账本加载 ENOENT、健康检查 degraded）。
- 部署时发现 8180 被前一 agent 会话遗留的 dev 实例占用（`node src/server.js`，LEDGER_DIR=live，00:53 启动），已 kill 由 systemd 接管；18180 上的 `/tmp/qbff-tail-fixture` 测试实例与本任务无关，未动。
- 验证：`GET /api/v1/health` → `status=ok, ledger_tail_ts=2026-08-28T15:50:22+00:00, replay_events=2`（真实账本；夹具 tail 为 03:00:00Z/pending_risks=3，可区分）。
- BFF 源码零改动，28/28 测试基线不受影响。

## 2. 前端构建（/quantv6/ 子路径）

- `vite.config.js` 增加 `base: '/quantv6/'`。
- `src/api.js`：调用方逻辑路径（`/api/v1/...`）统一经 `urlFor() = API_BASE + path` 挂前缀；`API_BASE = VITE_API_BASE || ''`（dev/preview 同源不受影响）；`fetchEvents` 亦改走 `urlFor`。
- 生产构建 `VITE_API_BASE=/quantv6`：dist 资源引用 `/quantv6/assets/...`。
- 返工记录：初版 `/quantv6/api` + 剥 `/api/v1` 的方案经无头浏览器验证 404（后端契约是 `/api/v1/*`），最终改为 `/quantv6` 前缀 + 保留逻辑路径，nginx 侧 `/quantv6/api/` 前缀替换后 BFF 恰好收到 `/api/v1/*`。

## 3. nginx（443 TLS 终止块）

- 变更文件：`/etc/nginx/sites-enabled/www-zhengqiangnan`（备份 `.bak-task0547`）；12145 SNI conf 未动。
- 新增（只加不改，置于 `location /` 之前）：
  - `location ^~ /quantv6/api/`：Basic Auth + `proxy_pass http://127.0.0.1:8180/api/`（带 Host/X-Real-IP/XFF/XFP 头）
  - `location ^~ /quantv6/`：Basic Auth + `alias .../quant-dashboard/dist/` + `try_files $uri $uri/ /quantv6/index.html`
- 认证：`/etc/nginx/.htpasswd_quantv6`，用户 `wuming`，随机密码（已入 `/root/.openclaw/secrets.env` 的 `QUANTV6_BASIC_AUTH`）。
- 红线遵守：`nginx -t` 通过才 reload；未触碰 8055 根路由、`/df0s6p`、`/triple`、80/ACME、crontab；reload 后回归 `/`=200、`/df0s6p`=302、`/triple/`=200。

## 4. 端到端验证

| 检查 | 结果 |
|---|---|
| 无凭据 `GET /quantv6/` | 401 ✅ |
| 带凭据 `GET /quantv6/` | 200 ✅ |
| 无凭据 `/quantv6/api/v1/health` | 401 ✅ |
| 带凭据 `/quantv6/api/v1/health` | 真实数据 JSON（tail 2026-08-28T15:50:22+00:00，replay_events=2，pending_risks=0）✅ |
| 静态资源 `/quantv6/assets/*.js` | 200 ✅ |
| 无头浏览器 390×844 + Basic Auth | status 200，`scrollWidth=390` ✅ |
| 总览页渲染 | 账本尾 2026-08-28 23:50、对账✅一致、待处理风险 0、引擎 2 全部在役、vC-0(paper) 权重 58.0%/42.0% 与账本一致 ✅ |

截图：`work/task-0547-quantv6-390.png`（视觉复核：暗色主题布局正常，无溢出/错位/报错；「待接入」为信息性占位——NAV 序列待 HP 产物接入，符合不伪造数据原则）。

## 5. 使用说明

- 地址：`https://www.zhengqiangnan.cn/quantv6/`（Basic Auth：`wuming` / 密码见 secrets.env `QUANTV6_BASIC_AUTH`）
- 只读承诺不变：BFF 零写面、回环监听 127.0.0.1:8180、前端全站 GET；写操作仍需走任务中心。
- 回滚：还原 `www-zhengqiangnan.bak-task0547` + `systemctl reload nginx`；停服 `systemctl disable --now quant-bff`。
