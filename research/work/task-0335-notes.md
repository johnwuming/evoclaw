# task-0335 笔记：量化表格宽度自适应 + 容器内横滑

## 前置调查（02:1x）
- server.js 639538 字节，已备份 server.js.bak-task0335-20260817-020941
- task-0326 折行元凶定位（L6125-6132）：
  - `#screen-quant .quant-table th,td{overflow-wrap:anywhere;word-break:break-word}`
  - `#screen-quant .quant-table td{white-space:normal}`
  - `#screen-quant .quant-table td span,td div{display:inline-block;max-width:100%;...break-all}`
  - 基础规则 L6055-6056 本来就是 nowrap（正确，将被恢复并加 #screen-quant 特异性防御）
- quant-table 渲染点 16 处，全部已包 `<div style="overflow-x:auto">`（L8405/8633/8987/9312/9385/9416/9481/9497/9770/9789/9824/9842/10424/10641/10853/11090），无裸表
- 描述性长文本列（需要 .cell-wrap 的候选）：
  - L8419 资产盘点表 备注
  - L9395 择时A-B-C对照表 信号描述
  - L9421 早期9信号研究档案 说明
  - L9483 择时配置信号表 说明
  - L9801 五门禁危机对照表 说明
- quantHScrollGuard(L8260)：仅当 de.scrollWidth>clientWidth 时才降级；改后页面本无横滚则不触发；其 inline overflowWrap/wordBreak 遇 td nowrap 无折行机会，table min-content 不受 max-width 压缩 → 对表格容器理论无伤，保持不动，CDP 实测确认
- CDP 方法沿用 task-0326：/tmp/task0326-cdp.mjs（Node22 WebSocket 零依赖）；登录 POST /api/login admin/Ak704223；导航 showPage('quant',this) + qseg-* 子Tab
- 无 JS 依赖容器内联样式选择器（grep style*=overflow 无结果）→ 可安全把 16 处 `<div style="overflow-x:auto">` 换成类 .quant-table-scroll

## 修改方案
1. CSS：替换 task-0326 折行块 → nowrap 恢复 + .cell-wrap 例外（min 220/max 460px）
2. 容器类 .quant-table-scroll：overflow-x:auto + -webkit-overflow-scrolling:touch + scrollbar-width:thin + overscroll-behavior-x:contain；16 处 sed 替换
3. 5 处描述列 td 加 class="cell-wrap"
4. 页面级横滚禁令（#screen-quant overflow-x:hidden 块、quantHScrollGuard）不动

## 修改完成（02:1x）
- CSS 块替换：task-0326 折行三连（td normal / anywhere / span break-all）→ nowrap 恢复 + .cell-wrap 例外（min220/max460px, break-word）+ .quant-table-scroll 容器类（touch 惯性 + overscroll-contain + thin 滚动条）
- 16 处 `<div style="overflow-x:auto">` → `<div class="quant-table-scroll">`（sed 全量替换，0 残留）
- 5 处描述列 td 加 class="cell-wrap"：L8419 资产备注 / L9395 择时信号描述 / L9421 早期9信号说明 / L9483 择时配置说明 / L9801 五门禁说明
- 页面级禁令（#screen-quant overflow-x:hidden 块、quantHScrollGuard、svg/img max-width、tl-body/desc 折行）均未动
- 验证：node --check OK；systemctl restart agent-dashboard → active
- 静态页核验（/tmp/task0335-page.html 落盘，不重复拉取）：`quant-table td{white-space:normal` 计数=0 ✅；quant-table-scroll 18 处（16 div + 1 CSS 规则 + 1 注释）✅；td.cell-wrap CSS 规则 1 处 ✅
