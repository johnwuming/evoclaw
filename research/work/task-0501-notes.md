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
