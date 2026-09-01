# R-389 L50 errata 草稿（task-0610 阶段一产出，待阶段二统一发布，勿直接改 R-389）

**对象**：R-389《两腿基线694pp分歧溯源与insufficient_obs条款》L50（§4「主因机制」段）。
**触发**：R-391 A2 修复实施（task-0610 阶段一）：gold 引擎两文件 asof/ffill 语义修复，全历史重算落盘 `output/staging_gold_a2/shadow_nav_a2fixed.csv`（157 行，内部 w 对账 157/157 一致）。

**原文（缺陷语义账本）**：
> …而 gold 引擎当月 w_applied=0（信号空仓持货基），月收益 **+0.04%**，接住了组合——展示口径因此最深处仅 −9.67%。两条金腿逐月收益差 >2pp 的月份多达 54/156，是系统性实现差异而非单月噪声。

**更正（修复语义重算，2026-06 账本行）**：
- w_applied：0 → **0.3171**（2026-05-29 月末信号，asof 修复后不再 NaN 归零）
- gold 引擎 6 月净收益：+0.04% → **−3.40%**（净差 −3.45pp，含成本；gross −3.4467pp→net −3.4049%，见 wdiff_months.csv）
- 结论修正：修复后引擎当月仅**部分避险**（31.7% 仓位趋势腿、68.3% 货基），并非完全「接住」组合；展示口径一线最深回撤将**变深**，具体值待阶段二 nav_curves 管线重刷新后定。
- 连带：gold 引擎净值 MDD −5.90% → −8.09%（本次重算逐位复现 R-391 反事实：终点 2.6046→3.1707、ann 7.59→9.22%）；「逐月差 >2pp 的月份 54/156」需以修复后账本重算（33 个语义变更月，方向不预设）。

**波及**：R-380 / R-386 / R-388 中引用 gold 引擎净值/收益/回撤的表述，阶段二以独立对照报告统一标注。
**依据文件**：`output/staging_gold_a2/{compare_results.json, wdiff_months.csv, shadow_nav_a2fixed.csv, fix_asof.diff}`；复跑：`/home/noname/miniconda3/envs/quant/bin/python output/staging_gold_a2/recompute_full_history.py`（HP ~/quant-evolve）。
