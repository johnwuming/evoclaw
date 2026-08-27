# task-0503 notes: QDII 宽基ETF月频趋势信号 E1画像
[12:14] 笔记初始化

## [12:16] 参照序列定位
- a13 locked NAV: `shared/results/04-投资研究/a13_rsraw_e1f10_locked_nav.csv`（2006-01-04..2024-06-28，131KB 不全读）
- gold 在役引擎月度曲线: `shared/results/04-投资研究/f6_curves/gold_alone_nav.csv`（2013-08-31..2026-07-31，3264B 直接读）
- akshare 版本 1.18.94（与 R-303 同版）
- 工作目录约定: shared/results/work/r323/{raw,out}/

## [12:17] 待核验清单
1. QDII ETF 日线可得性: sh513100 国泰纳指100 / sh513500 博时标普500 / sz159941 广发纳指100 / sh000300 基准
2. 容量字段: fund_etf_hist_em 成交额
3. 现金增强: 000198 天弘余额宝货币 每万份收益
4. 缺口扫描=QDII 断供核查

## [12:20] 数据可得性实测第一轮（akshare 1.18.94, sina/em 双路）
- sh513100 纳指100ETF: OK 3178行 2013-07-31..2026-08-26（全史）
- sh513500 标普500ETF: OK 3066行 2014-01-15..2026-08-26
- sz159941 纳指100(深): OK 2704行 2015-07-13..2026-08-26
- sh513300 纳斯达克100ETF(华夏): OK 但仅 1410行 2020-11-05..2026-08-26（接口深度限制）
- sh000300 基准: OK 5979行 2002-01-04..
- sina 列含 volume/amount → 成交额可直接用于容量，em 源可弃
- em fund_etf_hist_em ×2 RemoteDisconnected FAIL（QDII 数据常规断连）→ 重试 1 次，再败则用 sina.amount
- mmf fund_money_fund_info_em(fund=) 参数签名不符 → inspect 后重调
