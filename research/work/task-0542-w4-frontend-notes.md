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

### 数据方案定稿
- 新建 `tools/quant-bff/live/`（可逆：删目录即回退）＝正式 LEDGER_DIR：
  - events/iteration-ledger-2026-08.jsonl（真实账本拷贝）
  - data/overview.json（nav_series=[]——HP 尚无 NAV 产物，UI 显「待接入」桩；sleeve_stub 删）
  - data/engines.json（vC-0 派生：真实 sleeve status+paper 天数；IC/最近信号日=null 待接入）
  - data/portfolios.json（vC-0 权威 status=paper）
  - data/versions/vC-0.json（全 schema+status_history+weight_solution 含 solver_meta，从真实文件/账本派生）
  - data/migration.json（沿用夹具内容，迁移页不在本批范围）
- BFF 改码（任务书授权口）：app.js 新增 3 只读 GET：/engines、/portfolios、/portfolios/:id，数据文件驱动同 migration 模式，均套 ledgerDerived 门卫（账本损坏→503）。id 白名单校验防 traversal。
- 总览页消费 health+overview+engines+portfolios（在役卡/权重条走 portfolios——投影 active_pv_id=null 因真实账本无 promotion.executed，不伪造事件）。

