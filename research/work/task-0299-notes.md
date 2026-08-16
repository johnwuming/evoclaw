# task-0299 笔记：Agent Dashboard 报告详情 TOC 修复

## 目标
1. 修 TOC 开关按钮失效（打不开也关不了）
2. 桌面端目录侧栏从左侧改到右侧
3. 目录区顶部从顶栏下方开始（top 不与顶栏重叠）

## 过程记录

### 2026-08-16 13:33 开始
- server.js 已备份：server.js.bak-task0299-20260816

## 根因分析（13:40 完成）

### 问题1根因：侧栏收起无隐藏规则
- `.toc-panel.toc-sidebar{transform:none}` + `.toc-panel.toc-sidebar.open{transform:none}`
- 两者 transform 都是 none → 桌面侧栏模式下无论 open 与否 panel 永远显示在左侧（fixed）
- buildTOC 末尾 `if (tocSidebarMode() && !getTOCCollapsed()) toggleTOC(true)` 默认已展开
- 点「目录」关：只移除 toc-pinned（正文回移），panel 仍盖在左侧 → 「关不了」
- 再点开：panel 本来就显示，视觉无变化 → 「打不开」
- 佐证：浏览器 script 块提取后 node --check 通过（非语法错误）；toggleTOC/buildTOC 各只定义一次；DOM #tocBtn/#tocPanel/#tocOverlay 都存在（HTML 723/729/730 行）；slugify 浏览器端只有 1 个（server.js 318 行那个是服务端代码，不冲突）
- 结论：纯 CSS 缺陷，加 `.toc-sidebar` 收起 translateX 即可

### 问题2：侧栏在左侧 → 改右侧
- 5849-5850 行：`.toc-panel.toc-sidebar{left:0;right:auto...}` + `.detail-overlay.toc-pinned{padding-left:260px}`
- media 1024-1279：`padding-left:220px`
- 改为 right:0 + padding-right，border-right→border-left

### 问题3：TOC 顶部与顶栏平齐
- 顶栏 = 报告详情页 `.detail-bar`（sticky top:0，padding 11px 14px，动态高度约 44-48px）
- 方案：CSS 变量 `--toc-top`（fallback 48px）+ JS syncTocTop() 实测 detail-bar 高度写入
- 生效对象：.toc-panel（top）、.toc-overlay（top，遮罩不盖顶栏，保顶栏可点）

## 关键代码位置（server.js）
- 5836-5837：.toc-overlay / .toc-panel 基础样式（top:0 待改）
- 5849-5853：.toc-sidebar + .toc-pinned + media（左→右 待改）
- 7550-7564：TOC 常量 + tocSidebarMode
- 7566-7606：buildTOC
- 7608-7622：toggleTOC
- 7623-7634：resize handler（含小 bug：toc-pinned 不看 show，顺手修为 sidebar && _tocOpen）
- detail-bar 样式 5828 行：position:sticky;top:0;padding:11px 14px
