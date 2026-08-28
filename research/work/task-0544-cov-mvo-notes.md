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
