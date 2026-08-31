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

### policy.json（tools/quant-dashboard/policy.json，3.1KB）
- metrics-display-policy@v1：只有 active_portfolio_version/benchmark 可展示绩效；引擎层禁字段 ann_return/ann_vol/sharpe/max_drawdown/nav_curve/metrics。
- caliber.authoritative=equal_vol_58_42_static_monthly，但 **authoritative_available=false**（「权威」标签已暂停）；display_name=设计口径·提案轨迹（静态 58/42 月度再平衡·无风控层）；hindsight_attribution_pending=true。
- rolling_compare 挂出：VC0_ROLLING_EQVOL_6M，ann 10.12%/vol 6.64%/sharpe 1.5233/mdd −5.71%，note「走前真解·待期限结构对齐与 hindsight 归因，未启用」。
- authoritative_rolling_candidate=rolling_equal_vol_58_42（月频适配无法锚定 dryrun 解，末端失配 26.6pp；待 HP 日频 sleeve 数据接入后升版）。
- current/authoritative curve column 均为 VC0_EQVOL_5842_M；enforcement 走 policy-lint.mjs，scope 覆盖 engines.json/BFF/performance.json/Candidates.jsx/perf-history.js。

### R-346（vC-0 快照与求解器，task-0540）
- vC-0：status=paper；equity_sleeve=a13_rsraw_e1f10dz（active）+ 腿级 DDC {dd_thresh 0.20, dd_reduce 0.5, dd_recover 0.05, t+1}；hedge_sleeve_gold=gold_trend_sma200（active_paper，2026-08-25 批准），frozen_form sma200/vol60/vol_target=0.1/月频首个交易日/货基 000198。
- **组合级 risk_control：在役宪章断路器（回撤 25% 降半/35% 清仓，config/risk-charter.json v1.0）+ vol_target: null（在役组合级未启用）**。
- capital_policy gross/net=1.0（无杠杆双腿独立链）；weighting 实况=dual_independent_paper_chains。
- solver_equal_vol_v1：w∝1/σ，闭式解；params window 60 日/年化 252/min_obs 40；再平衡带 0.02；fallback 等权+fb_* 必产事件。
- dryrun 解：w=(0.58030,0.41970)，σ_ann=(0.11113,0.15365)——**定义日短窗内 gold 波动反超 A 腿**（与全历史 A:gold≈2.5:1 相反），这就是 58/42 的来历。
- 事件账本 JSONL+flock+fsync+月滚动+sha256+seq 幂等；求解器月频调度未启用 cron（当时约束）。
- 版本迭代规程：改 solver/风控/腿 → 升 vC-0.y 子版本（parent_version 链）；协方差刷新不升版本。

### memory/2026-08-30.md
- **R-378(0589) gold 引擎核验：虚腿 by design**——paper_engine_gold.py 无下单接口，产出仅模拟账本；runtime 60/40 无黄金；R-307「激活≠真金」=有意分阶段门控；当前引擎模拟权重 w=0。
- 唯一待用户决策：黄金腿 A（纸面合成）/B（真买）/C（维持现状+标注）。
- B9(0588) 黄金卡已诚实标注（目标权重≠实际持仓）；B7(0583) policy.json+policy-lint.mjs；B8(0585) 权威口径管道上线（静态 58/42 主通道，滚动被否，policy 预留翻转位）；B10(0590) 徽标同源化+去权威标签+滚动对照挂出+lint 血缘断言；B11(0591) lint⑥重算断言+滚动四指标同构+PRD v1.5。
- 组合三层模型：构建/组合/风控（R-336/R-342/R-344）；绩效指标只有组合层有，看板不上单模型指标（用户 08-30 11:10 裁定）。

