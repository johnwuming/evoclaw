# task-0560 工作笔记（边查边写）

## 同步通道现状（14:26 排查）
- 既有通道：/root/.openclaw/workspace-quant/scripts/auto_sync_notify.py，cron 每30分钟（cron-auto-sync）+ 每日3:00全量，任务书所述"每日8:30"实为每30分钟，频率更高。
- MIRROR_INCLUDES 已含 `--include=baseline-paper-*`（task-0352）与 engines/**（task-0491）。
- 镜像目录 /root/.openclaw/workspace-quant/results/ 今日 10:43 已更新：baseline-paper-nav.csv(217B, 11行 date,nav，末行 2026-08-28,1.00993)、baseline-paper-portfolio.json、baseline-paper-summary.json、baseline-paper-trades.csv、paper-state.json(1161B)。
- ⇒ 运行态 NAV 同步通道已存在且工作正常；待 HP 侧确认文件名（paper-nav.csv vs baseline-paper-nav.csv），若 HP 原生名为 paper-nav.csv 且未镜像，则补 include。

## BFF 现状
- app.js 19342B：路由注册 L380-391；ledgerDerived 门卫；perf-history 为"独立文件源不随账本503"先例（navseries 采用同模式）。
- overviewHandler 已从 data/overview.json 的 nav_series 计算 nav/nav_chg_1d/mdd/drawdown_pct，但 overview.json 为 130B 空桩 → 总览页 NAV 空态根因。
- config.js：dataDir=live/data（LEDGER_DIR 下）；perf-history.js readCurve 为 CSV 读取范式。
- portfolios.json：仅 vC-0，status=paper，paper_entered_at 2026-08-25。

## HP 侧文件名核实（14:32）
- HP ~/quant-evolve/results/ 实际文件名：baseline-paper-nav.csv（header date,nav，mtime 2026-08-29，任务书所写 paper-nav.csv 不存在，系口径名差异）；baseline-paper-trades.csv（date,code,action,shares,price,cost）；baseline-paper-summary.json。
- 结论：任务书交付物1的"include 扩展"实际已由 task-0352 的 `--include=baseline-paper-*` 覆盖，无需改 auto_sync_notify.py；cron 每30分钟自动增量，今日 10:43 已同步末行 2026-08-28,1.00993（8/29 周六无新交易日，数据已最新）。

## BFF 实现（14:40）
- 新增 src/nav-series.js：readRuntimeNavCsv（表头按名取 date/nav，容忍附加列）+ summarizeNavSeries（末值/nav_chg_1d 4dp/nav_chg_1d_pct/mdd 负值/drawdown_pct 负值/data_start/data_end/points）+ navSeriesHandler。
- config.js 加 paperNavPath（env PAPER_NAV_FILE 覆盖；默认 /root/.openclaw/workspace-quant/results/baseline-paper-nav.csv）。systemd unit 零改动（默认值即生产路径）。
- app.js 注册 GET /portfolios/:id/navseries（独立文件源 .catch(next)，同 migration 形态；不套 ledgerDerived——镜像文件与账本无关，参照 perf-history 先例）。
- 语义：id 非法 400；portfolios.json 无此 id 404；非 paper 组合 → series=null+note（回测口径不冒充运行态）；文件缺失 → 200+null 空态。
- fixtures：good/data/portfolios.json（vC-0 paper）+ runtime-paper-nav.csv（11点含附加列）。
- 测试 test/nav-series.test.js 3 例：happy path（末值1.00993/首点8-14/MDD≈-2.55%/新高回撤0）、缺失降级 null、400/404/非paper。
- npm test：38 tests 全 pass（基线 33 + holdings/trades/W7 既有 2 + 新增 3）。

## 验收结果（14:55）
- 线上 HTTPS navseries：200，11 点，首点 2026-08-14/0.9996，末值 1.00993，chg +1.15%，MDD -2.55%，drawdown 0（新高）。
- 无头浏览器 390x844：bodyScrollW=390 无横滚；区块① navCard=true，「运行态 · 起始 2026-08-14」+ 角标（末值 1.00993/日变动 +1.15%/MDD -2.55%/回撤 新高）+ 30/90/1Y tabs + SVG path 渲染。截图存 work/task-0560-nav-section.png 与 task-0560-overview-390.png。
- 修复留痕：首版 load() 内 p 作用域 bug（try 块外引用）致空态，pidRef 方案修复后通过。
- 构建新 hash index-u5RmvFPM.js/index-DL_pGBEc.css，线上已引用。npm test 38/38。
- 报告已落盘：R-358-总览页NAV区块接入与同步通道.md（R-358 空闲，R-359 为并发任务 task-0561 所占）。
