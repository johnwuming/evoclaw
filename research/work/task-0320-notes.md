# task-0320 改图标为 🪙 过程笔记

## 前期勘察（2026-08-16 21:18+）
- server.js 580,601 字节（>30KB，禁止全读，全部用 grep/sed 定点）
- 两处 HTML：登录页 head 在 L5147（title L5151），主页 head 在 L5233（title L5239），均无 rel="icon"
- HTML 由 String.raw`...` 模板字面量承载，/ 路由在 L3630；待确认未登录返回登录页
- 品牌标识：登录页 L5179 `<h1><i class="ri-rocket-2-line"></i> 任务中心</h1>` = 站点品牌 logo（火箭图标）
- 主页 topbar 图标（ri-folder-3/ri-task 等）是分区图标非品牌，不动
- L10947 `ri-rocket-line` 是火山引擎 Agent Plan 用量图标，非品牌，不动
- 无 favicon.ico/png 文件引用（public/ 待快速确认）

## 方案
- favicon：两页 head 各加 `<link rel="icon" href="data:image/svg+xml,%3Csvg ...%3E🪙%3C/svg%3E">`（%3C/%3E 编码，emoji 直嵌 UTF-8）
- 页内品牌：L5179 h1 火箭图标 → 🪙（保持 h1 字号/布局）

## 实施记录（21:22）
- 备份：server.js.bak-task0320-20260816-212129（580,601 字节）
- 4 处修改（edit 精确替换）：
  1. 登录页 head 加 favicon SVG data URI（🪙，%3C/%3E 编码）
  2. 主页 head（title 任务中心 后）加同一 favicon
  3. 登录页品牌：`<h1><i class="ri-rocket-2-line"></i> 任务中心</h1>` → `<h1>🪙 任务中心</h1>`
  4. 首页落地屏（任务屏）顶栏：`<h1><i class="ri-task-line"></i>任务</h1>` → `<h1>🪙任务</h1>`（保持 h1 布局，顶栏图标即品牌位）
- 其余分区图标、火山 ri-rocket-line（L10947）、bottom-nav 均未动

## 验证结果（21:23）
- node --check 通过；systemctl restart 后 is-active = active
- curl / : grep -c 'rel="icon"' = 1，href 含 svg+emoji ✓
- curl / : grep -o '🪙' 出现 2 处（favicon href + 顶栏 h1）✓
