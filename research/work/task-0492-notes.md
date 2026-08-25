R-314 task-0492 中央风控双引擎仓位分配研究 - 过程笔记
开始时间: 2026-08-25 09:26

## 1. 数据源实查（2026-08-25 09:2x）
- registry/model/main.json（HP ~/quant-evolve）：version=a13_rsraw_e1f10dz, strategy=raw_universe_ranksum4, metrics(锁定窗): ann 0.2202 / mdd -0.3355 / sharpe 1.3561 / calmar 0.6562 / years 18.48 / 月胜率 0.6516
- A nav 两个口径：
  - full: results/a13_rsraw_e1f10dz_full_nav.csv 2006-01-04→2026-08-14（日频, 162KB），full_metrics: ann 0.2239/mdd -0.3355/sharpe 1.3737/calmar 0.6673/years 20.61
  - locked: 2006-01-04→2024-06-28（18.48y，与 main.json 完全吻合 → main.json 指标=locked 窗）
  - **决定：用 full nav**（覆盖最近 2024-07→2026-08 样本外段；gold 链路同起点 2013-08 对齐，重叠约 156 月），并附 locked 窗口径对照
- gold: results/engines/gold/shadow_nav.csv 2013-08→2026-08，157 月，月频 net 列。md5=3654c3e80103fc313e24c9eb641de4e2
- registry corr(A,gold)=-0.040 n=131 月 ≈ 2013-08..2024-06（locked 窗重叠），与本次 full 重叠窗 corr 需重算对照
