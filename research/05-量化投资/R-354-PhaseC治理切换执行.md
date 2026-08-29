# R-354 Phase C 治理切换执行报告（task-0552 阶段B）

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-29 10:43–10:58（切换主体 15 分钟，16:30 前完成 ✅） |
| 执行 | 主会话 spawn 子 agent；用户 2026-08-29 10:13 批准提前切换、当日切完、不考虑回退 |
| 依据 | R-336 v1.5 §8 Phase C 动作 1-5；R-353 GO 结论与 §6 切换前注意 4 项 |
| 结论 | **切换完成，验证 a/b/c/e 全绿；d（16:30 实跑）待当日确认，不阻塞** |

## 0. 一句话结论

Phase C 五项动作全部落地：治理写路径切换为「追加事件+重放投影」（毫秒级，flock/fsync/seq 幂等/投影头 sha256 全链路生效）、paper 指针切换至 `portfolio_version_ref=vC-0`、运行态镜像钩子（nav.daily/trade.fill）实跑并沙箱干跑通过、三方对账 PASS、checkpoint 恢复 diff=0、断路器实况 GREEN+注入触发干跑 PASS；重放重建 vs 切换前快照逐字段 diff=0，五个在役权威文件 sha256 切换前后逐一相同——**在役数值零变化声明成立**。

## 1. 各动作耗时

| 动作 | 耗时 | 结果 |
|---|---|---|
| 0 切换前处置：equity daily 补 8/28 + 标定留痕 | 2 min | 8/28 官方 NAV=1.00993（与重放投影逐位一致）；−21.4bp 建仓日口径差入账 CAL-20260829-01 |
| 1 切换前快照 | 1 min | /tmp + HP governance/preswitch-snapshot 双落位，SHA256SUMS 留档 |
| 2 事件溯源切换（3 事件+五投影） | 1 min | 追加各 ~4ms、重放 0.5ms、投影 7.5ms；ledger verify ok |
| 3 paper 指针切换 | （含动作 2） | vC-0 指针+在役实况映射，数值不落指针 |
| 4 运行态镜像接线 | 4 min | 镜像实跑 8 trade.fill（0.083s）幂等；watch 监视器自退出 17:05；BFF 数据投影落位 |
| 5 对账+断路器+checkpoint | <1 s | recon PASS / breaker GREEN / cp-off14 恢复 diff=0 |
| 验证 a–e | 3 min | 见 §2 |

## 2. 验证 a–e 结果

- **a. 重放重建 vs 切换前 JSON 快照 diff=0** ✅ — registry/gold/vC-0 逐字段 identical；证据 `work/task-0552-evidence-b/hp/verify-diff-2026-08-29.json`。过程注记：首轮 verify 脚本 composites 投影 inner 键笔误报假 DIFF，定位为取数键错误（数据本身 eq），修复复验通过。
- **b. 投影生成且 sha256 一致；BFF 正常** ✅ — HP 五投影文件头 sha256 与重放重建体全 ok；VPS `curl :8180/api/v1/portfolios` 与 `/api/v1/portfolios/vC-0` 数据正常（无独立 /versions 路由，列表+详情即对应物）。
- **c. 镜像钩子干跑** ✅ — 沙箱模拟 8/29 日更：nav.daily×2 + trade.fill×1（含 fee）追加、runtime 投影更新、复跑幂等 0/0。
- **d. 16:30 实跑=首个真实运行日** ⏳ — watch 监视器（20s 轮询、17:05 自退出、crontab 零改动）在位；**待 16:30 实跑确认**：watch 日志应记录 change→mirror，nav.daily 追加 8/29 行，复跑 recon 保持 PASS。已标注 notes，不阻塞退出。
- **e. 在役引擎数值零变化声明** ✅ — a13 registry 条目 / paper-state / baseline-paper-nav.csv / vC-0 / gold paper_state 五文件 sha256 切换前后逐一 SAME；paper_state 数值字段 diff=[]；crontab 未动、未杀在役进程、registry active 条目逐字未动、evolution_pipeline 零接触。

## 3. 落位清单

- 新增治理层：HP `~/quant-evolve/portfolio_v1/governance/`（governance.py、projections/×5、evidence/、checkpoints/、recon/、preswitch-snapshot/、logs/）
- 账本：`portfolio_v1/portfolio/events/iteration-ledger-2026-08.jsonl` 终态 15 事件（Phase B 原 2 + 切换 3 + 镜像 8 + recon 1 + checkpoint 1），verify ok
- 报告/笔记：本文 + `work/task-0552-phaseB-runbook.md`（含每步耗时与证据索引）
- BFF 供给：`tools/quant-bff/live/data/governance/{paper,runtime}.json`（holdings/trades/fee 只读投影；路由接线归 task-0553）

## 4. 已知口径与遗留（不阻塞）

1. **16:30 实跑确认**（§2d）：watch 日志 + recon 复跑；若钩子失败仅留缺口标记，对账兜底补齐（§3.6 语义）。
2. cash 精确带检查降级：holdings 无 last_price 字段，现金带（≤0.5% NAV）以 NAV 对账日核兜底；引擎侧计价不在治理层复算。
3. HP vC-0 无 weight_solution 块（VPS BFF 副本为 Phase B 合并新版）——已知 provenance 差，recon 该检查如实 null。
4. solver equity 输入 D1 缺口（回测 NAV 止 8/14）为 Phase B 遗留，与切换无关（R-353 §6.4 已留痕）。
5. BFF /portfolios/:id 只读视图的 route 接线（holdings/trades/fee 呈现）归 task-0553；本次完成数据投影供给与验证。

## 5. 在役零改动声明

全部写入仅落在：HP `portfolio_v1/governance/`、`portfolio_v1/portfolio/events/`（追加）、`/tmp/task0552-*` 沙箱、VPS `shared/results/work/` 与 BFF live/data/governance/（新增文件）；在役 state/trades/nav/registry/crontab/paper_engine 生产逻辑零接触，未杀任何在役进程。equity daily 补跑为在役 cron 同款命令（R-353 §6.1 授权动作），产出与既有日更链路一致。
