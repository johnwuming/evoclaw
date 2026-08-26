task-0497 notes init 2026-08-26 12:27:07

## 环境探查 (2026-08-26 12:30)
- server.js 813KB，服务名 agent-dashboard.service (running)
- e2e-curves API: L4615 附近，E2E_CURVES_DIR=/root/.openclaw/workspace/shared/results/04-投资研究/e2e_curves
- 可复用: e2eLoadSeries(csvPath, valueKey)、e2eNormalize(首日=1)、e2eMetrics(年化/夏普/mdd)、e2eAlign(共享时间轴+前向填充)
- E2E_INDEX_META: hs300/zz500/szs/sz50/szcz 五个指数; csv 格式 index_*.csv 列 (date, close)
- R-315 影子趋势图: 后端 L3756 /api/quant/engines/:id/shadow-nav; 前端 _v5ShadowNav 缓存 + L9630 数据驱动拉取(cross_engine+standalone_b 全拉) + L9825 渲染
- 量化Tab回测页(v5backtest)在 switchQuantTab 中
