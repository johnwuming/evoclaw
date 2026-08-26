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

## 数据源定位修正 (12:40) ★关键
- 任务书说 HP ~/workspace-quant/work/task-0494|0495 → 实际数据在 **VPS 本地** /root/.openclaw/workspace/work/task-0494/out/ 与 task-0495/out/（task-0494/0495 在 VPS 执行，无需 scp HP）
- task-0494/out/f6_monthly_th20_rd50.csv：月度**收益率**列 (date,wA_bar,rA_dd,rG,fill_f,cost_gold,F6)，F6=月收益，需累乘成 NAV；156 行(2013-08..2026-07)
- task-0495/out/f7_nav_curves.csv：**已是 NAV** (date,F1,F7a,F7b,A,gold)，A 终值 9.53、gold 终值 2.60、F1 5.23 —— A单独/gold单独直接可用
- R-316 口径：F6 终值 9.72（月收益累乘）；与 f7_nav_curves 的 A=9.53 同窗一致可互验

## 服务与回归基线 (12:45)
- agent-dashboard.service pid 912019，监听 127.0.0.1:8055（与任务中心同端口/同进程树）
- 回归基线：/api/quant/e2e-curves?versions=v1.4 → 200 ok; /api/quant/engines/A2/shadow-nav → 200 ok
- csv 对齐格式：date,nav（对齐 nav_v1.4.csv）；指数列 date,close

## 数据落盘完成 (12:50)
- 新目录 /root/.openclaw/workspace/shared/results/04-投资研究/f6_curves/ 共 7 个 csv（date,nav 格式，对齐 nav_v1.4.csv）
- f6_nav 156点 2013-08→2026-07 终值 9.7173（=R-316 的 9.72 ✓）
- a_dd_nav 8.2376（R-316 口径1 8.24 ✓）a_alone 9.5263（9.53 ✓）gold_alone 2.6032（2.60 ✓）f1 5.2295 f7a 5.2509 f7b 5.0451
- server.js 已备份 server.js.bak-task0497-20260826（813136B）
