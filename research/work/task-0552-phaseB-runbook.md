# task-0552 阶段B：Phase C 治理切换执行 runbook

- 开始 2026-08-29 10:43 / 切换主体完成 10:58（≤40min 预算内）；窗口约束 16:30 前完成 ✅
- 依据：R-336 v1.5 §8 Phase C 动作1-5；R-353 §6 切换前注意4项；用户 10:13 批准当日切完、不考虑回退
- 例外授权：治理写路径（registry/engines/composites 事件化）+ paper 指针 + 镜像钩子接线；HP crontab / 在役进程 / evolution_pipeline / registry active 零改动
- 实现落位：HP `~/quant-evolve/portfolio_v1/governance/governance.py`（544 行，复用 `portfolio_v1/event_ledger.py` 的 EventLedger：flock+fsync+seq 幂等+月滚动）；账本=`portfolio_v1/portfolio/events/`；VPS 留档副本 `work/task-0552-evidence-b/governance.py`

## 步骤1 切换前处置（10:43–10:45，2min）
- ① equity daily 补跑：`paper_engine.py --action daily` → **8/28 官方 NAV=1.00993**（总资产 ¥100,993.00，8 持仓），与阶段A 重放投影 1.009930 **逐位一致**；分红水位初始化 2026-08-28（不追溯）；引擎自带 rsync 已同步 VPS
- ② 标定留痕：事件 `calibration.recorded`（CAL-20260829-01：建仓日 8/14 官方成本+费用计价 vs 重放收盘计价 = −21.43bp，口径差非状态错误，8/17 起归零）写入 iteration-ledger
- gold marks 止 8/27 = T−1 正常节奏（R-353 §6.3），不处置
- 顺带核实：BFF `/api/v1/portfolios` 与 `/api/v1/portfolios/vC-0` 均正常；无独立 `/versions` 路由（列表+详情即对应物）

## 步骤2 切换前快照（10:45，1min）
- `/tmp/task0552-phaseB-preswitch/`：a13 registry 条目、paper-state、baseline-paper-nav.csv、vC-0、gold paper_state + SHA256SUMS；另持久留档 HP `portfolio_v1/governance/preswitch-snapshot/`
- 快照时点在补跑之后 → 快照即「切换前」权威底账

## 步骤3 事件溯源切换（10:46–10:47，1min）
- `governance.py switch`：追加 3 事件（`governance.baseline` 含 5 权威源全文+sha256 / `calibration.recorded` / `paper.pointer.switched`）
- 耗时：baseline 4.2ms、calibration 3.9ms、pointer 3.8ms、replay 0.5ms、五投影生成 7.5ms；ledger verify ok
- 投影（`portfolio_v1/governance/projections/`，文件头 sha256）：registry 551b271e…、engines 61e88ab…、composites c0e08eb…、paper a6159e00…、runtime 928d008b…（runtime 随镜像更新）
- 语义：在役文件仍为引擎权威读/写路径；治理层=append-only 账本+重放投影（Phase D 才退役旧件）

## 步骤4 paper 指针语义切换（含在步骤3 事件内）
- `paper.pointer.switched`：portfolio_version_ref=**vC-0**；from=A(a13)+gold(active_paper)+ddc 散装三元组；sleeves 映射带各权威文件 sha256；**持仓/现金/NAV 数值不落指针**（paper_live_facts 仅记录 cash 40393/initial 100000/8 持仓/last_daily 8-28 作切换时点事实），数值权威仍在引擎文件
- 投影 `paper.json` 同步生成（1.2KB）

## 步骤5 运行态镜像接线（10:48–10:52，4min）
- `mirror` 命令：按 date 去重增量翻译 CSV 新行 → `nav.daily`/`trade.fill` 追加；首次实跑 0 nav（11 行已在 baseline）+8 trade.fill（8/14 建仓单，0.083s）；复跑 0/0 幂等 ✅
- `watch` 常驻监视器：20s 轮询权威 CSV sha256 → 变更即调 mirror；**自退出 17:05**（覆盖 16:30 实跑，之后无常驻进程，crontab 零改动）；钩子异常只记缺口标记不阻塞引擎（§3.6）
- BFF 只读视图：paper.json + runtime.json（holdings/trades/fee/nav 数据投影）已落 `tools/quant-bff/live/data/governance/`；路由接线归 task-0553（§3.6 供给管道），本次完成数据侧验证

## 步骤6 三方对账+断路器+checkpoint（10:50，<1s）
- `recon`：**PASS**——持仓集合 paper账本=引擎记录、镜像 nav/trades 与权威 CSV 逐字段一致、equity registry 条目 active、gold active_paper、NAV 时效 1 天；两个如实降级：cash_band=null（holdings 无 last_price 字段，现金带检查以 NAV 对账日核兜底）、weight_solution_sums=null（HP vC-0 无 weight_solution 块；VPS BFF 侧副本是 Phase B 合并新版——已知 provenance 差，非缺陷）
- `checkpoint`：cp-2026-08-28-off14 落盘（offset=14）；恢复干跑=重放截断重建 vs checkpoint **diff=0**
- `breaker --sandbox-sim`：实况 GREEN（日收益 +1.15%、DD 0、nav_age 1 天）；沙箱注入 -3.03% 日 + 23.1% DD → 4 动作全触发（halt_new_opens_today/halt_new_opens/escalate_review/notify_user）pass=true；人工复位规则已写入状态文件

## 切换后验证 a–e
- **a. 重放重建 vs 切换前快照 diff=0** ✅：registry/gold/vC-0 逐字段 identical（首轮 composites inner 键笔误致假 DIFF，修复后复验通过；数据本身从未有差异）；证据 `governance/evidence/verify-diff-2026-08-29.json`（VPS 副本 `work/task-0552-evidence-b/hp/`）
- **b. 投影生成+sha256 一致；BFF 正常** ✅：五投影文件头 sha256 与重放重建体一致（projection_headers 全 ok）；`curl :8180/api/v1/portfolios` 返回 vC-0 行、`/api/v1/portfolios/vC-0` 返回全 schema
- **c. 镜像钩子干跑** ✅：沙箱 `/tmp/task0552-mirror-sb` 模拟 8/29 日更 → nav.daily×2 + trade.fill×1（含 fee 13.56）追加、runtime 投影更新、复跑幂等
- **d. 16:30 实跑**：watch 监视器在位，**待 16:30 实跑确认**（首运行日镜像与 CSV 逐字段一致由对账兜底+watch 日志佐证），不阻塞退出
- **e. 在役引擎数值零变化** ✅：切换前后 5 权威文件 sha256 逐一 SAME（a13/paper-state/nav.csv/vC-0/gold）；paper_state 数值字段 diff=[]；crontab md5 未变、未杀任何在役进程、registry active 条目逐字未动

## 账本终态
- iteration-ledger-2026-08.jsonl：15 事件（Phase B 原 2 + 切换 3 + 镜像 8 + recon 1 + checkpoint 1）；ledger verify ok
- 断点：无异常停顿；唯二返工=①verify 脚本 composites inner 键笔误（数据无差）②沙箱缺 event_ledger 副本（补拷贝）

## 证据索引（VPS `work/task-0552-evidence-b/`）
- `hp/verify-diff-2026-08-29.json`（验证a/e）、`hp/mirror-last-*.json`、`hp/checkpoint-recovery-*.json`、`hp/breaker-*.json`、`hp/recon-*.json`、`hp/cp-*.json`、`hp/SHA256SUMS`（切换前快照）、`hp/paper.json`+`hp/runtime.json`（投影）
- `governance.py`（本模块）、`event_ledger.py`（复用件）
- BFF 数据供给：`tools/quant-bff/live/data/governance/{paper,runtime}.json`

## 待 16:30 实跑确认（不阻塞）
1. 16:30 equity daily cron 跑后：watch 日志 `governance/logs/watch-2026-08-29.log` 应出现 change→mirror 记录，nav.daily 追加 8/29 行
2. 复跑 `governance.py recon` 应保持 PASS（镜像一致性）
3. gold 9/1 首交易日前 marks 由 07:40 cron 正常补齐
