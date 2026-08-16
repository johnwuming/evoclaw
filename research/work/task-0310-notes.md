# task-0310 任务中心 URL 化 — 工作笔记

## 踩点结论（与任务书差异）
- nginx 8052 根路径**不是静态账单页**，而是 `location = /` 302 按 UA 跳 /billing 或 /billing/mobile；账单编辑器**本就在 /billing 与 /billing/mobile**（alias desktop/mobile）。无需迁移账单，只需改根路径行为。
- **关键冲突**：8052 的 `/api/` → 8053（账单 API）。任务中心前端 `var API = window.location.pathname.replace(/\/$/,'')`（L6323），在根路径时 API='' → `/api/tasks` 会撞账单 API。**若根路径直接代理，必须让前端 API 走 /task 前缀**。
- 方案：nginx 根路径代理时带 `X-Forwarded-Prefix: /task` 头，express `/` 与 `/login` 处理器读该头把模板 `__API_BASE__` 占位符替换为 `"/task"`；无头时保持原 pathname 推导（8055 直连与 /task/ 访问不变）。
- 另发现 6 处硬编码绝对 fetch（登录页 /api/login、hp-stats、alerts×3、agents abort），在 /task/ 下**本来就是坏的**（打到 8053），本次一并改为 API 前缀（对 /task/ 与根路径都是修复）。
- auth 中间件当前注释停用（L571），登录页为装饰性，但仍同步修好其 API 前缀以防日后启用。
- 无 SSE/WebSocket；/vendor/html2canvas 已用 API 前缀加载。

## hash 路由方案（选型：#page= 与 #report= 互斥）
- tab 层：`#page=<name>`，showPage 尾部 `history.replaceState`（无历史污染；浏览器后退=离开页面）。
- 报告详情：沿用 `#report=<id>`，**优先级高于 #page=**（详情开着时 URL 由详情层接管，关闭回 `#page=reports`）。
- 启动：#report= → 进 reports + auto-open IIFE（原有）；否则 #page=xxx 合法则 showPage(xxx)；否则 tasks。
- hashchange 监听：手动改 hash / 粘贴链接时同步 tab 与详情。
- 量化子 tab（data/factor/models/btlc/paper）不做独立 URL（范围控制，留待扩展）。

## 实施记录
- server.js 已备份 server.js.bak-task0310-20260816
- nginx 已备份 /etc/nginx/sites-enabled/bill-editor.bak-task0310
（进行中）

## 验证结果
（待填）
