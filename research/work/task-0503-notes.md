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
