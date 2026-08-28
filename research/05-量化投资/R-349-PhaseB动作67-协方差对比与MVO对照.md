# R-349 Phase B 动作6-7：协方差对比留档与 MVO 对照跑批

> task-0544 · 2026-08-29 · 执行依据 R-336 v1.4 §8 动作6/动作7、§1.2④ A3/A5
> 位置：HP `~/quant-evolve/portfolio_v1/{cov_compare,mvo_compare}/`（在役零改动，新增子目录）
> **总声明：两项均为对照留档，不建服务、不换默认求解器行为、不接 cron、不切指针；promotion 仍走等波动率/ERC。**

## 1. 方法与参数

### 1.1 共用输入（只读）
- A 腿：registry locked_nav `results/a13_rsraw_e1f10dz_full_nav.csv`（vC-0 `a13_rsraw_e1f10dz` 同源；全量 5008 行 2006-01-04→2026-08-14，持仓段 `num_held>0` 共 4990 日）
- gold 腿：canonical 对齐月收益 `portfolio_v1/combo_selector/data/monthly_returns.csv`（156 个月 2013-08→2026-07，run_vc0_repro G1 md5 门校验件；gold 列=shadow net 月收益，含 mmf 停泊与 cost drag）
- 注：任务书所引「A 腿 4491 日」与 registry 实际不符（5008/4990），本报告如实采用实际值。

### 1.2 动作6 cov_compare
- 估计器：sample（ddof=1）/ LW（sklearn LedoitWolf，自动收缩）/ EWMA（指数衰减加权去均值；月频 λ=0.97 主 + 0.94 敏感性，日频 λ=0.94，RiskMetrics 惯例）
- 窗口：月频 60 个月（solver `window_days=60` 的月频类比，√12 年化）；日频 60 日 √252（与在役 gold vol60/solver 完全同源）
- 判定指标（R-336 指定）：OOS 波动率预测误差（月频：滚动窗估计→等波动率权重组合下月预测 vs 实现，附 Frobenius；日频 A 腿：60 日窗年化→前向 20 日已实现波动）+ 协方差条件数

### 1.3 动作7 mvo_compare
- 基线：在役 `EqualVolSolver`（monthly freq、60 期窗、√12）链式再平衡
- MVO：scipy SLSQP，`min 0.5·w'Σw − γ·μ'w`（γ=1 年化单位），Σ=样本协方差（透明基线）
- 约束（R-336 §8）：个股权重上限 5%、行业偏离 ≤5%、换手 ≤20%（vs 漂移后权重，首解起点=等波动率仓位）；成本 `0.0013×Σ|Δw|` 双方同用
- 收益预测接口（保留）：`forecast_returns(window)->Series`，已实现 `mu_hist`（60 月历史均值年化）与 `mu_zero`（min-variance）两场景
- OOS：96 个月链式再平衡（2018-08→2026-07）

## 2. 动作6 结果

全样本月频年化（2×2）：

| 估计器 | A vol | gold vol | corr | 条件数 |
|---|---|---|---|---|
| sample | 16.94% | 6.85% | 0.030 | 6.13 |
| LW（收缩 0.186） | 16.21% | 8.29% | 0.021 | 3.83 |
| EWMA λ=0.97 | 13.25% | 8.25% | 0.244 | 2.94 |
| EWMA λ=0.94 | — | — | — | 3.65 |

OOS（95 个月，2018-08→2026-06）：

| 估计器 | 波动率预测 RMSE | Frobenius | 条件数均值 |
|---|---|---|---|
| sample | **0.0593** | 0.0276 | 6.40 |
| LW | 0.0624 | 0.0264 | **2.40** |
| EWMA 0.97 | 0.0594 | 0.0242 | 4.76 |
| EWMA 0.94 | 0.0597 | **0.0227** | 4.19 |

- 等波动率权重路径 OOS 实现组合跨估计器几乎重合（vol 7.33–7.36%、ret 12.1–12.3%）。
- 日频 A 腿（4909 点）：EWMA(0.94) RMSE 0.0730/bias 0.0017 ＜ sample 0.0795/bias 0.0069。

### 结论（→ `solver_meta.cov_estimator_rationale`，已生成 `rationale_recommended.json`，`action=archive_only`）
1. 两腿等波动率只消费对角线，各估计器 OOS RMSE 差 <5% → **v1 维持样本口径**（与在役 gold vol60 同源、OOS 不劣），默认求解器行为不变。
2. LW/EWMA 优势在条件数与完整矩阵 → **ERC/风险预算（P2）阶段建议采 LW**（条件数均值 2.40 最优）。
3. EWMA(0.94) 对 A 腿日频对角线有改进（RMSE −8%）→ 留档备查。

## 3. 动作7 结果（**不启用，仅对照留档**）

| 配置 | 年化收益 | 年化波动 | Sharpe | maxDD | 平均换手 | 期末净值 | 约束满足 |
|---|---|---|---|---|---|---|---|
| 等波动率基线 | 12.07% | 7.33% | **1.646** | -5.46% | 1.93% | 2.465 | n/a |
| MVO 字面5%·μ_hist | -0.21% | 0.75% | -0.279 | -3.66% | 90.0% | 0.984 | **不可行**：95/95 月不收敛、换手违例 95/95 |
| MVO 字面5%·μ_zero | -0.21% | 0.75% | -0.279 | -3.66% | 90.0% | 0.984 | 同上 |
| MVO 腿级100%·μ_hist | 13.32% | 11.26% | 1.183 | -11.41% | 5.48% | 2.691 | 0 违例；**切角集中 100% A 腿** |
| MVO 腿级100%·μ_zero | 11.70% | 7.40% | 1.581 | **-4.34%** | 2.36% | 2.401 | 0 违例 0 不收敛 |

约束适用性（两腿场景）：
- 个股权重上限 5%：股票级设计；腿级字面应用**数学不可行**（2×5%<100%），照跑留作实证（10% 仓位陷阱、90% 换手）；主对照用腿级上限 1.0
- 行业偏离 ≤5%：两腿跨资产（全市场选股 / 商品CTA+货基）无单一行业暴露 → **n/a**，`industry_map`/benchmark 接口保留
- 换手 ≤20%：适用，逐月链式施加

对照结论：
1. μ_hist 场景切角集中 100% A 腿：波动 7.33%→11.26%、maxDD −5.46%→−11.41%、Sharpe 1.646→1.183 —— R-336「MVO 对收益预测误差极敏感、易过拟合集中」实数据复现。
2. min-variance（μ_zero）≈ 等波动率（Sharpe 1.581 vs 1.646，仅 maxDD 略优）：无收益预测条件下带约束 MVO 无启用证据。
3. **显式声明：MVO 不启用**；promotion 仍走现行等波动率/ERC 路径。**P3 复盘重议条件**（R-336 §8 L379）：待股票级 universe（个股权重/行业约束真正适用）与更可靠收益预测来源落地后，用本框架（本目录脚本）以实际数据重议。

## 4. 交付物与验证

| 项 | 路径（HP `~/quant-evolve/portfolio_v1/`） |
|---|---|
| 动作6 脚本/说明/数值 | `cov_compare/run_cov_compare.py` · `cov_compare/cov_compare.md` · `cov_compare/results/{cov_compare_results.json, rationale_recommended.json, cov_oos_monthly.csv, cov_oos_daily_a.csv}` |
| 动作7 脚本/说明/数值 | `mvo_compare/run_mvo_compare.py` · `mvo_compare/mvo_compare.md` · `mvo_compare/results/{mvo_compare_results.json, mvo_oos_paths.csv, mvo_constraint_check.csv}` |

- 幂等验证：重跑前后 4 个 CSV md5 逐位一致；3 个 JSON 去 `generated_at` 哈希一致（cov 4b2830a1 / rat 2385afe3 / mvo 2b50918e）
- 计算耗时：2.5s / 4.2s（远低于 40 分钟预算，无需 nohup）
- 在役零改动：`find -newermt` 核验，新目录外仅命中 paper 引擎/risk patrol cron 定点节奏产物（16:30:01/16:45:02 整分触发）；crontab 未触碰（基线 md5 3983e350）；solver/registry/paper_engine/portfolio/events 零改动；未用 rm

## 5. 备注
- 与等波动率求解器共用 cron 触发的设计（R-336 v1.3①）已在两脚本幂等化后具备接入条件，但按约束本任务不启用 cron；接入属「动 crontab」事项，需用户批准后另行操作。
- 过程笔记：`shared/results/work/task-0544-cov-mvo-notes.md`
