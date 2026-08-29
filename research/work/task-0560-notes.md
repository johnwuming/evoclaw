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
