# task-0597 过程笔记（R-384 研究）

任务：拆解「让组合第一次成为真的」→ 决策依据 + 实现规格，不实施。
编号：R-384（已实查，最大 R-383，R-384 空闲）。

## 实查记录

- R 号实查：`ls shared/results/05-量化投资/ | grep -oE 'R-[0-9]+' | sort | tail -5` → R-379/380/381/382/383，R-384 空闲。
- 文件大小：R-373 md 17.5KB / R-380 15.4KB / R-381 12.6KB / R-346 8.9KB / R-347 5.8KB / R-348 7.7KB / R-349 6.7KB / memory-0830 4.8KB / engines.json 3.8KB / baseline-paper-summary.json 2.5KB，均可全读。
- policy.json 位于 tools/quant-dashboard/policy.json（未读大小，读前再查）。

## 阅读要点（边读边补）

### R-380（双口径缺口归因，task-0591）
- 静态 58.03/41.97：ann 14.44% / vol 10.32% / Sharpe 1.399 / mdd −9.69%；滚动等波动 6m（band 0.02）：ann 10.12% / vol 6.64% / Sharpe 1.523 / mdd −5.71%（n=156 月，成本 0.13%×换手）。
- 收益差 4.32pp：权重水平 3.37pp（78%）+ 动态噪声 0.95pp（22%）；58/42 非全期最优（最优 wA≈0.29，ann ~11%），是定义日 2026-08-28 60d 日频快照解的 retro 展示。
- 回撤差 3.98pp：权重水平 4.86pp 变浅 − 滚动顺周期 0.88pp 变深，闭合。
- 两侧均无 DDC/vol_target 风控层（红线①核验）→「零实现」证据链的一环。
- 静态可称「设计口径/提案轨迹」，不应称权威/最优；滚动侧权威性同样未核验（同源性未归因）。

### R-381（滚动对照判定标准，task-0594）
- warmup：前 4 个月（2013-08~11）等权 50/50 fallback，与静态同起 BASE 2013-07，无区间错位；2013-12 首个非 fallback 月权重跳至 0.0026/0.9974。
- 区间对齐后缺口漂移 ≤0.07pp（ann），R-380 归因成立；对齐后滚动 Sharpe 1.430 vs 静态 1.316，Calmar 1.622 vs 1.394，滚动双优保持。
- **vol_target=8%±2pp 无文档出处**，是用户 08-30 提议语义，入 policy/policy-lint 前需用户确认。
- solver_equal_vol_v1：等波动闭式解（window_days=60/min_obs=4），定义日隐含组合波动 ≈12.90%，不瞄 vol 目标。
- 现状：gold 腿引擎有 vol_target=10%（sma200+vol_target 10%+货基）；equity 腿是 DDC（20% 回撤减半）；**组合层无 vol_target**。
- 三分标准：①波动带合规（8%±2pp，带内=滚动 6.64%，带外=静态 10.32% 超上沿 0.32pp、定义日快照 12.90% 超 2.90pp）②风险调整优性（Sharpe/Calmar 不劣）③口径纯净（PIT+成本+warmup 披露）。
- 「方向不对」一词废弃；滚动=「标注启用」候选（须先补同源性核验才能升级权威）；静态=「定义日快照 retro 展示」。
- policy.authoritative_rolling_candidate 预留位存在（R-379 预留）。

