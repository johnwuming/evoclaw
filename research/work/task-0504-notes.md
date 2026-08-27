# task-0504 notes — R-324 PEAD 真实披露日 PIT 面板复验

开始: 2026-08-27 12:15 GMT+8
假设: 真实披露日口径下，R-274 C2 残差化净增量 IC（deadline代理 +0.0152/t=3.49）若符号稳定 → PEAD 软惩罚线重获预注册资格；否则彻底关闭。
锚点纪律: 对照锚一律用 R-274 原文数字（C2 +0.0152/+0.326/t+3.49；C1 −0.0073/−0.099/−1.07；C3 −0.118pp/t−0.79/neg52.6%）；自洽锚 R-251 sue_std 全样本 0.0117/0.115、新鲜窗 0.0266/0.261。
注意（任务书偏差待澄清）: 任务书写锚 deadline-PIT(IC −0.0087/t−1.74)/strict-PIT(+0.0105/t0.96) —— 经 grep 核实该两个数字出自 **task-0442-notes §R-275 应计质量**（应计 IC 两 PIT 口径），并非 R-274 PEAD C2 数值。报告中如实澄清，PEAD 对照仍以 R-274 原文 C1-C3 为准。

## 数据资产盘点（12:18 完成）
- /tmp/r274_vps/raw/yjbb_*.csv：86 期全市场业绩快报表（东财回填「最新公告日期」=污染源；含 bps/roe 可作四因子代理），v1 污染面板缓存 events_sue.parquet（sue_std/sue_pct/net_profit_ttm/qidx 已算好，与 avail 无关，可直接复用）
- work/r274/{kline_monthly.parquet(728k 行 月度K线 close/amount/amt20/outstanding_share/td_cum), summary_v2.json(期限代理全部结果), ic_c2_resid.csv, spread_monthly.csv}
- r274_v2.py 全文已读：复刻点=W1 IC(spearman min_obs20 去极值1%/99%+zscore)、PIT(monthly_asof 同月取最新+按月ffill)、池(td_cum≥120+当月收盘)、C2 OLS 残差化(min100)、C3 双组≥20

## 待办
- [ ] 真实披露日采集方案测试（EM F10 利润表 NOTICE_DATE / 其他）
- [ ] 回填检测规则+量化
- [ ] 新面板重建+C1/C2/C3 复算
- [ ] 双锚对照表+判定
