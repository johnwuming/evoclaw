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
