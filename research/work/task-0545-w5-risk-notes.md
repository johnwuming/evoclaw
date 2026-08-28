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
- [2026-08-29 00:52] BFF 实装完成：config.js+reconDir/driftDir；新 src/risk-gates.js（latestDatedFile 取最新日期文件/driftInBand 打标 in_band→true,over_band→false,insufficient_*→null/circuitBreakerState=账本最后一条 circuit_breaker 事件/三视角摘要/pending=影子派生+账本三类合并去重）；app.js 挂 /api/v1/risk/gates（ledgerDerived 门卫）
- fixtures：good/{drift,recon}/ 各 2 文件（08-27 最新 D4 超带连超2 + 08-26 旧文件测选取）；测试新 test/api-risk-gates.test.js（7 用例：契约/打标/三视角/pending 合并/缺目录 null 源/覆写注入/单元）；api-contract 改用 /risk/drift 作 404 例；api-degrade 加 /risk/gates→503
- [2026-08-29 00:53] npm test 28/28 全绿（基线20+降级新增1+新契约7）；live 冒烟：run_date=2026-08-28，D1 insufficient_overlap(null)/D2 insufficient_obs(null)/D3 in_band(true)/D4 in_band(true)，cb not_triggered，recon v1:11.485bp 带内 v2 已知口径差 v3 ok，pending 0
- [2026-08-29 00:55] 前端实装：api.js+fetchRiskGates；新 pages/Risk.jsx（断路器状态卡/4维漂移卡超带置顶+连超n/2+冻结位/对账三视角卡 V1·V2·V3（V2 已知口径差打标文案）/pending_risks 关联列表/降级 SOP 引用区块；usePoll 120s §4.3；零写入口）；App.jsx 风 Tab 接 RiskPage；styles.css 追加 rk-* 样式
- [2026-08-29 00:56] npm run build ✓（42 modules）；重启 8180（LEDGER_DIR=live）+ 4173 preview，/api/v1/risk/gates 直连与代理均返回真实数据
- [2026-08-29 00:58] 无头验收 ✓：playwright 390x844 → scrollWidth html/body 均=390；D1-D4 全渲染（4 维名齐全）；断路器「未触发」；V1 max_abs_diff_bp=11.485（真实数据）；三视角卡+SOP 区块齐；数据日行=「数据日 2026-08-28 · drift-2026-08-28.json」；截图 docs/baseline/dashv6-risk-390x844.png（视口）+ -full.png（整页，重截隐藏 fixed TabBar 消除长图拼接伪影；实际页面无遮挡，DOM 文本断言为准）
- 改动文件清单：quant-bff{src/config.js,src/risk-gates.js 新,src/app.js,test/api-risk-gates.test.js 新,test/api-contract.test.js,test/api-degrade.test.js,fixtures/good/{recon,drift}/* 新 4 文件,README.md}；quant-dashboard{src/api.js,src/App.jsx,src/pages/Risk.jsx 新,src/styles.css,docs/baseline/dashv6-risk-390x844*.png 新}；quant-bff/live/{recon,drift}/* 新 5 文件（HP 只读拷贝）；未触碰 8055/nginx/crontab/agent-dashboard/HP 写路径
- 验收复核：npm test 28/28 全绿（含 /risk/gates 契约 7 例 + corrupt 503 例）；build ✓；无头验收 pass=true
