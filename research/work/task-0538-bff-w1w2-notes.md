# task-0538 quant-bff W1-W2 过程笔记

## 已读依据（摘要）
- §3.2 账本：`events/iteration-ledger-YYYY-MM.jsonl`，行格式 `{ts,actor,event_type,target,payload}`；17 事件类型枚举；热 12 月 + gzip 冷档 `events/archive/iteration-ledger-YYYY.jsonl.gz`（只建索引不参与热重放）；flock `events/.ledger.lock`；投影=缓存带 sha256。
- §3.3：状态本体只在重放结果；启动全量重放 ≤3s、后台执行不阻塞 API；未就绪返回显式「初始化中」（不返回空数据）；sha256 不一致= reconciliation.failed。
- §3.4 契约：10 端点；本批做 health/events/migration/overview；UTC ISO8601；cursor=事件行 ts+seq；响应头 X-Ledger-Tail-Ts；BFF 只听 127.0.0.1；版本策略 /api/v1/ 前缀。
- health 契约：`{ledger_tail_ts, projection_sha256_ok, sync_lag_seconds, pending_risks{count,items[{type,ref,opened_ts}]}}`；本批加 reconciliation_ok + replay_duration_ms（增量字段）。
- overview 契约：`{nav, nav_chg_1d, mdd, drawdown_pct, active_pv{portfolio_version_id,status}, sleeves[{id,weight,nav,mdd}], last_event_ts, reconciliation_ok}`（引擎卡数据桩实现）。
- migration 契约（L191）：`{phase:"A|B|C|D", items[{id,title,state:done|doing|todo,evidence_ref}], blocking:{a1_pass,a2_pass}}`。
- events 契约：`{items:[{ts,event_type,target,actor,payload摘要}], next_cursor}`，?type=&limit=&cursor=。
- §4.3 pending_risks 口径：断路器触发中 / 对账失败未解 / 漂移连续超带 / 退役 review 中 / promotion.requested 未决。
- §4.1 四件套：SIGTERM 优雅关停 / systemd Restart=always / 单请求 5s 超时 / SQLite busy_timeout（本批用 JSON 投影简化→以「文件读+重放 5s 超时包裹」等价落实第④条）。
- 附录 13 步重放幂等伪代码：全序=文件名序+行序；幂等键 evt.seq（兜底 文件名+行号）；version.created 建对象 / promotion.executed 移 active 指针 / promotion.downgraded 回退状态位 / weight.solved、gate.evaluated、risk.action 追加明细；逐对象 sha256；tmp+rename 原子写；重读校验。

## 设计决策
- 纯 JSON 投影（不做 SQLite），投影文件 `state/projection.json`，头部 meta.hashes 三对象（registry/engines/composites）。
- 读侧共享锁：优先 fs-ext LOCK_SH；装不上则降级为带 warn 日志的 advisory shim（测试锁文件存在性）。→ 结果见下文。
- 损坏账本语义：任一行 parse 失败 → ledger_corrupted → 记 reconciliation 失败类 pending_risk → 账本派生端点（events/overview）503；health 恒 200 携带降级标志；migration 独立文件数据保持 200。
- 未就绪（首次重放完成前）：账本派生端点 503 INITIALIZING。
- 乱序 ts 行：按文件序+行序应用（13 步口径），不按 ts 重排。
- cursor 实现：`${全局序号}:${ts}`，events 倒序分页（区块④全事件倒序）。
- fixtures：good 账本覆盖全部 17 事件类型 + 1 条乱序行；corrupt 账本=good 变体插入损坏行；冷档 2024 gzip。

## 环境核验
- node v22.23.2（node:test 可用）。
- npm 装 express：待验证 → 结果见下。
