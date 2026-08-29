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

## 项2 重放对照（2026-08-29 实测）
- 逐日表：work/task-0552-evidence/replay_diff.csv（8/14..8/28 共 11 行）
- 官方 10 日中 6 日 diff=0.00bp；8/19-21 约 -7.2bp（qfq 复权 vs 引擎 PIT 价源差，带内，8/24 起归零）；8/14 -21.43bp（建仓日：官方按成本+费用计价 vs 重放按收盘计价，可归因口径差，边界值）
- 8/28 在役官方行缺失（日更滞后，qfq 源已有 8/28）→ 重放投影 NAV=1.009930（标注 projected）
- 组合层对照 combined_diff.csv（8/24..8/27）：nominal 0.5/0.5 vs solver 0.5803/0.4197，逐日 8.32~12.27bp，≤20bp 带内；权重层差 ±8.03pp=已知口径差（R-348 留痕，Phase C 切换后 solver 权重才生效）
- 事件账本 V3：ledger 4 事件（原 2 + 演练追加）seq 连续、sha256 登记校验 ok

## 项3 模拟调仓对照（9/1，8/28 收盘口径）
- 在役侧（task-0546 修复版引擎沙箱副本跑真实逻辑，/tmp/task0552-sb）：数据校验 6 项全 PASS；d=2026-08-28 选股 20 只；订单=8 卖（旧持仓全清）+11 买；最终 11 持仓、NAV 1.008374、择时系数 0.6174（低配补仓）。证据 reb-sim-9.1.log
- 目标侧（solver_equal_vol，solve_date=2026-09-01）：w=(0.580297, 0.419703)，风险贡献严格相等，fallback 未触发，dry_run=true。证据 weight-solution-2026-09-01-dryrun.json
- 差异归因：①层级口径差（在役=个股级引擎订单；目标侧=sleeve 级权重解，个股订单属执行层未建）②权重基础差（0.5/0.5 双独立链 vs solver 等波动率，±8.03pp 超 2pp 再平衡带=Phase C 切换语义本身，非实现缺陷）③择时系数只在在役侧存在（组合层 vol_target 参数位空）。差异全部可解释
- 注：solver equity 输入仍为冻结回测 NAV（止 8/14，D1 缺口未解），σ 解与 vC-0 一致属预期；gold 输入 shadow_nav 月频

## 项4 切换演练（/tmp/task0552-drill2 临时副本，不含回退段）
- 基线 verify ok（0 violations）→ 追加 drill.rebalance_sim（actor=user）→ seq=3 写入成功
- 同 seq 重放追加 → 返回 null（seq 幂等跳过）✓
- 追加后 verify ok（sha256 登记一致）✓
- ledger.replay() 两次投影 sha256=38780127a5… 完全一致（确定性重放）✓
- 耗时：verify/append/replay 各步 <0.001s（毫秒级），无异常

## GO/NO-GO 判定
**GO**。依据：①重放差异全部可归因且带内（唯一越带项 8/14 -21.4bp 为建仓日计价口径差，非状态错误；次日起逐日归零）②模拟调仓两侧产出齐备、差异可归因为口径差/层级差，无实现矛盾③演练 sha256 对账一致+幂等+校验全绿。
断点/切换前注意：A) equity 8/28 日更缺口需在切换前补跑 daily（qfq 源已齐）；B) 建仓日 21.4bp 口径差建议写入漂移标定留痕；C) gold marks 止 8/27（T-1 机制正常，今晨 07:40 cron 未含 8/28 有待当日复核）；D) solver equity 输入 D1 缺口（回测 NAV 止 8/14）为已知 Phase B 遗留，不阻塞切换。
