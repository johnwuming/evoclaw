# task-0612 过程笔记 — A2 阶段二：清洁账本发布+BFF 刷新+0608 并入+0609 通知

## 输入与路径（开工前核实）
- staging 产物：HP ~/quant-evolve/output/staging_gold_a2/（7 文件）；本地镜像 shared/results/work/task-0610-staging-mirror/（5 文件）
- 生产账本：HP ~/quant-evolve/results/engines/gold/shadow_nav.csv（旧 sha256=1bec2035...49a2814bd，157 行，2026-08 行为激活日 stub px 9.564）
- paper_state.json（内嵌 audit，无独立 audit 文件）：HP 同目录
- 预期发布 diff（R-394 阶段一定义）：wdiff 34 行=33 语义月+1 舍入行（2014-07-31 |Δw|≈4.6e-5）；另有 2026-08-31 行 stub 修正（gold_ret +13.412%→+8.324%，px 9.564→9.135 月末值）——staging a2fixed 已含该修正，wdiff 不含此行（w 两版均 0）
- BFF/看板消费链（已实查）：HP 账本 →（auto_sync 每 30 分 rsync）→ VPS 镜像 /root/.openclaw/workspace-quant/results/engines/gold/shadow_nav.csv → agent-dashboard:8055 /api/quant/engines/gold_trend_sma200/shadow-nav；当前镜像仍旧账本（157 点 nav 2.60456，末行 ret 0.13412）
- 已知不刷新项（超范围，报告注明）：quant-bff live/data/nav_curves.authoritative.csv 的 gold 列（vC-0 权威展示 58/42 双腿链，R-379 冻结口径）与考核链仍消费旧数据，需另行批准后重建

## 执行日志（边查边写）

### [北京 17:3x] 前置自检不通过 → 全程零写入终态（阻塞）
- 自检项（任务书硬红线）：open.month==2026-09 且 last_signal==2026-08-31 → **实际 open.month=2026-08 / last_signal=2026-07-31 / audit_len=1**
- 根因：cmd_daily 滚动条件=最新 bar 月份≠open.month；09-01 15:40（北京）cron 时数据源最新 bar=08-31（同月，仅补 mark px=9.135），未触发 close_and_roll。9 月信号最早 09-02 15:40 cron 落盘
- 影响：①0608 更正事件无对象（9 月 NaN 记录未存在）②账本发布不做（发布应在引擎状态一致窗口进行，避免发布后次日滚动事件交错）
- 零写入清单：生产 shadow_nav.csv（sha 1bec2035...49a2814bd 未动）、paper_state.json（be9e30f1... 未动）、registry/paper_engine/crontab 未动、staging 未动
- staging 产物就绪度复确认（只读）：HP output/staging_gold_a2/shadow_nav_a2fixed.csv sha256 50afd135...a459ead，158 行（含表头），列序与生产一致（month,w_applied,gold_ret,mmf_ret,gross,net,nav）
- 重派建议（供主 agent）：09-02 15:45 北京后重跑同一任务书；预期届时 open.month=2026-09、last_signal=2026-08-31、audit_len=2（+month_close+rebalance）；发布 diff 预期不变（wdiff 34 行+2026-08 stub 行 gold_ret 13.412%→8.324%）；0608 更正事件仍按 9.135 追加（audit_len 2→3）
- BFF 链路勘察结论（已完成，只读）：agent-dashboard:8055 /api/quant/engines/gold_trend_sma200/shadow-nav ← VPS 镜像 workspace-quant/results/engines/gold/shadow_nav.csv ← auto_sync(*/30 cron) ← HP；当前镜像仍旧账本（157 点 nav 2.60456/末行 ret 0.13412）；发布后刷新=触发同源同步+curl 抽验 nav≈3.17068；quant-bff(8180) 不直接消费 gold 账本（config.goldShadowNavPath 为占位无引用）；vC-0 权威曲线 gold 列与考核链为旧数据消费方，重建成独立审批事项

### [北京 09-02 16:07] 阶段二重派执行·前置自检再不过 → 零写入阻塞终态（第二次）
- 自检实测（16:07 SSH 直读）：open_month=**2026-08**（要求 2026-09）✗；last_signal=**2026-07-31**（要求 2026-08-31）✗；audit_len=**1**（要求 2）✗；paper_state sha=be9e30f1...adeb6 与 09-01 基线一致；updated_at=2026-09-01T07:40:03+00:00（09-02 run 未写入任何状态）
- 新根因（与 09-01 不同：本次 cron 确实触发了但 run 失败）：log mtime=2026-09-02 07:40:32 UTC（=北京 15:40 准点）；log 末尾 Traceback → urllib/request.py → ssl.py read → **TimeoutError: The read operation timed out**——数据源 HTTPS 拉取超时，run 异常终止于拉数阶段（业务日志末行仍为 09-01 写入的 `mark 2026-08-31: px=9.1350`，09-02 run 未产出任何业务行），未走到 close_and_roll
- 行数口径备注：本次实测生产 shadow_nav.csv=158 行、staging=158 行（python splitlines 计数），两者 sha 均与基线一致（1bec2035.../50afd135...）；此前笔记「生产 157 行」疑为 wc -l 与末行换行符口径差异；重派执行 diff 校验时以实际 diff 输出行为权威
- 零写入清单（实测前后 sha 一致）：生产 shadow_nav.csv=1bec2035...49a2814bd 未动、paper_state.json=be9e30f1...adeb6 未动、staging=50afd135...a459ead 未动、registry/paper_engine/crontab 未动、无备份文件产生、发布与 BFF 刷新未做
- 重派建议（供主 agent）：下一次窗口=北京 09-03（周四）15:40 cron 后；但 TimeoutError 若为数据源持续故障则 cron 仍会失败——建议重派前先只读探测数据源连通性（若需手动跑一次 `--action daily` 属引擎写入动作，须用户批准后另派）；触发条件与发布 diff 预期均不变（wdiff 34 行+stub 行 13.412%→8.324%；audit 2→3；事件价 9.135）
- R-395 已按阻塞终态落稿（记录两次阻塞与根因链），验收以本笔记+实测 sha 为准
