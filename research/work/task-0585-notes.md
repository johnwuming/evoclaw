# task-0585 过程笔记（vC-0 权威口径供给管道）

## 0. 路径勘误（相对任务书）
- live/data 实际位于 tools/quant-bff/live/data/（nav_curves.csv 23721B，2013-08..2026-07，157 行含表头）
- BFF 源码 tools/quant-bff/src/{app.js 22340B, perf-history.js 6072B}
- performance.json 1619B：curve_source={file:nav_curves.csv,column:F1_quarterly}，metrics ann .135702/vol .094679/sharpe 1.4333/mdd -.090794
- policy.json 1275B：caliber.authoritative=rolling_equal_vol_58_42（已预留）、authoritative_available=false、current=f1_quarterly_50_50_static_quarterly
- Candidates.jsx 现警示文案实为「数据口径核验中（B0）」（cand-warn-line :119 + cand-badge-warn :291），非任务书转述的「近似口径（50/50 季度再平衡）」——按现场为准改
