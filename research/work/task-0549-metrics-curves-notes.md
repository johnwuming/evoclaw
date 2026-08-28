# task-0549 过程笔记（新看板接入回测指标与曲线）

## 现状核验
- BFF live/data 现有: migration.json(708B) overview.json(130B) portfolios.json(422B) versions/vC-0.json（快照文件，含 data_cut=2026-08-26）
- portfolios.json: vC-0, status=paper, solver=solver_equal_vol_v1, data_cut=2026-08-26
- BFF src: app.js(11.8KB) config.js ctx.js ledger.js pending-risks.js replay.js risk-gates.js server.js
- test: api-contract / api-degrade / api-risk-gates / replay；PRD 26.6KB、架构 45KB（>30KB 分段读）
