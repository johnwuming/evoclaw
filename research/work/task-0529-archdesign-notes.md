# task-0529 架构设计过程笔记
- 编号确认: 05-量化投资/ 最大 R-340，R-341 清白 → 报告定名 R-341
- R-336 共 52927B (>30KB, 分段读)

## R-336 v1.2 关键条款摘录（grep 锚点已核）
- §1.1 七层总图: Data→Alpha→Backtest→PortfolioConstruction→Portfolio→Execution→Risk + 横切 Iteration Ledger（append-only event_log，当前状态=重放投影）
- §1.2① Data: 四口径唯一出处（PIT/qfq/退市/涨跌停掩码+成本模型 R-333 4.0/11.5/15.7bp）；输出契约 bar(symbol,date,ohlqfq_adj,tradable_mask,pit_fields)
- §1.2② Alpha: signal(sleeve_id,date,positions,ic_series,turnover_estimate)；evolution_pipeline=Research-to-Production Pipeline
- §1.2③ Backtest: backtest_report(portfolio_version_id,metrics,gate_results[],assumptions[],md5_anchor)；审计后可信是前提(§5)
- §1.2④ 构建层: 配置与求解分离铁律，禁 model_weights 进 portfolio_version；weight_solution(+solver_meta{type,params,cov_estimator,cov_estimator_rationale,convergence_status,random_seed,diagnostics,fallback_triggered,fallback_reason})；v1.2 A2 tradable_mask 两步+后验(取整/最小单位/现金残留)；等波动率→ERC，不用 MVO；MVO 对比跑批不启用仅留档(§8 Phase B 动作7)
- §1.2⑤ Portfolio: portfolio_version{portfolio_version_id,sleeves{},risk_control{drawdown_gates,vol_target,backfill_rule},per_sleeve_risk_cap?,solver_ref,parent_version,status,gate_report,paper_entered_at,paper_duration}；v1.2 A1 sleeve 附 code_hash+data_cut、capital_policy{gross_limit,net_limit}、solver tolerances+fallback；data_cut≤min(输入源最大时间戳) 硬断言，违反=config.invalid 绝对阻塞
- §1.2⑤ 状态机: candidate→backtested→gated→shadow→approved→paper→canary→live；终态 archived/retired；反向 live→shadow(4维漂移§7.2任一维连续2期超带)、live→gated(reconciliation.failed/断路器/审计不合格)；降级走 promotion.downgraded 事件禁直改 JSON
- §1.2⑥ Execution: paper→canary→live 串行三段；execution_report(date,fills,slippage_actual,nav,checkpoint_ref)；canary 启用须定义期限与失效自动降级
- §1.2⑦ Risk: 裁决三段式(§7.5.3 唯一出处)=熔断硬上限>组合级>单腿级；组合级回撤闸门 <5/5-10/10-15(×0.5)/>15(熔断)；target_vol 8%±2pp；sleeve ddc ≤-20%×0.5 回补-5%(ddc_th20_rd50_rc5)；冷却期=1个完整调仓周期
- §3.2 事件枚举: version.created/updated, component.registered, solver.selected, weight.solved, gate.evaluated, promotion.requested/approved/rejected/executed/downgraded, risk.action, retirement.triggered/executed, backtest.completed, reconciliation.failed, checkpoint.created
- §3.3 事件格式: {ts,actor,event_type,target,payload}；actor=evolution_pipeline|user|risk_layer；flock+fsync+月滚动 iteration-ledger-YYYY-MM.jsonl；重放幂等 apply；投影 sha256 校验不一致=reconciliation.failed；不引入 MQ/DB
- §4 门禁: G-S1 OOS Sharpe≥1.0 / G-S2 IS/OOS≥0.5 / G-S3 扰动降幅≤30% / G-S4 成本后为正(11.5bp) / G-S5 持仓相关性≤0.70 / G-S6 g1-g6；G-P1 影子≥1月频周期 / G-P2 对齐率≥95% / G-P3 TE±1.5倍 / G-P4 4维无超带；G-L1 4维连续≥2周期 / G-L2 执行率≥90% / G-L3 滑点≤11.5×1.5bp / G-L4 用户批准唯一人工门
- §5 回测审计六项 A1-A6，A1/A2 FAIL=绝对阻塞；Phase C 硬前置
- §6 兜底三件套: circuit_breaker/checkpoint/三方对账(§6.3 PV↔registry↔engines)
- §7.1 RET-1..4 退役(回撤超1.5倍历史MDD/连续6月跑输/IC连续3月<0/危机相关>0.90)；退役≠删除
- §7.2 4维漂移 D1 日P&L≤20bp/日 D2 Sharpe偏差≤0.3(60日滚动) D3 执行率≥90%对齐≥95% D4 滑点≤1.5×
- §7.5.1 vC/PV 承诺边界(验收硬门): 预算怎么分进版本，分出来的数运行时算；换求解器/改预算/增减sleeve/改0.75阈值=升版本
- §7.5.2 双触发: 定时(每周一开盘前)+RC偏离；成本闸门；换手≤20%净值
- §7.5.4 相关性: 0.75入池筛查/0.85上升防御降仓/0.90提级审查
- §8 Phase A 审计地基(纯文档零接触)→B 影子双轨(vC-0快照=F1 md5 915e446388… 对齐;删文件即回退)→C 治理切换(唯一红线=改active需批准,分钟级停机,指针回滚)→D 旧件退役(归档可回切)
- 附录A GLOSSARY: vC→PV, registry=Model Registry, composites.json=Portfolio Registry, g1-g6=CG-1..6, A腿=Equity Sleeve, gold腿=Hedge Sleeve—Gold
- 附录B: B7 IC趋势线/B8 前视检测=统一开发待派(Phase B 批次,纯看板层零架构变更)
