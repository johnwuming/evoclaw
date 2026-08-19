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

## 执行记录（2026-08-19 13:0x）

### 1. 备份
- `~/quant-evolve/model/registry.bak.20260819_t0394.tar.gz`（60 文件, 31719B, 激活前全目录）

### 2. registry 条目（手工写 candidate → CLI activate）
- HP `model/registry/a9_ranksum_raw.json`（4545B, schema 对齐 v5h_xsub）
- selection.params = 回测 run config 原值（ext_mode=ranksum + 4因子 specs + raw_universe=1 + e1_guard/xsub365/n_hold20）
- backtest_refs.metrics/metrics_full 全部取自 a9_ranksum_raw_{locked,full}_metrics.json 实际值（见上）
- data_snapshot: kline_as_of=2026-08-10 hash=bcf45e9...（pipeline compute_data_snapshot 现算，与 v5h 登记一致）
- params_hash=49e38fa47cfbc1c7；pipeline compute_holdout_metrics(entry)=pass:true（ann_ok, mdd det -17.42pp）
- 激活命令: `cd ~/quant-evolve && python -m scripts.evolution_pipeline activate --version a9_ranksum_raw --reason "task-0394: ...用户2026-08-19 12:27拍板激活"`
- 输出: `✅ activate: a9_ranksum_raw → active | main.json md5 1e1983f3→c58759da`

### 3. 三处验证
① HP 在役: main.json version=a9_ranksum_raw, params 已带 ranksum specs; registry a9 status=active (activated_at 2026-08-19 04:59:00 HP钟)
   - status CLI 因 v*.json glob 不列非 v 前缀条目 + 预存台账 KeyError 'type' bug（激活前即崩），故以 main.json+registry json 为准确认（见发现2）
② VPS: cron-auto-sync(*/30min) 已自动同步 → `/root/.openclaw/workspace-quant/model/registry/a9_ranksum_raw.json` status=active
   - `curl -s http://127.0.0.1:8055/api/quant/registry` → ok:true, **active_version_id: a9_ranksum_raw**, n_versions=52, v5h_xsub→sota
③ decision-log: `D-20260819-002 type=activate version=a9_ranksum_raw`（含 metrics/holdout_pass=true/gate_verdict=PASS/params_hash/rollback_condition）
   - switch_log: model_switch v5h_xsub→a9_ranksum_raw (confirmed_by evolution_pipeline:activate)
   - history.jsonl: op=activate + 完整 reason

### 4. 状态流转核验（与备份 tar diff）
- v5h_xsub.json: active→sota（保留可回退, v5h_xsub.main.json.snapshot 4175B 在位, md5 对应旧 main 1e1983f3）
- v2b_trr.json: sota→retired（pipeline 旧 sota 降级, 预期行为）
- a9_ranksum_raw.json: 新建 → active；无其他文件改动

### 5. 回滚路径（一键回退 v5h_xsub）
```
cd ~/quant-evolve && /home/noname/miniconda3/envs/quant/bin/python -m scripts.evolution_pipeline rollback --to v5h_xsub --reason "task-0394 回滚: <具体原因>"
```
- 字节级还原 main.json（md5 回到 1e1983f3）+ v5h→active/a9→sota + decision-log 自动追加 rollback 条目
- 手工兜底: tar xzf model/registry.bak.20260819_t0394.tar.gz -C model/ （覆盖整个 registry 目录恢复激活前状态）
- VPS 侧等 cron-auto-sync 下个 */30 周期自动跟上（或手动 scp model/registry/*.json + model/main.json）

### 6. Dashboard 390x844 抽查（playwright headless chromium）
- 点开量化页后 bodyScrollW=390 / docScrollW=390（无横向滚动）; #screen-quant scrollW=clientW=370
- json 长串审查: 新条目最长无空格串 43 字符（q3z(win36,...)，与在役 a12/v5h 相同字段，非新增风险）

### 7. 遗留风险（需后续任务处理，本任务禁改引擎）
- ⚠️ paper_engine.py 未实现 ranksum/raw_universe 选股（仍是 circ_mv 单因子+默认质量闸门）；rebalance cron 自 08-16 PAUSED 无近期自动换仓，但**恢复 rebalance 前必须先给引擎适配 A9 patch**，否则实盘选股与回测口径不符
- status/find_active 的 v*.json glob 不识别非 v 前缀 active（a12_s2_reb 同病）；paper_engine 防漂移 guard 因此对 a9 静默跳过（不误报也不保护）
