# task-0318 报告详情顶栏显示报告文件名+路径

## 目标
- 详情顶栏显示报告完整相对路径
- 桌面: 文件路径与工具按钮同一行; 手机(≤768px): 双行
- 长路径不截断, 支持横向滑动
- 不回归: 返回/标题/分类/工具按钮/TOC pinned 模式

## 勘察记录

- 2026-08-16 20:48 backup: server.js.bak-task0318-20260816-204815 (578993 bytes)

## 结构确认（2026-08-16 20:52）
- detail-bar HTML: L5974-5989（back btn / #detailTitle / #detailMeta / .d-actions 五按钮）
- CSS: .detail-bar L5553（flex 单行 sticky, touch-action:none）；.d-title L5554（flex:1+ellipsis）；.d-cat L5555；.d-actions L5283（flex-shrink:0）
- scanReports() L566: 每条报告含 path 字段（workspace 相对路径）；/reports/:id 返回含 path
- openReportDetail L7274: 加载后 rep.title→detailTitle, category+size→detailMeta；buildTOC→toggleTOC→syncTocTop 实测顶栏高度写 --toc-top
- 量化报告 openQuantReportDetail L10331 复用同一 overlay，API 只返回 {id,content} 无 path → 显示 workspace-quant/results/<id>.md
- 代码库断点风格：@media(max-width:768px) 无空格（L5700）；行内独立媒体查询也有先例（L5584）
- syncTocTop 是函数声明（同 script 块内），提前调用安全（hoisting）
- toc-pinned 的 .detail-bar margin-right:-260px：toc-panel.toc-sidebar top=--toc-top 在顶栏下方，全宽顶栏不与侧栏重叠，改动兼容

## 改造方案
1. .detail-bar 增加 flex-wrap:wrap + row-gap:6px
2. .d-cat 与 .d-actions 之间插入 <div class="d-path" id="detailPath"></div>
3. .d-path: flex:1 + min-width:0 + overflow-x:auto + white-space:nowrap + 等宽 11px + scrollbar 隐藏 + -webkit-overflow-scrolling:touch + touch-action:pan-x（父级 touch-action:none 需覆盖）+ :empty 隐藏
4. @media(max-width:768px): .d-path{order:1;flex-basis:100%} → 换行独占一行（flex-wrap 下 order 后置到第二行），工具按钮组留第一行
5. openReportDetail: 重置时清空 path；rep 加载后 path=rep.path，title 同步，补 syncTocTop()
6. openQuantReportDetail: 显示 workspace-quant/results/<id>.md

## 实施与基础验证（2026-08-16 20:56）
- 6 处编辑完成：CSS(.detail-bar flex-wrap + .d-path 新样式 + 768px 媒体查询)、HTML(插入 #detailPath)、openReportDetail 重置/加载两处、openQuantReportDetail 两处（量化路径 workspace-quant/results/<id>.md）
- node --check 通过；systemctl restart agent-dashboard 后 is-active = active
- ⚠️ 任务书端口信息有误：dashboard 实际监听 127.0.0.1:8055（PORT=8055, L17）；8053 是小青账账单 API（另一 node 进程）。nginx 8052 的 / 和 /task/ 均 proxy_pass 到 8055
- curl 127.0.0.1:8055/ 落盘 /tmp/task0318-dash.html（353KB）：d-path 出现 5 次、detailPath 5 次，CSS/HTML/JS 三处改动均已生效

## CDP 无头浏览器验证（chrome 147 headless, 端口 9223 专用实例，2026-08-16 21:05）
截图：/tmp/task0318-mobile.png(390x844 R-214) /task0318-mobile-long.png(390x844 R-138) /task0318-desktop.png(1440x900 R-214) /task0318-desktop-toc.png(1440x900 R-138+TOC)
数值断言结果（/tmp/task0318-results.json + /tmp/task0318-recheck.json）：
- 手机 390x844：twoRow=true（path top=95 / actions top=55）；path 独占一行；R-138 长路径 scrollable=true 可滚动 maxScrollLeft=111；overflow-x=auto、white-space=nowrap、text-overflow=clip（无省略号）✓
- 桌面 1440x900：back/title/cat/path/actions 五元素垂直中心全部 cy=28 → 严格单行；path 在 cat 与 actions 之间；title/path 各占 495px ✓
- 窄桌面 1000x900 R-138：sameRow=true、actions 全可见、path scrollable+canScroll=true ✓（桌面溢出滚动也生效）
- TOC free 档(≥1420)：panel 顶边 57 == bar 底边 57，path 可见 ✓
- TOC pinned 档(1100px, 1024-1419)：pinned=true、margin-right=-240px、padR=240px、panel 在 bar 下方不重叠、正文右缘 825 < 面板左缘 ✓ 无错位
- 回归：关闭→重开 R-214 path 正常回填；loading 态 path 为空（:empty 不占行）
- 量化报告：openQuantReportDetail 显示 workspace-quant/results/R-188-….md，scrollable=true，overlay 正常
- 备注：初次断言 desktop oneRow=false 是按 top 边缘比高（path 高 20px vs 按钮 32px）的测量误差；按垂直中心复测 allCentered=true
- 本运行时不支持图片输入，无法目视截图；布局全部以数值断言覆盖（行位置/中心对齐/滚动几何/面板几何）

## 最终状态
- node --check ✓；agent-dashboard active ✓；curl 8055 首页 d-path 出现 5 次 ✓
- 唯一改动文件：tools/agent-dashboard/server.js（备份 server.js.bak-task0318-20260816-204815）；未动扫描逻辑/API；chrome 9223 实例与临时 profile 已清理
