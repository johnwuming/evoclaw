# task-0561 新看板未生效模块对照审计 — 笔记

开始时间：2026-08-29 14:30 ｜ 纯只读审计

## 0. 环境事实
- 前端页面：tools/quant-dashboard/src/pages/{Overview,Risk,Version,Events,Migration,Placeholder}.jsx（44KB 总量，全量可读）
- BFF：tools/quant-bff/src/app.js（19KB）
- 数据投影：tools/quant-bff/live/data/（engines.json 775B, migration.json 708B, nav_curves.csv 23KB, overview.json 130B, perf_history_index.json 9.7KB, performance.*.json 6 个版本, portfolios.json 422B, versions/ 目录, governance/ 目录）
- 报告编号：R-357 为当前最大（无 R-358/R-359）→ 本任务落 R-358？任务书指定 R-359。ls 确认最大为 R-357，为避免撞号采用任务书指定 R-359（间隔留白可接受，并在报告头注明）
  - 修正：任务书明确说"确认 R-358 为最大"，实际最大是 R-357。检查 .task-completions.jsonl 无 R-358 记录。稳妥起见先再查一次全 results 树，若无 R-358 则用 R-358（顺延），避免跳号；有则用 R-359。
- PRD = R-344（26.6KB，已读 §1-§6）；R-342 = 45KB（>30KB 只抽 §4.3/§1.2）

## 1. PRD 承诺清单（R-344 提取）

### 全局元素（§2.2）
- G1 健康条：数据新鲜度（同步滞后秒数）+ 投影校验状态；超阈值变黄「数据非最新」横幅；净值停摆≥2交易日→红色「自动决策已冻结」
- G2 风险角标：待处理风险→风控 Tab+健康条红点；计数=待处理事项聚合条目数

### Tab1 总览
- 区块① 驾驶舱 P0：净值曲线(30日窗,P1加90日/1年切换)、日变动%、当前回撤+四带带位、在役版本卡(版本号+状态+sleeve权重堆叠条)、三方对账徽标(P0红绿+触发时间,P1差异明细抽屉)、数据新鲜度
- 区块② 引擎卡片 P0：每sleeve一卡：状态(shadow/paper/live/archived)、最新IC+3月趋势(老化标黄)、ICIR_OOS、最近信号日、paper/shadow已进行天数；P1交互：信号明细抽屉、点状态跳版本页

### Tab2 风控
- 区块⑤ 风控闸门 P0：六组闸门=当前值+带宽+状态：回撤四带(仪表)、波动率带(8%±2pp)、两腿20日相关性(0.75/0.85/0.90三档)、漂移四维D1-D4(20bp/0.3/90%+95%/×1.5+连续超带期数)、断路器状态(触发→顶部红条+原因+时间)、退役监视(P1:RET-1..4余量)
- P1 待处理事项视图：聚合断路器/对账失败/漂移超带/退役review

### Tab3 版本
- 区块③ P0：在役版本卡高亮、状态机胶囊流(approved→paper→live,当前段高亮,canary不入主图)、版本列表(状态过滤)
- P1 版本详情抽屉：sleeve清单(component_ref+code_hash+data_cut)、风险控制配置、门禁成绩单(gate_report逐条pass/fail+阈值+实测值)、权重方案、求解留痕(solver_id+参数+fallback原因)、版本树(parent_version链)
- P2 两版本diff

### Tab4 事件
- 区块④ P0：倒序时间线、17种事件类型着色(晋升蓝/风控红/求解绿/对账失败高亮)、每条=时间+类型+对象+执行者(pipeline/user/risk_layer)+摘要；P0交互=类型/执行者/对象过滤+分页50条
- P1：点降级事件展开触发规则+实测值vs阈值、对账失败差异明细、晋升批准显示批准人时间

### Tab5 迁移
- 区块⑥ P0：四阶段卡片(A审计/B影子/C治理/D退役)、动作done/doing/todo+证据链接、A1/A2置顶(FAIL=红色绝对阻塞)、Phase C需用户批准红线标注
- P1：双看板并行对照验收项

### 非功能（§6）
- N1 数据新鲜度分频轮询 60/120/300/600s
- N2 事件≤5min可见；投影校验不一致显示对账失败状态条不静默用旧数据
- N3 零写入口
- N4 390px 无横向滚动
- N5 首屏≤2s

## 2. 已知项（排除重复报告，但表内保留标状态）
- K1 总览区块① NAV与回撤 → task-0560 进行中
- K2 引擎卡 IC待接入/最近信号待接入 → 已知待接投影
- K3 版本页持仓/交易/fee三视图 → task-0557 已生效
- K4 版本页四指标+NAV曲线 → task-0553/0555 已生效
- K5 说明卡版本化 → task-0558 已生效

## 3. 代码核验（进行中…）

## 3. BFF 端点核验（2026-08-29 14:35，curl 全部 200/404，响应落 /tmp/q561/）
实装端点（12 个，全部 HTTP 200）：health, overview, engines, portfolios, portfolios/vC-0(12.3KB), portfolios/vC-0/holdings(1KB), portfolios/vC-0/trades(1.3KB), events(limit=3 OK, cursor 分页), migration, risk/gates(2.4KB), perf-history, perf-history/:id
未实装（404 NOT_IMPLEMENTED_THIS_BATCH）：**/risk/drift**、**/portfolios/:id/timeline**（R-342 §3.4 契约承诺但 W3+ 未做）
BFF 端口 127.0.0.1:8180（systemd quant-bff.service, LEDGER_DIR=tools/quant-bff/live）

### 端点内容要点
- health ✓ 契约全字段（ledger_tail_ts/projection_sha256_ok/sync_lag_seconds=3358s/pending_risks{count,items}）+ 扩展（replay 统计/cold_archive）
- overview：**nav/nav_chg_1d/mdd/drawdown_pct=null、sleeves=[]、active_pv=null**（overview.json 静态文件注明 HP NAV 产物未输出）；last_event_ts/reconciliation_ok ✓ → 根因=数据源缺（HP 侧 NAV 汇总产物），task-0560 处理中
- engines：2 引擎（equity_sleeve/A, hedge_sleeve_gold/gold_trend_sma200），status/data_cut/description/paper_or_shadow_days=4 ✓；**ic_latest/icir_oos/last_signal_date=null**（已知 K2，HP 引擎指标产物待接入）
- portfolios：vC-0 一条 ✓；migration：phase=B，仅 5 items（A1✓A2✓done，B1 doing，B2/B3 todo），blocking a1/a2 pass
- risk/gates：**仅 circuit_breaker + drift(D1-D4 含 consecutive_out_of_band/freeze_trigger) + recon(v1/v2/v3) + pending_risks**；契约承诺的 **portfolio_dd_gate（回撤四带）/vol（波动带）/sleeves_ddc/correlation（两腿相关性三档）四组全部缺失**
- perf-history（扩展端点，非 R-342 契约）：W6 task-0553/0555 已生效（K4）

## 4. 前端逐页核验（grep/read 实据）

### Overview.jsx（9.2KB 全读）
- 已实装：健康卡（滞后秒数+数据截止+账本尾）、③待处理风险卡（count+对账徽标 ✅/❌）、②引擎活性摘要卡、在役版本卡+WeightBar 权重堆叠条（detail 接口取 weight_solution）、引擎卡第二屏（status/IC 待接入/信号日待接入/paper 天数）、NAV 待接入桩、lag>=72h 红横幅、60s/300s 轮询
- 缺口：①NAV 曲线+30/90/1Y 切换（K1 task-0560 进行中）；②当前回撤数值与四带带位展示（依赖 overview 数据源，同为 K1 范围）；③PRD「点对账徽标→差异抽屉 P1」未见（P1 未做）

### Risk.jsx（8.6KB）
- 已实装：断路器状态卡、4 维漂移逐项（带内/超带/观察不足+连超计数+冻结触发）、对账三视角摘要、关联待处理风险、降级 SOP 说明、超带置顶逻辑（overBandCount 徽标）
- 缺口（对照 PRD §4.2 六组闸门验收）：①回撤分级闸门四带仪表（无渲染+BFF 无数据）②波动率带 8%±2pp（同）③两腿 20 日相关性三档 0.75/0.85/0.90（同）④退役监视 RET-1..4 余量（PRD 标 P1，无渲染）⑤「点闸门→事件页定位 risk 事件」交互未见

### Version.jsx（17.7KB）
- 已实装：状态机胶囊流 approved→paper→live（canary 不渲染 ✓ 符合 PRD 差异点5）、版本列表状态过滤、详情抽屉（sleeve/code_hash/data_cut/gate_report 显「未评级」/求解器/求解类型/fallback 契约/权重解合计100%）、三视图+说明卡版本化（K3/K4/K5 已生效）
- 缺口：①版本树（parent_version 链，R-342 §4.3 区块③承诺）grep 无 → 未渲染（当前仅 vC-0 单版本，树退化；P1 范围）②风险控制配置展示（回撤四带阈值/波动目标 8%±2pp，PRD 区块③ P1 详情抽屉字段）grep 无 → 未渲染 ③两版本 diff（PRD P2 backlog，不算缺口）

### Events.jsx（3.9KB）
- 已实装：倒序时间线、EVENT_TYPES 17 种全集着色族（promotion 蓝/risk 红/weight+solver 绿/reconciliation.failed critical/retirement）、payloadSummary 摘要、前端过滤（W3 简化：全量载入后过滤）、cursor 分页、待决/待决超期计算（computePendingFlags，35 天周期）
- 缺口：①过滤维度=单一 filter（需对照验收「按类型/执行者/对象过滤」——W3 简化为全量前端过滤，actor/target 过滤维度待确认 UI）②P1：点降级事件展开触发规则+实测 vs 阈值、点对账失败展开差异明细、晋升批准显示批准人时间（未做）

### Migration.jsx（4.1KB）
- 已实装：A1/A2 审计置顶+绝对阻塞红条（blocked 判定）、Phase C 未完成项「需用户批准」标签、证据链接（evidence_ref 有则显路径）、四阶段数据渲染
- 缺口（数据侧为主）：migration.json 仅 5 行——Phase B 缺动作 1-5 行（R-346/347/348 已完成的 vC-0 快照/求解器/选择器化/影子对账/漂移监控未入表）；**B2(MVO 对照)/B3(协方差对比) 标 todo 但 R-349(task-0544) 已完成留档 → 投影滞后**；Phase C/D 动作行全缺（R-344 区块⑥要求四阶段卡片列按 R-336 §8 总览表口径）

### 全局
- HealthStrip（799B）：新鲜度+刷新按钮 ✓；**投影校验状态未展示**（health 接口有 projection_sha256_ok 字段，条上不显示；sha 失败时 BFF 503→页面报错条兜底）
- TabBar（20 行）：无风险角标红点 → PRD §2.2「待处理风险→风控 Tab+健康条红点」**Tab 侧角标未实现**（健康条侧也无红点，只有总览页内 ③ 卡片）
- 零写入口 ✓（全站无表单/提交）
- 轮询分频：overview/events 60s（PRD/R-342 定 120s for events——W3 简化注明，轻微偏差）
- Placeholder.jsx 为 W3 骨架遗留，五 Tab 均已实装页面，Placeholder 未被引用（需确认 App.jsx TABS 表）

## 5. 无头浏览器实访（14:38，390×844，Basic Auth，截图 /tmp/q561/shots/）
- 五 Tab 全部渲染正常，scrollWidth 均=390（无横向溢出 ✓ G4）
- overview：三问卡全呈现+引擎卡 2 张+权重条 58/42+NAV 待接入桩 ✓
- risk：断路器未触发+D1-D4（D1/D2 暂不判带如实）+recon V1带内/V2超带(口径差打标)/V3带内+SOP ✓；无回撤/波动/相关性/退役四组闸门 ✗
- version：状态过滤+vC-0 卡+胶囊流 ✓已批准→paper当前→live ✓
- events：17 类型过滤（含计数）+倒序+payload 摘要（recon 类显原始 JSON）+trade.fill 事件（W7 扩展类型）
- migration：A1/A2 置顶✅+Phase A/B 卡+B2/B3「未开始/暂无证据」← R-349 已完成仍 todo（投影滞后实证）；无 Phase C/D 行

## 6. 报告落盘
R-359 → shared/results/05-量化投资/R-359-新看板未生效模块对照审计.md（8.5KB，43 模块对照表）
编号说明：任务书指定 R-359（R-358 留给并行 task-0560），落盘时树内实际最大 R-357。
