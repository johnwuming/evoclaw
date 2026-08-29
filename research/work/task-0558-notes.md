# task-0558 过程笔记：模型组成说明卡从 engines.json description 投影

## 摸底
- engines.json 597B，静态数据文件，无派生脚本（grep tools/ 与 scripts/ 只命中 app.js 读取与测试）。
- BFF app.js:184-188 enginesHandler 直接 `res.json({engines: doc.engines})`，无字段白名单 → 新增 description 自动透传。
- 现有 engines：equity_sleeve/engine_id=A（active，pv_ref vC-0）；hedge_sleeve_gold/engine_id=gold_trend_sma200（active_paper，4 天）。

## 计划
1. engines.json 每个 engine 加 description（逐字保留既有字段）
2. Version.jsx 说明卡改为从 engines 投影渲染，缺省回退现有文案
3. test/ 新增投影透传测试（mock vC-1 引擎）
4. npm test（quant-bff）+ npm run build（quant-dashboard）+ 无头浏览器 390x844
