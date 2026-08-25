# R-315 量化 Tab UI 优化：生命周期折叠 + 评估指标/回测趋势前置 + 底部导航固定

- 任务号：task-0493（R-315）
- 日期：2026-08-25
- 改动范围：`tools/agent-dashboard/server.js`（仅前端 TEMPLATE 内 CSS/JS + 一处前端渲染链补丁；零数据层改动），先备份 `server.js.bak-task0493-20260825`
- 服务：agent-dashboard.service 127.0.0.1:8055，改动后重启 active

## 一、用户反馈三项与对策

| # | 用户反馈（12:32 原话转述） | 对策 |
|---|---|---|
| 1 | 生命周期卡片（决策时间线/实验台账/迭代轨迹）占用太大可视面积，需要折叠 | 引擎级生命周期视图整体改为折叠面板，默认折叠一行式摘要，localStorage 记忆展开态 |
| 2 | 需要一眼看到引擎评估结果指标 + 回测趋势；A2 和黄金都要体现在回测趋势里 | 新增前置区块：三引擎评估指标徽标行 + A2/gold 影子回测趋势同图对比；原有回测趋势/指标卡随之上移 |
| 3 | 底部导航跟随页面滚动 | transform:translateZ(0) 强制合成层 + 微信 X5 内核 backdrop-filter 降级纯色底 |

## 二、改动明细

### 1. 生命周期折叠（R-315 §2）
- 新增 `r315LcPanelHtml(lcOpen)`：折叠面板头 = 「🧭 引擎级生命周期视图 + 当前引擎徽标（如 `A ✅ 已激活`）+ 决策时间线 · 实验台账 · 迭代轨迹 + ▾」一行式；面板体 = 引擎切换器 + 因子/模型卡 + 生命周期层（决策时间线/实验台账/迭代轨迹散点/A2 管线/影子观察）。
- 默认折叠；`r315ToggleLc()` 切换并写 `localStorage['r315-lc-open']`；展开时重画迭代散点（display:none 下 Chart.js 尺寸为 0，必须重画）。
- `v5EngineSwitcherHtml()` 去内部标题行（由折叠头承担）；`v5SetEngine()` 切引擎后同步更新折叠头徽标，折叠态跳过散点重画。
- 位置从子页顶部移到**末尾**（全版本排行之后）。

### 2. 评估指标 + 回测趋势前置（R-315 §3）
- 新增 `v5EngineEvalFrontHtml()`，置于回测子页**最顶**：
  - **指标行**（每引擎一行徽标）：A（✅在役）取现役版本回测 full 窗口：年化 22.4% / 回撤 -33.6% / Calmar 0.67；A2（👁影子）影子基线 2006-01→2024-06：年化 21.9% / Calmar 0.65 / corr(A_A2)=1.000；gold_trend_sma200（✅在役）影子基线 2013-08→2026-08（157 月）：年化 7.6% / 回撤 -5.9% / Calmar 1.29 / corr(A_gold)=-0.040。
  - **影子回测趋势对比图**：`r315Monthlyize()` 将 A2 日频 4491 点月度化（222 点）与 gold 157 个月频点合并到同一时间轴，各自区间首月=1 归一，Chart.js 双线同图（spanGaps:false，区间外断线），图例标注各自起止区间；脚注说明 A 引擎 a13 长回测 nav 见下方「回测趋势 · 策略 vs 基准」（任务书允许不并入）。
- 数据链：`loadV5BtlcQuant` Promise.all 新增 engines→shadow-nav 链式拉取（数据驱动，cross_engine + standalone_b 全拉，不硬编码引擎 ID），缓存 `_v5ShadowNav`，纳入渲染签名。
- **关键坑**：innerHTML 插入的内联 `<script>` 不执行，对比图 canvas 停留在 300x150 未实例化；在 `renderV5Btlc` 的 `body.innerHTML` 后补 `executeInlineScripts(body)`（复用现有机制）后正常。
- 子页新顺序：引擎评估指标+影子对比图 → 版本选择器+指标卡 → 回测趋势 → 全版本排行 → 折叠生命周期。

### 3. 底部导航固定（R-315 §4）
- 现状复核：`.bottom-nav` 本就是 `position:fixed`，headless chromium 滚动前后 y 不变——bug 复现于用户手机（微信内置浏览器 X5/WKWebView 对 fixed + backdrop-filter 的已知兼容性问题）。
- 修复：① `.bottom-nav` 加 `transform:translateZ(0)` 强制独立合成层；② UA 含 MicroMessenger/X5/MQQBrowser 时 JS 加 `.wx-no-bf` 类：`backdrop-filter:none` + 纯色 `var(--card)` 底（观感接近毛玻璃，彻底避开兼容性问题）；普通浏览器保留毛玻璃。
- safe-area（iOS 刘海屏）原有 `padding-bottom:env(safe-area-inset-bottom)` 保留；页面底部 padding（`.app` 的 `calc(var(--nav-h)+24px)`）保留。

## 三、验证（全部实际执行，2026-08-25）

### 无头浏览器 playwright（390x844 与 1440x900）
| 检查项 | 390x844 | 1440x900 |
|---|---|---|
| 评估指标+对比图在首屏 | y=142（视口顶部）✓ | y=146 ✓ |
| A2+gold 双曲线同图 | 数据集 `A2（2006-01→2024-06）`+`gold_trend_sma200（2013-08→2026-08）` ✓ | 同左 |
| 生命周期默认折叠 | display:none，头高 69px | display:none，头高 41px |
| 折叠态 < 展开态 1/3 | 69px vs 9335px ✓ | 41px vs 6669px ✓ |
| 滚动时 nav y 不变（脚本断言） | 782→782→782 fixed ✓ | 838→838→838 ✓ |
| 滚到底最后可见内容不被遮挡 | bottom 619 < navTop 782 ✓ | 668 < 838 ✓ |
| 无横向滚动 bodyScrollW | 390 ✓ | 1440 ✓ |
| JS pageerror | 无 | 无 |

- v5btlc 子页总高 12172px → 4925px（390 宽，约 -59%）。
- 微信 UA 伪装验证：`wx-no-bf` 类加载成功，backdropFilter=none，背景 rgb(28,28,30)，position=fixed；普通 UA 下保留 `saturate(1.8) blur(20px)` 毛玻璃。

### API 冒烟（4 条）
- `/api/quant/engines`：ok，[A, A2, gold_trend_sma200]
- `/api/quant/engines/A2/shadow-nav`：ok，4491 点
- `/api/quant/engines/gold_trend_sma200/shadow-nav`：ok，157 点
- `/api/quant/engines/gold_trend_sma200/paper`：ok，status=active_paper
- 备注：gold 的 engine_id 是 `gold_trend_sma200`（不是 `gold`），前端按 engines.json 数据驱动取用，无硬编码。

### 离线单测
- gold 月度化 157 点归一尾值 2.595（手算期望 2.594 ✓）；A2 月度化 222 点归一尾值 38.969（=38.97 ✓）。
- `node --check` 通过；改动未触碰数据层/同步链/HP。

### 截图（4 张，tools/agent-dashboard/）
- `r315-after-390x844-collapsed.png` / `r315-after-390x844-expanded.png`（折叠/展开对比）
- `r315-after-1440x900-collapsed.png` / `r315-after-1440x900-expanded.png`

## 四、遗留与说明
- A2 与 gold 曲线纵轴为各自归一净值（首月=1），量级差异大（A2 终值 38.97 vs gold 2.60）属真实历史收益差异，如实展示；如需对数轴可在后续迭代调整。
- 微信内 fixed 兼容修复（translateZ + 降级）为标准方案，但最终效果需用户真机确认；若仍跟随滚动，下一步候选方案是改用 body 高度锁 + 内层滚动容器。
- 备份：`server.js.bak-task0493-20260825`（回滚直接 cp 覆盖 + systemctl restart）。
