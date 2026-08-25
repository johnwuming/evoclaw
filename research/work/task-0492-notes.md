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

## 2. 口径复核（全部命中）
- A full 日频 nav 复核: ann 0.2239 / mdd -0.3355 / 20.61y —— 与 HP results/a13_rsraw_e1f10dz_full_metrics.json 完全一致
- gold shadow 复核: ann 0.0759 / mdd -0.059 / 157月 —— 与 registry 落盘值一致
- corr locked 窗(2013-08..2024-06, n=131): **-0.040 精确复现 registry shadow.evals**；全重叠窗(n=156): +0.0297
- 注意: A 月频采样 mdd -16.95% ≠ 日频官方 -33.55%（月频低估回撤，报告须注明）

## 3. 回测结果（2013-08..2026-07, n=156, 成本0.13%×双腿|Δw|, 全PIT）
基线: A单: ann 18.93/vol 16.94/sharpe 1.111/calmar 1.117/mdd -16.95/worst -14.03/win 65.4%
      gold单: ann 7.64/6.85/1.111/1.294/-5.90/-3.93/80.8%
- F0 买入持有50/50: ann 14.86 calmar 1.148 mdd -12.95（漂移向A）
- **F1 等权月度: ann 13.54 vol 9.23 sharpe 1.428 calmar 1.636 mdd -8.28 worst -6.91 win 69.2%**
- F1 季度: ann 13.57 calmar 1.495 mdd -9.08（略差于月度）
- F2 网格 w_gold 0→50: calmar 1.117→1.636 单调升, sharpe 1.111→1.428 单调升; 域内无内点最优, 50%为边界最优
  - 域外探索: wg55 1.755 / wg60 1.909 / wg70 2.264（calmar续升但ann降至11.2%, 域外仅供参考）
  - IS/OOS(60/40切): wg50 IS calmar 1.692 / OOS 2.104 均最优, 全程单调 → 平台性结论稳健
- F3 波动率平价(36月滚动): mean w_gold 0.659 (wG区间 0.517-0.859), ann 9.51 sharpe 1.359 calmar 1.573 mdd -6.05
- F4 ERC(36月滚动,含corr): **与F3逐月权重差=0.000000000（数学恒等: 两资产ERC≡反波动率, 交叉风险项相消）**
- F5 回撤条件式(A dd≤-10%触发21月, -20%档从未触发): b50_tilt65_80 ann 13.37 calmar 1.623; 全部变体≤F1 → **负结果: A回撤后倾向反弹, 倾斜gold反而卖飞**
- 子期: 2013-2020 F1 calmar 1.797 ≫ F3 1.284; 2021-2026 F3 2.151 > F1 1.932（近期弱A期vol parity占优）
- 公共窗(2016-09+,n=119): F3/F4 calmar 1.575 > F1 1.402, sharpe 1.354>1.300; 但 ann F3 9.52≈F1 9.55
- F1 再平衡成本: 13年合计 0.51%（年化0.039%）→ 成本可忽略
- corr≈0 两引擎 → 等权已获绝大部分分散收益

## 4. 推荐
F1 静态 50/50 月度再平衡（容忍带±5pp），40%gold 为进取变体（ann 14.66/calmar 1.46/mdd -10.03）。不推荐 F3/F4/F5。
实施为 registry 层2人工门；两引擎资金池化记账是前置改动。

## 5. 零生产改动抽查（2026-08-25 09:3x）
- HP model/main.json mtime=2026-08-19 09:27（未动）
- HP results/engines/gold/shadow_nav.csv mtime=2026-08-24 15:13（未动,只cat读取）
- HP ~/quant-evolve 顶层无 2026-08-25 新改动的 .py
- crontab 未触碰；VPS 侧产物仅 work/task-0492/ + shared/results/
- 数据 md5: a13_full_nav.csv 358ce8192880d615d620d2297387601d / gold_shadow_nav.csv 3654c3e80103fc313e24c9eb641de4e2
