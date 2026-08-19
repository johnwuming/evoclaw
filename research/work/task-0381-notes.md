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
