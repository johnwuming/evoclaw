# task-0394 notes: a9_ranksum_raw registry 写入 + 激活

## 进度
- [ ] HP registry schema/score 数据勘察
- [ ] 备份 registry 目录
- [ ] 写 candidate 条目
- [ ] activate + 三处验证
- [ ] 回滚路径文档化

## 勘察结论（2026-08-19 12:3x）
- schema 样本 v5h_xsub.json（3000B）：version_id/status/created_at/main_alias/selection{strategy,params,factors}/timing/data_snapshot{}/code_ref/backtest_refs{endtoend,baseline,metrics,metrics_full,eval_window,snapshot_hash,stale_snapshot,backtested_at}/gate{...}/provenance/activated_at
- a13_score_summary.json: top1=a9_ranksum_raw score=0.867（p1.0/dsr0.999/oos_calmar0.7844/oos_sharpe0.9322/is满/dd0.65/corr0.3755/logic1.0）stat_warn=false flags=[] rank_in_pool=1 n_trials=91
- gates: g1 ICIR_IS 1.4651 PASS / g2 ICIR_OOS 1.4298 p=0.4033 PASS / g3 max_corr 0.6249(amt20,circ_mv) PASS / g4 DSR 0.9999 PASS / g5 PASS / g6 N/A(D-20260819-G6DEL 禁用, mdd恶化3.75pp仅入评分)
- holdout(a13): ann 25.84% mdd -16.13% det_pp -17.42 pass=true (n_days 517)
- 回测产物: results/a9_ranksum_raw_{locked,full}_{nav,metrics,...}.csv/json (2026-08-17 11:10)
  - locked: ann 21.76% mdd -33.55% sharpe 1.3435 calmar 0.6485 years 18.48 reb 222 avg_hold 19.94 turnover 0.4661 cum 37.02 win 0.6516 (2006-01-04~2024-06-28)
  - full: ann 22.16% mdd -33.55% sharpe 1.3624 calmar 0.6605 years 20.61 reb 248 turnover 0.4582 cum 60.87 win 0.6559 (~2026-08-14)
  - run config: sort=ext ext_mode=ranksum ext_specs=[('log_mv',1.0,-1),('amt20',1.0,-1),('pb_inv',0.7,1.0),('roe',0.3,1.0)] ext_filter_all=1 raw_universe=1 e1_guard=1 xsub_days=365 n_hold=20 cost v2 limit_board on
  - 代码: scripts/a9_sel.py L133 + a9_common.py(A9 patch: raw_universe/ranksum ext 排序) + a13_run.py S1 equiv 复检通过
- ⚠️ 发现1(兼容性): scripts/paper_engine.py 选股仍是旧实现(sort=ext→按 circ_mv 单因子排序+amt20过滤)，不识别 ext_mode/ext_specs/raw_universe → live 引擎尚未实现 ranksum 选股。
  缓解: rebalance cron 自 2026-08-16 起 #PAUSED（仅 daily/validate 在跑），无近期自动换仓风险；需后续任务给 paper_engine 适配 A9 patch（本任务禁改引擎）。
- ⚠️ 发现2(工具限制): evolution_pipeline find_active()/status 只 glob v*.json → 非 v 前缀条目(a12_s2_reb 先例)不出现在 status 列表；a9_ranksum_raw.json 同样不会列出。
  status 另有预存 bug: 台账统计行 KeyError 'type'（与本任务无关，激活前已存在）。真实验证以 main.json version + registry json status + decision-log 为准。
- activate 语义(_do_activate): 旧active→sota(旧sota→retired), 目标→active+activated_at, 冻结 main.json 字节快照, 写 switch_log/history/decision-log(自动), rollback_condition 自动带 --to 旧版本
- rollback 语义: 存在 {to}.main.json.snapshot → 字节级还原 main.json + 状态翻转 + decision-log；确切命令见下
