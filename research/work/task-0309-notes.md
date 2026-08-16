# task-0309 工作笔记：报告列表筛选/搜索 + 详情 inline code 配色修复

## 踩点结论（15:12-15:20）

### 数据结构
- `/api/reports` 返回 192 篇，category = 最深层目录名（实际为一级目录名，带编号前缀如 `01-AI行业研究`），18 个分类
- 纯前端过滤即可，后端 API 不动

### 关键定位
- 后端 scanReports(): L576-605（不动）
- GET /api/reports: L1640（不动）
- 前端报告屏 HTML: L6228-6231（topbar + reportList）
- loadReports(): L7420-7436（改造：存全局 + 委托渲染）
- .report-list 样式: L5856 附近
- L5908 `.md code{...color:var(--yellow)...}` ← 需求2根源
- 主题变量: :root(深色) L5576-5590, [data-theme="light"] L5591-5599
  - 深色 --yellow:#FFD60A on code-bg #1C1C1E（对比好，不动）
  - 浅色 --yellow:#FFCC00 on code-bg #F2F2F7（对比 ~1.6:1，不可读）
- 布局：.app 统一 max-width:960px + padding:14px，toolbar 无需自带水平 padding
- 参考交互：M3.7 renderBtlcReportLibrary (L9730) = 单选 chip + 全部 + 搜索，toggle 模式
- api() L6340, esc() L6349 均已存在

### --yellow 引用排查（同类问题）
正文文字类只有 1 处：L5908 .md code。其余 17 处均为状态色/badge/图表填充（L5622 stat 数字、L5625 badge.proposing、L5668/5778/5786 running 边框、L5806 状态点、L5813/5814 running 任务标签、L7333/9014/10361 状态 UI、L11361 quant 回放 UI）——按任务要求全部不动。

## 方案决策

### 需求1：筛选交互
**单选 chip + 「全部」 + toggle 取消**（再点当前选中项回到全部），与 M3.7 一致。理由：
1. 站内交互语言统一（用户已熟悉 M3.7 模式）
2. 192 篇/18 类，多选组合场景罕见；搜索×分类 AND 已覆盖组合需求
3. 移动端单选状态清晰，多选易误触
- chip 显示去编号前缀名（`01-AI行业研究`→`AI行业研究`）+ 计数徽章
- 搜索匹配：title + id + category 原文 + 去前缀分类名，不区分大小写
- localStorage key `reports-filter-state` = {cat, q}
- chips 横向滚动（参考 docs-tabs 移动端做法：scrollbar-width:none + webkit 隐藏）

### 需求2：配色修正（方案 A 变体）
- 不动 :root / [data-theme="light"] 变量体系（task-0308 刚上线，--yellow 被 18 处状态色引用）
- L5908 `.md code` 保持 color:var(--yellow)（深色模式 #FFD60A 不变）
- 新增覆盖：`[data-theme="light"] .md code{color:#C7254E}`（Bootstrap 经典 inline code 深玫红，on #F2F2F7 对比度 ≈5.4:1 达 WCAG AA；与链接蓝 #0A84FF 明显区分）
- pre code 已是 --text 色不受影响

## 执行记录
- [x] 15:12 备份 server.js.bak-task0309-20260816
- [x] CSS toolbar 样式（L5856 插入 .report-list 前）
- [x] CSS 浅色 .md code 覆盖（L5925）
- [x] HTML toolbar 插入（L6248）
- [x] JS loadReports 改造 + filter 函数（L7447）
- [x] node --check 通过 / systemctl restart + active / curl 200
- [x] 注入验证：reports-toolbar/reportsChips/reportsSearchInput/rs-clear/.md code{color:#C7254E} 全部在响应中
- [x] CDP 浏览器 E2E：192 条全列 → 选「AI行业研究」32 条 → 匹配信息「32/192」→ AND 搜索 → 清空按钮 → toggle 重置回 192 → localStorage 持久化 → 刷新恢复 → 无 JS 错误
- [x] CDP 配色：浅色 inline code rgb(199,37,78)=#C7254E ✓，深色 rgb(255,214,10)=#FFD60A 不变 ✓
- [x] 移动端 375px：无横向溢出、chips 可横滚、搜索框不挤压
- [x] diff 确认仅 4 个改动区块，TOC/主题变量/API 均未碰
- [x] 完成回报已写入 .task-completions.jsonl

## E2E 实测数据（CDP 真实浏览器）
- chips = 「全部192」+ 19 个分类（去前缀名+计数）
- 分类筛选：点「AI行业研究」→ 32 条；localStorage {cat:01-AI行业研究}
- AND 搜索、清空、toggle 取消、刷新恢复全部通过
