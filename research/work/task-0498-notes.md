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

## 4. 补取证 A：死链雪球与孤儿 div 可达性（2026-08-27 01:45 取证）

### 4.1 孤儿 div 结论修正（重大，推翻前笔记「无 renderer 写入」）
- quant-page-models (L7425)：有写入者 loadModelsQuant (L11377)，但该函数唯一调用点 L11696（quantEnqueueAction 的 idea 回调，写进永不可见 div）
- quant-page-btlc (L7426)：写入者 loadBtlcQuant (L11887)，唯一触发 btlcOnVersionChange (L11952) 仅在其自渲染 HTML onchange (L11928) 中出现 → 自引用闭环，无引导入口
- switchQuantTab (L9483-9500) 只派发 6 个 V5 loader，永不调 loadModelsQuant/loadBtlcQuant → **双 div + 双 loader 均为死 UI**
- 死链 A（models 岛）：L11377-11885，~509 行。含 quantEnqueueAction/quantRefreshQueueBadge/renderActionQueueBadge/renderModelsQuant/决策时间线/想法池表单
- 死链 B（btlc 岛）：L11887-12830，~944 行。含 renderBtlcPage/版本切换器/四层归因链/对比卡/净值图/年度表/危机段/walkforward/历代最优/报告库/btlcE2E/基线卡(loadQuantBaselineCard)/模型层(loadQuantModelLayer)/验证层(loadQuantValidationLayer+gates+dsr+q4b-contrast)/drawDsrCurve
- 全部 onclick/onchange 引用（L11510/11614/12308/12495/12678 等）均在死岛自渲染 HTML 内，无活 loader 引用（grep 逐函数验证 external_refs）
- loadQuantLifecycleLayer (L12836) 唯一调用者也是死岛 renderBtlcPage (L12567/12607)，但其渲染函数 renderLifecycleLayer/drawLifecycleScatter 被活 V5 回测 loadV5BtlcQuant 调用（L10218/10246）→ 该函数族存活，仅 loadQuantLifecycleLayer 薄壳死

### 4.2 死链独占端点（前端层面零活调用，比前笔记 +10 个）
死岛 A 独占：decisions (L2448)、pending (L2471)、ideas (L2525)、ledger (L2543)、timing-config (L2417)、timing-matrix (L4891)、action-queue (L4104)、POST action (L4053)
死岛 B 独占：btlc (L4575)、gates (L2915)、dsr (L2943)、q4b-contrast (L2870)、models (L2959)、reports 列表 (L2143)、baseline/meta (L2818)、e2e-curves (L4689)
- ⚠️ 修正前笔记：q4b-contrast L12735 前端调用属死岛 B 的 loadQuantValidationLayer，不是 factor 段——q4b-contrast/gates/dsr 实为死链独占
- ⚠️ POST action / action-queue：前端虽死，但 action 队列是主 agent 心跳消费的在役机制（AGENTS.md 量化链路），删除需先确认生产者迁移方案，降级为「合并/迁移」档而非纯删除
- reports/:id (L2171) 活（L14042/14065 历史Tab 在用）；reports 列表死
- evolution/models、timing、registry、lifecycle、paper/summary、baseline/summary 均有活引用（13166-13190 paper 段、9762-9777 V5btlc 段），保留

### 4.3 端点总量修正
60 端点中：7 deprecated + 8 零调用 + 14 死链独占 = **29 个可删/待迁移（48%）**；其中 12 个纯删（deprecated+零调用-1）+ 17 死链独占（含 action 对降级迁移）
（注：8 零调用里的 e2e/endtoend/engines shadow-nav flat 与死链独占有交集已去重，明细见报告）

### 4.4 版本类端点数据源矩阵（5 端点 4 数据源）
| 端点 | 数据源 | 前端状态 |
| version-options L3318 | versions-manifest.json | 活（V5模型/V5回测切换器+排行表 L9666/9764/10258）|
| registry L2431 | registry/*.json | 活（V5btlc L9777、paper L13176）|
| models L2959 | model/registry ⊕ manifest ⊕ v0_seed ⊕ archive | 死岛B独占 |
| evolution/models L3583 | model/main.json + sota.json + history.jsonl | 活（paper L13171）|
| history L3384 | manifest + decisions | 活（V5hist L10416）|

### 4.5 趋势图类矩阵（呈现层）
- v5DrawNav (L10330)：策略vs基准净值（active/curves）— V5回测主图，活
- v5F6CurveHtml (L10014)：F6 曲线模块 R-319（f6-curves）— V5回测引擎区，活
- shadow-nav (engines/:id/shadow-nav L3756)：影子净值趋势 — paper Tab，活（L9771/13184 动态拼接）
- btlcE2E* (L12260-12445)：多版本端到端对比（e2e-curves）— 死岛B
- 归并结论：删 e2e-curves 后，趋势图=3 种各司其职（在役策略/因子贡献/影子），无重复

### 4.6 死数据文件探测
- timing_iter3_*.csv（TIMING_ITER3_* L4126-4128 引用）：**已不存在**于 workspace-quant/results/ → endtoend 端点 (L4190) 是读空文件的僵尸，385 行 handler 可整删
- timing_matrix：VPS results/ 下无此目录，仅 shared/results/04-投资研究/timing_matrix/（HP 同步落盘）存在 → 死岛A删除后该数据亦无消费方
- VPS workspace-quant 体积：2.1G = venv 1.1G + data 913M + results 38M；data/ 是 HP 全量数据副本（dashboard 不读，需确认 VPS 上是否还有脚本读）

## 5. 补取证 B：HP 主机（2026-08-27 01:55 取证，SSH 只读）

### 5.1 目录布局（与 TOOLS.md 记载不同——实际主力目录是 quant-evolve）
- ~/quant-evolve：**主力**，4.1G = data 3.6G + results 551M(1428文件) + scripts 213个(50387行) + logs 22M + model 1.2M
- ~/quant：220K（仅 qlib-verify，疑废弃）
- ~/quant-backups：9.9M；~/openclaw-backup：43M；backup_paper_state_20260812：28K
- ~/.openclaw/workspace-quant：424K（metrics.db + collect-metrics.sh），仅指标采集用
- 注意：VPS 侧 /root/.openclaw/workspace-quant 是另一份 2.1G 副本（venv 1.1G + data 913M + results 38M），与 HP 的 quant-evolve 是两套

### 5.2 crontab：36 行（24 活行），零死行（所有引用脚本均存在）
分类：
- 数据链 6 行：refresh_data(周日20:00)、fetch_valuation(周日06:30)、cron_qfq_daily(工作日18:00)、collect_qfq_baostock+rebuild_merged(周日18:00)、w6_collect_delisted(每月1日)
- paper 链 5 行：paper_engine daily(工作日16:30)/rebalance(工作日15:00)/validate(周日20:00)、paper_engine_gold daily(工作日07:40)/verify(周日03:00)
- 进化链 2 行：p3_3_evolution_standalone(1/15日02:00,5轮)、evolution_pipeline cycle(周六09:00)
- 影子链 2 行：engines_shadow_nav_gold append(3日09:38)、engines_shadow_evaluate_gold(3日09:40)
- 风控 3 行：risk_patrol(工作日16:45)、collect_crowding(周日07:00)、snapshot_crowding(1日19:35)
- 基建 6 行：collect-metrics.sh(每分钟→VPS:8055)、notify_hub(每小时)、reboot_autostart(@reboot)、heartbeat_selfheal(5min)、a12_monthly_evaluate(2日17:10)、a10_monthly_monitor(3日09:05)

### 5.3 脚本分类（213 个 / 50387 行）
- 在役（cron 22 + hp_api_server + reboot/heartbeat 引用 2）：约 24 个
- paper_engine.py 1759 行、evolution_pipeline.py 1605 行为最大在役单体
- 其余 ~189 个为研究一次性/历史迭代脚本（前缀聚类：a2/a4/a9/a10/a12/q4b/r251/iter2/macro/tm/backtest*/collect* 等）
- __pycache__ 46 项
- 同步机制：sync_to_vps.sh + cron_paper_daily/rebalance.sh 内嵌 rsync → VPS shared/results/04-投资研究（239M）

### 5.4 HP 侧结论
- crontab 健康，无需清死行；脚本目录是主要瘦身对象（~189 个一次性脚本 + __pycache__）
- ~/quant(qlib-verify)、quant-backups、openclaw-backup、backup_paper_state_20260812 为归档候选
