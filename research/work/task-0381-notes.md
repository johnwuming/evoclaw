# task-0381 notes：a12_s2_reb 月度 evaluate 自动推进机制设计
(2026-08-19 启动)

## 待办
- [ ] 确认报告编号空位
- [ ] 读 R-238 shadow_watch/SHADOW_CONFIG 衔接条款
- [ ] HP 调研 evolution_pipeline evaluate 是否支持轮动型
- [ ] 设计月度机制（触发/幂等/重试/通知）
- [ ] 落地脚本 + 干跑
- [ ] 写报告 + 更新 README

## 2026-08-19 20:4x 调研记录

### 1. 编号占位（已确认）
- R-244 → 04-投资研究/ZeroTier；R-246 → results 根/A10-4（task-0370）；R-245 未见于 05 目录（默认已占）；R-247 为 R-0386 预留
- **本报告占 R-248**

### 2. SHADOW_CONFIG（来源 R-241 + task-0353 notes）
- 常量：N=3 次评估窗口，holdout 2024-07 起，ann ≥ 0.60×locked，MDD ≤ locked+10pp
- 实现位置：evolution_pipeline.py（task-0353）：_seg_nav_metrics + compute_holdout_metrics + _shadow_update 状态机(gate.shadow_watch)；cmd_evaluate 晋升链 rank1→影子→holdout→activate；score_holdout 写入 gate
- task-0398 g3 护栏豁免修正已入 evolution_pipeline.py（SCORE_CONFIG v1.1 口径：排序因子/护栏登记项区分，月度IC兜底）

### 3. HP crontab 现状（2026-08-19 查）
- paper daily：`30 16 * * 1-5` paper_trade.py --action daily
- paper rebalance：`30 16 * * 1-5` cron_paper_rebalance.sh（gate 自检月首才真正调仓）
- refresh_data：周日 20:00；fetch_valuation：周日 06:30
- p3_3 evolution：每月 1/15 日 02:00
- evolution_pipeline cycle：周六 09:00
- risk_patrol：16:45；collect_crowding：周日 07:00
- 结论：月首附近负荷=1日02:00 evolution+16:30 paper；2日仅 16:30 paper 常规 → **每月2日 17:10 为低冲突窗口（任务书建议一致）**

### 4. registry 中 a12_s2_reb（2026-08-19 查）
- 位置：model/registry/a12_s2_reb.json（有 .bak-task0384-20260819）
- status=candidate；gate.shadow_watch={active:true, clean_evals:0, required:3, since:2026-08-18}（task-0379 人工登记进影）
- selection=dividend_quality_smallcap_seedB(ext low_amount, e1_guard, xsub365) ≡v5h_xsub 选股层不变；轮动在 timing 层（type=a12_rotation_overlay）
- code_ref=scripts/a12_rot_engine.py（task-0374）；backtest_refs.nav=results/a12_s2_reb_formal_full_nav.csv，endtoend=..._locked_nav.csv，metrics/calmar 全样本 0.6182
- 在役 incumbent = a9_ranksum_raw（task-0394 激活，main.json version 已指）

### 5. evolution_pipeline.py evaluate 路径确认（核心结论）
- SHADOW_CONFIG（L107）：watch_periods=3, holdout_start_ym=2024-07, ann_ratio_min=0.60, mdd_extra_pp=10
- cmd_evaluate（L1005+）：**不重跑回测**；g1/g2 ICIR 走 load_ic_monthly（selection.factors=v5h_xsub 同款，数据在）；g3 corr 已含 task-0398 护栏豁免；g4 DSR 读 endtoend nav；g5 logic 读 reg.gate.logic；g6 数值保留判定禁用；score_composite 六分项=v1.1；compute_holdout_metrics 读 backtest_refs.nav 分段算指标
- 产物：results/bt_{version}/gate-report.json + 回写 reg.gate（_shadow_update：stat_warn→清零，clean→+1，满 3 出影）
- **轮动型兼容性结论**：evaluate 全程只读 registry + nav csv + factor_ic，不依赖选股引擎入口 → a12_s2_reb 可直接被 evaluate。gap 实质在于"nav 不会自动更新到最新月"——月度机制 = 先用 a12_rot_engine 重算 nav 再 evaluate（wrapper 职责=刷新 nav + 调 evaluate，不改 evolution_pipeline.py 本体）✅ 任务书要求"不改本体"可满足
