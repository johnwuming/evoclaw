# task-0408 工作笔记：crowding 月度快照机制落地

- 日期：2026-08-21（01:39 开工）
- 任务：task-0408 / proj-0003 dev。R-250 §四结论 1a——E2 前置条件：每月锁存 crowding 状态快照，消除 qfq 全量重算漂移（R-237 风险处置）。
- 状态：2026-08-21 01:39 已 PUT task-0408 status=running（API 返回 ok）。

## 口径锁定（来源 R-250 §2.2/§2.3）

- 快照值 = crowding_history.csv 当月最后可得行的 `micro_turnover_share_roll20` 的 expanding pct（min 250 日）——与 R-250 E1 主画像口径一致。
- 残余风险背景：微盘宇宙按总市值（qfq 收盘×总股本）后 20% 划分，qfq 复权因子刷新会改写历史 → 历史值漂移。快照 = 把"当下重算出的状态"每月定格一份，未来 E2 用快照序列而非滚动重算序列。
- 快照文件：HP ~/quant-evolve/results/crowding_snapshots.csv，一行一月，append-only，同月去重。

## 现场勘查（边查边记）

1. crowding_history.csv 269,852B，9 列，最新行 2026-08-19；2026-07 有 23 行，末行 2026-07-31 share_roll20=0.0243777058358952。
2. r250_profile.py L40-42 原式确认：`shr=crow['micro_turnover_share_roll20'].dropna(); epct=shr.expanding(min_periods=250).apply(lambda x:(x[:-1]<=x[-1]).mean()*100.0, raw=True)`。快照必须逐字复刻该式（含 x[:-1] 排除自身的 PIT 形式）。
3. HP crontab 31 行（与 task-0402 先例一致）：L17 周日 07:00 collect_crowding.py（**周频采集**）；L29 工作日 18:00 qfq 日更；L31 周日 18:00 qfq init+rebuild；另有 20:00 周任务。logs/ 目录存在；quant env pandas 2.3.3。
4. cron 时点决策：每月 1 日 19:35（`35 19 1 * *`）——在 18:00 qfq 之后、20:00 周任务之前，快照脚本只读 crowding_history.csv（周日更新，工作日稳定），无写冲突；flock 防重叠。
5. 快照规则决策：锁「最近一个完整月」的最后一个可得数据行——若数据末行在生成时刻所在月（当月未走完）则回退到上一有数据月。首次运行（08-21）→ 锁 2026-07（data date 2026-07-31）；未来每月 1 日 cron → 锁刚结束的月。不锁当月部分值，避免「部分月被永久锁死」缺陷。
6. 列设计：month,date,share_roll20,share_roll20_epct,share_roll20_roll3y_pct,micro_turnover_share,micro_turnover_pct60,n_hist,generated_at。roll3y(756d,min250) 列是 E2 预注册指定口径（R-250 §四1b），必须一并锁存。

## 实施

1. 脚本落盘：HP ~/quant-evolve/scripts/snapshot_crowding.py（5,103B，VPS 本地底稿 /tmp/snapshot_crowding.py）。scp 无 SFTP 子系统，改用 cat 管道传输。py_compile COMPILE_OK。
2. 首次运行：`[ok] locked month 2026-07 (data date 2026-07-31, epct=1.3609, roll3y=3.3113)`。
3. 快照文件 results/crowding_snapshots.csv：7 行 # 注释（口径元数据）+ 1 表头 + 1 数据行；行：2026-07,2026-07-31,share_roll20=0.0243777058,epct=1.3609,roll3y=3.3113,pct60=51.6667,n_hist=1838,generated_at=2026-08-20 17:42:23。
4. 幂等验证：同月复跑两次均 `[skip]`，数据行数=1，md5 前后一致（1886e0bdc156babd8b27e3adf736f769）→ 不增行、不覆盖 ✓。
5. 历史一致性抽查（质量要求 5）：快照 2026-07 行 vs crowding_history.csv 当前的 7 月末行（同时刻同文件）→ share_roll20 0.0243777058358952 完全一致；epct 1.3609 与 R-250 今晨 r250_profile.py 算出的 crowding_monthly.csv 2026-07 行 epct=1.3609145345672293 完全一致。关系结论：快照=锁存时点的当前重算值，一致；「漂移」是指未来 qfq 刷新后重算历史会变，快照从此不再变——这正是机制目的。注：2026-07 值在 07-31→08-21 间可能已漂移过（无历史备份可验证，R-250 §2.2 已披露），从本月起新月度在月末后≤1 天内锁定。
6. HP 系统时钟为 UTC（generated_at 2026-08-20 17:42 UTC = 北京 08-21 01:42）；cron 表这式按 HP 本地时间评估，19:35 HP-UTC = 北京 03:35 次日——避开了 HP 本地 18:00 qfq 行与全部既有行时点。
