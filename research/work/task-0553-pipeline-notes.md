# task-0553 过程笔记 — Performance 指标持续供给管道（vC-0）

日期：2026-08-29。预算 40 分钟。R-355 未被占用（README 最新 R-354），编号可用。

## 已知事实（来自 R-354，2026-08-29 切换完成）
- HP 治理层：`~/quant-evolve/portfolio_v1/governance/`（governance.py + projections/×5 + recon/ + checkpoints/）
- 账本：`portfolio_v1/portfolio/events/iteration-ledger-2026-08.jsonl` 终态 15 事件，verify ok
- BFF 数据投影（VPS）：`tools/quant-bff/live/data/governance/{paper,runtime}.json`（BFF 端口 8180，路由 `/api/v1/portfolios`、`/api/v1/portfolios/vC-0`）
- 已知遗留：route 接线（holdings/trades/fee 呈现）原属 task-0553 范围，但本任务书明确 BFF 零改动，仅做数据供给管道；呈现接线不在本次范围（如需另行立项）
- 在役零变化：五权威文件 sha256 切换前后相同；vC-0 数字以切换前 performance.json 为基准

## 待核验清单
- [ ] HP 实查：vC-0 引用的 NAV 曲线文件、performance.json 归属、id 对齐（账本/投影/权威文件三方）
- [ ] task-0549 的 hp_export_metrics.py 现状与契约
- [ ] 幂等化改造 + 手动跑 diff=0
- [ ] BFF /portfolios 实查
- [ ] rsync sync cron 既有挂点（对齐不新开）
- [ ] 月频挂点提案两方案

## 发现记录
（边查边写）
