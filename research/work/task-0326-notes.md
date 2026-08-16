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
