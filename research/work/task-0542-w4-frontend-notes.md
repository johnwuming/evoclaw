# task-0542 W4 新看板前端 总览页+版本页 过程笔记

开始时间: 2026-08-29 00:15
范围: quant-dashboard 总览页+版本页实装；数据源从夹具升级为真实 vC-0 数据（quant-bff 数据目录新增文件）
约束: 390px 无横滚；零写入口；只改 quant-dashboard + quant-bff 数据目录 + README 一行

## 执行日志

### 00:20 现状勘察
- R-344 PRD 26KB / R-342 架构 44KB，均按 grep/sed 抽取，未全读。
- BFF (8180) 运行中，现有端点仅 4 个：health/events/migration/overview（app.js 确认）。
- **缺口**：版本页需 `/api/v1/portfolios` + `/api/v1/portfolios/:id`；总览页引擎活性卡需 status/IC/最近信号日（R-342 契约=区块②走 `/api/v1/engines`）——均未实装（404 NOT_IMPLEMENTED_THIS_BATCH）。
- overview 现逻辑：nav_series/mdd 从 data/overview.json；active_pv + weight_solution 从账本投影；sleeves 只透传 weight+nav+mdd。
- migration 模式 = 独立文件源（data/migration.json），不随账本 503。新增数据文件驱动端点可循此模式。
- vite dev(5173)/preview(4173) 代理 /api → 127.0.0.1:8180。
- health 现返回夹具数据（qdii_trend/gold_momentum），pending_risks.count=4，ledger_tail 2026-08-27。
- 8180 与 18180 两个 node 进程并存（18180 用途待查）。
- HP SSH：`hp-quant` 主机名解析失败，改用 IP 直连（TOOLS.md: ssh -p 22 noname@10.12.192.174，密码在 secrets.env QUANT_SSH_PASSWORD）。

### 00:35 关键事实（定稿依据）
- R-344 §4.1 一屏三问原文：①健康条同步滞后秒数≤阈值绿+净值日期最近交易日；②下滑引擎卡无「状态未知/停更」；③对账徽标绿+断路器未触发+无超带红点，任一异常首屏红指示。§4.3 版本页：在役高亮、胶囊流与账本重放一致、不渲染 canary。
- 真实账本仅 2 事件：version.created + weight.solved（均 vC-0）。**无 promotion.executed** → 投影 active_pv_id=null、vC-0.status 投影=candidate；权威 status='paper' 只在 vC-0.json 文件（paper_entered_at 2026-08-25）。
- 真实权重（账本 weight.solved）：equity_sleeve 0.5803 / hedge_sleeve_gold 0.4197，solver=equal_volatility(solver_equal_vol_v1)，solve_date 2026-08-28。
- vC-0 sleeves 真实 status：equity_sleeve=active（engine A a13_rsraw_e1f10dz）、hedge_sleeve_gold=active_paper（gold_trend_sma200）。
- 8180 进程无 LEDGER_DIR（默认 fixtures/good 夹具）；18180 是 tail 测试实例（/tmp/qbff-tail-fixture）不动。无 nginx 站点，验收走 vite dev 5173。
- 截图惯例：docs/baseline/dashv6-{block}-390x844.png。
- HP 拷贝：scp -O -P 2222（sftp subsystem 不可用）；源实际路径 portfolio_v1/portfolio/{versions/vC-0.json, events/iteration-ledger-2026-08.jsonl}（任务书路径少 v1 段）。

### 01:05 前端实装与验收（35/35 PASS）
- 改动文件：
  - `src/pages/Overview.jsx`（新）：一屏三问健康卡/风险角标/引擎摘要+第二屏引擎卡/在役卡+权重条/NAV 待接入桩；顶部 R-344 §4.1 验收锚注释
  - `src/pages/Version.jsx`（新）：版本卡高亮+胶囊流（approved→paper→live，canary 不渲染）+详情展开（sleeve/code_hash/门禁/求解留痕/fallback/状态历史）+状态过滤
  - `src/components/WeightBar.jsx`（新）：堆叠条（≤390 饼降级，末段吸收浮点误差保 100%）
  - `src/App.jsx`：挂载两页，version Tab 里程碑标注提前实装
  - `src/api.js`：新增 5 个 GET fetch；`src/styles.css`：ov-*/ver-*/wbar-*/pv-chip 样式
- BFF 修复：Overview 曾误取 `portfolios.portfolios`（BFF 返回数组），已修；npm run build ✓
- 无头验收（playwright chromium 390×844，/tmp/task-0542/verify-w4.mjs）：**35/35 PASS**
  - 两页 scrollWidth=390 无横滚；一屏三问元素均在首屏 844px 内
  - 真实数据断言：data_cut=2026-08-26、滞后 46 分钟绿、pending=0、权重 58.0/42.0 合计 100%、paper 4 天、status=paper、状态历史 2 条、批准留痕 task-0540
  - 零写控件：无 text input/textarea/form；按钮仅刷新/展开/Tab（写动词黑名单断言）
- 截图：docs/baseline/dashv6-{overview,version}-390x844.png（覆盖/新增）；全页版 /tmp/task-0542/dashv6-*-full.png
- 视觉目检：布局无溢出无破损；健康条 ellipsis 截断为既有行为可接受
- 遗留（W5+）：NAV 序列/IC/最近信号日待 HP 产物接入；portfolios 详情数据文件需随账本更新重新派生（当前一次性生成）；engines equity sleeve paper 天数 null（status=active 非 paper）
- BFF app.js 新增 3 只读 GET（engines/portfolios/portfolios/:id），套 ledgerDerived；测试更新（W1-W2 守卫测试原断言 engines 404，已改为实装后预期）；npm test 20/20 过。
- 8180 进程已重启：LEDGER_DIR=live（原夹具进程 2821156 已 TERM；nohup 日志 /tmp/quant-bff-8180.log）；18180 tail 测试实例未动。
- API 验证（真实数据）：health tail=2026-08-28T15:50:22Z sync_lag≈2151s 绿 pending=0；overview nav=null（真实无 NAV 产物）；engines 2 sleeve（equity=active / gold=active_paper，gold paper 4 天）；portfolios vC-0 paper；详情全 schema+weight_solution（0.5803/0.4197）+status_history 2 条。
- 事实：equity sleeve status=active（registry_ref，非 paper），paper_or_shadow_days 仅 gold=4。
- 新建 `tools/quant-bff/live/`（可逆：删目录即回退）＝正式 LEDGER_DIR：
  - events/iteration-ledger-2026-08.jsonl（真实账本拷贝）
  - data/overview.json（nav_series=[]——HP 尚无 NAV 产物，UI 显「待接入」桩；sleeve_stub 删）
  - data/engines.json（vC-0 派生：真实 sleeve status+paper 天数；IC/最近信号日=null 待接入）
  - data/portfolios.json（vC-0 权威 status=paper）
  - data/versions/vC-0.json（全 schema+status_history+weight_solution 含 solver_meta，从真实文件/账本派生）
  - data/migration.json（沿用夹具内容，迁移页不在本批范围）
- BFF 改码（任务书授权口）：app.js 新增 3 只读 GET：/engines、/portfolios、/portfolios/:id，数据文件驱动同 migration 模式，均套 ledgerDerived 门卫（账本损坏→503）。id 白名单校验防 traversal。
- 总览页消费 health+overview+engines+portfolios（在役卡/权重条走 portfolios——投影 active_pv_id=null 因真实账本无 promotion.executed，不伪造事件）。

