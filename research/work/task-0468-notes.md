# task-0468 影子可视化泛化：数据驱动跨引擎影子卡

## 2026-08-23 13:30 初始状态核实
- server.js 位于 /root/.openclaw/workspace/tools/agent-dashboard/server.js，772609 字节（745KB+）。
- git status: server.js 有未提交改动（M）。
- git log -1: 2df99b3 (task-0439 监控口径修正)。
- engines.json (VPS) 5999 字节。

## 13:31 设计文档与 engines.json 核实
- R-259 §4.2 schema: engine_id/status/layer1{registry,nav_source,signal_desc}/layer3{tabs,api_prefix}/shadow{mode,since,nav_path,required_clean_evals}/audit。
- R-259 §5.3: 端点为 /api/quant/engines（清单+状态）与 /api/quant/engines/B/shadow-nav（B 影子 NAV）。VPS 落点 engines.json + shadow_nav.csv。
- engines.json (VPS) 现有 A（active, shadow.mode=none）+ A2（shadow, type=sub_engine_overlay, parent=A, shadow.mode=cross_engine, nav_path=results/engines/a2/shadow_nav.csv, clean_evals=0, evals[1] baseline）。
- A2 layer1.nav_source.base_segment=results/overlay_combo_a14_w050_nav.csv（task-0458 O2 锁定窗）。

