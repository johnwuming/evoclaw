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

## 核验点 3（17:17）：数据实证
- /tmp/engines.json：2 个引擎；A（status=active, parent=None, shadow.mode=none）、A2（status=shadow, parent=A, shadow.mode=cross_engine）。
- /tmp/shadow.json：A2 shadow-nav 4491 点，month=2006-01-04→2024-06-28，nav=1→38.97，source=flat。
- /tmp/curves.json：active/curves strategy.full dates 1003（2006-01-04→2026-08-14），values 1003（1→64.31）。字段名 values（非 nav）。
- 修复方案：loadPaperQuant 补拉 active/curves；renderCrossEngineShadowCard 新增参数 activeCurves；parent 为 active 引擎时用 full 月度化（month 键=最后观测），否则 navPoints 兜底。

## 基线提交
- cd tools/agent-dashboard && git add server.js && git commit -m "baseline: pre-0469" → 3451812

## 改动实施（17:2x）
- loadPaperQuant：+activeCurves var（L12504）；Promise.all +api('quant/active/curves'+v5QuantVersionQ())（L12529）；sig 数组 +activeCurves（L12531）；renderPaperQuant 传 activeCurves（L12541）。
- renderCrossEngineShadowCard：签名 +activeCurves（L12913）；activeEngId/fullByMonth 预聚合（L12917-12926）；parentIsActive 判断（active 引擎或 parentId===activeEngId，零硬编码）→ aByMonth 用 fullByMonth，否则 navPoints 兜底（L12996-13005）。
- renderPaperQuant：destructure activeCurves（L13049）；调用传 activeCurves（L13134）。
- node --check server.js：SYNTAX OK。

## 待办
- 重启 agent-dashboard 服务。
- playwright 390x844 模拟实盘页抽查：A 在役线可见、无横滚、console 零 error。
- 完成后提交 git + 写完成回报。

## 核验点 4（17:2x）：服务重启
- systemctl restart agent-dashboard → active；curl active/curves OK（截断 200B 确认响应正常）。
- 下一步：playwright 390x844 抽查模拟实盘页。

## 核验点 5（17:3x）：服务状态确认（重试后）
- agent-dashboard active；root 页面 HTTP 200。
- node --check server.js：SYNTAX OK（上一步已验证）。
- 待跑：playwright 390x844 模拟实盘页。

## 核验点 6（17:4x）：playwright 390x844 抽查结果（通过）
- canvasCount=1（ceShadowChart_1）；Chart 实例 id=1 两条数据集：
  - "A 在役 NAV"：222/222 非 null，firstNonNull=1
  - "A2 影子 NAV"：222/222 非 null，firstNonNull=1
  - labelsCount=222（2006-01→2024-06 共 222 个唯一月份，与 4491 日频点月度化一致）
- bodyScrollW=390 / docScrollW=390 / clientW=390 → 无横向滚动。
- pixelInfo：canvas 295x200，非零像素 18916 → 像素非空，A 线已画出。
- console errors：[] 零 error。
- 结论：A 在役 NAV 蓝色线在 2006-2024 段可见、与 A2 影子橙线同图对比正确；零回归。

## git 提交
- cd tools/agent-dashboard && git add server.js && git commit -m "task-0469: shadow card A active NAV line switches to active/curves full (monthly) with navPoints fallback"
