# task-0558 工作笔记：模型说明卡版本化绑定（前端文案 map 方案，已交付）

> ⚠️ 并行写入说明：本文件 14:14 曾被另一并行执行者覆写为「BFF engines.json description 投影」方案笔记（该方案需改 BFF，违反本任务书「不改 BFF」约束）。其原文快照存于 `task-0558-notes-alt-engines-projection.snapshot.md`。本文件为按任务书执行的前端 map 方案记录，已交付验证。

## 环境事实（已核验）
- Version.jsx 18271B；ModelCard 四行文案原为静态内联
- 报告编号：shared/results/05-量化投资/ 最大 R-356 → 本任务用 **R-357**
- 测试基线：quant-bff `npm test` = 33/33（本任务未动 BFF，回归通过）
- quant-dashboard 原无 test 脚本/测试依赖（零新依赖 → node:assert 最小脚本）
- 部署：nginx `/quantv6/` alias → `tools/quant-dashboard/dist/`（build 即上线）
- 上一版产物 hash：index-CoQGba57.js（R-356）→ 本版 **index-DtWNv2_o.js**

## 关键发现（真实数据 vs 任务书）
- 线上 /api/v1/portfolios/vC-0 实测：equity_sleeve.component_ref = `{type:'registry_ref', engine_id:'A', registry_entry:'a13_rsraw_e1f10dz', status:'active'}` —— **engine_id 是类 ID「A」，具体引擎在 registry_entry**；hedge 是 engine_ref 型（engine_id=gold_trend_sma200 直接可用）
- → 因此 resolver 必须双查找：先 engine_id 后 registry_entry，任一命中 map 即用；均未命中才降级 `<engine_id>（说明待补）`（任务书允许「按 engine_id（或 registry_entry）键控」）
- 首版只按 engine_id 查 → 线上首行显示「A（说明待补）」，无头验证抓出后修复

## 交付物
- `src/engineCopy.js`：ENGINE_COPY map（4 键）+ engineCopy() + resolveCopy() + buildModelRows(detail) 纯函数
- `src/pages/Version.jsx`：ModelCard 改为渲染 buildModelRows 输出，删除全部内联引擎文案
- `scripts/engine-copy.test.mjs` + package.json `"test"` 脚本：31 条断言（含 test_engine_x 降级、registry_ref 双查找、换引擎后旧文案不出现、DDC engine_id 未来扩展降级、空详情）
- 真实权重 58.0%/42.0%、SMA200、DDC 参数、solver 窗口 60 天均从 schema 动态渲染（截图确认）

## 验证结果（全过）
| 项 | 结果 |
|---|---|
| dashboard npm test | 31/31 断言通过 |
| quant-bff npm test（回归） | 33/33，fail=0 |
| build（VITE_API_BASE=/quantv6） | 产物含 /quantv6；index-DtWNv2_o.js |
| 线上 index 引用 | 与 dist 一致（已生效） |
| 无头 390x844 | bodyScrollW=390，verCards=1，modelRows=4，labels 四行全对 |
| 截图 | task-0558-version-390.png（视口）/ task-0558-version-390-full.png（全页，视觉确认） |

## 教训
- 文案键控必须对真实 API 抽样校验，不能只按任务书字段名实现（engine_id/registry_entry 语义分层）
- 无头验证 SPA 内嵌组件三件套：`--ignore-certificate-errors`（自签 HTTPS）+ CDP click 展开折叠面板 + `captureBeyondViewport` 全页截图；Node22 原生 WebSocket 直连 CDP 即可零依赖完成
