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

## §1 数据源确定与预注册（计算前写定 12:22）
- 真实披露日源：东财 F10 主要指标 API `datacenter.eastmoney.com/securities/api/data/v1/get` reportName=RPT_F10_FINANCE_MAINFINADATA，filter=(SECUCODE="XXXXXX.SH/SZ/BJ")，单股一次返回全历史 REPORT_DATE+NOTICE_DATE（122 期，0.23s/股）。抽样验证：000001 2024FY→2025-03-15（真披露日；对比 yjbb 回填版 2026-03-21 ✗）、2025Q1→2025-04-19、2018FY→2019-03-07 ✓
- 回填/异常清洗规则（先于任何 C2/C3 计算写定）：
  lag=NOTICE_DATE−REPORT_DATE；0≤lag≤180 天 → 视为真实披露日；lag 缺失/负/>180 天 → 回退法定期限上界代理（R-274 口径），并计入替代率。依据：季报法定上限 30/62/31 天、年报 120 天，180 天留余量；yjbb 型回填特征≈+479 天必被此规则捕获
- **预注册判定规则（禁事后调线）**：
  - P1（唯一资格判据，沿任务书假设句）：新口径 C2 残差化净增量 IC 均值>0 且 t≥2 且与 R-274 锚(+0.0152)同号 → PEAD 软惩罚线重获预注册资格
  - P2 否则（均值≤0 / t<2 / 符号翻转任一）→ 彻底关闭，不再挂口子
  - P3 附带观察项（不入判据）：C1、C3、PEN 覆盖（vs R-251 真实 674 / R-274 代理 1492）、sue_std 自洽、敏感性(≤1月/sue_pct)
  - 口径完全复刻 r274_v2.py：W1 IC(spearman min_obs20 去极值1%/99%+zscore)、池(td_cum≥120+当月收盘)、PIT(monthly_asof 同月取最新+ffill)、C2 OLS 残差(cross≥100)、C3(双组各≥20)
- 对照锚澄清（终版）：本任务书所写 deadline-PIT(−0.0087/−1.74)/strict-PIT(+0.0105/+0.96) 两数经核实出自 task-0442-notes（R-275 应计质量两 PIT 口径），非 R-274 PEAD 数字。依「对照锚以 R-274 原文为准」纪律，PEAD 对照锚=R-274 v2（C1 −0.0073/−1.07、C2 +0.0152/+3.49、C3 −0.118pp/−0.79）；strict-PIT 侧另引 R-251 sue_std 全样本与新窗口做定性参照
