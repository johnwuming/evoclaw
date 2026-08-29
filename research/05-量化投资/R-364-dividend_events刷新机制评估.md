# R-364 — dividend_events 数据刷新机制评估（方案，未实施）

- 任务：task-0551 ｜ 日期：2026-08-29 ｜ 类型：纯方案零改动（HP 只读侦察，未执行 prep、未改任何文件）
- 结论先行：**推荐「修刷新脚本 + C（引擎前置新鲜度闸）+ D（账本侧告警）」组合，B（独立每日 cron）作为 9 月分红季的兜底增强，需用户批准 crontab 后再加**。A（并入 auto_sync）不适配，理由见 §4。

---

## 1. 现状盘点（数字均可溯源，见 §6）

### 1.1 数据源 freshness
`~/quant-evolve/data/derived/dividend_events.parquet`：
- 48,081 行，列 `[code, ex_date, cash_per_share, period]`，cash_per_share 无缺失
- ex_date 覆盖 **2005-09-09 → 2026-08-21**；period 覆盖 20050630 → 20260630
- 文件 mtime **2026-08-13 03:30**（截至 2026-08-29 已 16 天未刷新）
- 数据生成日（8/13）能看到未来已公告事件，故 ex_date 上限（8/21）晚于 mtime；**8/13 之后公告的分红（含全部中报派息落地）不在数据内**

### 1.2 供给端：prep_dividend_roa --only div（scripts/prep_dividend_roa.py，16.7KB）
- 数据源：akshare `stock_fhps_em(date=报告期末)`，按报告期批量拉全市场分红方案；周期列表 2005→2026 每年 1231+0630 共约 44 期，脚本内无 sleep
- `--only div` → 仅执行 `fetch_dividend_events(resume=True)`（L103、L384-390）；无 `--force` 类参数
- **断点续传是 period 级**：`done_dates = set(已有 parquet 的 period)`，循环直接跳过已缓存报告期（L112-135）
- **关键缺陷：当前手动重跑已是 no-op**。20251231 与 20260630 两期均已缓存，重跑只补拉一个空的 20261231（未来期，返回空），**抓不到同报告期内后公告的任何分红**。mtime 8/13 + ex_date 上限 8/21 与该机制完全吻合。
- 幂等性：period 级幂等成立（重跑不重复），但对增量刷新是反作用
- 耗时：44 次 akshare 批量请求、无 sleep，估计 1-3 分钟（脚本无日志，此为估计值）；依赖外网东财接口，失败进 fail 列表
- 附带事实：2026-05 以来分红事件 3,470 条（与 task-0550 笔记口径一致）

### 1.3 消费端：paper_engine（task-0546 接线）
- `credit_dividends(state, upto_date)`（L1068）读同一 parquet，按 `(last_div_date, upto_date]` 窗口过滤 ex_date（L1093-1094），水位幂等，入账写 `results/paper-div-ledger.csv`
- 语义要点：**晚到事件（ex_date ≤ 已推进水位）会被窗口过滤永久跳过**——数据缺一天、漏账就是永久的；parquet 读失败时水位不推进（好），但「文件存在、内容缺事件」引擎无法感知（盲区）
- 当前运行态：`paper-state.json` 显示 8 只持仓（300824/002107/603551/000848/300009/600867/002027/601600），水位 last_div_date=2026-08-28；**paper-div-ledger.csv 尚不存在（接线后零入账）**
- 持仓 2026 年 ex_date 全部 ≤8/21（002107 最近 8/18），当前数据覆盖内，**尚无实际漏账发生**

### 1.4 紧迫性：9 月窗口真实存在
- A 股分红双峰：年报派息 5-7 月（2026-06 单月 1,721 条），**中报派息 9-10 月（2025-09=397 条、2025-10=287 条）**
- 中报 8/31 披露完毕，其派息除息日集中在 9-10 月——**全部在 8/13 快照之外**；8 只持仓若无脑等下一次手动刷新（且该刷新本身是 no-op），9 月起任何持仓跨除息日即静默漏账

## 2. 既有通道事实（选项评估前提）
- HP crontab（39 行）：16:30 工作日 paper daily、15:00 工作日 rebalance、周日 20:00 refresh_data、工作日 18:00 qfq 日更等，**无任何分红数据任务**
- 「auto_sync 30min」在 **VPS 侧** crontab：`auto_sync_notify.py --job-name cron-auto-sync`，方向是 **HP→VPS 结果 rsync 回传+通知**，不是给 HP 喂数据的通道

## 3. 选项评估

| 选项 | 做法 | 成本 | 延迟 | 风险/依赖 | 判定 |
|---|---|---|---|---|---|
| A 并入 auto_sync 通道 | 30min 一轮 | 高频无意义 | 小 | 方向不符（HP→VPS）；分红数据日频足够；44 请求×288 轮/日会浪肤 akshare 接口 | **不适配，否** |
| B 独立低频 cron | HP crontab 加每日一条（如 17:00 收盘后） | 改脚本+加 1 行 cron | ≤1 交易日 | **需用户批准 crontab 变更**；akshare 接口偶发失败需 fail 告警 | **推荐（分红季兜底）** |
| C 引擎前置新鲜度闸 | paper daily 前置检查：parquet 覆盖上限（max ex_date）落后当前日期 N 天即刷新或告警 | 改 engine 侧少量代码；复用 prep | 随 daily 节奏（16:30） | 改 paper_engine 需谨慎走验证；改动范围小 | **推荐（必做）** |
| D 维持手动+水位告警 | 账本/日报检测「持仓除息窗口临近而 parquet 未覆盖」即提示 | 最低 | 依赖告警后人工 | 治标；人工响应有时差 | **推荐（与 C 配对）** |

补充说明：
- C 的关键点：引擎现有窗口过滤意味着「先刷新、后推进水位」才安全；新鲜度检查必须发生在 credit_dividends 之前（16:30 daily 内、入账前）。
- B 若单独存在而无 C，仍是盲跑：akshare 拉回来的数据若因脚本 no-op 缺陷没写进去，cron 绿灯但数据没变。**所以「修 L112-135 的增量逻辑」是 B/C/D 任何组合的前置项**（见 §5 第一步）。

## 4. 推荐组合与理由

**推荐：先修脚本增量逻辑（P0，需批准改 HP 脚本）→ C+D 立即上线（engine 前置闸+告警）→ B 每日 cron 作为分红季兜底（需批准 crontab）。**

理由：
1. 修增量逻辑是一切选项的地基——不改它，手动和自动全都 no-op；
2. C+D 把「数据新鲜度」纳入引擎自己的视野，与水位语义绑定，不再依赖外部人肉记忆，成本是一次小改动；
3. B 每日一次与 16:30 daily 错峰（如 17:00），9-10 月中报除息密集期提供确定性供给；淡季也无害（脚本幂等）。
4. A 否决：方向相反且频率过度。

## 5. 实施拆解（均未实施；涉及 HP 脚本与 crontab，**全部需用户批准后执行**）

**P0 修增量刷新（prep_dividend_roa.py）**
- 改动点：`fetch_dividend_events` 内 done_dates 判定由「period 在缓存即跳过」改为「period 的 ex_date 最大值 < 今日-宽限期 才跳过」，或新增 `--refetch-periods 20251231,20260630` 参数（后者改动更小、更可控）
- 验证：跑一次后对比行数 >48,081、ex_date 上限前移、mtime 更新；老数据 diff 仅新增行
- 回退：还原脚本（改动前 `cp prep_dividend_roa.py prep_dividend_roa.py.bak-<date>`；已有 8/13 的 .bak 先例）

**P1 C：引擎前置新鲜度闸（paper_engine.py credit_dividends 前）**
- 加一个 `_div_events_fresh()` 检查：`parquet max(ex_date) < 今日-5交易日` 时 log 告警并（可选）就地调 prep；阈值与是否自动调 prep 由用户定
- 验证：构造旧 mtime 场景跑 daily，确认告警路径与水位不推进语义不变
- 回退：删除新增函数与一行调用

**P2 D：告警**
- 复用 notify_hub 通道：检测「持仓 code 在 (今日, 今日+10日) 有已知 ex_date 且 parquet mtime > 7 天」→ 写通知队列
- 验证：人工回拨 mtime 触发一次

**P3 B：HP crontab 增加一行（需批准）**
- 形如 `0 17 * * 1-5 cd ~/quant-evolve && ~/miniconda3/envs/quant/bin/python scripts/prep_dividend_roa.py --only div >> logs/prep_div.log 2>&1`
- 与 16:30 daily、18:00 qfq 错峰；加 flock 防重入；配套日志便于耗时实测
- 回退：删该行 cron

## 6. 数字溯源
- 行数/列/ex_date 范围/mtime：HP python 读 parquet 实测（2026-08-29）
- 月度分布（2026-06=1721、2025-09=397、2025-10=287 等）：同上实测
- 3,470 条（2026-05 以来）：实测，与 task-0550 笔记一致
- 8 持仓与水位 2026-08-28：results/paper-state.json 实测
- 水位窗口过滤：paper_engine.py L1093-1094；入账触发点 L1447/1468/1531；台账 L1064/1126-1127
- period 级断点续传与 --only 参数：prep_dividend_roa.py L103-135、L384-390
- auto_sync 方向：VPS crontab + auto_sync_notify.py 文档头（25.9KB）
- ledger 不存在：HP find 实测
