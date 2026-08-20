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
## crontab 变更（HP）

- 备份：`crontab -l > ~/crontab.backup.20260821`（31 行，4,212B）。
- 追加（仅追加，diff 确认仅 2 新行，既有 31 行零改动）：
  - `# --- task-0408 crowding 月度快照（R-250 §4.1a，锁存最近完整月，幂等 append-only）---`
  - `35 19 1 * * cd /home/noname/quant-evolve && flock -n /tmp/snapshot_crowding.lock /home/noname/miniconda3/envs/quant/bin/python scripts/snapshot_crowding.py >> /home/noname/quant-evolve/logs/snapshot_crowding.log 2>&1`
- 时点：每月 1 日 19:35（HP 本地 UTC = 北京次日 03:35），避开 HP 本地 18:00 qfq 日更与 20:00 周任务；flock 防重叠；日志 logs/snapshot_crowding.log（已由手动预跑创建，首两行见 [ok]/[skip]）。
- 预计行为：每月 1 日锁存刚结束月份的最后一个可得数据行（crowding 源为周日 07:00 周采集，故月末值通常为该月最后一个周五/交易日）；同月重复触发一律 [skip]。
- 回滚：`ssh HP 'crontab ~/crontab.backup.20260821'`（恢复 31 行）；如需彻底回退再删 scripts/snapshot_crowding.py、results/crowding_snapshots.csv、logs/snapshot_crowding.log（均为本任务新建文件，删除不影响任何既有机制）。

## 验收自检（与主 agent 复跑命令一致）

- `grep snapshot_crowding <(crontab -l)` → 1（任务行存在）；crontab 总行数 31→33，既有行 md5 语义未变（diff 仅追加）✓
- 快照文件存在，数据行数=1（2026-07），字段 9 列完整 ✓
- 幂等：直接复跑×2 + cron 原样命令（flock+重定向）复跑×1，均 [skip]，行数与 md5 不变 ✓
- py_compile COMPILE_OK；未改 registry/pipeline/paper_engine；未杀任何进程（零进程操作）✓
- cron 原样命令手动预跑成功，日志创建 ✓

## 交付物清单

- HP ~/quant-evolve/scripts/snapshot_crowding.py（5,103B，新建）
- HP ~/quant-evolve/results/crowding_snapshots.csv（810B，新建：7 注释+1 表头+1 数据行）
- HP ~/crontab.backup.20260821（4,212B，crontab 备份）+ crontab 新增 2 行（1 注释+1 任务）
- HP ~/quant-evolve/logs/snapshot_crowding.log（新建，运行日志）
- VPS 本任务笔记：shared/results/work/task-0408-notes.md；脚本底稿 /tmp/snapshot_crowding.py（VPS）

## 结论

R-250 §四结论 1a（E2 前置条件「crowding 月度快照机制」）已落地：月度 cron 锁存最近完整月的 share_roll20 主口径 expanding 分位（与 E1 画像逐字同式）+ roll3y 分位（E2 预注册口径）+ 参考列，append-only、同月幂等。首锁 2026-07，与 R-250 今晨重算值完全一致。漂移风险自本月起在月末后≤1 天内被锁定。后续 E2 预注册可直接消费 crowding_snapshots.csv（roll3y 列，60/40 阈值）。

- 状态：完成，待主 agent 独立验收。2026-08-21 01:5x（北京）
