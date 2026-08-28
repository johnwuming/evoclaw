# task-0544 过程笔记：Phase B 动作6-7 协方差对比 + MVO 对照

## 环境事实
- 报告编号确认：R-349（R-348 为最新已用）
- HP portfolio_v1/ 结构：solver_equal_vol.py(7.7KB)、build_vc0.py、event_ledger.py、portfolio_version.py、combo_selector/、portfolio/versions/vC-0.json、drift_monitor.py、shadow_recon.py
- vC-0 sleeves：A腿=registry_ref engine A entry `a13_rsraw_e1f10dz`（data_cut 2026-08-26）；gold腿=engine_ref `gold_trend_sma200`（frozen_form: sma200/vol60/vol_target 0.1/月频首交易日）
- 数据文件（combo_selector/data/）：a13_full_nav.csv（A腿）、gold_shadow_nav.csv（gold腿）、monthly_returns.csv
- 求解器口径（solver_equal_vol.py）：window_days=60, annualization=252, min_obs=40；等波动率=各腿 1/σ 年化归一；fallback=等权+fb_* 枚举；COV_RATIONALE 字段已预留动作6结论更新
- solver_meta 契约（R-336 §1.2④）：weight_solution(portfolio_version_id, solve_date, weights{}, solver_meta{type, params, cov_estimator, cov_estimator_rationale, convergence_status, random_seed, diagnostics, fallback_triggered, fallback_reason})

## R-336 规格摘录（grep 定位）
- 动作6（§8 L378）：LW vs 样本 vs EWMA 各跑一遍留档（2-3腿成本≈0）；判定指标=OOS 波动率预测误差 + 协方差条件数；结论记 solver_meta.cov_estimator_rationale；不建服务、不换默认；deadline Phase B 中期
- 动作7（§8 L379）：约束=个股权重上限5% + 行业偏离≤5% + 换手≤20%；跑批不启用、仅对照留档；保留收益预测接口与组合权重输出；promotion 仍走等波动率/ERC；P3 复盘用实际跑批数据重议；与等波动率求解器共用同一 cron 触发（本任务不启用 cron，只交付可跑脚本+对照产出）
- v1.2⑤：MVO 对收益预测误差极敏感、易过拟合集中 → 晋升路径明确不用 MVO，对照仅留档

## 数据口径核验（已确认）
- registry locked_nav：~/quant-evolve/results/a13_rsraw_e1f10dz_full_nav.csv，5008 数据行（2006-01-04→2026-08-14），md5=358ce8…，与 combo_selector/data/a13_full_nav.csv 逐位相同；num_held>0 段=4990 日（2006-02-07 起）。任务书「4491 日」与实际不符，报告如实记录实际值
- canonical 对齐月收益：combo_selector/data/monthly_returns.csv，156 个月（2013-08→2026-07），cols=month/A/gold，md5=0113f4…（run_vc0_repro.py G1 门校验件）；gold 列=shadow nav net 月度收益（含 mmf 停泊与 cost drag，w_applied 44 个不同值）
- gold_shadow_nav.csv：157 行，末行 2026-08-31 为未完月，canonical 月收益止于 2026-07（repro 口径）
- 环境：sklearn 1.9.0 + scipy 1.17.1 可用
- P3 复盘条件原文（R-336 L379/L91）：「P3 复盘用实际跑批数据重议」；promotion 仍走等波动率/ERC；晋升路径明确不用 MVO（对收益预测误差极敏感）
- solver_equal_vol 契约尾部：weight_solution() 产出 solver_meta 全字段；COV_RATIONALE 已预留动作6结论

## 设计决策
- cov_compare：主分析=月频 2x2（A/gold，canonical 月收益），估计窗 60 个月（solver 60 期窗口的月频类比，√12 年化）；估计器=样本(ddof=1) / LW(sklearn LedoitWolf) / EWMA(λ=0.97 月频 RM 惯例+0.94 敏感性，加权去均值)；指标=全样本条件数+滚动 OOS 波动率预测误差(等波动率权重组合预测 vs 下月实现)+Frobenius 误差；辅助=A 腿日频 4990 日 60 日窗√252 口径（solver 当前口径）sample vs EWMA(0.94) 的前向 20 日已实现波动率预测 RMSE
- mvo_compare：月频链式滚动再平衡 OOS 96 个月（2018-08→2026-07）；基线=solver_equal_vol（monthly freq, 60 月窗）；MVO=scipy SLSQP，目标 0.5·w'Σw−γ·μ'w（γ=1）；μ 两场景=60月历史均值年化 / 0(min-variance)；权重上限两配置=字面5%(两腿退化证据) / 腿级100%(主对照)；行业偏离=两腿不适用(接口保留 industry_map)；换手≤20% vs 漂移后权重；成本=0.0013×Σ|Δw| 双方同口径；Σ 用样本协方差（透明基线，MD 注明）
- 幂等：全部输出确定性、覆盖式写 results/

## 运行结果（已验收）
### cov_compare（2.5s，95 个 OOS 月 2018-08→2026-06，日频 4909 点）
- 全样本月频年化：sample A=16.94%/gold=6.85%/corr=0.030/cond=6.13；LW A=16.21%/gold=8.29%/corr=0.021/cond=3.83(shrink=0.186)；EWMA0.97 A=13.25%/gold=8.25%/corr=0.244/cond=2.94
- OOS 等波动率组合波动率预测 RMSE：sample 0.0593（最优）≈EWMA0.97 0.0594≈EWMA0.94 0.0597＜LW 0.0624（差异<5%）；Frobenius：EWMA0.94 最优 0.0227；cond_mean：LW 最优 2.40
- 等波动率权重路径 OOS 组合表现跨估计器几乎无差（vol 7.33-7.36%，ret 12.1-12.3%）→ 两腿等波动率只消费对角线，协方差选型边际影响极小
- 日频 A 腿（solver vol60 口径）：EWMA0.94 RMSE 0.0730＜sample 0.0795（前向 20 日，bias 0.0017 vs 0.0069）
- 结论方向：v1 等波动率维持 sample 对角线（与在役 gold vol60 同源、OOS 不劣）；LW/EWMA 优势在条件数与完整矩阵 → ERC/P2 阶段采 LW；EWMA 日频对 A 腿对角线有改进 → 留档备查。archive_only，不换默认
### mvo_compare（4.2s，OOS 96 个月 2018-08→2026-07，含成本 0.0013×turnover）
- equal_vol 基线：ann_ret 12.07%/vol 7.33%/Sharpe 1.646/maxDD -5.46%/turnover 1.93%/nav 2.465；最新解 (A,gold)=(0.414,0.586)，RC=50/50
- mvo_literal_5pct（两 μ 场景同）：腿级不可行——2×5%<100%，95/95 月不收敛，turnover 0.90 违例 95/95，ann_ret -0.21%/vol 0.75% → 字面约束在两腿层面不可行的实证
- mvo_leg_level_mu_hist：100% 切角进 A 腿（最新解 (1.0,0.0)），ann_ret 13.32%/vol 11.26%/Sharpe 1.183/maxDD -11.41% → 收益预测驱动集中、风险劣化，正是 R-336 否 MVO 的实证
- mvo_leg_level_mu_zero（min-var）：11.70%/7.40%/1.581/-4.34%（maxDD 优于基线）/turnover 2.36%/0 违例 0 不收敛 → 与等波动率接近，仅尾部略优
- 违例计数器 bug 已修（原把 turnover=0 误计违例）；修复后字面配置 95 违例、腿级配置 0 违例
- 幂等验证：重跑前后 4 个 CSV md5 逐位一致；3 个 JSON 去 generated_at 后哈希一致（cov:4b2830a1, rat:2385afe3, mvo:2b50918e）

## 执行进度
- [x] 编号确认 R-349
- [x] HP 结构探查 + 数据口径核验（实际 5008 行/持仓段 4990 日，任务书 4491 不符已留档）
- [x] cov_compare/ 实现+运行（幂等验证通过）
- [x] mvo_compare/ 实现+运行（幂等验证通过）
- [ ] 在役零改动核验（find -newermt）
- [ ] cov_compare.md + mvo_compare.md
- [ ] 报告 R-349
- [ ] README 更新日志
- [ ] 完成回报
