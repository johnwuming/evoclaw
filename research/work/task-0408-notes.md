# task-0408 工作笔记：crowding 月度快照机制落地

- 日期：2026-08-21（01:39 开工）
- 任务：task-0408 / proj-0003 dev。R-250 §四结论 1a——E2 前置条件：每月锁存 crowding 状态快照，消除 qfq 全量重算漂移（R-237 风险处置）。
- 状态：2026-08-21 01:39 已 PUT task-0408 status=running（API 返回 ok）。

## 口径锁定（来源 R-250 §2.2/§2.3）

- 快照值 = crowding_history.csv 当月最后可得行的 `micro_turnover_share_roll20` 的 expanding pct（min 250 日）——与 R-250 E1 主画像口径一致。
- 残余风险背景：微盘宇宙按总市值（qfq 收盘×总股本）后 20% 划分，qfq 复权因子刷新会改写历史 → 历史值漂移。快照 = 把"当下重算出的状态"每月定格一份，未来 E2 用快照序列而非滚动重算序列。
- 快照文件：HP ~/quant-evolve/results/crowding_snapshots.csv，一行一月，append-only，同月去重。

## 现场勘查（边查边记）

（待补）
