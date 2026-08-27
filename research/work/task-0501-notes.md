# task-0501 阶段A证据收集笔记（边查边写）

任务：量化系统「一轮迭代」全流程节点化分析——取证落盘
日期：2026-08-27
状态：收集中

---

## §0 证据源索引（持续更新）

- versions-manifest.json：1975 个同步文件所在目录 04-投资研究/，121KB，generated_at=2026-08-27T01:00:02，active=a13_rsraw_e1f10dz，结构 {generated_at, active, versions:[{version_id, strategy_prefix, status, strategy, registered_at, windows:{full:...}}]}
- 05-量化投资/ 目录：R-195 ~ R-321+ 方案报告

---

### 同步机制与目录事实（VPS 侧）
- VPS crontab：*/30 auto_sync_notify.py（增量）、0 3 * * * full-sync；脚本 /root/.openclaw/workspace-quant/scripts/auto_sync_notify.py，rsync HP:10.12.192.174 result_dir → VPS shared/results/04-投资研究/（include 白名单含 versions-manifest.json、risk-status.json、crowding-indicators.json、baseline-paper-*、engines/ 等）
- notify_hub.py（VPS）：监视 results/risk-status.json（新 generated_at→红黄告警）+ crowding-indicators.json（latest_date 新且 flag=red→橙色告警）；即通知层生产者=HP，消费者=VPS notify_hub
- 注释指明生产者：risk-status.json ← risk_patrol（退出纪律/风控巡检）；crowding-indicators.json ← collect_crowding（微盘拥挤度）。这两个脚本不在 VPS 镜像（镜像停 08-15），需 SSH 确认
- VPS 镜像 /root/.openclaw/workspace-quant = HP ~/quant-evolve 的开发副本/旧同步：scripts/ 143 py，mtimes 08-09~08-15
- 最新结果文件（04-投资研究）：risk-status.json generated_at=2026-08-26 16:45:02 charter_version=1.0 overall_status=green 含 nav_sources(rules引用 baseline-paper-nav.csv + strategy_track_record)、rules(drawdown_circuit_breaker.level1_cut_half 等)、crowding_reference(micro_turnover_share red)
- paper-state.json：基线模拟盘 cash/holdings/model_version=a13_rsraw_e1f10dz last_daily=2026-08-25 updated=08-26T16:30
- engines/gold/paper_state.json：engine_id=gold_trend_sma200 status=active_paper task_ref=task-0485/R-307 activation.approved_by=user(微信主会话 影子期豁免)；frozen_form{sma_n200,vol_n60,vol_target0.1,cost,freq monthly}; shadow_nav.csv 承载157月模拟史; mmf 000198 月度推仓
- model/main.json：active 版本全参数（a13_rsraw_e1f10dz, ext_specs ranksum log_mv/amt20/pb_inv/roe, timing q3z×EW-trend overlay, metrics annual 22.02% dd -33.55% sharpe 1.356）
- model/registry/engines.json（14KB schema_v1）：中央引擎注册表，每引擎{engine_id,name,status,layer1{registry{hp_dir,entry,version_line},nav_source{kind,path_hp,frequency,sync},signal_desc,timing_internal},layer3{tabs[],api_prefix},shadow{mode,since,nav_path,required_clean_evals},audit{created_at/by,changes[]}}；A=微盘在役(active)，A2=T4拥挤度防御叠加臂 sub_engine_overlay status=shadow w=0.5 nav_source=monthly_shadow_script results/engines/a2/shadow_nav.csv
- model/registry/ 目录 74 文件：main.json.snapshot ×N（版本切换留档）+ 各版本条目 json；model/ 下 switch_log.jsonl、decision-log.jsonl、pending.json、rejected_last.json、candidates/、scoring_v12_frozen.json、history.jsonl、factor_pool.json、sota.json、registry_backup_*.tar.gz ×7+
- versions-manifest.json：118 版本，status ∈ {active, candidate, backtest-only}；candidate=a12_s2_reb, a14_crowdf2, a15_csad_resid

## §1-HP 证据源1：HP 真实 crontab（2026-08-27 实查，noname@10.12.192.174:2222）

| cron(HP本地) | 脚本 | 角色 |
|---|---|---|
| 0 20 * * 0 | refresh_data.py | 周度数据刷新 |
| 0 2 1,15 * * | p3_3_evolution_standalone.py --rounds 5 | 每月1/15号进化轮 |
| 30 16 * * 1-5 | paper_engine.py --action daily | 每日净值 |
| 0 15 * * 1-5 | paper_engine.py --action rebalance --check-month-start | 月度调仓 |
| 0 20 * * 0 | paper_engine.py --action validate | 周日6项数据校验 |
| * * * * * | collect-metrics.sh → VPS:8055 | HP指标采集上报 |
| 30 6 * * 0 | fetch_valuation_data.py | 择时层估值数据周更 |
| **45 16 * * 1-5** | risk_patrol.py | risk-status.json 生产者（退出纪律/风控巡检）|
| 0 7 * * 0 | collect_crowding.py | crowding-indicators.json 生产者 |
| **0 9 * * 6** | evolution_pipeline.py cycle | 七步进化编排（周六09:00）|
| 10 * * * * | notify_hub.py（HP侧每小时）+VPS侧也有 | 双端通知 |
| 0 6 1 * * | w6_collect_delisted.py | W6退市股月采 |
| */5 * * * * | heartbeat_selfheal.sh；@reboot reboot_autostart.sh | 自愈 |
| 10 17 2 * * | a12_monthly_evaluate.sh | A12月评 |
| 5 9 3 * * | a10_monthly_monitor.sh | A10月监控 |
| 0 18 * * 1-5 | cron_qfq_daily.py；周日 collect_qfq_baostock --mode init + rebuild_merged.py | 前复权数据链 |
| 35 19 1 * * | snapshot_crowding.py | 拥挤度快照（月）|
| 38 9 3 * * | engines_shadow_nav_gold.py append | 黄金影子净值月追加 |
| **40 9 3 * *** | engines_shadow_evaluate_gold.py --mode monthly --engines model/registry/engines.json | 影子评估出影判定 |
| 40 7 * * 1-5 | paper_engine_gold.py --action daily | 黄金paper日常 |
| 0 3 * * 0 | paper_engine_gold.py --action verify | 黄金paper周校验 |

### evolution_pipeline.py（HP，80KB，核心状态机）
子命令：bootstrap/fork/backtest/evaluate/activate/rollback/override/status/cycle
- evaluate=五项数字门禁 g1_icir_is(ICIR年化≥min)/g2_icir_oos(OOS劣化单侧t检验 p>0.05)/g3_max_corr(|ρ|≤0.7)/g4_dsr(DSR≥0.95)/g5_logic(经济学逻辑文本必填)/g6_mdd_vs_parent(已禁用D-20260819-G6DEL,数值入评分)
- R220-#7：五门禁一票否决→综合评分制 SCORED+score；上岗由 score_rank_pool rank==1 决定（权重：p .175/dsr .175/oos_calmar .125/oos_sharpe .125/is_calmar .075/is_sharpe .075/dd .10/corr .10/logic .05）
- GATE_CONFIG 含 oos_split_ym=2021-01；GUARD_CORR_CONFIG 护栏vs替身豁免（D-20260819-G3CORR/G3SYM）
- _shadow_update 影子状态机：stat_warn→进影清零；clean_evals+1 满 SHADOW_CONFIG.watch_periods 出影（reg.gate.shadow_watch）
- cmd_cycle 七步：Step0 数据校验(data_validator.run_all fail-fast)→Step0b 新鲜度+漂移→Step1 快照登记→Step2 想法消化(ideas/pool.jsonl)→Step3 因子迭代(W1占位)→Step4/5 候选backtest+evaluate→Step6 通知→Step7 门禁PASS自动activate(R220移除人工确认)
