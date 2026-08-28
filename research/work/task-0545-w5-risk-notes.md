# task-0545 W5 风控页 + BFF risk-gates 端点 + 影子产物同步 — 过程笔记

## 计划
1. HP 影子产物同步（recon/ + drift/ → VPS quant-bff/live/）
2. BFF /api/v1/risk/gates 只读端点 + 契约测试
3. 前端风控页实装
4. npm test + build + 390x844 无头验收 + 截图

## 进度

## 已完成核验点（边查边写）
- [2026-08-29 00:45] HP 产物确认：~/quant-evolve/portfolio_v1/recon/（recon-2026-08-28.json 3568B + .md 1386B）+ drift/（drift-2026-08-28.json 3721B + .md 1262B + drift-history.jsonl 128B）
- [2026-08-29 00:45] 已 tar-over-ssh 只读拷贝到 VPS tools/quant-bff/live/recon/ + live/drift/，md5 逐文件比对一致（ad48664e…/018fc520…/fc42e6a1…/90d16dc9…/a1ba6a27…）
- 数据结构：drift_monitor@v1 {run_date, dims[D1-D4]{dim,name,band,status,sides/rebalance_days/trades}, consecutive_out_of_band{D1:0..D4:0}, freeze_trigger{全 false}}；状态枚举 in_band/over_band/insufficient_overlap/insufficient_obs；shadow_recon@v1 {v1_nav_diff(in_band:true,max 11.485bp,tol 20), v2_weight_diff(in_band:false,已知口径差打标), v3_event_coverage(coverage_ok:true), errors:[]}
- BFF 现状：8 端点；W4 数据文件驱动模式=readJsonWithTimeout(dataDir/xxx.json)+ledgerDerived 门卫；测试=node:test+fixtures/good|corrupt；risk/gates 现为 404 NOT_IMPLEMENTED_THIS_BATCH（api-contract.test.js 尾部断言，需同步改）
- 断路器数据源决策：账本 risk.action 事件（replay.js composites.risk_actions{ts,target,type,action,dim,in_band,...}）为断路器事实源（§1.2⑦ risk.* 事件进 event_log）；fixtures/good 触发后 reset→not_triggered；live 账本无 circuit_breaker 事件→未触发，与任务书一致
- fixtures/good 账本派生 pending_risks（risk 相关过滤后）= 2 条 drift_over_band（sleeve:gold_momentum#D3、sleeve:qdii_trend#D2，均 consecutive 2）
- 部署现状：8180=node src/server.js LEDGER_DIR=live（W4 部署）；4173=vite preview（dist）；18180=/tmp/qbff-tail-fixture 测试遗留（不动）；headless 工具=pip playwright 1.58.0（chromium_headless_shell-1208 已缓存）
