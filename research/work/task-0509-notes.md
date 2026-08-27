# task-0509 过程笔记：国债ETF趋势层2第三腿E1画像（R-331）
开始时间：2026-08-27 18:16 CST（本机时区 Asia/Shanghai）

## 数据清单（本地定位，2026-08-27 18:17）
- gold 月度序列：shared/results/04-投资研究/engines/gold/shadow_nav.csv（15330B；列 month,w_applied,gold_ret,mmf_ret,gross,net,nav；范围 2013-08 ~ 2026-08）
- 货基月收益（现金增强输入）：04-投资研究/engines/gold/mmf_monthly_push.csv（4399B；2013-08 起）
- a13 净值：04-投资研究/a13_rsraw_e1f10_full_nav.csv（161804B，日频；metrics 同名 json：period 2006-01-04~2024-06-28，18.48y，ann 21.63%，MDD -33.55%）——corr 用其全样本日净值聚合为月收益
- 中央 paper-nav.csv 仅含 2026-08-14 起少量行，不用于 corr
- 方法论先例：05-量化投资/R-303/R-304/R-305、独立性门槛 R-255(corr<0.5)、接口 R-292

## 待办
1) akshare 拉 511010/511260/511090 日线（东财）落盘 /tmp
2) 新浪源核验一致性
3) SMA200×波动上限×货基增强画像
4) 月频 corr(a13/bond)、corr(gold/bond)、corr(a13/gold)
5) 容量：近20日均额
