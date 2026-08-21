# task-0419 feat_csad_sigma20 E1 IC画像 过程笔记
启动 2026-08-21 16:19 GMT+8。目标：零回测，IC 画像五要素 + 达线判定。

## 16:2x 数据源核验（HP 实查）
- K线: ~/quant-evolve/data/all_stocks_qfq/*_daily_qfq.parquet, 5448 文件, cols=[date,open,high,low,close,volume,amount,outstanding_share,turnover], 000001 范围 2005-01-04~2026-08-20（与 r251/R-251 同源）
- ths_ttm_panel.parquet: code,report_date,net_profit_ttm,equity,roe_ttm,roa_ttm,debt,avail_date（PIT 用 avail_date）
- fin_deep_monthly_panel_ak.parquet: 无 pb 列 → pb_inv 自构 = (equity/流通股)/close（rank 相关下量纲无关，报告中披露）
- 在役 IC 序列: ~/quant-evolve/results/factor_ic_monthly.csv（248 月 2006-01 起, 含 market_cap_log/avg_amount_20d/roe_ttm/volatility_20d/idiosyncratic_vol/amihud_illiquidity）
- crowding: results/r250/crowding_monthly.csv 2020-01 起, 市场层月度时序（无个股截面 → 冗余检查改用 IC/时序相关，报告披露）
- R-257 编号确认: 全库最大 R-256（task-0416v2 已占）, R-257 可用

## 构建口径决策（帖子模糊处）
- 同伴群: 前一月末定群, 滚动120交易日收益相关, corr>0.5 且取相关最高前20只; <5只 → 当月 NaN
- 相关近似: 窗内有效收益≥100/120 才入池, 去均值后 nan→0 标准化内积（轻微低估, 披露）
- CSAD_i,t = mean_j |ret_it − ret_jt|, j∈同伴群, 当月每日
- feat_csad_sigma20 = CSAD 滚动20日 std（min 20 有效日, 停牌日 NaN）; 月末取值
- PIT: 因子月 m 只用到 m 月末及以前数据（同伴群在 m-1 月末用 [m-1月末-120d, m-1月末] 窗定）; IC[ym]=spearman(F_ym, ret_ym→ym+1)
- 脚本: r0419_csad.py (VPS work/ 与 HP scripts/ md5 一致 d0a000005d633971cc76364930d5fac3), HP nohup 启动

## 运行记录
- 16:27 首次启动失败（nohup 重定向目录不存在），mkdir 后重启 PID 621958 正常（HP 本地钟 08:27 UTC）
- 预计: Phase A 加载 5448 parquet ~3-5min; Phase B 月循环 ~250 月 × ~2-3s; Phase C IC 画像
- 报告骨架预置: 背景(小红书帖动机, OCR 置信中低不作依据) / 方法(构建口径+与帖子差异) / 核心发现(IC五要素+达线判定) / 结论 / 来源
