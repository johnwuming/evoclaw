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

## 2. HP 实查 round2（cost_model_v2.py 全文 L1-80 + 引擎机制）
- v2 公式（单边bps）= max(2.5, 5元/order_amt×1e4)佣金 + 卖5bp印花 + 10×√(order_amt/ADV20) 冲击；side=sell 加印花
- 引擎 ddc 机制：L340 pos_ratio=1.0 起始；L535-540 逐日 cur_dd 判定切 0.5/回 1.0；**L386 eff_ret=day_ret×pos_ratio×timing_ratio → ddc 在引擎内是收益缩放器，不产生显式交易成本**（a15_ddc15 实际 nav 只含月频调仓成本，不含 ddc 层换手成本）
- → 本任务对称处理：闸层与 ddc 层的仓位变更都按 v2 显式计价（组合 overlay 仓位 P_t 的 |ΔP_t| 逐名交易）
- 引擎 v2 计价细节：capital_base=1e7（名义本金）；port_val=nav_t×1e7；每名 order=port_val×w_each（等权近似）；adv20=K线 amount 列 20 日均值（min 10 窗）；total_cost_frac=Σ total_bps/1e4×w_each，上限 0.05；失效兜底=legacy 一半（单边 5bp）
- 数据：results/a13_rsraw_e1f10dz_full_holdings.csv 存在（88KB）；K线 data/all_stocks_qfq/（目录，逐票文件）；data/all_stocks_merged.parquet 合并面板备选

## 3. 数据与计价口径定格（运行前预注册 2026-08-30 12:3x）
- 对象数据：results/a13_rsraw_e1f10dz_full_nav.csv（raw 无 ddc 无 q3z）+ full_holdings.csv（月频 20 只等权，target 管道分隔）+ zz500_daily parquet（闸标的，E1 同款）
- 闸形态（E1 判门唯一候选，先验固定不复选）：zz500 close≥MA20（暖机满仓），confirm=0 即日生效，shift(1) 执行；full(0/1) 与 half(0.5/1) 两档
- ddc15：引擎语义复刻（E1 ddc_sim 同款：nav 先按当日 P 结算→cur_dd→≤-15% 切 0.5 / ≥-5% 回 1.0）；闸配置的 ddc 作用于闸后收益流
- 成本主口径=v2 在役同款（import scripts/cost_model_v2.estimate_cost）：切换日逐名 order=|ΔP|×(1/N)×nav_own_gross[t-1]×1e7，adv20=成交额 20 日均值(min10)，side 按ΔP 符号，失效名兜底 5bp，总成本上限 5%；敏感性=平坦 15bp/30bp×|ΔP|（E1 粗估带）
- 对称性：闸层与 ddc15 层仓位变更统一计入组合 P=gate×ddc 的 |ΔP|（引擎对两层都不计显式成本，本算补上）
- 配置 6：RAW / DDC15 / GATE_FULL / GATE_HALF / GATE_FULL+DDC15 / GATE_HALF+DDC15；各 × {gross, v2, flat15, flat30}
- WF 双窗 OOS（形态先验固定无需再选择）：OOS1 2016-2021、OOS2 2022-2026-08；五痛段 E1 同款
- 锚校验：raw MDD=-0.3355；gross gate_full≈19.17%/-15.51%、gate_half≈21.43%/-20.43%（R-374）；ddc15 sim≈-25.29%（E1 复算）
- 验证点：adv20 查询用 searchsorted as-of；K线 data/all_stocks_qfq/<code>.parquet 列「日期/成交额」
