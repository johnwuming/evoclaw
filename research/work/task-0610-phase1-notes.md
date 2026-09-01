# task-0610 阶段一过程笔记（A2 asof 修复 + staging 重算）

- 开始: 2026-09-01 10:12 北京时间
- 规格: R-391 §5。修复 = 两处 compute_signals 改 asof 语义:
  sma200 = s.rolling(SMA_N).mean().reindex(m.index, method="ffill")
  vol60  = s.pct_change().dropna().rolling(VOL_N).std().reindex(m.index, method="ffill") * np.sqrt(252)
  热身期 <200 日仍 NaN→w=0。涉两文件: ~/quant-evolve/scripts/paper_engine_gold.py (compute_signals L85-92) 与 engines_shadow_nav_gold.py (L76-84, w=shift(1) L90)。
- 缺陷事实(R-391): 61/158 月末 sma200=NaN（10 热身 + 51 日历无交易），33 月错误归零；现行账本 157/157 对账一致（=缺陷语义复现）。
- 反事实方向对照: 终点 2.6046→3.1707、ann 7.59→9.22、MDD 5.90→8.09。

## 备份完成 (HP UTC 2026-09-01 02:34)
- ~/quant-evolve/backup/task0610_preA2_20260901_023404.tar.gz（16916B，含两脚本+results/engines/gold 全目录）
- sha256 清单: backup/task0610_preA2_20260901_023404.sha256
  - paper_engine_gold.py a193182a22e8272a7e2463c8119daa61ae8911cc4abbc6fb53bc4958211dbbff
  - engines_shadow_nav_gold.py 1293dc617bf09e6a5b7573dc1fb789b0968c223d5754574061587486c0684caf
  - shadow_nav.csv(生产账本) 1bec2035195b8946ea6d133d37fdce12773cabc9f444b0bab1f781a49a2814bd
- HP 无独立 paper_state.audit 文件（审计在 paper_state.json 内）；生产 mtime 快照已存 backup/mtimes_before_task0610.txt：
  - paper_engine_gold.py 2026-08-24 16:55:31 / engines_shadow_nav_gold.py 2026-08-24 15:13:34 / shadow_nav.csv 2026-08-24 15:13:35 / paper_state.json 2026-08-31 07:40:03 (UTC)
