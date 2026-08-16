# A1/task-0285 因子池深化：财务深因子 + 量价/微盘因子 + IC评估 + catalog_v3（更正版）

> ⚠️ 本版为 **2026-08-16 更正版**：修复首跑统计错位 bug（详见 §9 更正记录）。§2/§3/§6/§8 的 IC 数字以本版为准。

- **日期**：2026-08-16　**数据区间**：2006-01 ~ 2026-07（月度前瞻，因子@月末m 预测 m+1 收益）
- **股票池**：全A（qfq前复权，剔除当月停牌/上市未满120交易日），实际参与 5448 只K线档案
- **新增因子**：35 个（Phase2 财务深 21 + Phase3 量价/微盘 14；另有 debt_to_asset 因与存量同名 |ρ|=1.00 剔除，见 §4）
- **IC口径**：月度截面 Spearman Rank IC，样本 2006-01~2026-07 共 245 个前瞻月；Rank IC 对单调变换（去极值/标准化）不变，与 W1 `mad_winsorize(3)+zscore` 口径等价；ICIR_annual=ICIR_monthly×√12；t=ICIR_monthly×√N
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
- **dupont_roe_check 首跑误报覆盖 0**（真实原因：统计层 enumerate 错位读到重名碰撞孤儿列，非数据问题）：实际 240 个月样本、IC -0.0122（t=-1.61），本版已更正；其经济含义仍由 dupont_np_margin / dupont_asset_turn / dupont_leverage 三个分量因子承载
- **总覆盖**：zcfz 起始 2005，东财季报数据 2005Q1~2026Q2 全期可得，missing_periods=0

### 1.2 月度PIT面板
- `data/derived/fin_deep_monthly_panel_ak.parquet`：每 (code,ym) 取披露日 ≤ 月末的最近一期（merge_asof backward）
- 披露日 = max(四表公告日+1, pit_map.usable_from 优先 / 法披期限回退（Q1=4/30, H1=8/31, Q3=10/31, FY=次年4/30）+1日)

## 2. Phase 2 财务深因子（全部 PIT 对齐，真实IC）

### 2.1 PIT 机制（逐因子适用）

- **披露日（usable_from）** = max(四表公告日(pubDate)+1天, `pit_disclosure_map.parquet` 的 usable_from(回退法披期限 Q1=4/30 / H1=8/31 / Q3=10/31 / FY=次年4/30, +1天))
- **月度化**：每 (code, ym) 取 usable_from ≤ 月末的最近一期（`merge_asof backward`），严禁报告期直接 join
- **公告日缺失**（lrb 276 / zcfz 432 / xjll 330 / yjbb 50 行）由法披期限回退覆盖，无硬造数据
- 下表「PIT来源」列标明各因子取数表；派生类因子（加速度/稳定性/持续性）在同一 PIT 宽表内按 code 时序 rolling/diff(4) 生成，所用历史期同样仅含已披露报告

| 因子 | 定义 | PIT来源 | mean_ic | icir_annual | t_stat | n月 | 结论 |
|------|------|---------|--------|-------------|--------|-----|------|
| gp_margin | 销售毛利率 (yjbb 销售毛利率,%) | yjbb | -0.0011 | -0.037 | -0.17 | 240 | 不显著 |
| roe_report | 报告期ROE (yjbb 净资产收益率,%) | yjbb | -0.0120 | -0.359 | -1.61 | 240 | 不显著 |
| accrual_quality | 应计质量: 1-OCF/净利润 (OCF/NI<1=应计高=质量差, pos方向取1-ratio) | 三表派生(lrb/zcfz/xjll 合并宽表) | -0.0043 | -0.261 | -1.17 | 240 | 不显著 |
| cf_or_ratio | 现金流收入比: OCF/营业总收入 | 三表派生(lrb/zcfz/xjll 合并宽表) | 0.0003 | 0.012 | 0.06 | 240 | 不显著 |
| cf_np_ratio | 现金净利比: OCF/净利润 | 三表派生(lrb/zcfz/xjll 合并宽表) | 0.0043 | 0.261 | 1.17 | 240 | 不显著 |
| ocf_stability | 现金流稳定性: 近4期OCF/净利均值/|std| (派生) | 三表派生(lrb/zcfz/xjll 合并宽表) | 0.0011 | 0.051 | 0.23 | 237 | 不显著 |
| dupont_np_margin | 杜邦净利率: 净利润/营业总收入 | 三表派生(lrb/zcfz/xjll 合并宽表) | -0.0065 | -0.217 | -0.97 | 240 | 不显著 |
| dupont_asset_turn | 杜邦总资产周转率: 营业总收入(年化)/总资产 | 三表派生(lrb/zcfz/xjll 合并宽表) | -0.0031 | -0.167 | -0.75 | 240 | 不显著 |
| dupont_leverage | 杜邦权益乘数: 总资产/股东权益 | 三表派生(lrb/zcfz/xjll 合并宽表) | -0.0110 | -0.332 | -1.48 | 240 | 不显著 |
| dupont_roe_check | 杜邦ROE重构: 净利率×周转×权益乘数 | 三表派生(lrb/zcfz/xjll 合并宽表) | -0.0122 | -0.361 | -1.61 | 240 | 不显著 |
| dupont_tax_burden | 杜邦税收负担: 净利润/利润总额 | 三表派生(lrb/zcfz/xjll 合并宽表) | 0.0038 | 0.183 | 0.82 | 240 | 不显著 |
| cash_to_asset | 现金资产比: 货币资金/总资产 (zcfz) | zcfz | 0.0060 | 0.237 | 1.06 | 240 | 不显著 |
| inventory_to_asset | 存货占比: 存货/总资产 (zcfz) | zcfz | 0.0007 | 0.040 | 0.18 | 240 | 不显著 |
| ar_to_asset | 应收占比: 应收账款/总资产 (zcfz) | zcfz | 0.0060 | 0.157 | 0.70 | 240 | 不显著 |
| asset_yoy | 总资产同比 (zcfz,%) | zcfz | -0.0107 | -0.435 | -1.95 | 240 | 不显著 |
| revenue_yoy | 营收同比 (yjbb,%) | yjbb | -0.0131 | -0.586 | -2.62 | 240 | 显著弱负 |
| net_profit_yoy | 净利润同比 (yjbb,%) | yjbb | -0.0130 | -0.724 | -3.24 | 240 | 显著弱负 |
| profit_accel | 盈利加速度: 净利YoY(t) - 净利YoY(t-4) (派生) | 三表派生(lrb/zcfz/xjll 合并宽表) | -0.0043 | -0.354 | -1.55 | 231 | 不显著 |
| revenue_accel | 营收加速度: 营收YoY(t) - 营收YoY(t-4) (派生) | 三表派生(lrb/zcfz/xjll 合并宽表) | -0.0051 | -0.400 | -1.76 | 231 | 不显著 |
| growth_persist | 成长持续性: 近4期营收YoY>0的个数 (派生) | 三表派生(lrb/zcfz/xjll 合并宽表) | -0.0009 | -0.044 | -0.20 | 237 | 不显著 |
| margin_trend | 毛利率趋势: 毛利率(t)-毛利率(t-4) (派生) | 三表派生(lrb/zcfz/xjll 合并宽表) | -0.0066 | -0.600 | -2.63 | 231 | 显著弱负 |

### 2.2 财务因子小结（真实IC下的再认识）

- 月频口径下财务因子整体显著弱于量价因子：最强 net_profit_yoy / revenue_yoy 也仅 |IC|≈0.013（t≈-3），与 A 股月频动量缺失+反转生态一致
- 成长类（revenue_yoy / net_profit_yoy / margin_trend）呈一致弱负向：高增长股票次月跑输——反转溢价的财务映射
- 应计/现金流质量类（accrual_quality / cf_* / ocf_stability）月频不显著（|t|<1.2），不排除季频/组合内剔除器价值（交 A2 验证）
- 杜邦三因素中 leverage 弱负向，np_margin / asset_turn 不显著；dupont_roe_check 实际有 240 月样本（首跑误报 0 覆盖系统计错位），IC -0.0122/t-1.61，仅作链路校验不建议入模

## 3. Phase 3 量价 + 微盘因子（真实IC）

| 因子 | 定义 | 类别 | mean_ic | icir_annual | t_stat | n月 | 与存量maxρ |
|------|------|------|--------|-------------|--------|-----|-----------|
| vp_divergence_20d | 价量背离评分: 20日Σsign(ret)×sign(Δvol)/20, 正=量价同向 | 量价 | -0.0475 | -2.288 | -10.23 | 240 | 0.5519 |
| up_vol_shrink_ratio | 价升量缩占比: 20日中上涨且缩量日占比 | 量价 | 0.0203 | 1.111 | 4.97 | 240 | 0.2811 |
| down_vol_expand_ratio | 价跌量增占比: 20日中下跌且放量日占比 | 量价 | 0.0457 | 1.798 | 8.04 | 240 | 0.5361 |
| turnover_zscore_20d | 异常换手: (换手-MA20)/std20 | 流动性 | -0.0308 | -1.241 | -5.55 | 240 | 0.9115 |
| turnover_momentum_5_20 | 换手动量: MA5换手/MA20换手-1 | 流动性 | -0.0302 | -1.212 | -5.42 | 240 | 0.9718 |
| realized_vol_ratio_5_60 | 已实现波动分解: σ5/σ60 (近期波动占比) | 波动 | -0.0162 | -0.655 | -2.93 | 240 | 0.4605 |
| overnight_gap_ratio_20d | 隔夜跳空比: 20日均|跳空|/均|日内| | 波动 | -0.0283 | -1.440 | -6.44 | 240 | 0.1931 |
| large_order_proxy_20d | 大单近似: 20日(量>1.5×MA5量)成交额占比 | 量价 | -0.0461 | -2.496 | -11.16 | 240 | 0.7087 |
| vol_ma_ratio_5_20 | 量能比: MA5量/MA20量-1 | 量价 | -0.0308 | -1.242 | -5.56 | 240 | 1.0 |
| price_level_log | 股价对数 (低价股效应) | 市值 | -0.0750 | -1.754 | -7.84 | 240 | 0.2565 |
| shell_value_proxy | 壳价值代理: exp(-log总市值) | 市值 | 0.0581 | 1.200 | 5.37 | 240 | 1.0 |
| mktcap_rank_pct | 市值排名分位 (月截面, 0=最小盘) | 市值 | -0.0581 | -1.200 | -5.37 | 240 | 1.0 |
| microcap_liq_interact | 微盘流动性交互: (1-市值分位)×amihud | 市值 | 0.0746 | 1.531 | 6.85 | 240 | 0.9279 |
| strong_reversal_micro | 微盘强化反转: -ret20d×(1-市值分位) | 反转 | 0.0509 | 1.191 | 5.33 | 240 | 0.8561 |

- 量价新因子是本轮主力：large_order_proxy_20d（t=-11.2）、vp_divergence_20d（t=-10.2）、price_level_log（t=-7.8）、down_vol_expand_ratio（t=+8.0）
- 微盘组（shell_value_proxy / mktcap_rank_pct / microcap_liq_interact / strong_reversal_micro）全部显著正向（小盘+流动性交互），但与存量市值类 |ρ|≥0.86，增量信息有限
- direction 先验与实证冲突提醒：shell_value_proxy / down_vol_expand_ratio / up_vol_shrink_ratio 目录标注 neg、实证为正，A2 入模前需统一方向字段

## 4. 与存量72因子重叠分析 (|ρ|>0.7 标注重叠)

- 参与相关性计算的新因子 35 个（另 debt_to_asset 与存量同名剔除）；其中与存量 |ρ|>0.7 的 9 个
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
- **debt_to_asset（已剔除）**：与存量 v2 同名同义（|ρ|=1.00），新增版本不入册，仅 fin 面板存档 debt_to_asset_fin；Top重叠 debt_to_asset(1.00), circ_mv(0.23), market_cap_log(0.19), float_ratio(0.16)
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

## 6. 显著性汇总（真实IC）

- ICIR_annual |≥0.5|：17 个 → large_order_proxy_20d, vp_divergence_20d, down_vol_expand_ratio, price_level_log, microcap_liq_interact, overnight_gap_ratio_20d, vol_ma_ratio_5_20, turnover_zscore_20d, turnover_momentum_5_20, shell_value_proxy, mktcap_rank_pct, strong_reversal_micro, up_vol_shrink_ratio, net_profit_yoy, realized_vol_ratio_5_60, margin_trend, revenue_yoy
- |mean_ic| ≥ 0.02：13 个 → price_level_log, microcap_liq_interact, shell_value_proxy, mktcap_rank_pct, strong_reversal_micro, vp_divergence_20d, large_order_proxy_20d, down_vol_expand_ratio, vol_ma_ratio_5_20, turnover_zscore_20d, turnover_momentum_5_20, overnight_gap_ratio_20d, up_vol_shrink_ratio
- |t_stat| ≥ 2：17 个
- |t_stat| < 2（真实但不显著，仅入册观察）：18 个

## 7. 输出文件

- `results/factor_catalog_v3.json`：v2 全量(72) + 35 新因子 = 107 条目（结构兼容 v2，W2 因子Tab可读；含 overlap_with_v2 / pit / correction 字段）
- `results/factor_ic_monthly_v3_new.csv`：新因子月度IC明细（36 列，含存档 debt_to_asset_fin；孤儿列已清理）
- `results/factor-expansion-report.md`：本文档（更正版）
- `data/fin_deep/{yjbb,zcfz,xjll,lrb}.parquet`：东财四表原始数据（86/86 期完整）；`data/derived/fin_deep_monthly_panel_ak.parquet`：PIT月度面板（3.0M行×22财务因子）
- 脚本：`scripts/factor_expansion_v3ak.py`（已修复 fidx 版）+ `scripts/fix_v3_catalog_report.py`（本修复）+ `scripts/spot_price_level.py`（独立复算）

## 8. A2模型迭代建议（基于真实IC）

1. **独立增量优先**（与存量 max|ρ|≤0.7 且 |t|≥5）：`large_order_proxy_20d`(ρ0.71边缘,t-11.2), `vp_divergence_20d`(ρ0.55,t-10.2), `price_level_log`(ρ0.26,t-7.8), `down_vol_expand_ratio`(ρ0.54,t+8.0)——A2 首批入模候选；`overnight_gap_ratio_20d`(ρ0.19,t-6.4) 次之
2. **近重复勿重复入模**（|ρ|>0.7）：turnover_zscore_20d, turnover_momentum_5_20, large_order_proxy_20d, vol_ma_ratio_5_20, shell_value_proxy, mktcap_rank_pct, microcap_liq_interact, strong_reversal_micro, dupont_leverage ——与存量市值/流动性/量能类高度重叠，A2 选代表即可（建议保新增定义、剔存量旧口径，因新口径数据链路可复算）
3. **财务因子降频使用**：月频全线弱于量价（最强 |t|≈3），建议 A2 以季频重估或用作组合剔除器（如 accrual_quality 剔应计恶化票），不直接进月频 alpha 池
4. **微盘结构再确认**：microcap_liq_interact(t+6.8) 为存量池新增『小盘×低流动』交互维度，与纯市值(ρ-0.88~1.0)不同源，可作 size 因子的条件化增强；配合 strong_reversal_micro 构造微盘择时信号（A2 回测）
5. **工程复用**：PIT 面板 `fin_deep_monthly_panel_ak.parquet` 与月度 IC 管线可直接被 A2 引用；catalog v3 已带 overlap/pit/correction 字段，因子Tab 可读
6. **风险**：量价强因子多为拥挤类（换手/量能/大单），2024-2026 小盘风格反转期 IC 衰减风险高，A2 需做分年度 IC 稳健性检验（CSV 已含月度序列可直接分组）

## 9. 更正记录（2026-08-16）

- **bug**：首跑 `factor_stats_from_ic` 以 `enumerate(new_fids)` 索引全局 108 列 IC 矩阵（v2 在前 0..71）→ 首版报告 §2/§3/§6/§8 与 catalog 统计字段实为 v2 因子数字；`dupont_roe_check` 读到重名碰撞孤儿列误报 0 覆盖
- **不受影响**：月度 IC CSV（按列名导出）、§4 存量相关性、§5 聚类、PIT 面板（各自走 fidx/列名，已逐一复核）
- **修复**：按 CSV 列名重算统计并重建本报告与 catalog；`factor_expansion_v3ak.py` 已改 fidx 版 + 重名 dup-guard（py_compile 通过）；重跑仅统计层即可复现本版
- **端到端独立复算**（spot_price_level.py，从K线原始数据独立重建月末因子+次月收益）：
> [spot] n_months=253 mean_ic=-0.0751 icir_annual=-1.765 t=-8.10
> [ref ] n_months=240 mean_ic=-0.0750 icir_annual=-1.754 t=-7.84
> [check] |mean_ic diff| = 0.0001 -> PASS

