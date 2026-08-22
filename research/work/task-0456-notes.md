# task-0456 notes — excess_decay E1 画像（边查边写）

## A1. 指标口径确认（来源：tmp/task-0373/collect_crowding.py，生成 crowding-indicators.json 的脚本）

- excess_decay 定义（脚本行180-207）：微盘组（每日全市场按总市值后20%，等权）日收益 micro_ret_mean − hs300 日收益 = 日超额；nan→0；cum_ex=∏(1+excess)；log_cum=ln(cum_ex)；对最近 60 个交易日（ROLL=60）做 log_cum 对时间 idx 的 OLS 回归 → slope、tstat（se=sqrt(SSE/(60-2)/denom)）。
- 阈值（脚本行424-433，JSON note 同）：**slope<0 且 tstat<−2 → red**；仅 slope<0 → yellow；否则 green。
- R-273 §三.6 引用：2026-08-19 值 slope=−0.001889，t=−4.643，red ✓（与 crowding-indicators.json latest 一致，可溯源）。
- 指标历史序列文件 crowding_history.csv **VPS 无**（HP 侧未同步）→ 需 VPS 本地重算（脚本在 VPS，数据 all_stocks_qfq 5205 只 parquet 在 VPS workspace-quant/data/）。
- 脚本 hist 输出过滤 date>=2019-01-01 → 监控面板口径 2019 起。E1 普查同样以 2019 起为基准（与监控一致），更早仅作参考。
- 60 日窗口指标 + 盘中日频更新；**PIT 约定（画像用）**：月末最后可用日定值，次月才可作信号用。

## A2. 数据盘点
- all_stocks_qfq: /root/.openclaw/workspace-quant/data/all_stocks_qfq/，5205 个 *_daily_qfq.parquet（待确认最早/最晚日期、hs300 文件名）。
- crowding-indicators.json（9149B, generated 2026-08-19）：microcap_eqw_index 仅 90 日（2026-04-10→08-19），峰 793.09(05-11)→谷 538.36(07-22) = −32.12%（R-273 §三.1）。
- 微盘等权指数全历史需重算（脚本内部有 eqw 全序列，仅存 90 日）。

## A4. 重算结果（compute_e1.py → excess_decay_daily.csv）
- 面板：5205 只、10,819,439 行、2818 交易日 2015-01-05→2026-08-07（**VPS parquet 止于 08-07；监控 JSON 08-19 为 HP 侧数据，t=−4.643 的最新点不在 VPS 重算范围，缺口如实记录**）。
- 口径复刻：micro=每日市值后20%（lexsort 截断）、等权日收益（nan→0 计入分母）、excess=micro−hs300、log 累计、60d OLS slope/tstat、red=slope<0且t<−2（同 collect_crowding.py 行160-207/424-433）。
- 初步：red 日 989/2818（35.1%）——触发频繁，需 episode 化统计。
- 验证：eqw 序列与 task-0413 microcap_idx_90d.csv 对照（待做，择机抽 3 点）。

## A5. q3z 状态可用性
- timing_layer_prod.json：仅 monthly_series_tail 24 个月（2024-09→2026-08，pos_ratio 0.503-0.818，当前 0.522）；全套 248 个月需 index_valuation.parquet，**VPS 无 data/macro/（缺口）**。
- 已存 q3z_pos_ratio_tail24.csv。正交性分析以 2024-10→2026-07（tail 内有效月）重叠段 + in-sample 记录（R-222：q3z off 纯趋势 MDD −38~−52%）为准，标注缺口。

## A6. 触发普查与判定结论（最终数字全部落 census_summary.json / ep_dist_stats.json / q3z_overlap_summary.json）
- 2019+：red 日 747/1843（40.5%），episode 21 个，red 月末 36/92（16 段）。
- 首日锚 fwd21：均值 +1.63%/中位 +2.23%/胜率 71.4%（n=21）；fwd42 +0.84%/61.9%；fwd63 −0.96%/52.4%。基准：−0.57%/49.0%、−1.10%/47.8%、−1.57%/51.3%。
- 末日锚（n=20）：−0.56%/45%、−0.99%/45%、+0.14%/50% ≈ 无信息。
- PIT 月度：red 月次月 −0.02%/55.6% vs 全体 −0.41%/48.4% vs 非 red −0.65%/42.9%；2015+ 48 red 月 +0.16%/54.2% vs 全体 +1.21%/53.2%（符号跨窗不稳）。
- 2026 案例：red 04-10（t=−2.59，dd250=−9.1%）先于 05-11 峰 18 交易日；fwd21/42/63=−2.47%/−14.56%/−23.82%；峰谷超额 −29.44%（微盘 −32.17% vs hs300 −4.74%）；episode t 最深 −29.6，08-07 t=−12.5 仍 red（JSON 08-19 t=−4.643 缺口外佐证）。
- 2024-01 案例：微盘 01-02→02-08 −37.0%，red 01-25 迟到 17 交易日（dd250=−20.3%）。
- q3z tail 24 月：red 10 月，9/10 pos_ratio≥0.6，corr +0.264；2026-04/05 大跌月 pos_ratio 0.685/0.716 无警示；red&高 pos_ratio 次月均值 −0.8%（n=9）。
- **判定：假阳性过多关闭（E2 因子路径）；监控保留。复活=条件化变体（red∩dd250<10%）预注册+≥10 非重叠 episode，或补 2006-2014；反向线索（首日锚反弹）待独立预登记。**

## A3. 待办
- [x] 重算 2019→2026 日频 slope/tstat 序列（实际 2015 起，2019+ 为主窗口）
- [x] 触发普查 + 1/2/3 月前瞻超额胜率
- [x] q3z 重合度（tail 24 个月）
- [x] R-280 报告（7.6KB）+ README 更新日志
