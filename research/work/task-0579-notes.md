# task-0579 微盘 P2 趋势闸合并裁决补充研究 — 过程笔记

2026-08-30 12:17 启动。承接 task-0576（R-374 A线 / R-376 B线）E1 判门唯一候选：zz500 指数级 MA20 日频形态。三问：
- Qa 切换成本：实查 HP cost_model v2 定义；有→用其重算 MA20 日频形态全期+WF 双窗 OOS 净改善；无→两档保守假设分档重算。必须回答「计成本后净改善是否仍成立」
- Qb ddc15 叠加：闸×ddc15（或 ddc15×闸）vs 各自单独 ann/MDD/WF 双窗 OOS → 替代/叠加/弃用 三选一
- Qc 合并裁决：连同「执行层与 ddc15 同阻断」建议 → E2 预注册 GO/NO-GO/有条件 GO；GO 须列前提与口径（闸形态/成本口径/对比基准/判门阈值）

纪律：HP 新代码只放 ~/quant-evolve/work_tmp_task0579/；results/ 只新增；零改在役；预算 ≤40min；边查边写本文件。

## 进度日志

## 1. HP 实查 round1（2026-08-30 12:2x，只读）
- 编号：本地 05-量化投资 最大 R-376 → 本报告取 R-377 ✓（R-377 未被占用）
- **cost_model v2 已在役定义**：model/main.json L36 `"cost_model": "v2"`；引擎 scripts/backtest_dividend_quality_iter.py L52 `from cost_model_v2 import estimate_cost, is_untradeable`；L493-527 v2 路径=estimate_cost(order_amt, adv20, side).total_bps，退化兜底 legacy 一半（单边 cost_rate=0.001/2），上限 total_cost_frac≤0.05；L787 注释：legacy=固定单边0.1%，v2=佣金+印花+ADV平方根冲击
- 引擎默认 DEFAULTS: cost_rate=0.001, cost_model="legacy"（v2 需 cfg 显式指定；registry 已 v2）
- scripts/ 下含 cost_model 字样的脚本：a11_rules.py / r278_run.py / r297_run.py / a8_bucket.py / a2_registry_bootstrap.py / a4b_run.py / a10_v6a_formal.py / e2_eng_timing.py 等（复用先例多）
