# task-0610 阶段一过程笔记（A2 asof 修复 + staging 重算）

- 开始: 2026-09-01 10:12 北京时间
- 规格: R-391 §5。修复 = 两处 compute_signals 改 asof 语义:
  sma200 = s.rolling(SMA_N).mean().reindex(m.index, method="ffill")
  vol60  = s.pct_change().dropna().rolling(VOL_N).std().reindex(m.index, method="ffill") * np.sqrt(252)
  热身期 <200 日仍 NaN→w=0。涉两文件: ~/quant-evolve/scripts/paper_engine_gold.py (compute_signals L85-92) 与 engines_shadow_nav_gold.py (L76-84, w=shift(1) L90)。
- 缺陷事实(R-391): 61/158 月末 sma200=NaN（10 热身 + 51 日历无交易），33 月错误归零；现行账本 157/157 对账一致（=缺陷语义复现）。
- 反事实方向对照: 终点 2.6046→3.1707、ann 7.59→9.22、MDD 5.90→8.09。
