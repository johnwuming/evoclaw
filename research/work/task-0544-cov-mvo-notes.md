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

## 执行进度
- [x] 编号确认 R-349
- [x] HP 结构探查
- [ ] 数据口径核验（4491日、列名、频率）
- [ ] cov_compare/ 实现+运行
- [ ] mvo_compare/ 实现+运行
- [ ] 在役零改动核验（find -newermt）
- [ ] 报告 R-349
- [ ] README 更新日志
- [ ] 完成回报
