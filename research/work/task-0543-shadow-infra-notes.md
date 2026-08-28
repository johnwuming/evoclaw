# task-0543 过程笔记（Phase B 动作4-5：影子对账+漂移监控）

## 编号确认
- 已有最大 R-347，本任务报告编号 R-348 ✓

## R-336 关键节摘录

### §7.2 影子 4 维漂移监控表（shadow/live 通用）
| 维度 | 定义 | 带宽（初版） | 监控频率 |
|---|---|---|---|
| D1 日P&L偏差 | |shadow P&L − 回测同日P&L|/NAV | ≤20bp/日（月累计≤1.5×回测月波动×权重） | 每日 |
| D2 Sharpe偏差 | rolling 60日 Sharpe(shadow)−(backtest同窗) | |Δ|≤0.3 | 每周 |
| D3 成交/调仓执行率 | 实际成交笔数/计划调仓笔数；信号对齐率 | 执行率≥90%；对齐率≥95% | 每调仓日 |
| D4 滑点偏差 | 实测滑点 vs 假设(11.5bp/边) | ≤假设×1.5 | 每调仓日 |
- 任一维连续2期超带 → 晋升冻结+漂移归因报告

### §8 Phase B 动作4-5
- 动作4：影子双轨观察——目标侧(event_log+portfolio_version+求解器输出) vs 在役运行态逐日对账，diff 容忍带内持续≥1完整月频调仓周期
- 动作5：影子4维漂移监控在影子侧启用，paper实测滑点回填成本模型
- 退出条件：双轨≥1调仓周期全在带内；vC-0复现R-317 md5一致
- 回退：目标侧产物全在新增文件，删文件即回退，在役零改动

## HP 数据源盘点（2026-08-29 00:15–00:35）
### 目标侧（portfolio_v1/）
- portfolio/versions/vC-0.json（3.9KB）：双 sleeve——equity_sleeve(registry_ref A:a13_rsraw_e1f10dz,active)+hedge_sleeve_gold(engine_ref gold_trend_sma200,active_paper)；solver=solver_equal_vol_v1(window60,ann252,min_obs40,tol: weight_sum 1e-6, rebalance_band 0.02)；capital gross/net=1.0；status=paper；created 2026-08-28T15:50Z；data_cut 2026-08-26；weighting.in_service=dual_independent_paper_chains
- portfolio/samples/weight-solution-2026-08-28-dryrun.json：equity 0.580297 / gold 0.419703；vols 0.1111/0.1537；dry_run=true
- portfolio/events/iteration-ledger-2026-08.jsonl：seq1 version.created + seq2 weight.solved（共2行1.8KB）
- combo_selector/results/nav_curves.csv：月频157行至2026-07-31（A/gold/F0/F1...）
### 在役运行态（只读消费）
- equity paper：results/paper-state.json（cash 40393，8只持仓 2026-08-14 建仓，last_rebalance 2026-08-14，last_data_date 2026-08-26，updated 2026-08-27T16:30）
- equity NAV：results/baseline-paper-nav.csv（2026-08-14→2026-08-26 共9行，基期1.0=10万）
- equity trades：results/baseline-paper-trades.csv（8笔 buy @2026-08-14，价=信号价）
- equity 回测日线：results/a13_rsraw_e1f10dz_full_nav.csv（date,nav,N 3列，末行 2026-08-14,64.31,0）；locked_nav 末行2024-06-28（不覆盖 paper 窗口，D1 只能用 full_nav）
- equity summary：results/baseline-paper-summary.json（current_nav 99740，price_date 2026-08-26）
- gold paper：results/engines/gold/paper_state.json（marks 4条 08-24..08-27 nav≈1.00007；w_signal(2026-07-31)=0.0，current_weight=0.0，mmf 000198）
- gold 监控链：results/engines/gold/shadow_nav.csv（月频，列 month,w_applied,gold_ret,mmf_ret,gross,net,nav，至2026-08-31 net=5.38e-4，nav=2.6046）
- registry：model/registry/a13_rsraw_e1f10dz.json status=active（gate.nav_file=full_nav.csv）；model/registry/engines.json 含 gold_trend_sma200 slot=B status=active
- 在役 cron：equity daily 16:30 工作日 paper_engine.py；gold daily 07:40 paper_engine_gold.py；gold 月度 3日 09:38/09:40 shadow_nav append/evaluate；equity rebalance 15:00 月初
### 关键发现（撰写报告素材）
1. 回测日线 full_nav 末行=2026-08-14，paper NAV 起 2026-08-14 → 日线重叠仅1天，D1 equity 交集不足（insufficient_overlap），Phase B 需回填/扩展回测 NAV 至数据日
2. weight_solution 0.5803/0.4197 vs 在役 dual_independent_paper_chains 名义 0.5/0.5 → 权重差 ±0.08 > rebalance_band 0.02，属已知口径差（在役无组合层），对账标记 out_of_band+说明
3. equity last_data_date 2026-08-26 vs gold marks 至 08-27：equity 数据滞后1个交易日（08-27 周五缺）→ 对账新鲜度项
4. paper 成交价=信号价 → D4 滑点=0 by construction，标注 paper 口径，真实滑点回填属动作5 A5 校准后续
5. gold shadow_nav 2026-08-31 已有行（月末行预生成/含 mmf est），gold paper 8月 MTD +6.95e-5 vs 监控链 net 5.38e-4（口径：paper w=0 仅 mmf est 部分月内 vs 链含 gold_ret？w_applied=0 → net 应同 mmf est 口径，需脚本细看列含义）
