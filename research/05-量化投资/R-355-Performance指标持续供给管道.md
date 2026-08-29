# R-355 Performance 四指标+NAV 曲线持续供给管道（task-0553）

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-29 |
| 任务 | task-0553（Phase C 新治理层 vC-0 指标/曲线持续供给） |
| 结论 | **幂等投影导出脚本固化完成并实跑验证通过；BFF 端到端闭环正常；月频挂点提案成文待批（本次零 crontab 改动）** |

## 背景与目标

Phase C 治理切换（R-354，2026-08-29）后，BFF 版本页的四指标卡与 NAV 曲线仍依赖 task-0549 的一次性手动导出（`performance.json` + `nav_curves.csv` 落 `tools/quant-bff/live/data/`），无自动供给通道。本任务目标：①实查 vC-0 的 NAV 曲线/指标归属与 id 对齐；②把 `hp_export_metrics.py` 固化为幂等可重复执行的投影导出脚本（同口径同契约）；③给出 HP→VPS 同步挂点说明；④月频调仓日自动更新提案（只出文档，严禁改 crontab）。

## 方法与数据来源

- HP 实查（ssh noname@10.12.192.174，只读）：`portfolio_v1/portfolio/versions/vC-0.json`、`portfolio_v1/governance/projections/{paper,runtime}.json`、`portfolio/events/iteration-ledger-2026-08.jsonl`、`portfolio_v1/combo_selector/results/`、`crontab -l`
- VPS 实查：`tools/quant-bff/live/data/` 现役产物、`quant-bff.service`（127.0.0.1:8180）与 `/api/v1/portfolios` 端点、双侧 cron/timer
- 导出验证：HP 上以 `/home/noname/miniconda3/envs/quant/bin/python` 实跑固化脚本两次 + `--check`，产物取回 VPS 与现役文件 diff，同名覆盖后复查 BFF

## 核心发现（结论先行）

**1. id 三方对齐成立**：权威文件 `versions/vC-0.json`（id=vC-0、status=paper、equity sleeve=registry_ref a13_rsraw_e1f10dz、solver_equal_vol_v1、data_cut=2026-08-26，纯组合定义无 NAV/指标块）→ 投影 `paper.json`（body.portfolio_version_ref=vC-0，header sha256 a6159e00…）与 `runtime.json`（同 ref，nav_daily 镜像自 `results/baseline-paper-nav.csv`）→ 账本 15 事件中 14 条引用 vC-0（verify ok）。

**2. 指标与曲线归属明确，存在两条口径不同的 NAV 曲线**：
- **回测全期曲线**（版本页消费）：`combo_selector/results/nav_curves.csv` 列 `F1_quarterly`（vC-0 满仓复现曲线，md5 9704a300…，157 行=156 月+表头，末值 5.22921278108852；由 `run_vc0_repro.py` 于 8/28 再生，**非月频自动延长**）。
- **运行态 paper NAV**：`baseline-paper-nav.csv` → 治理层 runtime 投影 nav_daily（R-354 已接镜像，不归本管道）。
- 四指标仅存在于 `performance.json`，由回测曲线 F1_quarterly 列全期计算（几何 CAGR、ddof=1×√12、rf=0、maxDD 含基期），交叉锚 all_results.json F1_quarterly（ann 0.1357/vol 0.0947/mdd -0.0908）。

**3. 无既有 rsync 通道（对齐前提不成立，如实修正）**：HP crontab 全量、VPS root crontab/systemd timers、`/etc/cron.d` 三处实查均无 HP→VPS 数据文件同步；task-0549 为一次性手动 scp。最接近的既有模式是 VPS→HP 拉取式 `sshpass + scp -O`（本任务验证同款）与 HP 每分钟 collect-metrics.sh HTTP 推送（非文件通道）。

**4. 固化脚本实跑验证全绿（diff=0 或可归因）**：
- 脚本部署：VPS 仓 `tools/quant-bff/live/export/hp_export_metrics.py` + HP 副本 `portfolio_v1/governance/export/hp_export_metrics.py`（两端 md5 43f3932a… 一致）。
- 幂等：同输入连跑两次输出字节相同（performance.json md5 e959d21a…），`--check` CHECK-SAME exit 0；关键设计为 `generated_at` 取源 csv mtime（UTC 确定性）+ 新增 `generated_at_basis` 字段 + 原子写（tmp+fsync+rename）。
- 对现役 diff：`nav_curves.csv` md5 逐位相同（=0）；`performance.json` 除 `generated_at`/`generated_at_basis`/`generator` 三字段（幂等语义变更，逐项可归因）外逐字段一致；四指标 ann=0.135702/vol=0.094679/sharpe=1.4333/maxDD=-0.090794 与切换前完全一致。
- 端到端：新产物 tmp+mv 原子覆盖 `live/data/` 两文件 → BFF `/api/v1/portfolios/vC-0` 返回上述同值；降级探针 `/portfolios/vNOPE` → performance=null（app.js:207 降级语义未动、生效）。回滚点：`/tmp/task0553-bak-performance.json`、`/tmp/task0553-bak-nav_curves.csv`。

## 月频调仓日自动更新提案（独立节，待用户批准；本次未改任何 crontab）

**共同前提**：
- 导出器幂等：无新月末数据 → 输出字节相同 → `--check`/md5 判定后不做任何同步，天然适合反复重跑。
- 同步方式（两案共用）：VPS 侧拉取式 `sshpass -p "$QUANT_SSH_PASSWORD" scp -O noname@10.12.192.174:/tmp/perf_export/* → live/data/`（tmp+mv 原子落位，杜绝半途文件触发 BFF 降级 null）；密码引 `secrets.env`（600）不入 cron 明文。HP 侧脚本先行 `--out-dir /tmp/perf_export` 导出。**该挂点+包装脚本均为新增项，须用户批准后方可落 crontab。**
- 边界如实声明：本管道保证「回测曲线一更新（selector/repro 再生成），下个节拍自动重算并供给」；曲线文件本身的再生成（月度延长）不在本管道职责内，BFF 在曲线未更新期间继续展示既有全期指标（data_as_of 如实标注）。
- 失败降级：导出或同步失败仅记日志（`logs/perf_export_*.log`）+ notify_hub 提醒；BFF 无感知，继续用旧文件；仅当文件真缺失/损坏且被半途覆盖时才触发降级 null（原子落位已规避）。
- 回滚：删除新增 cron 行即回到现状（一次性 scp 模式）；数据面回滚用覆盖前备份（或由 HP 源按同口径重导）。

**方案 A：求解器/进化周期挂点**

| 项 | 内容 |
|---|---|
| cron 表达式 | `40 9 * * 6`（周六 09:40，错开在役 `0 9 * * 6` evolution cycle 之后 40 分钟） |
| 触发时序 | cycle（候选评估/五门禁/可能 activate）→ 导出器重跑 → md5 有变才 scp VPS → BFF 下次请求即新数据 |
| 优点 | 版本切换日（新 vC-X 激活当天）指标即刷新，覆盖「切换场景」最好；与求解器产物同源同节奏 |
| 缺点 | ①周频触发但曲线非周频变，多数空转（幂等无害）；②**新版本需要版本感知**：当前脚本硬编码 `vC-0`/`F1_quarterly`，vC-1 上线须先更新两常量（或参数化 --version），否则继续导 vC-0；③与「月频调仓日」语义不直接对齐 |

**方案 B：月度调仓日账本投影导出挂点（推荐）**

| 项 | 内容 |
|---|---|
| cron 表达式 | `0 16 1-7 * *`（每月 1–7 日 16:00，HP 上；刻意避开 vixie cron「日+星期 OR」陷阱，不用 `1-7 * * 1-5`） |
| 触发时序 | 月度调仓（在役 `0 15 * * 1-5` rebalance --check-month-start，实际发生在每月首个交易日 15:00）→ 1 小时后导出器重跑 → 有新月末点则重算全期指标并同步 |
| 优点 | ①幂等重跑，无变化零副作用，1–7 日每日兜底覆盖「首个交易日碰上周一延迟」等日历抖动；②与调仓日月度节拍对齐，语义即「调仓日刷新月度指标」；③不依赖求解器、不受版本切换影响（曲线未变则 vC-0 指标不变，真实） |
| 缺点 | 不覆盖「版本激活当天」场景（激活属人工门，当日手动跑一次导出器即可，可作为激活 checklist 一行） |
| 落地物 | HP crontab 追加 1 行 + VPS 包装脚本 1 个（拉取+tmp+mv+日志），均为新增文件/行，零在役改动 |

**两案对比结论**：推荐 B 为主挂点；A 的版本切换场景由「激活 checklist 手动一步」替代（人工门本就要求人到场）。vC-1 激活前须完成脚本的版本参数化改造（后续任务）。

## 结论建议

1. 管道本体已可用：固化脚本（VPS 仓 + HP 部署副本）+ 同名双文件契约 + 幂等语义 + BFF 零改动，验证全绿。
2. 待用户批准月频挂点（§提案方案 B）后，由主会话/授权任务落 crontab（本次严禁改动的约束已遵守，双侧 crontab 零接触）。
3. 后续建议：①vC-1 前把 `CURVE_COLUMN`/`PORTFOLIO_VERSION_ID` 参数化（--version + versions/*.json 映射）；②曲线月度再生成机制（selector 定期重跑）另行立项，属在役进化链路，不在本管道范围。

## 修改文件与验证记录

- 修改：`tools/quant-bff/live/export/hp_export_metrics.py`（固化版）；HP 新增 `portfolio_v1/governance/export/hp_export_metrics.py`（部署副本）
- 数据面同名覆盖：`tools/quant-bff/live/data/{performance.json,nav_curves.csv}`（数值与切换前一致；备份 `/tmp/task0553-bak-*`）
- BFF 代码、前端、registry、paper_engine、evolution_pipeline、双侧 crontab：零改动
- 验证命令与结果：HP 双跑 md5 相同 + `--check` exit 0；`md5sum` csv 两端 9704a300… 一致；performance.json diff 除三可归因字段外为空；`curl -s http://127.0.0.1:8180/api/v1/portfolios/vC-0` 返回同值四指标；`/portfolios/vNOPE` → performance=null

## 来源清单

- R-354 Phase C 治理切换执行报告（口径与切换后状态）
- HP：`portfolio_v1/portfolio/versions/vC-0.json`、`governance/projections/{paper,runtime}.json`、`events/iteration-ledger-2026-08.jsonl`、`combo_selector/results/{nav_curves.csv,all_results.json}`、`crontab -l`
- VPS：`tools/quant-bff/live/data/`、`tools/quant-bff/src/app.js`（L207 降级语义）、`quant-bff.service`（:8180）
- task-0549 完成记录与 `work/task-0549-metrics-curves-notes.md`
- 过程笔记：`shared/results/work/task-0553-pipeline-notes.md`
