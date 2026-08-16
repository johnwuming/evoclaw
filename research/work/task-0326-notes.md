# task-0326 量化 Tab 防横向滚动加固笔记

## 任务
量化 Tab（btlc 页）任何数据量下不允许页面横向滚动。多层防御：区块级 overflow-x 约束、长内容治理（word-break/ellipsis）、极端数据兜底验证。

## 时间线
- 22:32 开始，先查文件大小与现状。

## 现状核验（22:33-22:34）
- server.js = 641,503 bytes（>30KB，只用 grep/sed 局部读）；备份已建 server.js.bak-task0326-20260816-223216
- CSS 区段定位：
  - L6093 .quant-cards（flex, overflow-x:auto ✅）
  - L6096 .quant-chart-wrap（卡片容器，无 overflow 约束 ❌）
  - L6107-6110 .quant-table：th/td 均 white-space:nowrap，宽表依赖各处内联 `<div style="overflow-x:auto">` 包裹（20+ 处）
  - L6186 .quant-page{display:none} / .quant-page.active{display:block}（无 overflow 约束 ❌）
  - L5955 .md-table-wrap 有 overflow-x:auto ✅
- 台账/决策时间线/五门禁等 API：/api/quant/ledger (L2553)、lifecycle (L2569)、pending (L2502)
- btlc 页渲染：loadBtlcQuant L9585 → page#quant-page-btlc → div#quantBtlcBody
- 登录：有 /login (L527)，CDP 验证需先处理登录

## 补充情报（22:3x，重试前）
- 导航：底部 nav 按钮 onclick="showPage('quant',this)"；量化子Tab switchQuantTab('btlc',true)，按钮 id=qseg-btlc
- 登录：POST /api/login {username,password} → Set-Cookie dash_sess（HMAC 签名，密钥 .session-secret）；默认用户 admin/alison/john，默认密码环境变量 DASHBOARD_PASSWORD 未设时用代码内默认（systemd Environment 只见 NODE_ENV=production，待确认完整 unit）
- Chrome 可用：/usr/bin/google-chrome-stable、/usr/local/bin/chromium-browser；Node 22 自带 WebSocket → 可写零依赖 CDP 脚本
- 量化表全部被内联 overflow-x:auto 包裹（17 处，无裸表）；md-table-wrap 也有 overflow-x:auto
- 台账表 L10448、决策 L2552+、lifecycle L2569+
- 拟定 CSS 加固点：#screen-quant 与 .quant-page.active / .quant-chart-wrap 加 overflow-x:hidden + min-width:0 + max-width:100%；.quant-page.active 继承 overflow-wrap:anywhere（防 flex/grid 长串撑破）；canvas/svg/img max-width:100%；select max-width

## 实施（22:5x）
- CSS 加固块插入 L6193 后（</style> 前）：#screen-quant 系 max-width/overflow-x:hidden；flex/grid 子项 min-width:0；td/th word-break；td span/div break-all；svg/canvas/img max-width:100%；tl-body/desc/summary overflow-wrap
- JS 兜底 quantHScrollGuard 插在 quantRestoreScroll 后：量化页可见时若 de.scrollWidth>clientWidth → 根禁止横滚 + 超宽元素降级内部横滚；resize 防抖触发
- node --check 通过（NODE_OK）；服务仍 active（重启前快照）
- 密码默认 'Ak704223'；用户默认 admin/alison/john

## 服务重启（22:5x 续）
- systemctl restart agent-dashboard → active；/login 200 正常响应
- 下一步：CDP 双视口验证 + 极端注入 + 回归 + 截图

## CDP 首跑（22:5x，脚本 /tmp/task0326-cdp.mjs）
- NAV: ok:39367（btlc 渲染完成）
- MOBILE_NAT 390x844: scrollWidth=390 <= clientWidth=390 ✅
- DESKTOP_NAT 1440x900: scrollWidth=1425 <= clientWidth=1425 ✅
- INJECT: ledgerInjected=true scatterInjected=true pipelineInjected=true
- MOBILE_STRESS: scrollWidth=390 <= 390 ✅ / DESKTOP_STRESS: 1425 <= 1425 ✅
- 回归断言 eval 抛 SyntaxError（正则字面量 flags 解析问题）→ 需改用 includes 重跑；截图未拍
- 结论：核心验收 2/3 已过（自然+极端均无横滚）
