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

### 关键脚本解剖（HP 实查）
- **risk_patrol.py**（21KB）：按 config/risk-charter.json 退出纪律章程逐规则算当前值vs阈值→ results/risk-status.json 供页面 M4.8 消费；规则三类：drawdown_circuit_breaker(HWM回撤25%→降仓至50%)、underperform_discipline(rolling_6m_excess<-10%→观察+暂停模型升级)、live_vs_backtest(live sharpe/backtest<0.5 持6月→策略失效review)；含 run_replay 2015 演练模式
- **engines_shadow_evaluate_gold.py**：读 B 影子NAV(monthly) + A 在役NAV(a13锁定) 对比 → append engines.json B条目 shadow.evals[]，维护 clean_evals/monitoring/termination；零改动原则（A/A2字节级不动）
- **a12_monthly_evaluate.sh**：A12 影子月评包装（flock 幂等+重试1次）；**L3晋升守卫：clean_evals≥required-1 时停止自动评估→出人工评审通知**；通知走 results/notifications-queue.jsonl
- **model_manager.py**（VPS镜像34KB）：旧一代模型管理层——evaluate_candidate/register_candidate/run_versioned_backtest/write_pending/merge_candidate/reject_candidate/rollback/check_degradation/action_status；维护 pending.json/factor_pool.json/switch_log.jsonl/history.jsonl
- **gen_versions_manifest.py**：读 model/registry/* + results 指标 → results/versions-manifest.json（task-0329 看板去硬编码）
- **data_validator.py** 6项校验：kline_freshness/panel_coverage/holdings_kline/price_reasonable/dividend_continuity/selection_count

## §0b 中央状态字典（合并自 registry+engines.json+manifest）
- 版本状态：backtest-only → candidate → (shadow_watch active/clean_evals N/N) → active（registry entry + main.json 同步）→ 回退 rollback（switch_log）
- 引擎状态：active / shadow / sub_engine_overlay / active_paper（gold 例）

## §证据源2：方案层既有设计提取

### R-203 五层架构（被 R-223 引用为现行）
L1 因子层(72因子字典+IC/ICIR) → L2 选股层(三重gate+WF) → L3 择时层 → L4 模拟盘(paper cron全自动) → L5 进化闭环

### R-223（流程总纲，当时评分制未实施；现代码已升级为 SCORED）
一轮迭代生命周期六环节：①候选设计(parent只改一维度,g5预埋,先算通过线,ext runner源码字符串插入引擎零改动) ②回测新基建(全量池含退市+成本v2+一字板不可成交+AUDIT_LOCK_END=2024-06-30+ST区间表,full+locked双窗口) ③等价校验EQUIV(patch全关复跑parent逐位一致diffs={}才挂新分支) ④门禁评估/评分→PASS自动activate(R220#8移除人工确认) ⑤记录规范(decision-log.jsonl trigger/action/backup/params/rollback_condition/expected_impact/phash/data_snapshot + experiment-ledger.jsonl experiment_id=IT-批次-序号) ⑥rollback安全网(冻结registry/{version}.main.json.snapshot字节快照)
口径：locked=2006-01-01~2024-06-30(18.48y/222调仓,audit_lock.py统一clamp)；OOS split=2021-01；DSR n_trials跨批累计防多重检验

### R-206 模块编号体系（五Tab+版本体系v4）
- Tab数据：M1.1数据健康看板 M1.6数据资产盘点
- Tab因子：M1.1(重复列出!) M1.2因子注册表 M1.3在役IC监控 M1.4相关性热力图 M1.5月度体检
- Tab模型：M2.1当前生效总览卡 M2.2选股模型卡 M2.3择时模型卡 M2.4仓位系数图 M2.5决策时间线 M2.6Pending确认卡(人工决策点——R220后已过时) M2.7想法池 M2.8生命周期进化历史 M2.9试验台账
- Tab回测：M3.0版本绑定器+四层归因链 M3.1对照卡 M3.2净值对比 M3.3分年度 M3.4危机段回撤 M3.5WF样本外 M3.6历代最优对比 M3.7报告库 M3.8DSR校准曲线
- Tab模拟实盘：M4.1净值曲线 M4.2持仓 M4.3交易记录 M4.4运行状态条 M4.5运行版本卡 M4.6月度复盘入口 M4.7微盘风控卡 M4.8退出纪律卡
- ⚠️设计文档内部即有重复编号：M1.1 同时挂在Tab1与Tab2下
- v4后端版本体系：「三张皮」问题(main.json/pending/R-report各说各话)→版本对象Versioned Model Object+registry五操作(bootstrap/fork/backtest/evaluate/activate)+防漂移校验(drift signature/phash)

### R-320 抽象合并精简方案（task-0498，已有完整重复矩阵 D1-D11）
D1 模型/版本展示两套UI(死loadModelsQuant L11377 vs v5model L9658)；D2 回测归因两套(死renderBtlc* vs v5btlc)；D3 指标采集双通道(collect-metrics push vs pull-hp-metrics 写同一metrics.db)；D4 结果同步三套(auto_sync_notify在用,sync_to_vps.sh孤儿,hp_api_server /sync无调用方)；D5 跨机动作编排两套均无人消费(quant/action队列+hp_api_server /run)；D6 因子进化双cron并行(p3_3_evolution_standalone 939行旧 vs evolution_pipeline.py registry版)；D7 paper_engine vs paper_engine_gold 有意隔离建议抽公共层；D8 影子净值双路由(engines/:id/shadow-nav L3800 vs engines/shadow-nav L3756)+生产者×2(_gold在用,_append孤儿)；D9 报告库双层死；D10 factor_catalog v1/v2/v3三代并存(L1862-1864降级链)；D11 主机监控SSH实时vs metrics.db历史
死码清单：29后端路由死、UI死树L11377-12836+14029(-1500行)、HP孤儿脚本107/182(含evolution_engine/evolution_review被pipeline替代,risk_control.py被paper_engine内联替代,a12_rot_engine?,4×iter2_evolution,4×macro_timing_layer…)
分期：P0清死码/P1通道收敛/P2抽象重构(quant_common.py公共层,v5组件化)

### R-321 前端可视化精简（活UI模块全景+信息重叠矩阵）
六Tab活UI模块带行号：v5model(M1版本选择器/M2头卡/M3指标卡×6/M4解释三层卡/M5仓位图) v5btlc(B1引擎评估徽标/B2影子对比图/B3F6组合图/B4版本选择器/B5指标卡×6/B6策略vs基准净值/B7全版本排行/B8引擎生命周期面板) v5hist(H1分页列表/H2legacy开关/H3详情抽屉含Gate评估区) data(D1健康校验+PIT等4卡) factor(F1类型栏/F2注册表14列+36月IC/F3在役IC监控/F4相关性簇) paper(P0一致性徽标/P1策略描述/P2指标卡/P3运行状态条/P4净值+仓位双轴/P5跨引擎影子卡/P6持仓可解释/P7交易记录/P8运行版本卡/P9微盘拥挤度/P10退出纪律/P11参数&采纳因子)；全局横件 quantConsistDot(L7416)+quantFreshness(L7417)
信息重复矩阵（活UI）：
- 净值曲线类：A引擎回测净值3处活(B6主图/B3 F6 a_alone/P5 parent线)+死岛2处；gold影子净值3处活(B2/B3 gold_alone/P5)；A2影子2处；指数叠加2处(+死岛2处)；paper实际净值仅P4一处
- 指标卡类：同源指标数字≥9渲染点(v5MetricCardsHtml组件渲染点M3/B5/H3×2×6卡+B1徽标行+F6脚注+B7排行4列+H1行内+B8台账)，B1的A类回退指标与M3/B5完全同值=最高优先级去重点
- 影子观察进度clean_evals 2处(B8版本级lifecycle.shadow_watch L12963 vs P5引擎级engines.evals L13560)，粒度不同建议保留两级
- 版本列表3处非实质重复/引擎列表2处视角不同保留/单值徽章2处语义不同保留
- 无重复：持仓仅P6/交易仅P7
- 跨Tab端点重复拉取6组(registry/active-curves/engines/version-options/shadow-nav/data-health)
- 死岛复活结论：无高优复活项；DSR折扣曲线是硬编码假数据(L12806-12816)；五门禁面板读8月16日中性态假数据；verdict/gate核心信息已在H3 Gate评估区呈现
