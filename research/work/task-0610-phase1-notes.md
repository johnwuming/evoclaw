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

## 补丁完成 (HP)
- paper_engine_gold.py → sha256 0d6fe3ee3653394ca89288d3031212d30b3b217d7ab19b0ce288d12375f618f9（L86-87 加 method="ffill"）
- engines_shadow_nav_gold.py → sha256 d2730dc94d583d920adabebfe1f2ca46776a862a715393bfd2f262d5a02931bf（L78-79 同）
- 两文件 py_compile 通过；最小 diff 落盘 output/staging_gold_a2/fix_asof.diff（26 行，每文件恰 2 行变更）

## 重算+对账结果 (staging_gold_a2/recompute_full_history.py，可重跑)
- daily_rows=3184（2013-07-29~2026-08-31，含 8/31 周一交易日行）
- 行为差异证明：sma200 NaN 月 缺陷=60 vs 修复=10（热身）；缺陷 NaN 且 w_true≠0 = 33 月（=R-391 污染月数）
- 新账本 shadow_nav_a2fixed.csv：157 行 2013-08-31~2026-08-31，内部 w 对账 allclose=True（157/157）
- 旧账本=缺陷语义复证：w 对账 allclose=True（157/157）
- 新旧逐月 diff：34 行进 wdiff_months.csv = 33 语义月 + 1 舍入行（2014-07-31，|Δw|≈4.6e-5 < R-391 舍入阈值 5e-5，账本 4 位小数存储所致）
- 四维（157 行同窗）：
  - 旧：终点 2.6046，ann 7.59%，vol 6.85%，MDD -5.90%，corr(a13)=0.0798
  - 新：终点 3.1707，ann 9.22%，vol 8.42%，MDD -8.09%，corr(a13)=0.0411
  - 与 R-391 反事实（2.6046→3.1707 / 7.59→9.22 / 5.90→8.09）逐位一致；vol 6.85→8.42 为新增维度
- a13 口径：results/a13x_equiv_v5h_full_nav.csv 日频 → 月末 resample → pct_change，与 gold 月 net 相关
- d_net 定义差：R-391 表2 为毛收益差 (w_true−w_applied)×gold_ret；本次为净账本差（含 mmf 腿与成本），方向一致量级略大（如 2014-09：毛 -4.89pp vs 净 -5.11pp）
- R-391 小勘误：61 NaN 月实为 60——2026-08-31 为周一交易日（腾讯有行情行），R-391 误记为周日；不影响其结论
- 账本观察（不阻塞）：生产 shadow_nav.csv 与 shadow_nav_seed.csv 字节相同（sha256 1bec...4bd），mtime=08-24 15:13 UTC，但内容含 2026-08-31 行（gold_ret +13.41%）；疑种子一次性构建后 cp -p。留阶段二复核。

## 终验与交付 (北京 2026-09-01 ~13:05)
- 生产零改动复测：shadow_nav.csv mtime 08-24 15:13:35 UTC sha 1bec…14bd ✅；paper_state.json mtime 08-31 07:40:03 UTC sha 3a31…5d91 ✅；mmf_monthly_push.csv sha a5c5…aff99 ✅（均=备份清单值）
- staging 7 文件：fix_asof.diff / recompute_full_history.py / gold_daily_used.csv / shadow_nav_a2fixed.csv / wdiff_months.csv / compare_results.json / errata_R389_L50_draft.md
- 本地镜像：work/task-0610-staging-mirror/（5 文件）
- 报告：05-量化投资/R-394-A2阶段一-asof修复与全历史重算staging.md（R-394 空闲已确认，无碰撞）；README 日志已前置
- 状态回写：pending_review
