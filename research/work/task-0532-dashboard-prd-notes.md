# task-0532 Dashboard 产品方案 PRD — 过程笔记

开始时间：2026-08-28 19:1x。边查边写，本文件为唯一证据落点。

## 输入文件确认
- R-342：30389B（略超30KB → 分段读，先抓标题结构）
- R-336：52927B（>30KB → 分段读）
- R-344 文件名未被占用（ls 确认，最大编号 R-342）
- agent-dashboard：server.js 718KB（禁全读，只 grep 路由/模块名）；PROGRESS.md 2.5KB、CLAUDE.md 1.7KB、V4-DESIGN.md 12.5KB（可读）

## R-342 第4章 Dashboard 设计要点（已读 L179-298）
- 心智转换：旧量化Tab=「产物文件浏览器」→ 新=「组合治理驾驶舱」，打开即答三问：组合什么状态/谁在管风险/迁移到哪一步
- 技术栈：推荐 Vite+React SPA + Express BFF（产品文档不展开实现，只知 BFF 只读零写面）
- 六区块：①总览驾驶舱(NAV曲线/回撤带位/在役PV/对账徽标,60s) ②引擎卡片(shadow/paper/live/archived,IC+ICIR+信号日+天数,300s) ③组合版本视图(版本树+状态机胶囊流,300s) ④事件流水(type着色+actor+payload摘要+过滤+cursor分页,120s) ⑤风控闸门(回撤4带<5/5-10/10-15/>15、vol±2pp、相关性三档0.75/0.85/0.90、漂移D1-D4、断路器,120s) ⑥迁移进度(Phase A-D done/doing/todo+证据链接,A1/A2置顶阻塞,600s+手动)
- 实时性：HTTP轮询 60/120/300/600s 分频，不用 SSE/WebSocket；全局健康条 sync_lag_seconds 超阈黄色「数据非最新」
- 390px 硬约束：≤390 无横向滚动；单列+底部Tab；表格→卡片；状态机→2行折返；触控≥44px；详情用 drawer/bottom-sheet；390×844 截图基线
- 过渡：并行新建→双看板对照≥1个调仓周期→nginx路由切换、旧看板降 /legacy 保留≥1周期→Phase D 归档
- API契约 10 个 endpoint（§3.4）：overview/engines/portfolios/portfolio详情/timeline/events/risk.gates/risk.drift/migration/health，全 JSON、cursor 分页、BFF 零写面

## R-342 第5章排期（W1-W9）
- W1 事件流水读取层 | W2 只读API(events/portfolios/health) | W3 前端骨架+区块④⑥ | W4 驾驶舱+引擎卡+版本视图(卡PhaseB动作1 vC-0快照) | W5 风控闸门+对账徽标(卡PhaseB动作4/5) | W6 双看板验收 | W7 切换准备(Phase C批准后) | W8 切换+观察 | W9 收尾归档
- 原则：事件流水API先行是地基；旧看板不下线，全程观测能力不断档

## 旧看板能力盘点（完成，server.js 718KB 仅 grep 未全读）
主导航4 Tab：任务 / 用量 / 报告 / 量化（#page= hash 路由）
1. **任务**：任务中心看板（projects/tasks/task_events/agent_status，状态 pending→running→done/failed），创建/编辑/重试/删除/审核（/internal/review）、项目文档查看（docs 子Tab）
2. **用量**：多模型配额面板（zai/volc/volc-coding/deepseek，各带手动 refresh POST）、metrics 趋势/成本/系统指标（/api/metrics/*）、HP状态（/api/hp-stats）、调度状态（/api/dispatch-status）、agent监控（agent-monitor 详情+告警+会话replay+abort）
3. **报告**：shared/results 扫描列表+详情渲染（marked）、筛选
4. **量化**（6子Tab）：数据（timing-config/data-health/data-assets/registry/freshness/consistency/crowding）、因子（factor-catalog/ic-series/models/evolution）、模型、回测（btlc/e2e-curves/f6-curves/timing-matrix/q4b-contrast）、模拟实盘·灰度（paper-summary/nav/trades/portfolio/engines/shadow-nav/run-status）、迭代历史（history/decisions/pending/ideas/ledger/lifecycle/gates/dsr/active/version-options/baseline）
5. 全局：告警（alerts 表，active/history + acknowledge POST）、30s 自动刷新、登录鉴权（多用户 auth 有规划文档 docs/multi-user-auth-plan.md）
6. **旧看板里的写操作**（新看板必须零写面）：任务 CRUD+retry+review、配额 refresh、agent abort、alerts acknowledge、**/api/quant/action（量化动作队列）**
7. 量化 deprecated 端点：quant/summary|nav|factors|evolution、microcap/*
→ 对照表直接用这份清单（4主Tab+6子页+全局告警/鉴权）

## R-336 关键治理语义（已读 §4/§5/§6/§7/§7.5/§8）
- **状态机**：candidate→backtested→gated→shadow→approved→paper→canary→live；反向 live→shadow（4维漂移连续2期超带）/live→gated（对账失败/断路器/审计不合格）→archived/retired；canary 预留未启用；G-L4 用户批准=唯一人工门
- **门禁阈值**：G-S1-S6（候选→影子：OOS Sharpe≥1.0等）；G-P1-P4（影子→paper：影子期≥1调仓周期/对齐率≥95%/TE带/漂移初查）；G-L1-L3+G-L4（paper→canary→live：漂移连续2周期在带/执行率≥90%/滑点≤11.5bp×1.5/用户批准）
- **组合级风险闸门（§4.4）**：回撤4带 <5%正常/5-10%提级审查/10-15%降仓×0.5/>15%熔断；target_vol 8%±2pp带；单腿ddc -20%×0.5回补-5%；运行时相关性>0.85且升→防御降仓、>0.90→提级审查；裁决三段式=熔断硬上限>组合级>单腿级
- **断路器（§6.1）**：单日亏≥2%NAV停新仓/回撤>15%熔断+用户通知/连续2次调仓失败或日频任务3日失败转人工/NAV停摆≥2交易日冻结自动决策；只能人工复位
- **三方对账（§6.3）**：paper账本 vs 引擎持仓 vs portfolio_version；每调仓日强制+每周例行；容忍带单腿≤1pp/现金≤0.5%NAV/标的集合完全一致；超限→reconciliation.failed+冻结新仓+用户通知。旧看板一致性徽标升级为对账呈现
- **漂移4维（§7.2）**：D1日P&L偏差≤20bp/日(每日)、D2 Sharpe偏差≤0.3(每周)、D3执行率≥90%+对齐率≥95%(调仓日)、D4滑点≤假设×1.5(调仓日)；任一维连续2期超带→晋升冻结+归因报告
- **退役 RET-1..4（§7.1）**：回撤超历史MDD×1.5(现役触发线-10.2%)/连续6月跑输/因子IC连续3月<0/危机窗相关性>0.90；退役≠删除，留档可回溯
- **迁移四阶段（§8）**：A审计地基(六项审计A1/A2绝对阻塞+gate spec+兜底定稿+GLOSSARY)→B影子双轨(vC-0快照+等波动求解器+回测选择器化+影子对账≥1调仓周期+漂移启用+协方差对比+MVO跑批不启用)→C治理切换(唯一红线：paper指针切换=改active需用户批准，分钟级停机；事件溯源写路径+对账上线+断路器/checkpoint接入)→D旧件退役(旧命名/旧脚本归档+退役规则转正式)；全部可回退
- **事件类型17种**：version.created/updated、component.registered、solver.selected、weight.solved、gate.evaluated、promotion.requested/approved/rejected/executed/downgraded、risk.action、retirement.triggered/executed、backtest.completed、reconciliation.failed、checkpoint.created；actor∈{evolution_pipeline,user,risk_layer}
- **版本承诺边界（§7.5.1）**：「预算怎么分」进版本，「分出来的数」运行时算；换求解器/改预算/增减sleeve/改相关性阈值=升版本

## 冲突点/待 R-342 修订对齐（写作中记录）
1. R-342 §4.3 区块④更新频率120s vs 区块②300s：引擎状态变化由事件驱动，建议②改为事件驱动+300s兕底（待商榷，写作时定）
2. R-342 API 契约无「告警/异常汇总」单一入口（断路器/对账失败/漂移超带分散在③区块），四场景之「风险事件响应」需要一个统一的问题清单入口——PRD 建议新增「待处理事项」视图（数据全部来自既有 endpoint，不需要新 API）→ 建议修订时对齐
3. R-342 §4.2 导航为底部Tab≤5项但六区块>5：需明确Tab归并方案（驾驶舱/引擎+风控/版本/事件/迁移=5 或六区块并入四Tab）→ 建议修订时对齐
4. 旧看板的任务中心/用量/报告三大功能与量化无关：新看板若只做量化治理，这三块在过渡期由旧看板 /legacy 承接——R-342 §4.7 只说旧看板降级保留，需明确「新旧分工边界」→ 建议修订时对齐
