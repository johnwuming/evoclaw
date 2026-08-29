# task-0553 过程笔记 — Performance 指标持续供给管道（vC-0）

日期：2026-08-29。预算 40 分钟。R-355 未被占用（README 最新 R-354），编号可用。

## 已知事实（来自 R-354，2026-08-29 切换完成）
- HP 治理层：`~/quant-evolve/portfolio_v1/governance/`（governance.py + projections/×5 + recon/ + checkpoints/）
- 账本：`portfolio_v1/portfolio/events/iteration-ledger-2026-08.jsonl` 终态 15 事件，verify ok
- BFF 数据投影（VPS）：`tools/quant-bff/live/data/governance/{paper,runtime}.json`（BFF 端口 8180，路由 `/api/v1/portfolios`、`/api/v1/portfolios/vC-0`）
- 已知遗留：route 接线（holdings/trades/fee 呈现）原属 task-0553 范围，但本任务书明确 BFF 零改动，仅做数据供给管道；呈现接线不在本次范围（如需另行立项）
- 在役零变化：五权威文件 sha256 切换前后相同；vC-0 数字以切换前 performance.json 为基准

## 待核验清单
- [ ] HP 实查：vC-0 引用的 NAV 曲线文件、performance.json 归属、id 对齐（账本/投影/权威文件三方）
- [ ] task-0549 的 hp_export_metrics.py 现状与契约
- [ ] 幂等化改造 + 手动跑 diff=0
- [ ] BFF /portfolios 实查
- [ ] rsync sync cron 既有挂点（对齐不新开）
- [ ] 月频挂点提案两方案

## 发现记录
（边查边写）

## 发现1：契约与现状（VPS 侧实测）
- BFF 数据目录 `tools/quant-bff/live/data/`：performance.json(1518B) + nav_curves.csv(23721B,157行=156月+表头)，2026-08-29 02:11 由 task-0549 产出
- 导出脚本位置：`tools/quant-bff/live/export/hp_export_metrics.py`（VPS 侧，task-0549 交付）
- performance.json 契约：portfolio_version_id=vC-0；curve_source(file=nav_curves.csv,column=F1_quarterly,md5=9704a300...)；metrics ann=0.135702/vol=0.094679/sharpe=1.4333/maxDD=-0.090794；data 2013-08~2026-07 n=156；caliber 全段口径说明；generator 字段
- 指标口径：月频基期1.0，几何CAGR，ddof=1×sqrt(12)，rf=0，maxDD含基期，全期窗口
- NAV 源列：F1_quarterly（vC-0 口径），列末值 5.22921278108852

## 发现2：id 对齐三方对照（HP 实查 2026-08-29）
- 权威文件 `portfolio_v1/portfolio/versions/vC-0.json`：id=vC-0、status=paper、equity sleeve=registry_ref(engine_id=A, registry_entry=a13_rsraw_e1f10dz, status=active)、solver_equal_vol_v1、data_cut=2026-08-26；**组合定义文件，无 NAV/指标块**
- 投影 `governance/projections/paper.json`：header sha256=a6159e00…，body.portfolio_version_ref=vC-0（对齐权威 id）
- 投影 `governance/projections/runtime.json`：portfolio_version_ref=vC-0；nav_daily 11 条（最新 2026-08-28 nav=1.00993，source_file=results/baseline-paper-nav.csv）；trades/authoritative_sources/semantics
- 账本 `portfolio/events/iteration-ledger-2026-08.jsonl`：15 事件中 14 条引用 vC-0，verify ok（R-354 结论）
- 结论：vC-0 id 在 权威文件(定义)→投影(引用)→账本(事件) 三处一致对齐

## 发现3：NAV 曲线与指标归属（两条曲线，口径不同）
- 回测全期曲线（BFF 版本页消费）：`portfolio_v1/combo_selector/results/nav_curves.csv`，列 F1_quarterly=vC-0 口径满仓复现曲线，md5 9704a300767613523815173a5881c304，157行(156月+表头)，末值 5.22921278108852；列还含 A/gold/F0/F1_equal/F3/F4/F5
- 运行态 paper NAV：`results/baseline-paper-nav.csv` → 已镜像进 runtime.json nav_daily（11 条起步，16:30 日更追加）；与回测曲线口径不同（实盘日频 vs 回测月频全期），**版本页四指标卡消费的是回测曲线**
- 交叉锚：`combo_selector/results/all_results.json` F1_quarterly = ann 0.1357 / vol 0.0947 / sharpe 1.397(算术口径) / mdd -0.0908，脚本仅提示性比对
- 月频持续供给语义：每月月末点入表后全期重算（口径/契约不变），写入同名两文件

## 发现4：既有同步通道实查（无 rsync cron）
- HP crontab 全量核查：无任何 rsync/scp 到 VPS 的数据同步条目；相关在役挂点：`0 15 * * 1-5` paper_engine rebalance --check-month-start（月度调仓门）、`30 16 * * 1-5` paper daily、`10 8 * * 1-5` shadow_recon、`15 8 * * 1-5` drift_monitor、`0 9 * * 6` evolution cycle
- HP `~/.openclaw/workspace-quant/scripts/` 仅 collect-metrics.sh（1 分钟推送任务指标到 VPS:8055，非数据文件通道）
- VPS root crontab/systemd timers//etc/cron.d：无 quant-bff 相关同步
- task-0549 为一次性手动 scp。**结论：BFF 双文件目前无自动供给通道，"对齐既有 rsync cron"前提不成立，提案需如实给出（含新挂点必须用户批准）**

## 发现5：固化脚本实施与验证（2026-08-29）
- 新脚本：VPS `tools/quant-bff/live/export/hp_export_metrics.py`（覆盖更新，7891B）+ HP 部署副本 `~/quant-evolve/portfolio_v1/governance/export/hp_export_metrics.py`（md5 43f3932a… 两端一致）
- 变更点（可归因）：①新增 --out-dir 同时导出 performance.json+nav_curves.csv（原名，原子写 tmp+rename+fsync）②generated_at 改为源 csv mtime（UTC 确定性）+新增 generated_at_basis 字段③generator 标注 task-0549/0553④新增 --check 比对模式（exit 0/3）⑤指标计算逐行未动
- HP 实跑验证（/tmp/task0553-export）：两次运行输出字节相同（performance.json md5 e959d21a…、csv 9704a300…），--check CHECK-SAME exit=0；四指标 ann=0.135702/vol=0.094679/sharpe=1.4333/maxDD=-0.090794 与 0549 完全一致
- 对现役文件 diff：nav_curves.csv md5 逐位相同=0；performance.json 除 generated_at/generated_at_basis/generator 三字段（幂等语义变更，可归因）外逐字段一致
- BFF 实查：quant-bff.service active，127.0.0.1:8180；/api/v1/portfolios 返回 vC-0 正常；/api/v1/portfolios/vC-0 performance.metrics 四指标=导出值，data_as_of=2026-07-31，curve_md5=9704a300…；BFF 代码零改动（缺失降级 null 逻辑原样保留，grep 到 performance 注入点 fallback）
- 约束遵守：未动 registry/paper_engine/evolution_pipeline/crontab/在役进程；HP 新增文件仅 governance/export/ 子目录（Phase C 治理层内新增，additive）
