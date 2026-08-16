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

## 改动执行
- [x] 备份
- [ ] 主 :root / light 块重写（纯黑系/系统灰系，radius 12px，去重 --blue）
- [ ] 登录页 :root 合并 + tile.sel 蓝色 tint + 登录卡圆角 16→14 / tile 14→12
- [ ] badge 语义色 15% alpha 新值
- [ ] 卡片 hairline 描边 + 轻阴影（0 1px 3px var(--shadow)）
- [ ] .btn radius 10px / ghost 透明底蓝字
- [ ] topbar h1 17px / fab 阴影 .35 / bottom-nav blur 20px
- [ ] L11333 错误 tint → 红（先于全局品红 sed）
- [ ] 全局色调映射 sed
