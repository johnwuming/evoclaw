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

## 13:32 server.js 相关区段核实
- 端点位置：/api/quant/engines L3680（已通用，遍历 engines.json 输出 engine_id/name/status/layer1/layer3/shadow{mode,since,nav_path,required_clean_evals,evals,clean_evals}/audit，文件缺失返回 available:false）；/api/quant/engines/shadow-nav L3716（硬编码读 QUANT_REPORTS_DIR/shadow_nav.csv 单文件平铺，列 month,nav,ret,weights_json）。
- 前端：loadPaperQuant L12439-12488（api('quant/engines') + api('quant/engines/shadow-nav') 单请求，L12466 硬编码）；renderCrossEngineShadowCard L12850（已有引擎徽标行通用，但明细+双线图写死 A vs A2 单图）。
- 双线图区段 L12905 起：A 在役 NAV 月度化（navPoints by date.slice(0,7)） vs shadowPoints。
