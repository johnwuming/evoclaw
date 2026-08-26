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

## E6. HP 侧盘点（2026-08-27 SSH 实查）

- ~/quant-evolve/scripts/ 共 182 个 py/sh（ls 实数；含 __pycache__ 目录另计）
- crontab 24 条有效行（PATH 行 + 23 任务）。核心 cron：refresh_data(周日20:00)、p3_3_evolution_standalone(1,15日02:00,5轮)、paper_engine daily(一二三四五16:30)/rebalance(15:00)/validate(周日20:00)、collect-metrics hp(每分钟,push VPS:8055)、fetch_valuation(周日06:30)、risk_patrol(一二三四五16:45)、collect_crowding(周日07:00)、evolution_pipeline cycle(周六09:00)、notify_hub(每小时:10)、w6_collect_delisted(每月1日)、reboot_autostart、heartbeat_selfheal(*/5)、a12_monthly_evaluate(每月2日17:10)、a10_monthly_monitor(每月3日09:05)、cron_qfq_daily(18:00工作日)、collect_qfq_baostock+rebuild_merged(周日18:00)、snapshot_crowding(每月1日19:35)、engines_shadow_nav_gold+evaluate_gold(每月3日)、paper_engine_gold daily(工作日07:40)/verify(周日03:00)
- 进程：hp_api_server.py 常驻（Flask 0.0.0.0:8060，398行，API key 鉴权；路由 /health /run /backtest /reports /report/<f> /data/status /sync）；**VPS 侧 grep hp_api_server/8060 引用=0**（dashboard 不调；动作走 action-queue→主agent心跳 SSH；数据走文件同步）→ 待确认死服务
- 双进化系统并存：p3_3_evolution_standalone.py（939行，旧"VPS本地自包含因子进化"，采样100股2.5年） vs evolution_pipeline.py（1605行，registry 驱动统一 Runner R-207/task-0275，--cycle 七步编排）——两者都在 crontab；p3_3 产出是否仍被消费待确认
- 双模拟盘引擎：paper_engine.py（1759行，registry 版本驱动） vs paper_engine_gold.py（365行，gold 金属引擎独立 cron）——gold 为独立赛道设计并存合理但代码路径重复
- 严格孤儿脚本（无 cron、无 HP 内部引用、无 import）：107/182（清单 /tmp/hp-orphans.txt）。代表：a2*/a2b*/a2c* 候选三套、iter2_evolution* 4个、generate_timing_report* 4个迭代版、macro_timing_layer* 4个、r25x/r26x/r27x/r29x 研究一次性、t0396/task03xx 一次性、cron_paper_daily.sh/cron_paper_rebalance.sh/cron_refresh.sh（被直接 cron 行替代）、rebalance.py/risk_control.py（paper_engine 内联实现，未 import）、engines_shadow_evaluate.py/engines_shadow_nav_append.py（被 *_gold 版替代）、evolution_engine.py/evolution_review.py（被 evolution_pipeline 替代）、sync_to_vps.sh（被 VPS 侧 auto_sync_notify.py 替代）
- 注意：107 孤儿是"无调度/无程序化消费"，主 agent 可能 SSH 手动调用（研究线），方案中一律标"待确认"不直接删

## E7. HP→VPS 数据同步路径（5 条，重复核心证据）

1. push 指标：HP collect-metrics.sh(每分钟) → POST VPS:8055 /api/metrics/ingest（server.js L5959-5960 确认存在）
2. pull 指标：VPS pull-hp-metrics.sh(每2分钟) SSH 拉 HP metrics.db watermark 增量合并——与①同一数据双通道（task-0434 重构遗留并存）
3. VPS auto_sync_notify.py（*/30分钟 + 每日3点全量）SSH 检查 HP results 新文件 rsync 回传 → VPS workspace-quant 镜像（dashboard /api/quant/* 全部读该镜像）
4. VPS sync_timing_matrix.sh（task-0288）单独拉 HP timing_matrix → 双目的地
5. HP sync_to_vps.sh（孤儿）+ hp_api_server.py /sync 端点（无调用方）——历史同步机制残留

## E8. VPS 侧 dashboard→HP 动作链

- dashboard POST /api/quant/action（L4053）→ 写队列 → 前端提示"由主 agent 心跳在 HP 侧实际执行（跨机）"（L11685 注释）→ 心跳 SSH 执行。与 hp_api_server.py /run+/backtest 能力重复（第三套编排通道）
- fetchHpStats（L1697-1760）：dashboard 经 SSH top/free/df 实时采 HP 主机状态（30s 缓存）——与 metrics.db 指标通道功能重叠（实时性 vs 历史曲线，算并存理由但需明确定位）

## E9. VPS workspace-quant 镜像

- /root/.openclaw/workspace-quant/scripts/ 241 个文件（含 auto_sync_notify.py 等）；镜像由 HP 同步而来，与 HP 侧存在版本漂移风险（如 collect-metrics.sh 两份）
- dashboard 后端 31 处引用 workspace-quant 路径读数据
## 2026-08-26 R-319 F6组合回测趋势图可视化（task-0497，量化Tab回测页新增F6模块，与R-316口径逐项一致，零生产改动）
（上行为插入前的 README 首行）

## 6. 报告完成（01:58）
- 正式报告落盘：shared/results/05-量化投资/R-320-量化系统抽象合并精简方案.md（8.4KB，五部分齐）
- 核心数字：60 端点 → 删 31（52%）；死代码 ~3000 行 ≈ server.js 20%；VPS 释放 ~2.0G；HP crontab 24 行零死行不动
- 重大修正 vs 前笔记：①孤儿 div 实为「有 loader 但永不可达」的整页死 UI（~1453 行）；②死链独占端点 16 个（非 0）；③q4b-contrast/gates/dsr 属死岛 B；④action 队列无生产者无消费者（heartbeat.sh 无 quant 引用、HP 无 api/quant 引用）；⑤timing_iter3 CSV 已不存在，endtoend 是读空文件的僵尸
- README 更新日志已插顶部一行

## E10. 死 UI 集群确认（关键发现，证据链完整）

旧「模型」「回测」页（quant-page-models / quant-page-btlc，L7425-7426）无 Tab 入口（switchQuantTab L9484-9498 只路由 6 个新 Tab）。死树包含（均为 server.js 内嵌函数，行号）：
- loadModelsQuant 11377 / renderModelsQuant 11764 / renderDecisionTimeline / renderPendingConfirm / renderIdeasPool（11510/11543/11614 按钮）
- loadBtlcQuant 11887 / renderBtlcPage 12544 / renderBtlcVersionSwitcher / renderBtlcAttributionChain / renderAttribution* / renderBtlcCompareCards / renderBtlcNavChart / renderBtlcYearly / renderBtlcCrisis / renderBtlcGenerations 12190 / renderBtlcE2E 12260 / btlcE2E* handlers / btlcOnVersionChange
- 层加载器（仅 renderBtlcPage 调用 12564-12607）：loadQuantBaselineCard 12446 / loadQuantModelLayer 12656 / loadQuantValidationLayer 12729 / loadQuantLifecycleLayer 12836
- openQuantReportDetail 14029（onclick 仅由上述死树生成）
- 动作链：quantEnqueueAction 11685（POST quant/action）+ quantRollbackConfirm/quantConfirmPending/quantRejectPending/quantSubmitIdea 11701-11714（按钮仅死树）+ renderActionQueueBadge/quantRefreshQueueBadge 11664/11669（仅 renderModelsQuant 11870/11877）
- **动作队列无消费者**：/api/quant/action 写 QUANT_ACTION_QUEUE jsonl；HEARTBEAT.md v3 心跳契约无 quant action 步骤且明文"心跳 lane 禁止 SSH HP"；heartbeat.sh 无 action-queue 逻辑 → 队列疑似无人消费（待确认：可能主会话手动处理过）

## E11. 端点消费归属最终矩阵

仅死 UI 消费（= 有效死端点候选，加上 E4 的 14 个零引用）：
- E4 零引用 14 个 + 死树独占 13 个：btlc(11898)、e2e-curves(12356)、reports(11388/11899)、reports/:id(14042/14065)、dsr(12734)、gates(12733)、q4b-contrast(12735)、timing-config(11386)、timing-matrix(11390)、decisions(11393)、pending(11394)、ideas(11395)、ledger(11396)
- 合计 27/60 端点为死（45%）【btlc 路由 L4575 是最大单体 handler 之一】
- POST /api/quant/action + action-queue：入口死 + 队列无消费者 → 双死（但 idea 类型会同步写 ideas/pool.jsonl，HP 半月度 runner 消化——池本身有独立价值）

活跃端点（33 个）：factor-catalog、factor-ic-series、paper/summary、paper/nav、paper/trades、paper/portfolio、timing、data-health、data-assets、registry、lifecycle、baseline/summary、models、active、active/pos、active/curves、version-options、history、history/:id、freshness、consistency、evolution/models、engines、engines/:id/shadow-nav、engines/shadow-nav、engines/:id/paper、run-status、crowding、risk-status、btlc?否、f6-curves
（注：btlc 归死树；f6-curves/e2e 归 v5btlc 活页）

## E12. 双 Tab 渲染体系并存（前端重复核心）

- 新 v5 系（v5model/v5btlc/v5hist，L9658/9756/10410 起）与旧系（models/btlc 页 + 层加载器，L11377-12836+）功能域高度重叠：版本切换器、归因链、净值图、年度表、危机段、生命周期、报告库——两套实现并存，旧套零入口
- 同数据多 Tab 拉取：registry 被 v5btlc+paper 双拉；active/curves 被 v5btlc+paper 双拉；timing 仅 paper 活用
