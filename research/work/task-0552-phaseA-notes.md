[2026-08-29 10:15:30] task-0552 PhaseA 开始：数据底账核实

## 依据摘录（R-336）
- §4.3 G-L 系（paper→canary→live）：G-L1 4维漂移在带内连续≥2调仓周期；G-L2 执行率≥90%；G-L3 滑点≤11.5bp/边×1.5；G-L4 用户批准（唯一人工门）
- §8 Phase C 动作：①事件溯源切换（append+replay+投影sha256）②paper指针语义切换（portfolio_version_ref）③三方对账上线 ④断路器+checkpoint接入
- §8 Phase C 退出条件：切换后首个调仓日三方对账全绿；断路器/checkpoint干跑通过；重放重建状态 vs 旧JSON状态 diff=0
- Phase B 已落（R-346/347/348）：vC-0快照、等波动率求解器v1、复现门F1 md5=915e446388…、影子双轨对账、4维漂移监控
- 用户 2026-08-29 10:07/10:13 已批准提前切换、不考虑回退、当日切完；本阶段只验证不切换

## 项1 数据底账核实（HP 实测 2026-08-29 上午）
- equity paper：results/baseline-paper-nav.csv 10 行 8/14..8/27（**缺 8-28 行**）；paper-state.json created 8/17、last_rebalance 8/14、last_daily 8/27、8 持仓全部 buy 8/14、cash 40393/initial 100000、updated_at 8/28T16:30:01
- **8-28 缺口归因**：qfq 源 max=2026-08-28（数据已在库），8/28 16:30 日更 cron 有跑（updated_at）但当日数据未及入库→last_daily 停 8/27（R-348 已知 equity 日线滞后问题再现）
- gold：results/engines/gold/paper_state.json marks 8/24..8/27（4 条，nav 1.0→1.0000695）、current_weight=0.0（month_end 7/31 信号 w_signal=0，px<sma200 防御态）、frozen sma200/vol60/vol_target0.1/月频首交易日/货基000198
- 结论：底账可用于重放对照，8-28 在役官方行缺失→重放侧 8-28 标注 projected；覆盖面 8/14..8/27 官方对照 + 8/28 投影
