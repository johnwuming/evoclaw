# task-0319 报告详情顶栏工具按钮按 Apple HIG 调整字号与触达区 — 过程笔记

## 背景
- 项目：/root/.openclaw/workspace/tools/agent-dashboard/server.js（单体，580323 字节）
- 服务：agent-dashboard.service（127.0.0.1:8055）
- 任务：顶栏 .detail-bar 工具按钮（.d-actions 内 4 个 .iconbtn + 返回按钮）按 Apple HIG 调字号与触达区

## 已核验的现状（grep/sed，非全文读）
- L5280 `.iconbtn{width:34px;height:34px;min-height:34px;padding:0;...}`（base 类，topbar 也在用，**不能动 base**）
- L5283 `.d-actions{display:flex;align-items:center;gap:2px;flex-shrink:0}`（全局唯一用途是报告详情 L5984）
- L5553 `.detail-bar{...padding:11px 14px...gap:10px;row-gap:6px...}`（padding 11/14 决定 54px 高：11+11+32；JS L7410 注释依赖 54px → 不改 padding）
- L5555 `.detail-bar .d-cat{...}`
- L5557 `.detail-bar .d-path{...}`（task-0318 路径行，flex:1 横滑）
- L5560 `@media(max-width:768px){.detail-bar .d-path{order:1;flex-basis:100%;width:100%}}`（手机双行）
- L5305 `.btn.small{padding:7px 12px;font-size:12px;min-height:32px}`
- L5711 `@media(max-width:768px){.btn.small{min-height:38px;padding:8px 12px}}`
- L5979-5990 HTML：返回按钮 `.btn.small.ghost` + `.d-actions` 内 4 iconbtn（fs-btn 两个内联 font-size 13px/17px；toc/截图/复制链接三个无内联样式）
- TOC pinned 两档：L5587 `.detail-overlay.toc-pinned .detail-bar{margin-right:-260px}`；L5589 `@media(min-width:1024px) and (max-width:1419px){...-240px}`

## 方案（按 Apple HIG 提炼点落地）
1. 触达区：`.detail-bar .d-actions .iconbtn{min-width:44px;min-height:44px}`（base 34px 被 min 覆盖 → 44×44 可点区；图标视觉靠 inline-flex 居中，不加 padding 不改 box）
2. 图标字号：`.detail-bar .d-actions .iconbtn i{font-size:18px;line-height:1}` 统一 18px；移除 fs-btn 两个内联 13px/17px（内联优先级高于类规则，必须移除才能统一）
3. 返回按钮：`.detail-bar .btn.small.ghost{min-height:44px}`（specificity 高于 base 与移动端 38px 覆盖 → 恒 44px）
4. 4pt 网格：detail-bar gap 10→8、row-gap 6→4；`.detail-bar .d-actions{gap:2→4}`（缩小方向，不引溢出）
5. 不改 padding（54px 高与 JS --toc-top 耦合）；不动 TOC 规则；不动 iconbtn base 类

## 风险控制
- 桌面单行：d-title/.d-path 均 flex:1 min-width:0 可收缩；d-actions flex-shrink:0，4×44+3×4=188px，1440px 视口无溢出风险
- 手机双行：d-path 独占第二行（order:1 flex-basis:100% 不变）；第一行 back+title+cat+actions，title flex:1 收缩
- 待验收：node --check、服务 active、iconbtn 渲染 ≥44、图标 ≥18px、桌面 scrollWidth≤clientWidth、截图落盘

## 验证记录（后续追加）
