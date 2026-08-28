# task-0540 PhaseB 动作1-2 过程笔记（边查边写）

## 规范要点摘录（来源：R-336 v1.4 / R-342 v1.2，已分段读）

### portfolio_version schema（R-342 §3.1，v1.2 A1 冻结结构）
- 必备字段：portfolio_version_id / sleeves{} / risk_control{drawdown_gates, vol_target, backfill_rule} / per_sleeve_risk_cap / solver_ref{solver_id, params, tolerances, fallback} / capital_policy{gross_limit, net_limit} / parent_version / status / gate_report / paper_entered_at / paper_duration
- sleeves 每条组件指针附 code_hash + data_cut（model manifest 最小集）
- risk_control 只存组合级；单腿 ddc 参数下沉 sleeve 版本对象
- 示例：sleeve 键 equity_sleeve / hedge_sleeve_gold

### vC-0 构建规程（R-342 §3.1 落地要点 v1.2 补）
1. cutoff 时刻 = Phase B 启动日构建；data_cut 取 T-1 交易日（A 股交易日历）
2. 三组件（A 引擎/gold 引擎/ddc）code_hash 锚定 = 组件仓库 git sha + registry 快照 id 双锚
3. 在役代码变更 → 重打快照（parent_version 链留痕），不回溯
4. 签名与时间 = HP 侧执行者（actor 记账）+ 用户批准引用（任务中心登记），快照体内记 built_ts

### vC-0 首条内容（R-336 §8 Phase B 动作1）
- A:a13_rsraw_e1f10dz + gold:active_paper + ddc 0.20/0.5/0.05 + 权重口径

### data_cut 硬断言（§1.2⑤）
- data_cut ≤ min(所有输入数据源最大时间戳)；违反即 config.invalid，绝对阻塞，不允许降级放行

### weight_solution 契约（§1.2④）
- weight_solution(portfolio_version_id, solve_date, weights{}, solver_meta{type, params, cov_estimator, cov_estimator_rationale, convergence_status, random_seed, diagnostics, fallback_triggered, fallback_reason})
- fallback 生效必产 weight.solved 事件（reasons 含 fb_* 前缀枚举）
- 等波动率：w_i ∝ 1/σ_i 归一

### 事件账本（R-342 §3.2 / R-336 §3.3）
- 文件：portfolio/events/iteration-ledger-YYYY-MM.jsonl（本次任务指定 portfolio/events/ 下）
- 行格式：{ts, actor, event_type, target, payload}；actor ∈ {evolution_pipeline, user, risk_layer}
- flock：锁文件 events/.ledger.lock，LOCK_EX|LOCK_NB，失败短重试+告警；每行写完 fsync；月滚动
- 幂等（附录伪代码）：重放 key=evt.seq；无 seq 用文件名+行号；重复 seq 跳过
- 相关事件类型：version.created / solver.selected / weight.solved / checkpoint.created
- promotion.executed payload 引用 data_cut 或市场快照标识

### 等波动率求解器 v1
- w_i ∝ 1/σ_i 归一；两腿 σ·w 贡献相等
- solver_id=solver_equal_vol_v1；solver_meta 含 cov_estimator+rationale（Phase B 校准期 LW vs 样本 vs EWMA 留档）
- tolerances + fallback 进 solver_ref

## 环境勘察（HP）

（待填）
