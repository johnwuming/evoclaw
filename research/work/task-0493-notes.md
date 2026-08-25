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
