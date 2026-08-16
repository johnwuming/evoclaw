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
- server.js 已备份 server.js.bak-task0310-20260816；nginx 已备份 /etc/nginx/bill-editor.bak-task0310（勿放 sites-enabled，会被 include）
- server.js：
  1. 新增 injectApiBase()：按 X-Forwarded-Prefix 头替换模板 __API_BASE__（/ 与 /login 两处处理器接入）
  2. 模板两处 var API 改为 __API_BASE__ 占位符（dashboard 主模板 + 登录页）
  3. showPage 尾部 syncHashRoute(name)：replaceState 写 #page=<name>；详情打开时让位（切 tab 先收详情）；var _hashSyncSuspended 暂停开关
  4. closeReportDetail：清空 hash 改为回写 #page=reports（带暂停开关守卫）
  5. auto-open IIFE：showPage('reports') 包 suspend，避免 #report= 被 #page= 覆写
  6. 启动路由：#report= 优先（交给 IIFE）→ #page=<name>（合法 screen）→ 默认 tasks；另加 hashchange 监听（手动改地址同步 tab/详情）
  7. 6 处硬编码绝对 fetch 改 API 前缀：登录页 /api/login + 登录后跳转、hp-stats、alerts active/history/acknowledge、agents abort（前五处在 /task/ 下原本就打到 8053，属修复）
- nginx：location = / 的 UA 302 块 → location / 代理 8055 + X-Forwarded-Prefix /task；/task/、/api/(8053)、/billing、静态资源等其余 location 不变
- **教训：同一消息里对同一文件的多个 apply_patch 会互相覆盖（后者基于旧快照写入，吞掉前者）**，本次丢过 3 处补丁，串行重打后解决；多补丁必须串行发或合并为一个补丁

## 验证结果（全过）
- node --check ✓；agent-dashboard restart 后 active ✓；nginx -t + reload ✓
- curl：8052 根=任务中心 HTML（nav-btn×11，var API="/task"）；/billing→301→/200；/billing/mobile/ 200；/task/ 200（pathname 推导 API）；/task/api/tasks ✓；/api/login POST 仍 8053（{"error":"未登录"}）；/task/vendor/… 200；chart/marked/remixicon 200
- CDP 有头 E2E（chrome 9222 + Security.setIgnoreCertificateErrors）：21/21 PASS ——
  根路径默认 #page=tasks；点 tab→#page=reports；刷新保持 reports/quant；#report=R-212 直达详情且 URL 保持；关闭详情→#page=reports；详情开着切 tab 自动收起并让位 hash；/task/ 旧路径同样支持；/billing/ 账单页（title=小青账）+ 账单 API 归 8053；根路径页面经 /task 前缀调 API ✓；hp-stats/alerts 前缀化后可达 ✓
- 报告分享链接 copyShareLink 用 origin+pathname+#report=，在根路径与 /task/ 下均生成正确 URL
- 未改：TOC 侧栏、报告筛选（0309）、视觉体系（0308）、账单 API/数据、tasks.db
- 注意：移动端 UA 访问 8052 根不再 302 到 /billing/mobile（按用户要求根=任务中心）；账单入口改为显式 /billing 与 /billing/mobile
