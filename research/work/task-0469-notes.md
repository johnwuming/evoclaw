# task-0469 笔记：影子卡 A 在役 NAV 曲线数据源改接 active/curves full

## 2026-08-23 任务启动
- 目标：跨引擎影子卡里 A 在役 NAV 曲线不可见修复。
- 根因（主 agent 定位）：renderCrossEngineShadowCard 画 A 在役线用 navPoints（/api/quant/paper/nav，4 点 2026-08-14~21），影子 NAV 是 2006-2024 4491 点历史段，时间轴错开，aVals 全 null → A 线画不出。
- 正确数据源：GET /api/quant/active/curves → strategy.full = 2006-01-04→2026-08-14（1003 点）。
- 相关代码：renderCrossEngineShadowCard L12910；loadPaperQuant L12495；renderPaperQuant L13023。

## 核验点 1（17:13）：active/curves 结构
- curl http://127.0.0.1:8055/api/quant/active/curves 落盘 /tmp/curves.json（65141 字节）。
- 结构：{ok, available, strategy:{locked:{dates,values}, full:{dates,values}}, benchmarks, notes, active_version, strategy_metrics}
- strategy.full: dates 1003 点（2006-01-04 → 2026-08-14），values 1003 个。
- strategy.locked: dates 899 点，values 899 个。
- 字段名是 values 不是 nav。

## 核验点 2（17:15）：代码区段定位
- loadPaperQuant：L12495；取数 Promise.all 在 L12511-12530；renderPaperQuant 调用 L12538；quantSigOf L12535。
- renderPaperQuant：L13023；destructure 在 L13025-13026；renderCrossEngineShadowCard 调用 L13112（传 engines, shadowNav, navPoints）。
- renderCrossEngineShadowCard：L12910，签名 (enginesData, shadowNav, navPoints)；parent 查找 parentEng 在 forEach 内；aByMonth 由 navPoints 构建；调用处 L13112。
- api() L7293、v5QuantVersionQ L9390（active/curves 已有 L9518 用法：api('quant/active/curves'+v5QuantVersionQ())）。
- 计划：loadPaperQuant 补拉 active/curves → 传入 renderPaperQuant → 传 renderCrossEngineShadowCard；parent 为 active 引擎时用 curves full 月度化，否则 navPoints 兜底。
