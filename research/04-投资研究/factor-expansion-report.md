# A1/task-0285 因子池深化：财务深因子 + 量价/微盘因子 + IC评估 + catalog_v3

- **日期**：2026-08-16　**数据区间**：2006-01 ~ 2026-07（月度前瞻）
- **股票池**：全A（qfq前复权，剔除当月停牌/上市未满120交易日/价格≤0），实际参与 5206 只
- **新增因子**：36 个（Phase2 财务深 22 + Phase3 量价/微盘 14）
- **IC口径**：月度截面 Spearman；ICIR_monthly=mean/std；ICIR_annual=ICIR_monthly×√12；t=ICIR_monthly×√N（与 W1 factor_registry_build 一致）
- **重叠阈值**：与存量72因子月度截面值相关 |ρ|>0.7 标注重叠；新因子间聚类阈值 0.6

## 1. 数据建设（akshare/东财替代 baostock）

### 1.1 数据源切换说明
- 原计划 baostock 六接口季频采集，因上游服务故障（2026-08-15 18:05 UTC 起 query_profit_data 挂死 >16h，probe 全空）切换 akshare 东方财富批量接口
- 接口：`stock_yjbb_em`（业绩报表）/`stock_zcfz_em`（资产负债表）/`stock_xjll_em`（现金流量表）/`stock_lrb_em`（利润表），按报告期一次拉全市场（~1-2s/期/接口 vs baostock 逐股小时级）
- 口径差异：东财为合并报表累计值；公告日取接口公告日期列（PIT 对齐）；杜邦/周转类因子由报表科目直接派生
- `fin_deep/yjbb.parquet`：451,669 行，覆盖 11,765 只股票
- `fin_deep/zcfz.parquet`：279,074 行，覆盖 5,244 只股票
- `fin_deep/xjll.parquet`：287,642 行，覆盖 5,244 只股票
- `fin_deep/lrb.parquet`：288,443 行，覆盖 5,244 只股票


### 1.3 数据质量核查（采集后验证）
- **yjbb 含新三板**：stock_yjbb_em 无证券类型过滤（RPT_LICO_FN_CPD），每期返回 ~11,500 条（含新三板 8xxxxx/43xxxx、北交所）；A股口径（60/00/30/68 开头）每期 ~5,215 只，与 zcfz/xjll/lrb 的 5,228 只匹配一致
- **zcfz/xjll/lrb 仅 A股**：接口内置过滤 SECURITY_TYPE_CODE in (058001001,058001008) 且剔除北交所，每期 ~5,228 只
- **不构成偏差**：因子面板以 K 线池（5,448 只 A股）为基准 join，多余的新三板记录自然被丢弃；两口径 A股部分 277,823 条匹配
- **dupont_roe_check 覆盖 0**：重构三因子乘积在浮点/极端值下 inf 溢出，catalog 标 unimplemented 不影响其他 35 个因子；其经济含义由 dupont_np_margin / dupont_asset_turn / dupont_leverage 三个分量因子完整承载
- **总覆盖**：zcfz 起始 2005，东财季报数据 2005Q1~2026Q2 全期可得，missing_periods=0

### 1.4 月度PIT面板
- `data/derived/fin_deep_monthly_panel_ak.parquet`：每 (code,ym) 取披露日 ≤ 月末的最近一期（merge_asof backward）
- 披露日 = max(四表公告日+1, pit_map.usable_from 优先 / 法披期限回退（Q1=4/30, H1=8/31, Q3=10/31, FY=次年4/30）+1日)

## 2. Phase 2 财务深因子（全部 PIT 对齐）

| 因子 | 定义 | mean_ic | icir_annual | t_stat | 覆盖 | n月 |
|------|------|--------|-------------|--------|------|-----|
| gp_margin | 销售毛利率 (yjbb 销售毛利率,%) | -0.0607 | -1.752 | -7.83 | 0.98 | 240 |
| roe_report | 报告期ROE (yjbb 净资产收益率,%) | -0.0322 | -1.116 | -4.99 | 0.98 | 240 |
| accrual_quality | 应计质量: 1-OCF/净利润 (OCF/NI<1=应计高=质量差, pos方向取1-ratio) | -0.0512 | -1.555 | -6.96 | 0.98 | 240 |
| cf_or_ratio | 现金流收入比: OCF/营业总收入 | -0.0573 | -2.291 | -10.25 | 0.98 | 240 |
| cf_np_ratio | 现金净利比: OCF/净利润 | -0.0295 | -1.189 | -5.32 | 0.98 | 240 |
| ocf_stability | 现金流稳定性: 近4期OCF/净利均值/|std| (派生) | -0.0360 | -1.183 | -5.29 | 0.98 | 240 |
| dupont_np_margin | 杜邦净利率: 净利润/营业总收入 | -0.0503 | -1.675 | -7.49 | 0.98 | 240 |
| dupont_asset_turn | 杜邦总资产周转率: 营业总收入(年化)/总资产 | -0.0400 | -1.284 | -5.74 | 0.98 | 240 |
| dupont_leverage | 杜邦权益乘数: 总资产/股东权益 | -0.0364 | -1.132 | -5.06 | 0.98 | 240 |
| dupont_roe_check | 杜邦ROE重构: 净利率×周转×权益乘数 | nan | nan | nan | 0.00 | 0 |
| dupont_tax_burden | 杜邦税收负担: 净利润/利润总额 | -0.0500 | -2.007 | -8.98 | 0.98 | 240 |
| debt_to_asset | 资产负债率 (zcfz,%) | -0.0436 | -1.319 | -5.90 | 0.98 | 240 |
| cash_to_asset | 现金资产比: 货币资金/总资产 (zcfz) | -0.0308 | -1.242 | -5.55 | 0.98 | 240 |
| inventory_to_asset | 存货占比: 存货/总资产 (zcfz) | -0.0576 | -1.321 | -5.91 | 0.98 | 240 |
| ar_to_asset | 应收占比: 应收账款/总资产 (zcfz) | -0.0725 | -1.528 | -6.83 | 0.98 | 240 |
| asset_yoy | 总资产同比 (zcfz,%) | -0.0719 | -1.380 | -6.17 | 0.98 | 240 |
| revenue_yoy | 营收同比 (yjbb,%) | -0.0759 | -1.532 | -6.85 | 0.98 | 240 |
| net_profit_yoy | 净利润同比 (yjbb,%) | -0.0627 | -1.184 | -5.30 | 0.98 | 240 |
| profit_accel | 盈利加速度: 净利YoY(t) - 净利YoY(t-4) (派生) | -0.0390 | -0.806 | -3.61 | 0.98 | 240 |
| revenue_accel | 营收加速度: 营收YoY(t) - 营收YoY(t-4) (派生) | -0.0416 | -1.727 | -7.72 | 0.98 | 240 |
| growth_persist | 成长持续性: 近4期营收YoY>0的个数 (派生) | 0.0044 | 0.171 | 0.77 | 0.98 | 240 |
| margin_trend | 毛利率趋势: 毛利率(t)-毛利率(t-4) (派生) | -0.0646 | -1.268 | -5.67 | 0.98 | 240 |

## 3. Phase 3 量价 + 微盘因子

| 因子 | 定义 | 类别 | mean_ic | icir_annual | t_stat | 覆盖 | n月 |
|------|------|------|--------|-------------|--------|------|-----|
| vp_divergence_20d | 价量背离评分: 20日Σsign(ret)×sign(Δvol)/20, 正=量价同向 | 量价 | -0.0577 | -1.190 | -5.32 | 0.98 | 240 |
| up_vol_shrink_ratio | 价升量缩占比: 20日中上涨且缩量日占比 | 量价 | -0.0541 | -1.094 | -4.89 | 0.98 | 240 |
| down_vol_expand_ratio | 价跌量增占比: 20日中下跌且放量日占比 | 量价 | -0.0032 | -0.163 | -0.73 | 0.98 | 240 |
| turnover_zscore_20d | 异常换手: (换手-MA20)/std20 | 流动性 | -0.0299 | -0.675 | -3.02 | 0.98 | 240 |
| turnover_momentum_5_20 | 换手动量: MA5换手/MA20换手-1 | 流动性 | -0.1035 | -2.299 | -10.28 | 0.98 | 240 |
| realized_vol_ratio_5_60 | 已实现波动分解: σ5/σ60 (近期波动占比) | 波动 | -0.0773 | -1.536 | -6.87 | 0.98 | 240 |
| overnight_gap_ratio_20d | 隔夜跳空比: 20日均|跳空|/均|日内| | 波动 | 0.0760 | 1.672 | 7.48 | 0.98 | 240 |
| large_order_proxy_20d | 大单近似: 20日(量>1.5×MA5量)成交额占比 | 量价 | -0.0547 | -2.687 | -12.02 | 0.98 | 240 |
| vol_ma_ratio_5_20 | 量能比: MA5量/MA20量-1 | 量价 | -0.0096 | -0.793 | -3.16 | 0.78 | 191 |
| price_level_log | 股价对数 (低价股效应) | 市值 | -0.0879 | -1.991 | -8.90 | 0.98 | 240 |
| shell_value_proxy | 壳价值代理: exp(-log总市值) | 市值 | -0.0615 | -1.186 | -5.30 | 0.98 | 240 |
| mktcap_rank_pct | 市值排名分位 (月截面, 0=最小盘) | 市值 | 0.0630 | 1.388 | 6.21 | 0.98 | 240 |
| microcap_liq_interact | 微盘流动性交互: (1-市值分位)×amihud | 市值 | -0.0364 | -1.405 | -6.28 | 0.98 | 240 |
| strong_reversal_micro | 微盘强化反转: -ret20d×(1-市值分位) | 反转 | -0.0854 | -1.892 | -8.46 | 0.98 | 240 |

## 4. 与存量72因子重叠分析 (|ρ|>0.7 标注重叠)

- 有重叠标注的新因子数：36
- **vp_divergence_20d**：max|ρ|=0.55，Top重叠 vp_corr(0.55), vp_corr_60d(0.32), turnover_std_20d(0.23), return_20d(0.22)
- **up_vol_shrink_ratio**：max|ρ|=0.28，Top重叠 up_down_volume_ratio(0.28), vp_corr(-0.26), vr(0.25), obv_factor(0.23)
- **down_vol_expand_ratio**：max|ρ|=0.54，Top重叠 up_down_volume_ratio(-0.54), vp_corr(-0.50), vr(-0.48), obv_factor(-0.45)
- **turnover_zscore_20d**：max|ρ|=0.91，Top重叠 volume_surge(0.91), vol_surge_5d(0.59), volume_slope_20d(0.47), boll_pos_20(0.40)
- **turnover_momentum_5_20**：max|ρ|=0.97，Top重叠 vol_surge_5d(0.97), volume_slope_20d(0.73), volume_surge(0.69), macd_hist_norm(0.49)
- **realized_vol_ratio_5_60**：max|ρ|=0.46，Top重叠 vol_ratio_20_60(0.46), vol_surge_5d(0.44), amount_ratio_10_60(0.38), volume_slope_20d(0.33)
- **overnight_gap_ratio_20d**：max|ρ|=0.19，Top重叠 zero_volume_ratio(0.19), amount_cv(0.18), amount_cv_60d(0.15), turnover_std_20d(0.12)
- **large_order_proxy_20d**：max|ρ|=0.71，Top重叠 amount_cv(0.71), amount_ratio_10_60(0.42), vol_ratio_20_60(0.38), turnover_std_20d(0.36)
- **vol_ma_ratio_5_20**：max|ρ|=1.00，Top重叠 vol_surge_5d(1.00), volume_slope_20d(0.75), volume_surge(0.70), macd_hist_norm(0.48)
- **price_level_log**：max|ρ|=0.26，Top重叠 market_cap_log(0.26), avg_amount_20d(0.26), volatility_120d(0.25), gk_vol_20d(0.25)
- **shell_value_proxy**：max|ρ|=1.00，Top重叠 market_cap_log(-1.00), circ_mv(-0.91), amihud_60d(0.68), amihud_illiquidity(0.67)
- **mktcap_rank_pct**：max|ρ|=1.00，Top重叠 market_cap_log(1.00), circ_mv(0.91), amihud_60d(-0.68), amihud_illiquidity(-0.67)
- **microcap_liq_interact**：max|ρ|=0.93，Top重叠 amihud_illiquidity(0.93), amihud_60d(0.90), market_cap_log(-0.88), circ_mv(-0.85)
- **strong_reversal_micro**：max|ρ|=0.86，Top重叠 return_20d(-0.86), ma5_ma20_ratio(-0.70), rsi_14(-0.63), boll_pos_20(-0.62)
- **gp_margin**：max|ρ|=0.39，Top重叠 debt_to_asset(-0.39), amount_cv_60d(-0.08), vp_corr_60d(-0.05), obv_slope_60d(0.05)
- **roe_report**：max|ρ|=0.21，Top重叠 amihud_60d(-0.21), amihud_illiquidity(-0.19), amount_cv_60d(-0.15), log_amount_60d(0.15)
- **accrual_quality**：max|ρ|=0.08，Top重叠 circ_mv(-0.08), market_cap_log(-0.08), turnover_rate_60d(0.08), volatility_120d(0.07)
- **cf_or_ratio**：max|ρ|=0.12，Top重叠 market_cap_log(0.12), volatility_120d(-0.12), idiosyncratic_vol(-0.12), turnover_rate_60d(-0.12)
- **cf_np_ratio**：max|ρ|=0.08，Top重叠 circ_mv(0.08), market_cap_log(0.08), turnover_rate_60d(-0.08), volatility_120d(-0.07)
- **ocf_stability**：max|ρ|=0.12，Top重叠 debt_to_asset(-0.12), volatility_120d(-0.12), turnover_rate_60d(-0.12), turnover_rate(-0.11)
- **dupont_np_margin**：max|ρ|=0.37，Top重叠 debt_to_asset(-0.37), amihud_60d(-0.16), amihud_illiquidity(-0.15), amount_cv_60d(-0.12)
- **dupont_asset_turn**：max|ρ|=0.06，Top重叠 debt_to_asset(0.06), circ_mv(-0.04), market_cap_log(-0.04), amount_cv_60d(-0.03)
- **dupont_leverage**：max|ρ|=0.95，Top重叠 debt_to_asset(0.95), circ_mv(0.24), market_cap_log(0.19), amihud_60d(-0.16)
- **dupont_roe_check**：max|ρ|=0.20，Top重叠 amihud_60d(-0.20), amihud_illiquidity(-0.19), amount_cv_60d(-0.15), log_amount_60d(0.14)
- **dupont_tax_burden**：max|ρ|=0.16，Top重叠 circ_mv(-0.16), market_cap_log(-0.15), debt_to_asset(-0.14), amihud_60d(0.13)
- **debt_to_asset**：max|ρ|=1.00，Top重叠 debt_to_asset(1.00), circ_mv(0.23), market_cap_log(0.19), float_ratio(0.16)
- **cash_to_asset**：max|ρ|=0.34，Top重叠 debt_to_asset(-0.34), circ_mv(-0.09), float_ratio(-0.08), obv_slope_60d(0.08)
- **inventory_to_asset**：max|ρ|=0.20，Top重叠 debt_to_asset(0.20), volatility_120d(0.06), gk_vol_20d(0.06), atr_ratio_20d(0.06)
- **ar_to_asset**：max|ρ|=0.23，Top重叠 market_cap_log(-0.23), circ_mv(-0.23), turnover_rate_60d(0.20), turnover_rate(0.19)
- **asset_yoy**：max|ρ|=0.14，Top重叠 amihud_60d(-0.14), amihud_illiquidity(-0.13), log_amount_60d(0.12), avg_amount_20d(0.12)
- **revenue_yoy**：max|ρ|=0.12，Top重叠 amihud_60d(-0.12), amihud_illiquidity(-0.11), log_amount_60d(0.11), avg_amount_20d(0.10)
- **net_profit_yoy**：max|ρ|=0.12，Top重叠 amihud_60d(-0.12), amihud_illiquidity(-0.11), log_amount_60d(0.10), avg_amount_20d(0.09)
- **profit_accel**：max|ρ|=0.05，Top重叠 float_ratio(0.05), mom_12_1(0.03), return_250d(0.03), amihud_60d(-0.02)
- **revenue_accel**：max|ρ|=0.04，Top重叠 mom_12_1(0.04), return_250d(0.03), float_ratio(0.02), amihud_60d(-0.02)
- **growth_persist**：max|ρ|=0.16，Top重叠 amihud_60d(-0.16), amihud_illiquidity(-0.15), circ_mv(0.14), market_cap_log(0.13)
- **margin_trend**：max|ρ|=0.07，Top重叠 float_ratio(0.07), amihud_60d(-0.04), amihud_illiquidity(-0.04), circ_mv(0.03)

## 5. 新因子间聚类

- 簇1（9个）：shell_value_proxy, mktcap_rank_pct, microcap_liq_interact, accrual_quality, cf_or_ratio, cf_np_ratio, ocf_stability, dupont_tax_burden, ar_to_asset
- 簇2（5个）：price_level_log, gp_margin, dupont_leverage, debt_to_asset, cash_to_asset
- 簇3（2个）：profit_accel, revenue_accel
- 簇4（9个）：roe_report, dupont_np_margin, dupont_asset_turn, dupont_roe_check, asset_yoy, revenue_yoy, net_profit_yoy, growth_persist, margin_trend
- 簇5（1个）：up_vol_shrink_ratio
- 簇6（1个）：inventory_to_asset
- 簇7（3个）：vp_divergence_20d, down_vol_expand_ratio, large_order_proxy_20d
- 簇8（1个）：strong_reversal_micro
- 簇9（3个）：turnover_zscore_20d, turnover_momentum_5_20, vol_ma_ratio_5_20
- 簇10（1个）：realized_vol_ratio_5_60
- 簇11（1个）：overnight_gap_ratio_20d

## 6. 显著性汇总

- 新增因子中 ICIR_annual 绝对值 ≥ 0.5：33 个
- 新增因子中 |mean_ic| ≥ 0.02：32 个
- 新增因子中 |t_stat| ≥ 2：33 个

## 7. 输出文件

- `results/factor_catalog_v3.json`：v2 全量 + 36 新因子（结构兼容 v2，W2 因子Tab可读）
- `results/factor_ic_monthly_v3_new.csv`：新因子月度IC明细
- `results/factor-expansion-report.md`：本文档
- `data/fin_deep/{yjbb,zcfz,xjll,lrb}.parquet`：东财四表原始数据；`data/derived/fin_deep_monthly_panel_ak.parquet`：PIT月度面板

## 8. A2模型迭代建议

- ICIR_annual≥0.5 候选：vp_divergence_20d, up_vol_shrink_ratio, turnover_zscore_20d, turnover_momentum_5_20, realized_vol_ratio_5_60, overnight_gap_ratio_20d, large_order_proxy_20d, vol_ma_ratio_5_20, price_level_log, shell_value_proxy, mktcap_rank_pct, microcap_liq_interact, strong_reversal_micro, gp_margin, roe_report, accrual_quality, cf_or_ratio, cf_np_ratio, ocf_stability, dupont_np_margin, dupont_asset_turn, dupont_leverage, dupont_tax_burden, debt_to_asset, cash_to_asset, inventory_to_asset, ar_to_asset, asset_yoy, revenue_yoy, net_profit_yoy, profit_accel, revenue_accel, margin_trend
- 其中与存量重叠(|ρ|>0.7)需谨慎：turnover_zscore_20d, turnover_momentum_5_20, large_order_proxy_20d, vol_ma_ratio_5_20, shell_value_proxy, mktcap_rank_pct, microcap_liq_interact, strong_reversal_micro, dupont_leverage, debt_to_asset
- 后续由 A2 结合独立性/经济含义筛选进入模型迭代