# task-0493 (R-315) 量化Tab UI优化 过程笔记
启动时间: 2026-08-25 12:33


## 现状诊断（2026-08-25 12:40-12:50，playwright chromium headless）

### 底部导航
- CSS（server.js:6978）：.bottom-nav{position:fixed;bottom:0;...;z-index:500;padding-bottom:env(safe-area-inset-bottom)}
- HTML（server.js:7287）：nav 是 body 直接子元素（在 .app 关闭后），无 transform/filter 祖先
- headless 实测（chromium）：390/1440 两种视口，滚动前后 nav y 不变（782 / 838）——标准浏览器正常
- **用户在微信内置浏览器看到跟随滚动** → X5/WKWebView 对 fixed + backdrop-filter 的已知兼容性问题。
  .bottom-nav 有 backdrop-filter:saturate(180%) blur(20px)（6978 行）
- 修复方案：给 nav 加 -webkit-transform:translateZ(0) 强制独立合成层 + will-change，微信 UA 下降级 backdrop-filter 为纯色背景；同时确认 html 无 overscroll 问题

### 量化 Tab v5btlc（回测·生命周期子Tab）结构（区块顺序，yDoc=文档位置）
390x844 实测（总高 12172px，viewport 844）：
1. 🧭 引擎级生命周期视图（y=142 起，含引擎切换器+多卡）— 外层容器总高 11822
2. 生命周期层·引擎 A·决策时间线+实验台账+迭代轨迹（y=246，自身高度 7613px ← 最大占比）
3. 最新版回测（a13_rsraw_e1f10dz）
4. 回测趋势 · 策略 vs 基准
5. 全版本排行
- 关键行号：9675-9900 引擎级生命周期视图；12185 生命周期层挂载点；12205 版本标题；12238 loadQuantLifecycleLayer
- 用户诉求对应：#2 生命周期层(7613px)折叠；评估指标+回测趋势(#4)前置；底部导航修复

### 渲染链路
- quantTabMode 默认 'factor'；switchQuantTab('v5btlc') 切子Tab（server.js:9323）
- 生命周期层由 loadQuantLifecycleLayer() 异步填充（12238）

## 改动内容（server.js，备份 server.js.bak-task0493-20260825）

### 1. 前置区块（renderV5Btlc 重排 + 新增函数）
- 新函数 `v5EngineEvalFrontHtml()`（server.js ~9707）：引擎评估指标徽标行 + 影子回测趋势对比图
  - 指标行：遍历 engines.json 三引擎。A 用 versionOptions 现役版本回测 full 窗口；A2/gold 用 shadow.evals 最新条
  - 对比图：`r315Monthlyize()` 把 A2 日频 4491 点月度化(222 点) + gold 157 月频点，各自区间首月=1 归一，Chart.js line 同图双线，spanGaps:false，图例标各自区间
  - 内联 script 经 `executeInlineScripts(body)` 重放（renderV5Btlc 新增调用；innerHTML 的 script 默认不执行——第一轮验证发现 canvas 300x150 未实例化，补此调用后 318x260/880x260 正常）
- 区块顺序：引擎评估指标+影子对比图 → 版本选择器+指标卡 → 回测趋势 → 全版本排行 → 折叠生命周期

### 2. 生命周期折叠（r315LcPanelHtml / r315ToggleLc / r315LcOpen）
- 引擎切换器+因子模型卡+决策时间线+实验台账+迭代轨迹全部包进折叠面板（#quantV5LcPanel）
- 默认折叠：一行式头（🧭 标题 + 当前引擎徽标 + "决策时间线·实验台账·迭代轨迹"提示 + ▾箭头）
- localStorage('r315-lc-open') 记忆展开态；展开时重画迭代散点（display:none 下 Chart 尺寸为 0）
- v5EngineSwitcherHtml 去掉内部标题行（由折叠头承担）；v5SetEngine 同步更新折叠头引擎徽标、折叠态跳过散点重画
- loadV5BtlcQuant Promise.all 新增 engines→shadow-nav 链式拉取（数据驱动 cross_engine+standalone_b 全拉），sig 含 _v5ShadowNav

### 3. 底部导航固定
- CSS：.bottom-nav 加 transform:translateZ(0)（强制独立合成层，修复 X5/WKWebView fixed 跟随滚动）
- 新增 .wx-no-bf 降级类：MicroMessenger/X5/MQQBrowser UA 时 JS 加 class，backdrop-filter:none + 纯色 var(--card) 底
- headless chromium（改动前已正常）+ UA 伪装微信验证：wxClass=true, bf=none, bg=rgb(28,28,30), pos=fixed ✓；普通浏览器保留毛玻璃 ✓

## 验证结果（2026-08-25 13:0x，全部实际执行）

### 无头浏览器 playwright（r315-verify.py / r315-verify2.py）
| 检查项 | 390x844 | 1440x900 |
|---|---|---|
| 评估指标+对比图前置首屏 | eval_front_y=142 | 146 |
| 双曲线数据集 | A2(2006-01→2024-06)+gold(2013-08→2026-08) 同图 ✓ | 同左 |
| 对比图 canvas | 318x260 | 880x260 |
| 生命周期默认折叠 | display:none, 头高 69px | display:none, 头高 41px |
| 折叠 vs 展开 | 69px vs 9335px（<1/3 ✓） | 41px vs 6669px |
| nav 滚动前后 y | 782/782/782 fixed ✓ | 838/838/838 ✓ |
| 滚到底最后可见内容 | bottom 619 < navTop 782 ✓ | 668 < 838 ✓ |
| bodyScrollW | 390（无横滚）✓ | 1440 ✓ |
| JS pageerror | 无 | 无 |
- v5btlc 子页总高：12172px → 4925px（390 宽，-59%）
- 区块顺序断言（1440）：引擎评估指标(y=146) → 最新版回测(694) → 回测趋势(931) → 全版本排行(1429) → 生命周期折叠面板(文档尾 y=4759)
- A 行指标（在线 versionOptions 生效）：A ✅在役 年化22.4% 回撤-33.6% Calmar0.67 回测full；A2 👁影子 年化21.9% Calmar0.65 corr(A_A2)1.000；gold ✅在役 年化7.6% 回撤-5.9% Calmar1.29 corr(A_gold)-0.040

### API 冒烟（4 条）
- /api/quant/engines：ok，[A, A2, gold_trend_sma200]
- /api/quant/engines/A2/shadow-nav：ok，4491 点
- /api/quant/engines/gold_trend_sma200/shadow-nav：ok，157 点（注意 engine_id 是 gold_trend_sma200 不是 gold）
- /api/quant/engines/gold_trend_sma200/paper：ok，status=active_paper

### 截图（4 张，tools/agent-dashboard/）
- 最终 8 张：r315-{390x844,1440x900}-{front,scrolled,collapsed,expanded}.png（front=首屏前置区块；scrolled=滚动中 nav 固定；collapsed/expanded=滚到生命周期面板处折叠/展开对比，头高 69/41px vs 面板 9335/6669px）
- 首批 4 张 after-* 因面板在视口外未体现差异已删除重截

### 离线单测（/tmp/r315-unit.js + 补充）
- gold 月度化 157 点归一尾值 2.595（期望 2.594 ✓）；A2 月度化 222 点归一尾值 38.969（=38.97 ✓）
- node --check 语法通过；服务重启后 active
