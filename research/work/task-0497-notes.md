task-0497 notes init 2026-08-26 12:27:07

## 环境探查 (2026-08-26 12:30)
- server.js 813KB，服务名 agent-dashboard.service (running)
- e2e-curves API: L4615 附近，E2E_CURVES_DIR=/root/.openclaw/workspace/shared/results/04-投资研究/e2e_curves
- 可复用: e2eLoadSeries(csvPath, valueKey)、e2eNormalize(首日=1)、e2eMetrics(年化/夏普/mdd)、e2eAlign(共享时间轴+前向填充)
- E2E_INDEX_META: hs300/zz500/szs/sz50/szcz 五个指数; csv 格式 index_*.csv 列 (date, close)
- R-315 影子趋势图: 后端 L3756 /api/quant/engines/:id/shadow-nav; 前端 _v5ShadowNav 缓存 + L9630 数据驱动拉取(cross_engine+standalone_b 全拉) + L9825 渲染
- 量化Tab回测页(v5backtest)在 switchQuantTab 中

## HP 数据源探查 (12:35)
- ssh noname@10.12.192.174 -p 2222 可连（别名 hp-quant 本机 DNS 不通，用 IP）
- 任务书路径 ~/workspace-quant/work/task-0494|0495/out/ **不存在**（home 下无 workspace-quant）
- HP 侧 find ~ -maxdepth 5 未找到 f6_results.json / task-0494 / task-0495 目录
- HP 主仓库 = ~/quant-evolve（无 work/ 子目录，无 f6 产物）
- 待查：VPS 侧是否已有 F6 同步镜像（R-316/R-317 报告引用的数据源）
