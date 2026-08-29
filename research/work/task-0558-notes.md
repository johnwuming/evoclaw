# task-0558 过程笔记：模型组成说明卡从 engines.json description 投影

> 注：本文件在本次执行中被重写过一次（14:18:52 主执行写版本覆盖了并行执行的早期草稿；并行执行曾在 14:18:34 留有快照 task-0558-notes-alt-engines-projection.snapshot.md，内容为早期摸底+计划）。本文为最终完整版。

## 0. 并行执行事件（重要）
- task-0558 于 14:10 心跳派发，14:13 本执行（run 模式子 agent）被 spawn；另有并行执行者在 14:11–14:19 对同一任务做了实现：前端 ENGINE_COPY 静态 map 方案（engineCopy.js + Version.jsx + engine-copy.test.mjs + dist build + 截图），14:19 写完成回执并置 pending_review，报告 R-357。
- **该方案未满足任务书验收**：engines.json 无 description 字段、前端未从 engines 投影渲染、无 BFF description 测试——换引擎仍需改前端代码发版，与用户诉求（说明自动跟随）不符。
- 本执行在其完成后接手（sessions_list 确认无活动并发会话），保留其可用部分（组件结构、降级思路），重构数据链路为 engines 投影方案，并在 R-357 追加更正节。

## 1. 摸底结论
- engines.json（597B→现 651B）为 VPS 侧静态投影文件，无派生/同步脚本（grep tools/ 与 scripts/ 仅 app.js 读取、测试与 agent-dashboard 历史备份命中）→ description 直接写数据文件即可，无派生丢失风险。
- BFF app.js:184-188 enginesHandler：`res.json({engines: doc.engines})` 整组透传，无字段白名单 → 加字段即透传；readJsonWithTimeout 每请求现读无缓存 → 改文件即时生效，无需重启。
- vC-0 详情 schema：equity component_ref = {engine_id:"A", registry_entry:"a13_rsraw_e1f10dz"}（类 ID 与具体引擎 ID 两层）；gold = {engine_id:"gold_trend_sma200"}。engines.json 的 engine_id（A/gold_trend_sma200）与详情 schema 可直接对上。
- task-0557 原文案（R-356）：A股因子选股 a13·月频·58.0%；黄金ETF趋势择时 gold·SMA200·42.0%；DDC；solver_equal_vol_v1·60天。
- nginx /quantv6/ alias 直接指向 quant-dashboard/dist → build 即上线；API 反代 127.0.0.1:8180。

## 2. 改动清单
1. `tools/quant-bff/live/data/engines.json`：每 engine 新增非空 description：
   - A →「A股因子选股：全市场股票池月频调仓」
   - gold_trend_sma200 →「黄金ETF趋势择时：200日均线（SMA200）信号，月频首个交易日调仓」
   - 与现说明卡文案语义一致；python json 原位改，diff 验证仅 +2 行 description（既有字段逐字保留）。备份 /tmp/engines.json.bak-task0558-142525。
2. `tools/quant-dashboard/src/engineCopy.js`（重构，4.7KB）：
   - 新增 `buildEnginesIndex(engines)`：engines 数组 → Map(engine_id→description)，只收非空字符串，容忍脏数据/null/undefined。
   - `buildModelRows(detail, enginesIndex)` 投影优先：equity/gold 行 description 取 enginesIndex.get(engine_id)（equity 支持 registry_entry 兜底查找）；gold 无投影时回退 schema 动态 SMA；DDC/solver 仍 schema 参数优先+默认文案；投影命中但静态 map 未注册的新引擎 label 用 engine_id（不误标「待补」）。
   - ENGINE_COPY 降级为回退默认文案；两级都缺 → `<id>（说明待补）`；绝不渲染空白/undefined。
3. `tools/quant-dashboard/src/pages/Version.jsx`：ModelCard 挂 useEffect 拉取 fetchEngines（失败静默置空数组→回退默认文案），useMemo 构建 buildEnginesIndex 传入 buildModelRows；修正前次残留的重复 import。卡片 JSX 结构未动。
4. `tools/quant-dashboard/scripts/engine-copy.test.mjs`（重写）：39 断言 —— 索引容错、投影上卡、**mock vC-1 引擎（vC1_momentum_x + 新 description）换引擎说明自动跟随且旧文案消失**、回退（null/空数组/缺 description/空详情）、降级、真实 vC-0 形状。npm test 全过。
5. `tools/quant-bff/test/engines-description.test.js`（新增，仿 w7 风格）：临时 DATA_DIR mock engines（vC-0 双引擎带 description + vC-1 shadow 新引擎）断言 /api/v1/engines 透传 description、既有字段逐字保留、新引擎可见；另一 case 无 description 字段 → 200 向后兼容。
6. `shared/results/05-量化投资/R-357-模型说明卡版本化绑定.md`：追加「更正」节（数据链路升级为准，静态 map 描述留作过程记录）。

## 3. 验证记录（全部实跑）
- 前端：`npm test` → engine-copy assertions: 39 passed。
- BFF：`npm test` → 35/35（33 基线 + 2 新增），0 fail。
- 验收②：python3 读 live/data/engines.json → 2 引擎均含非空 description；diff 备份仅 +2 行。
- 验收③：grep Version.jsx 无模型文案字面量（回退默认值集中于 engineCopy.js ENGINE_COPY）。
- build：`VITE_API_BASE=/quantv6 npm run build` 成功 → dist/assets/index-DQ7wW3AC.js，线上 index.html 已引用新 hash。
- 线上 API：`curl -sk /quantv6/api/v1/engines` → A/gold_trend_sma200 description 原文透传。
- 验收④（无头 390x844，playwright + chromium-1208，ignoreHTTPSErrors，/quantv6/#/version 展开 vC-0）：
  - 说明卡渲染两条 engines description 原文（hasEqDesc/hasGoldDesc=true）；
  - 无「（说明待补）」、无 undefined/null 字样；
  - bodyScrollW=390（展开与收起态均 =viewport）；
  - console 仅 1 条 404：favicon（dist 从无 favicon，task-0557 起预存，与本改动无关）。
  - 截图：shared/results/work/task-0558-version-390.png（本次）；脚本 work/task-0558-verify.js。
- 未触碰：HP（全程未 SSH）、BFF 其他 live/data 文件、crontab、registry、paper_engine、evolution_pipeline。

## 4. 残留与前次产物说明
- 前次执行的 dist/screenshots、public/screenshots、task-0558-version-390*.png（14:16/14:17 旧版截图，已被本次 14:4x 截图覆盖 task-0558-version-390.png；-full.png 为前次全页截图未动）——非本执行清理对象。
- 前次完成回执（.task-completions.jsonl 中 task-0558 第一条）描述静态 map 方案，以本执行追加的第二条为准。
