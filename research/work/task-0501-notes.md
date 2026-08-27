# task-0501 过程笔记 —— 量化迭代全流程节点化分析（阶段A证据收集）

日期：2026-08-27。任务：只做证据收集与结构化发现；不写正式报告。
材料范围：R-206/R-320/R-321 + 当前实现（本地代码/文档）。禁止 SSH HP。

## 问题索引
- Q1：单模型一轮迭代全流程节点序列 vs 多模型中央风控节点序列，可合并点
- Q2：以「每节点=通用模块」视角盘点重复建设，给出合并抽象候选
- Q3：逐节点可视化必要性（人工决策频率、异常排查价值）+ 保留时重复模块处置建议

---

## [证据1] R-320 抽取（来源：shared/results/05-量化投资/R-320-量化系统抽象合并精简方案.md，task-0498 产出，2026-08-27）

### 双系统/双通道重复（对应 Q2 重复建设盘点）
| # | 功能 | 双方实现 | 状态 |
|---|---|---|---|
| D1 | 模型/版本展示 | 旧 loadModelsQuant(server.js L11377) vs 新 loadV5ModelQuant(L9658)；后端 /api/quant/models vs active/version-options | 旧套死 UI 零入口 |
| D2 | 回测归因/净值 | 旧 renderBtlc* L11900-12543 vs 新 v5btlc L9756；btlc API vs active/curves+f6-curves | 旧套零入口 |
| D3 | 指标采集回传 | push ingest(L5959) vs pull-hp-metrics.sh(每2分钟) | 双写同一 VPS metrics.db |
| D4 | 结果同步 HP→VPS | auto_sync_notify.py vs sync_to_vps.sh(孤儿) + hp_api_server /sync(无调用方) | 3 套机制仅 1 套在用 |
| D5 | 跨机动作编排 | quantEnqueueAction+POST quant/action（入口死）vs hp_api_server /run+/backtest（零调用） | 两套均无人消费 |
| D6 | 因子进化 | p3_3_evolution_standalone.py(939行,旧自包含,半月cron) vs evolution_pipeline.py(1605行,registry版,周六cron) | 双 cron 并行 ⭐核心 |
| D7 | paper 引擎 | paper_engine.py(A股) vs paper_engine_gold.py(黄金) | 有意隔离设计；建议抽公共层 quant_common |
| D8 | 影子净值 | engines/:id/shadow-nav + engines/shadow-nav 双路由(L3756/3800) | 前端只用动态拼接版 |
| D10 | 因子目录 | factor_catalog v1/v2/v3 三代文件并存(L1862-64优先级降级链) | 数据层三代冗余 |

### 死码规模
- 60 个后端量化端点中 29 个死（14 零引用含 7 deprecated 桩 + 15 死树独占：btlc/e2e-curves/reports×2/dsr/gates/q4b-contrast/timing-config/timing-matrix/decisions/pending/ideas/ledger/models/baseline-meta）
- 死 UI 树 server.js L11377-12836+14029（版本切换器/归因链/净值图/生命周期层/报告详情完整仍在），约 1500+ 行可删
- HP 182 脚本中 107 孤儿（无 cron/无引用/无 import）

### R-320 合并方案要点（模块收敛映射）
- 单一数据通道、单一渲染体系、死码先证据后删、HP 冻结在役件零改动
- P0 清死码 → P1 通道收敛（停 pull-hp-metrics、停 hp_api_server、孤儿移档）→ P2 抽象重构（factor_catalog v3 单源、paper/gold 公共层、p3_3 停用评估、前端 v5 组件化）
- 在役管线（HP crontab 实查）：refresh_data(周日)→evolution_pipeline cycle(周六)/p3_3(半月)→paper_engine daily/rebalance/validate→risk_patrol→collect_crowding→notify_hub(时)→w6退市月采→a10/a12月度→qfq双cron→crowding快照→gold三cron→metrics每分钟push

## [证据2] R-321 抽取（来源：shared/results/05-量化投资/R-321-前端可视化模块精简方案.md，task-0499 产出）

### 活 UI 模块清单（六 Tab 共 36 可见模块）
- 数据(2)：D1 数据健康校验卡组、D2 资产盘点表
- 因子(4)：F1 类型Tab栏、F2 因子注册表(行展开36月IC)、F3 在役IC监控、F4 相关性簇
- 模型 v5model(5)：M1 版本选择器、M2 头卡、M3 指标卡×6+窗口chips、M4 解释三层卡、M5 择时仓位趋势图
- 回测 v5btlc(8)：B1 引擎评估徽标行、B2 影子趋势对比图(A2+gold)、B3 F6组合回测图、B4 版本选择器(与M1同组件)、B5 指标卡×6(与M3同组件)、B6 策略vs基准净值图、B7 全版本排行表、B8 引擎级生命周期折叠面板（内含：引擎切换器/引擎因子模型卡/生命周期层=管线qLifecyclePipeline→影子观察→决策时间线→实验台账→迭代轨迹散点）
- 模拟实盘 paper(12)：P0 一致性徽标、P1 策略描述行、P2 指标卡×6、P3 运行状态条(mtime红绿灯)、P4 净值曲线(择时双轴)、P5 跨引擎影子卡、P6 持仓可解释表、P7 交易记录、P8 运行版本卡(registry一致性)、P9 拥挤度卡、P10 退出纪律卡、P11 参数&采纳因子
- 迭代历史 v5hist(3)：H1 分页列表、H2 legacy开关、H3 详情抽屉(选股参数→Gate评估verdict→Locked指标卡→Full指标卡→机制解释→决策记录)
- 公共横件(2)：quantConsistDot 一致性自检点、quantFreshness 数据更新条

### 信息重复矩阵（对应 Q2/Q3）
- 净值曲线重复：active 引擎回测净值在活 UI 出现 **3 处**（B6 主图/B3 F6 图/P5 影子卡 parent 线）；gold 影子净值 **3 处**（B2/B3/P5）；A2 影子净值 2 处；指数叠加 2 处
- 指标数字重复：同维度指标（年化/回撤/夏普/卡玛）活 UI 至少 **9 个渲染点**，其中 M3==B5 同组件同源、B1 徽标行 A 类回退与 M3/B5 完全同值（最高优先去重）
- 端点跨 Tab 重复拉取：registry/active-curves/engines/shadow-nav/version-options/data-health 均被多 Tab 重复请求
- 非实质重复（保留）：版本列表 3 形态（下拉交互/排行对比/分页流水）、持仓 P6 与交易 P7 各唯一

### R-321 合并方案（不动模块总数，靠折叠+瘦身+去重）
- 合并① B1 徽标行去指标数字只留状态徽章；合并② B2 影子对比图移入 B8 生命周期折叠；合并③ 会话级数据缓存 TTL30s
- 删：死岛 A1-A9+B'1-B'12 前端 + factor 死簇(~190行) + 修 onFactorGroupToggle 折叠 bug
- 死岛独有信息评估结论：无高优先级复活项；「回测深度分析」（年度收益/危机段/WF三窗OOS/历代最优，btlcBuild* 动态计算有真数据）为 P2 可选复活项——建议并入 v5hist 详情抽屉折叠区而非复活整页
- DSR 折扣曲线是硬编码假数据(L12806-12816)；五门禁面板读 8月16日 v0_seed 中性态为死数据——gate 核心信息已在 H3「Gate 评估」区呈现

### 效果图关键架构洞察（节点化视角）
生命周期层已形成流程叙事：「管线 → 影子观察中 → 决策时间线 → 实验台账 → 迭代轨迹散点」= 把进化迭代流程映射成了 UI 序列。v5hist 详情抽屉 = 单轮迭代的完整报告（参数/Gate/Locked/Full/机制/决策）。这两者是「节点化」现状最好的前端载体。

## [证据3] 当前实现抽取（本地副本，禁止 SSH HP）

### 来源
- /root/.openclaw/workspace/tmp/w5/evolution_pipeline.py（1605行副本；docstring 自证=R-207 W5/task-0275 统一Runner）
- /root/.openclaw/workspace/tmp/w5/paper_engine.py（46KB副本，v3 含择时层）
- work/task-0464/engines.json（多引擎状态机本地快照，schema_version 1）
- shared/results/05-量化投资/R-223-量化迭代流程与规则总纲.md §二/§3.1（2026-08-17 现读，权威）
- shared/results/05-量化投资/R-203-量化系统流程梳理与自动化改造设计.md §1/§4.1（2026-08-15 设计稿）

### evolution_pipeline 全貌
- 五操作：backtest / evaluate / activate / rollback / override(+status/bootstrap/fork)；--cycle 七步编排
- GATE_CONFIG(L57-65现读)：icir_is_min=0.5、oos_p_min=0.05(split 2021-01)、max_corr_max=0.7、dsr_min=0.95(N=n_trials_cum)+g5 logic非空+g6 MDD恶化≤2pp一票否决 ⇒ 实为 g1-g6
- STATUS_ENUM：candidate→pending→active→sota→retired
- cycle 实际骨架（cmd_cycle L995-1107）：step0 数据校验fail-fast(data_validator.run_all) → step0b/1 数据快照+active漂移标注(stale_snapshot) → step2 想法消化(仅统计pool.jsonl open项，「LLM假设卡消化待对接W8」) → step3 因子迭代【占位符:待W1因子注册表对接】 → step45 候选检查【骨架版不自动回测，提示人工命令】 → step6 notify入队 → 尾注「Step7 activate 为人工确认操作(本骨架不自动激活)」

### paper_engine v3 全貌
- 六action：init/daily/rebalance/validate(委托data_validator 6项)/shadow(--candidate 参数选股对比)/timing(择时诊断)
- guard_override_and_drift() 进程内防漂移+TTL override执行；timing_layer_prod 复算 q3z×trendvol；rebalance=选股→模拟交易→trades/portfolio；rsync_to_vps() 为引擎内置的第6条HP→VPS同步通道
- paper_engine_gold.py 另立黄金赛道（有意隔离）

### engines.json 多引擎状态机（task-0464快照）
- engine A: status=active，layer1.registry.entry=a13_rsraw_e1f10dz，nav_source=paper_engine_daily(sync标 pull-hp-metrics)，timing_internal=true
- engine A2: parent=A，type=sub_engine_overlay（a14_crowdf2 w=0.5 拥挤度防御叠加臂），status=shadow，registry_ref=a14_crowdf2
- layer3.tabs=[v5model,v5btlc,v5hist,paper]+api_prefix=/api/quant —— engines.json 直接声明了「引擎→UI Tab」的映射关系
- gold 引擎不在该快照清单（按 R-320：paper_engine_gold 三cron + engines_shadow_nav_gold 在 crontab 运营）⇒ 状态机文件与真实在役引擎集合存在滞后风险

### 关键口径漂移发现（重要）
1. 任务书/AGENTS 所述「五门禁 IC/ICIR/turnover/容量/相关性」与 pipeline 现读 g1-g6（ICIR_IS/ICIR_OOS/max_corr/DSR/logic/MDD_vs_parent）**不一致**——早期口径（或另一份规划）与在役代码口径冲突，节点化梳理必须以 g1-g6 为准并显式更名
2. pipeline 代码注释仍称「Step7 activate 人工确认」，而 R-223 记载 task-0345 已实施 PASS 自动 activate（R-220#8 移除人工确认）——**代码注释与生效规则脱节**
3. R-203 §4.1 设计稿八步含「⑦人工Dashboard确认→confirm」「②LLM因子引擎补位」均未实现：现状=cycle骨架占位+W1因子注册表独立承接迭代生成；「事实上的迭代主链」已从 R-203 设计迁移到 R-223/ext runner 批次任务制
4. 台账/留痕载体碎片化：decision-log.jsonl + experiment-ledger.jsonl + history.jsonl + switch_log.jsonl + results/n_trials_ledger.csv(05目录根另有986B副本) + cycle-report-{ts}.json/md —— 至少 6 种留痕形态并存

## [分析-Q1] 两流程节点序列对照与可合并点

### 流程甲：单模型一轮迭代（evolution 主线，来源：R-223§二 现行 + pipeline 代码核对）
| 节点 | 名称 | 实现 | 自动化 |
|---|---|---|---|
| N1 | 候选设计与想法消化 | 批次任务书(ext runner源码串插桩)＋fork --set；ideas/pool 仅统计 | 半自动(LLM外置) |
| N2 | 数据校验+快照防漂移 | data_validator.run_all + compute_data_snapshot + stale标注 | 自动(fail-fast) |
| N3 | 版本化回测 | fork→backtest，full+locked双窗口，AUDIT_LOCK_END clamp，候选注册不切役 | cron周六触发骨架/批次手动驱动 |
| N4 | 等价校验 EQUIV | patch开关全关复跑parent逐位diffs={} | 批次任务内置 |
| N5 | 门禁评估 | evaluate→g1-g6→verdict(PASS/REJECT一票否决；评分制已定案未实施) | 自动 |
| N6 | 上岗激活 | PASS⇒_do_activate 自动(R-220#8/task-0345)；override TTL 兜底 | 自动(残余人工门：registry变更批准) |
| N7 | 留痕版本化 | decision-log+ledger+main.json字节快照(registry/*.snapshot) | 自动 |
| N8 | 影子观察 | paper_engine--shadow/v2遗留；engines_shadow_nav_append月度NAV；clean_evals门槛 | 半自动 |
| N9 | 同步上云 | auto_sync_notify镜像+collect-metrics push(+pull/paper rsync冗余) | 自动×多通道 |
| N10 | 呈现 | v5hist详情/v5btlc/B8生命周期/history端点 | 自动 |

### 流程乙：多模型中央风控（跨引擎运营线；来源：HP crontab[R-320/notes E6] + engines.json + P9/P10模块）
| 节点 | 名称 | 实现 |
|---|---|---|
| C1 | 多引擎状态登记 | engines.json(active/shadow/overlay子引擎)+audit链 |
| C2 | 影子净值采集 | engines_shadow_nav_append + *_gold 月度 |
| C3 | 拥挤度监控 | collect_crowding(周)+snapshot_crowding(月)→crowding端点→P9卡 |
| C4 | 风险巡逻 | risk_patrol cron 工作日16:45→risk-status→P10退出纪律卡 |
| C5 | 劣化检测 | check-degradation 滚动60日超标→建议回退(R-203 L4,需现读核实是否并入risk_patrol) |
| C6 | 择时层运维 | timing_layer_prod+timing诊断action+timing_matrix专线 |
| C7 | 干预手段 | override TTL / rollback字节还原 / 快照冻结 |
| C8 | 一致性与告警 | paper↔active一致徽标+quantConsistDot+notify_hub每小时 |

### 可合并点（甲∩乙 同构节点）
1. **N2≡各处数据关**：data_validator 被 pipeline.evaluate/backtest、paper validate、data-health API 三方共用——已是事实通用件；剩余合并项是「数据面 UI」归一(D1卡即唯一出口，R-321 无重复✓)。候选抽象：`data_gate` 模块=校验+快照+漂移标注单一入口
2. **N7≡C1 留痕/登记**：6种留痕载体(decision-log/ledger/history/switch_log/n_trials_ledger/cycle-report)+engines.audit。候选抽象：统一 `event_bus`/单一台账 schema(types=backtest|evaluate|activate|rollback|risk_action)，registry 与 engines.json 各持状态、事件流共享
3. **N8≡C2 影子链路**：后端3实现(paper--shadow/shadow_nav_append/shadow_nav_gold)+前端3视图(B2图/P5卡/lifecycle.shadow_watch/B8嵌入)。候选抽象：单一 `shadow_service`(引擎无关)：采样→NAV序列→clean_evals判定，gold/A2仅参数差异
4. **N9 同步通道收敛**：5+1条通道中有效仅auto_sync_notify+push指标2条(R-320 D3/D4+rsync_to_vps)。候选：`sync_channel`=notify镜像(结果)+metrics push(指标)，删pull/rsync/sync_to_vps/hp_api_server
5. **N5≡C5 退化判据同源**：门禁(静态单轮g1-g6)与劣化检测(滚动60日)同为「业绩退化量化」。候选：评分制落地时抽 `scoring_core(gate=入场版, patrol=运营版)` 共用指标计算与阈值语义
6. **step6_notify≡C8**：notify()入队 vs notify_hub hub。候选：所有告警唯一出口 notify_hub，pipeline只投递
