# R-207-W1 因子注册表：72因子全量IC检验 + catalog_v2

- **数据区间**：2006-01 ~ 2026-07（月度前瞻，IC样本 246 个月）
- **股票池**：全A（剔除 当月停牌 / 上市未满6月≈交易日<120 / 价格≤0数据异常）
  - 注：K线为前复权(qfq)，2006年价格普遍<2元，任务的“价格>2元”ST代理不适用于qfq，且无历史ST标记，故以“上市≥120交易日+非停牌”近似剔除ST/新股
- **参与计算股票数**：5205 只（qfq日线 + THS财务 + ttm_panel + fundamentals）
- **检验日期**：2026-08-15
- **阈值**：IC准入 0.02 / ICIR年化最低 0.5 / 相关性上限 0.6

## 1. 方法说明

- **因子值**：每月最后一个交易日 as-of（滚动窗口，无前视）；财务因子按披露日可用（Q1=4/30, H1=8/31, Q3=10/31, 年报=次年4/30），TTM类使用 ths_ttm_panel 自带 avail_date
- **前瞻收益**：下月末收盘/本月末收盘 - 1（月度前瞻，与月度调仓一致）
- **IC**：月度截面 Spearman 秩相关；**ICIR_monthly** = mean_ic/std_ic；**ICIR_annual** = ICIR_monthly × √12
- **t_stat** = mean_ic/(std_ic/√N)，N=IC有效月数
- **coverage** = 有≥20个有效样本的月数 / 总月数
- **half_life_months** = lag1~12 前瞻IC的衰减半衰期（|IC_lag|<|IC_1|/2 的首个lag；未衰减到一半记12）
- **turnover_monthly** = 因子排序前30%股票池的月度进出比例（月际集合变化比例均值）
- **聚类**：72因子月度IC序列两两相关 → 层次聚类（distance=1-|ρ|, average linkage, 阈值0.6）
- **回撤类定义**：用「距窗口内滚动高点回撤」度量（max_drawdown_W = W日滚动高点/收盘-1；dd_area = 120日平均水下深度；dd_duration = 水下天数占比），向量化可实现且经济含义清晰

## 2. Top20 因子（按 |ICIR_annual| 排序）

| 排名 | 因子 | 类别 | mean_ic | icir_annual | t_stat | 覆盖率 | 半衰期 | 月换手 | 状态 |
|----|------|------|--------|-------------|--------|--------|--------|-------|------|
| 1 | amount_cv | 流动性 | -0.0542 | -2.639 | -11.80 | 0.98 | 2 | 0.66 | tested |
| 2 | vp_corr | 量价 | -0.0613 | -2.457 | -10.99 | 0.98 | 2 | 0.66 | tested |
| 3 | avg_amount_20d | 流动性 | -0.1049 | -2.334 | -10.44 | 0.98 | 6 | 0.22 | tested |
| 4 | vp_corr_60d | 量价 | -0.0525 | -2.061 | -9.22 | 0.98 | 2 | 0.36 | tested |
| 5 | log_amount_60d | 流动性 | -0.0886 | -2.009 | -8.98 | 0.98 | 12 | 0.12 | tested |
| 6 | turnover_std_20d | 流动性 | -0.0867 | -1.940 | -8.68 | 0.98 | 3 | 0.42 | tested |
| 7 | amount_ratio_10_60 | 流动性 | -0.0651 | -1.863 | -8.33 | 0.98 | 2 | 0.66 | tested |
| 8 | gk_vol_20d | 波动 | -0.0837 | -1.752 | -7.83 | 0.98 | 3 | 0.42 | tested |
| 9 | obv_factor | 量价 | -0.0512 | -1.712 | -7.66 | 0.98 | 2 | 0.61 | tested |
| 10 | return_skew_60d | 波动 | -0.0412 | -1.711 | -7.65 | 0.98 | 3 | 0.38 | tested |
| 11 | amihud_illiquidity | 流动性 | 0.0753 | 1.673 | 7.48 | 0.98 | 11 | 0.23 | tested |
| 12 | return_20d | 反转 | -0.0669 | -1.620 | -7.24 | 0.98 | 2 | 0.68 | tested |
| 13 | turnover_chg_20_60 | 流动性 | -0.0521 | -1.619 | -7.24 | 0.98 | 2 | 0.64 | tested |
| 14 | turnover_rate | 流动性 | -0.0784 | -1.575 | -7.04 | 0.98 | 3 | 0.29 | tested |
| 15 | volatility_20d | 波动 | -0.0740 | -1.574 | -7.04 | 0.98 | 4 | 0.49 | tested |
| 16 | return_60d | 反转 | -0.0676 | -1.539 | -6.88 | 0.98 | 2 | 0.40 | tested |
| 17 | idiosyncratic_vol | 波动 | -0.0754 | -1.525 | -6.82 | 0.98 | 3 | 0.25 | tested |
| 18 | amount_cv_60d | 流动性 | -0.0377 | -1.414 | -6.33 | 0.98 | 2 | 0.39 | tested |
| 19 | amihud_60d | 流动性 | 0.0618 | 1.384 | 6.19 | 0.98 | 12 | 0.12 | tested |
| 20 | ma5_ma20_ratio | 技术 | -0.0546 | -1.379 | -6.17 | 0.98 | 2 | 0.70 | tested |

## 3. 相关性聚类分析

- 聚类数：**10** 簇（阈值 0.6）
- 最大簇：簇 3，成员 21 个：['volume_slope_20d', 'volume_surge', 'up_down_volume_ratio', 'obv_factor', 'vr', 'mfi', 'vol_surge_5d', 'max_drawdown_20d', 'max_drawdown_60d', 'max_drawdown_120d', 'max_drawdown_250d', 'dd_current', 'dd_area_120d', 'return_5d', 'return_10d', 'return_20d', 'price_52w_pos', 'rsi_14', 'macd_hist_norm', 'boll_pos_20', 'ma5_ma20_ratio']
- 每簇保留策略：保留簇内 |ICIR_annual| 最高的因子，其余因子记 corr_alerts

| 簇 | 保留因子 | ICIR_annual | 成员 |
|----|---------|-------------|------|
| 1 | return_60d | -1.539 | obv_slope_60d, vwap_slope_20d, dd_duration_120d, return_60d, return_120d, return_250d, mom_3_1, mom_6_1, mom_12_1, mom_accel, ma20_ma60_ratio |
| 2 | amount_ratio_10_60 | -1.863 | amount_ratio_10_60, turnover_chg_20_60, vol_ratio_20_60 |
| 3 | obv_factor | -1.712 | volume_slope_20d, volume_surge, up_down_volume_ratio, obv_factor, vr, mfi, vol_surge_5d, max_drawdown_20d, max_drawdown_60d, max_drawdown_120d, max_drawdown_250d, dd_current, dd_area_120d, return_5d, return_10d, return_20d, price_52w_pos, rsi_14, macd_hist_norm, boll_pos_20, ma5_ma20_ratio |
| 4 | turnover_std_20d | -1.940 | float_ratio, mv_volatility_60d, turnover_rate, turnover_rate_60d, turnover_std_20d, volatility_20d, volatility_60d, idiosyncratic_vol, volatility_120d, downside_vol_20d, return_kurt_60d, atr_ratio_20d, gk_vol_20d, debt_to_asset, ocf_to_asset |
| 5 | amount_cv | -2.639 | amount_cv, amount_cv_60d, vp_corr, vp_corr_60d |
| 6 | div_yield_ttm | 0.911 | roe, roa, roe_ttm, roa_ttm, net_profit_margin, revenue_growth_yoy, profit_growth_yoy, div_yield_ttm |
| 7 | avg_amount_20d | -2.334 | market_cap_log, circ_mv, avg_amount_20d, amihud_illiquidity, log_amount_60d, amihud_60d, return_skew_60d |
| 8 | zero_volume_ratio | -0.605 | zero_volume_ratio |
| 9 | - | N/A | tail_volume_ratio |
| 10 | - | N/A | gross_profit_margin |

## 4. 与既有4因子结论对比

- 既有结论（factor_ic_summary.json，2026-08-13，仅4因子，ICIR为月度口径）：
  - div_yield_ttm：mean_ic=0.0246, ICIR(月)=0.234 → ICIR年化≈0.81；本次注册表 mean_ic=0.0276, ICIR年化=0.911（更强）
  - circ_mv：mean_ic=0.0507, ICIR(月)=0.292 → ICIR年化≈1.01；本次 mean_ic=-0.0540(负向即小盘), ICIR年化=-1.096（更强）
  - roe_ttm：ICIR(月)=0.005→年化≈0.02；本次 ICIR年化=-0.233，仍接近0（结论不变：ROE择股能力弱）
  - roa_ttm：ICIR(月)=0.002→年化≈0.01；本次 ICIR年化=-0.157，仍接近0（结论不变）
- **ICIR年化口径升级后结论**：div_yield_ttm 与 circ_mv 均跨越 0.5 准入线（ICIR年化 >0.5），方向/强弱与既有结论一致；
  roe_ttm/roa_ttm 依旧不具择股能力。即结论**方向不变、显著性因年化口径而增强**。

## 5. 假设方向 vs 实测IC符号（重要）

- catalog 中的 direction/econ_logic 为**先验假设**；实测 mean_ic 为事后结果。
- 共 21 个因子实测符号与假设相反，主要集中在 量价/动量/技术 类（如 vp_corr、obv_factor、mom_*、price_52w_pos、macd_hist_norm 等）：
  在A股月度频率上，这些“量价/趋势”因子对未来收益呈**负向**（短期反转主导），而非假设的正向延续。
- 含义：若用于实盘，需以实测符号/方向为准（例如 vp_corr 高→下月负收益）；catalog 保留假设方向用于定义与推导，实际权重应翻转。

## 6. 未实现因子清单与原因

- **tail_volume_ratio**（尾盘成交占比）：分钟数据(缺失) —— 数据缺失
- **gross_profit_margin**（销售毛利率）：sina财务(仅480只) —— 数据缺失

  - tail_volume_ratio：需分钟级数据（尾盘成交占比），当前仅有日线OHLCV，无法实现
  - gross_profit_margin：THS财务摘要无毛利率字段，仅 data/financial-full（sina）480只股票有，覆盖率不足，标记 unimplemented

## 7. 输出文件

- `factor_catalog_v2.json`：72因子 + 检验统计 + 聚类 + 门槛
- `factor_ic_monthly_v2.csv`：月度IC明细（ym × 72因子）
- 本文档
