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

### 决策：BFF 结构微调（任务书授权口「若结构需微调，报告说明」）
- 版本页要消费的 portfolios 端点不存在，不改码无法满足「渲染真实 vC-0 数据」验收。
- 方案：app.js 新增 3 个只读 GET 端点（engines / portfolios / portfolios/:id），全部数据文件驱动（data/ 下新 JSON，同 migration 模式），零写面，可逆；汇报时明确说明偏离。

