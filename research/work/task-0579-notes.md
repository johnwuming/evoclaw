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

## 4. 复算运行与排障（12:4x-13:1x）
- 运行1：adv20 searchsorted 类型错（int64 数组 vs datetime64 标量）→ dd 转 np.int64(Timestamp.value) 修复
- 运行2：锚点不符排查 → 与 A线 p2gate_task0576_states.csv 逐日对拍 pos_MA20_c0_full：**diff days=0（仓位序列逐位一致）**；真因=我的 build() 把纯闸配置也叠了 ddc → pure() 修复
- 运行3：锚点 MDD −15.51%/−20.43% 与 A线逐位吻合；ann 差=年化基数（A线 252 交易日年 vs 本任务/E1B 243）：换算 1.1843^(243/252)=19.19%≈A线 19.17% ✓、1.2059^(243/252)=21.42%≈21.43% ✓
- 运行4：v2 成本出现 full≈half 反常 → 抽样诊断：861 持仓码中 825 缺 <code>.parquet（引擎实际用 <code>_daily_qfq.parquet，5206 个）→ 96% 名目走 5bp 兜底，成本退化为常数 → 修 K线加载器（_daily_qfq 优先，missing=0）
- 运行5（最终）：full v2 2.871pp/年、half 2.504pp/年。half≈full 的 0.87 属实且正确：佣金 2.5bp 下限+印花 5bp 为固定 bps、冲击仅 √participation 缩放 → 半仓单次成本≈full 的 0.89（单日诊断 11.9bp vs 10.6bp）；平坦费率情景 half 恰为 full 一半（3.741/1.871）双口径互证
- 教训：ssh 远端命令中 `&` 会吞 stdin（cat 上传 0 字节）与 pkill/pgrep -f 模式自匹配 → 上传与启动分离、ps+grep -v bash 精确判进程

## 5. 最终结果（HP work_tmp_task0579/t0579_merged_ruling.{json,csv} + results/ 同名镜像；全期 243 日年化）
### 锚校验（全过）
raw 22.39%/−33.55%（逐位）；gate gross MDD −15.51%/−20.43%（逐位=A线）；ddc15 sim 20.22%/−22.89%（=E1B 引擎语义）；dd20 段口径 raw E2015 −31.6%（=E1B baselines 逐位）；switches 24.94/年（A线 25.86，计数边界差 ~3%，如实标注）
### Qa 计成本后净改善（主口径=v2 在役同款逐名 ADV 冲击，1e7 名义本金）
| 配置 | gross | v2净 | flat15净 | flat30净 |
|---|---|---|---|---|
| GATE_FULL | 18.43%/−15.51%/C1.188 | 15.07%/−21.17%/C0.712（cost 2.87pp/年）| 14.07%/−21.54%/C0.653 | 9.87%/−39.49%/C0.25 |
| GATE_HALF | 20.59%/−20.43%/C1.008 | 17.61%/−20.92%/C0.842（cost 2.50pp/年）| 18.36%/−20.92%/C0.877 | 16.16%/−22.19%/C0.728 |
| raw 对照 | 22.39%/−33.55%/C0.667 | 同左（无闸层成本）| — | — |
- **半仓档：三档成本口径净改善全部成立**（MDD +11~13pp，净 Calmar 0.73~0.88 > raw 0.667）
- **全仓档：全期勉强（C0.712）但 OOS2 净 2.03%/−17.26% vs raw 12.31%/−16.13% ann/MDD 双劣 → 不成立**；E1 粗估 5-8pp/年偏悲观（实算 2.87），但「成本吞噬样本外优势」的方向判断被证实
### Qb 叠加对比（v2 净口径）
| 配置 | 全期 | OOS1 2016-21 | OOS2 2022-26.8 |
|---|---|---|---|
| DDC15 单独 | 20.18%/−22.96%/C0.879（cost 0.038pp/年）| 6.71%/−14.53%/C0.462 | 11.75%/−15.68%/C0.75 |
| GATE_HALF_DDC15 | 16.59%/−18.61%/C0.891（cost 2.35pp/年）| 3.48%/−13.06%/C0.266 | 5.93%/−13.70%/C0.433 |
| GATE_FULL_DDC15 | 14.71%/−20.82%/C0.706 | 2.68%/−12.11% | 2.13%/−17.06% |
- ddc15 不被替代（闸单独/叠加的 ann 全低 4-6pp，OOS Calmar 全劣）
- 叠加增量（half+ddc vs ddc）：全期 ΔMDD +4.35pp ✓ 但 Δann −3.59pp ✗(>3pp)；OOS1 ΔMDD +1.5pp ✗、OOS2 ΔMDD +2.0pp ✗ 且 Δann −5.8pp ✗ → **按「全期+OOS MDD≥3pp 且 ann 代价≤3pp」预注册标准不达标**
- gross 口径下叠加增量同样 <3pp@OOS（gate_half gross OOS2 MDD −13.35% vs ddc gross −15.56% → +2.2pp）
### 五痛段 MDD（v2 净）：raw E2015 −31.60% → DDC15 −20.70% → GATE_HALF_DDC15 −15.57%；E2026 −12.66% → −12.19% → −9.46%；E2024Q1 −9.03% → −9.03% → −4.73%
### Qc 合并裁决输入
- paper_engine.py 只读复核（L1-26/76-77）：五 action（daily/init/rebalance/timing/…），仓位干预仅月频 rebalance 乘 timing_ratio，「timing_ratio<0.35 本月不新增买入」；**无 ddc/drawdown/日频 pos_ratio 字段 → 执行层同阻断成立**
- registry 实查：timing=q3z_x_ew_trend_overlay enabled（未动）；HP crontab 42 行未动；本任务零在役改动（只写 work_tmp_task0579/ 与 results/t0579_*）
