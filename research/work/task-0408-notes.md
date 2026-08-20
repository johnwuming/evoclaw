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
