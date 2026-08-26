# task-0498 / R-320 过程笔记（原始证据堆）

时间：2026-08-27 01:42 GMT+8 起。任务：量化系统与 Dashboard 抽象合并精简方案设计（零代码改动）。

## E1. Dashboard 仓库结构（VPS）

- 路径：/root/.openclaw/workspace/tools/agent-dashboard/
- server.js：825KB 单体（后端路由 + 前端 HTML/JS 全部内嵌，`res.send(\`<!DOCTYPE...) 未直接命中，HTML 以模板字符串内嵌于 server.js）
- public/：仅 vendor 静态库（chart.umd.min.js、marked.min.js、remixicon）
- scripts/：collect-metrics.sh、pull-hp-metrics.sh（VPS 每 2 分钟从 HP metrics.db 增量拉取，watermark 机制，2026-08-21 task-0434 重构）
- 备份文件：server.js.bak-* 共 40+ 个堆在仓库根目录（卫生问题）
- db：dashboard.db、metrics.db（含 hp 服务器行）、tasks.db

## E2. 后端量化 API 端点（grep server.js 全量，60 个）

deprecated 网关 quantDeprecated（task-0332 旧周期留档）：
- /api/quant/summary, /nav, /factors, /evolution（1854-1857）
- /api/quant/microcap/status, /microcap/phases（2684-2685）
- /api/quant/evolution/summary（3581）

活跃端点（行号见 /tmp/quant-endpoints.txt）：
factor-catalog 1990, factor-ic-series 2006, paper-summary 2036, paper-nav 2053, paper-trades 2077, paper-portfolio 2106, reports 2143, reports/:id 2171, timing 2214, data-health 2237, data-assets 2264, timing-config 2417, registry 2431, decisions 2448, pending 2471, ideas 2525, ledger 2543, lifecycle 2574, baseline/summary 2756, baseline/nav 2772, baseline/yearly 2794, baseline/meta 2818, q4b-contrast 2870, gates 2915, dsr 2943, models 2959, active 3230, active/pos 3240, active/curves 3277, version-options 3318, history 3384, history/:versionId 3441, freshness 3477, consistency 3535, evolution/models 3583, paper/summary 3626, paper/nav 3658, engines 3681, engines/:id/shadow-nav 3756, engines/shadow-nav 3800, engines/:id/paper 3809, paper/trades 3911, paper/portfolio 3943, run-status 3962, crowding 3987, risk-status 4032, action(POST) 4053, action-queue 4104, endtoend 4190, btlc 4575, e2e-curves 4689, f6-curves 4798, timing-matrix 4891

## E3. 前端量化 Tab 结构

- quantTabMode 默认 'factor'，五个子 Tab：数据 | 因子 | 模型 | 回测·生命周期 | 模拟实盘（task-0280 起，server.js:9377）
- localStorage quantTab 持久化

## E4. 前端调用方式与精确 FE 使用矩阵（2026-08-27 核验）

- 前端 helper：api('quant/xxx') / post('quant/action')，HTML 内嵌于 server.js（offset 283800，HTML+JS 约 480KB）
- 量化子 Tab（6 个按钮，L7408-7413）：数据|因子|模型(v5model)|回测(v5btlc)|模拟实盘·灰度(paper)|迭代历史(v5hist)
- quant-page div 共 8 个（7425-7426 两孤儿）：quant-page-models、quant-page-btlc 无任何 Tab 按钮入口，switchQuantTab(L9484-9498) 只路由 6 个新 Tab
- 孤儿页 loader：loadModelsQuant L11377（渲染 quant-page-models，仅 L11696 自身 action 刷新链调用）、loadBtlcQuant L11887（渲染 quant-page-btlc，仅 L11952 版本切换器内部调用）→ 死 UI/死代码候选（v5model/v5btlc 为替代新实现）

FE 零调用端点（精确 grep api('...')，14 个）：
1. /api/quant/summary L1854（deprecated 桩）
2. /api/quant/nav L1855（deprecated 桩）
3. /api/quant/factors L1856（deprecated 桩）
4. /api/quant/evolution L1857（deprecated 桩）
5. /api/quant/paper-summary L2036
6. /api/quant/paper-nav L2053
7. /api/quant/paper-trades L2077
8. /api/quant/paper-portfolio L2106
9. /api/quant/microcap/status L2684（deprecated 桩）
10. /api/quant/microcap/phases L2685（deprecated 桩）
11. /api/quant/baseline/nav L2772
12. /api/quant/baseline/yearly L2794
13. /api/quant/evolution/summary L3581（deprecated 桩）
14. /api/quant/endtoend L4190

FE 使用的端点（api('quant/x') grep 计数>0）：registry3/lifecycle3/engines6/version-options2/timing2/reports4/paper·summary2/models2/evolution·models2/data-health2/active·curves2/active2/timing-matrix/timing-config/run-status/risk-status/pending/paper·trades/paper·portfolio/paper·nav/ledger/ideas/history·:id/gates/freshness/factor-catalog/dsr/decisions/data-assets/crowding/consistency/btlc/active·pos/action-queue/baseline·summary2/q4b-contrast/factor-ic-series2/e2e-curves/f6-curves/action(POST·post()helper L11687)

## E5. 后端读的数据源（workspace-quant 镜像，VPS 侧）

data/code_name_map.csv、data/graycards_cache.json、data/model/main.json、data/stock_info/stock_info.csv、ideas/、model/decision-log.jsonl、model/main.json、model/registry/v1.1.json、models/main.json、results/factor_catalog{,_v2,_v3}.json、results/factor_ic_monthly_v2.csv、results/factor_ic_summary.json、results/model/、results/q4b/、scripts/.sync-state.json
