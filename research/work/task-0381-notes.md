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

### 6. 引擎与底表调研（2026-08-19 20:5x）
- a12_rot_engine.py（404 行）：一次性全量脚本（无 CLI 参数），跑四方案+敏感性；**实测 131.5s 完成**（logs/a12_rot_engine.log）；输出覆盖 timing_v2/a12_stats.json + a12_navs.csv + a12_pos_micro.csv；内置 anchor 对拍（vs a9_timing_MA15_on_f0_nav）
- 底表依赖（read_parquet，非引擎生成）：
  - timing_v2/a12_rot_series.parquet（RS/Mlarge/micro_state_ma60）= task-0365 VPS 侧 /root/sr365/（sr365_compute.py）基于 qfq 池计算 → **非 HP 常态化管线**
  - timing_v2/signal_series.parquet（flag_REB_bottom/flag_C_crisis）= tv2_compute_v2.py（HP results/timing_v2 内有 17KB 计算脚本）
- a12_formal_products.py（task-0384）：一次性脚本，从 timing_v2 复制 S2_reb 列到 results/a12_s2_reb_formal_{full,locked}_nav.csv，逐位校验；registry backtest_refs 指向 formal 文件
- evolution_pipeline.py evaluate CLI：`--version --oos-start`，**无 --dry-run**；副作用=写 results/bt_{v}/gate-report.json + 回写 reg.gate + decision_log + 满足条件时 _do_activate（自动上岗）
- **自动上岗风险**：clean_evals 推满 required(3) 出影后，若 rank=1 且 holdout pass=True → _do_activate 改 main.json。registry note 明示"观察期满由人工确认" → wrapper 必须**预检查拦截**：clean_evals >= required-1 时不自动 evaluate，改出人工评审通知
- **stat_warn 语义**（_shadow_update）：True→进影/清零；False 且在影→+1。stat_warn = g2 p<0.01 或 DSR<0.90（SCORE_CONFIG.stat_warn）

### 7. 机制设计定稿（三层）
- L1 评估层（本任务落地自动化）：evolution_pipeline.py evaluate --version a12_s2_reb；IC 底表随半月度 evolution（每月1/15 02:00）自动更新 → g1/g2/g3/n_trials 每月有增量；g4/holdout 基于 nav（静态则不变）
- L2 nav 刷新层（接口预留+检测式降级）：重跑 a12_rot_engine.py（131s）→ 重算 formal nav。**前置依赖**：a12_rot_series.parquet 需重新生成（当前为 VPS sr365 调研产物，非 HP 常态管线）→ wrapper 检测 parquet mtime，未更新则跳过引擎重跑并在结果中降级标注
- L3 晋升守卫：出影前最后一步（clean_evals>=2）停止自动评估 → 通知人工评审（符合"观察期满由人工确认"）
- cron 建议：`10 17 2 * *`（每月 2 日 17:10）：避开月首调仓（月首交易日 16:30 paper）与 1/15 日 02:00 evolution；月度 evaluate 与半月进化错开

### 8. 落地与验证结果（20:5x）
- HP scripts/a12_monthly_evaluate.sh（flock+重试1次+exit42归一）+ scripts/a12_shadow_eval.py（预检查/幂等/L3守卫/dry-run备份恢复/通知）传输成功（scp -O，HP sshd 无 sftp）
- bash -n + py_compile 全过
- 干跑 --dry-run：evaluate 跑通 rank=8/池8 score=0.6666 holdout_ann=0.2538 pass=True；registry/decision-log md5 恢复一致；通知写入 notifications-queue.jsonl；rc=0
- 补丁：dry-run 备份清单补 experiment-ledger.jsonl（干跑发现 evaluate 会写台账 ev_a12_s2_reb_20260819_1346）
- 幂等验证：模拟 last_eval_ym=2026-08 → live 模式正确跳过；registry md5 全程 2be515e74b7d 未变
- 报告 R-248 已写（5031B）；README 顶部变更记录已加；cron 建议行：10 17 2 * *（HP 本地，待用户批）
