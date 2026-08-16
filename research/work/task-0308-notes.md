# task-0308 工作笔记 — Dashboard 视觉重构（方案A 极简中性）

## 侦察结果（已完成）
- server.js = 585877 bytes，已备份 server.js.bak-task0308-20260816
- **e94560 共 5 处**：
  - L4665 agentColors 'research-reviewer'（JS 图表色）
  - L5466 登录页瓦片 palette
  - L5487 登录页残留 :root --accent2
  - L5578 主 :root --accent/--accent2
  - L5591 light 块 --accent/--accent2
  - rgba 形式：L5498 .tile.sel、L6006 .ptr-orb、L11333 replay 错误消息（这个应映射为红而非蓝）
- **5487 残留 :root 属于 getLoginHTML() 登录页**（独立内嵌 HTML），不能整块删——采用合并策略：token 值换成新深色系
- 主 :root L5577（有重复 --blue:4a9eff/--blue:0a84ff 两行，清理）；light 块 L5590
- --radius:14px 在 L5581；.btn L5636 radius 12px、.btn.ghost L5640（fill 底）→ 需改透明底+蓝字
- .topbar h1 18px @L5607；.fab L5974 阴影 rgba(10,132,255,.45)
- .bottom-nav L5976 blur(24px) → 统一 blur(20px)
- prefers-reduced-motion 已存在 L6048 ✅；theme-color meta L5567-5568 已是 #000000/#f2f2f7 ✅
- 卡片：.stat-card L5621、.proj-card L5644、.task-col L5661、.agent-card L5778（带 border-left:3px green，保留语义色）
- badge 块 L5627-5634（旧色调 tint），alert 行 L5694-5696
- 散落旧色调 tint：rgba(74,158,255 / 255,90,95 / 255,200,87 / 245,158,11 / 249,115,22 / 185,28,28 / 0,212,160 / 136,136,136 / 48,209,88 / 255,214,10) 及 #f59e0b/#4a9eff/#ff5a5f → 全局映射到新色
- 数据可视化 agent 调色板其余色（#2ecc71 等）保留，仅 e94560→#ff2d55(iOS pink)、4a9eff→#0a84ff

## 改动执行（全部完成 14:21）
- [x] 备份（server.js.bak-task0308-20260816，585877B）
- [x] 主 :root / light 块重写（纯黑系/系统灰系，radius 12px，去重 --blue；glass 0.75/0.78+border 0.1/0.08）
- [x] 登录页 :root 合并（纯黑系）+ tile.sel 蓝 tint + 登录卡 16→14 / tile 14→12（tile 底改 var(--card2) 层次更清晰）
- [x] badge 语义色 15% alpha 新值（黄/蓝/绿/灰/红/amber/orange/darkred）
- [x] 卡片 hairline 0.5px var(--border) + 0 1px 3px var(--shadow)（stat/proj/task-col/agent-card，agent-card 保留左侧 3px 绿语义条）
- [x] .btn radius 10px / ghost 透明底+var(--blue) 字
- [x] topbar h1 17px / fab 阴影 .45→.35 / bottom-nav blur 24→20px
- [x] L11333 错误 tint → 红（先于全局品红映射，避免误转蓝）
- [x] 全局色调映射：品红tint→蓝×3、旧蓝→iOS蓝(tint×3+hex×3)、旧红→iOS红×4、旧黄×5、amber×4、orange×1、绿×3+×7、灰×1、黄tint2×6、#f59e0b→#ff9f0a×8、#e94560→#ff2d55×2（JS图表/头像色板）、#ff5a5f→#ff453a×0
- [x] alert light tint（critical→红 / warning→amber）
- 脚本：/tmp/task0308-apply.py（全部断言恰好匹配，字节数 585877→586106，净+229）
- 注：python len() 是字符数（548697 字符=585877 字节，多字节中文），非数据丢失

## 验证结果（全部通过）
1. node --check ✅；systemctl restart + is-active=active ✅（端口 8055）
2. curl 首页：e94560=0 ✅；:root 含 --bg:#000000 --card:#1C1C1E --accent:#0A84FF ✅；light 含 --bg:#F2F2F7 --card:#FFFFFF ✅；prefers-reduced-motion ✅；theme-color #000000/#f2f2f7 ✅
3. CDP 计算样式（真 Chrome）：dark body=rgb(0,0,0)+字#F2F2F7(18.9:1)；light body=#F2F2F7+字#1C1C1E(15.3:1)；h1 17px/700；badge rgba(10,132,255,.15)+蓝字；.btn 10px；nav blur(20px) ✅
4. 像素直方图：dark 主色 #2C2C2E/#1C1C1E/#000，light 主色 #FFFFFF/#E5E5EA/#F2F2F7；品红像素 0；旧紫精确匹配 0（仅 0.013% 蓝辉光边缘误匹配）✅
5. 截图 ×5：/tmp/task0308-{dark,light}.png（reports 页）+ task0308-{home-dark? 命名 dark-home}.png + detail-{light,dark}.png（R-213 详情），--force-color-profile=srgb，390×844@2x ✅
6. console：无 JS 报错；唯一 404=/favicon.ico（存量问题，改动前同样无 favicon，非本次引入）

## 未动项确认
JS 逻辑/API/DOM/路由/TOC/iconbtn/量化tab/flex 骨架/max-width 全部未动；无新文件无新依赖
