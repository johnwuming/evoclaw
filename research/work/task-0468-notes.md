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
## 13:33 图表区段读完 + VPS 数据布局确认
- renderCrossEngineShadowCard 双线图 L12905-12940：A 在役 NAV 月度化（navPoints by date.slice(0,7)）vs shadowPoints，写死 label "A 在役 NAV"/"A2 影子 NAV"。调用点 L13035 renderPaperQuant 内。
- 空态：hasEngines=false → 「影子管道待同步」；无 shadowPoints → 「影子 NAV 待同步」。

## 13:34 关键发现：VPS 平铺 shadow_nav.csv 是日频数据（date,nav 列）
- /root/.openclaw/workspace-quant/results/shadow_nav.csv = 109543 字节，列头 date,nav（日频），首行 2006-01-04,1.0。
- 即当前「平铺 shadow_nav.csv」= A 的日频 NAV（或 A2 的日频 NAV 副本），非 R-259 §5.3 的月频 B 影子（month,nav,ret,weights_json）。
- 现有 /api/quant/engines/shadow-nav 解析器按 /month|nav/i 跳过列头，把 date 当 month 字段用——当前前端影子卡实际画的是一条日频曲线。
- QUANT_REPORTS_DIR='/root/.openclaw/workspace-quant/results'（server.js L2119）。
- results/engines/ 目录在 VPS 不存在（未同步）。

