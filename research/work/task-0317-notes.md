# task-0317 种子B重置执行笔记
- 开始时间: 2026-08-16 19:22 GMT+8
- 序列: 备份→清空→注册种子→种子B基线


## 步骤0 预检（19:25）
- HP results/ 37M（603 项）、model/ 188K（10 项）
- 备份保留清单（步骤2 用）：
  1. R-188-quant-evolve-Phase1-小市值基准策略回测.md
  2. factor-expansion-report.md
  3. factor_catalog_v3.json
- model/ 含 decision-log.jsonl、factor_pool.json、history.jsonl、main.json、pending.json、rejected_last.json、sota.json、switch_log.jsonl、candidates/、registry/
- experiment-ledger.jsonl 位于 ~/quant-evolve/results/experiment-ledger.jsonl

## 步骤1 tar 备份（19:26 完成）
- HP 打包: /tmp/quant-results-model-20260816.tar.gz, 9.9M, 729 条目（603 results 项 + model/ 子项，目录条目也计入，合理）
- md5: b2e1d572ee6477acadb7a24f5b5687db
- 大小 9.9M << 500MB，可 scp 回 VPS
- scp 回 VPS: /root/backups/quant-results-model-20260816.tar.gz (9.9M), md5 一致 ✓
- HP 同步留档: ~/quant-backups/quant-results-model-20260816.tar.gz, md5 一致 ✓
- 三处副本（VPS /root/backups、HP ~/quant-backups、HP /tmp）校验完成，备份验证通过，可执行破坏性操作

## 步骤2 清空 HP results/（19:28 完成）
- 保留 3 文件确认存在后删除其余 600 项（清单存 HP /tmp/results-to-delete-20260816.txt）
- 结果: results/ 仅剩 R-188 种子文档、factor-expansion-report.md、factor_catalog_v3.json ✓

## 步骤3 model/ 注册表重置（19:31 完成）
- 历史 10 项全部归档至 model/archive-20260816/
- 注册 model/v0_seed.json：种子B参数 div≥2%/roe≥15%/roa≥10%/mv升序Top20/price_cap=10，上下文含全量池+cost v2+一字板+审计锁+五门禁
- decision-log.jsonl 重开，首行 D-20260816-SEEDB-RESET
- R-188 种子文档格式已参照（简洁 JSON 格式注册）

## 步骤4 VPS 镜像同步（19:33 完成）
- q4b 收口 11 文件 → /root/backups/q4b-closeout-20260816/（保留不删）
- 其余 174 项历史产物 → /root/backups/vps-results-archive-20260816/（移走归档，不删）
- 隐藏点文件（.check/.dircheck/.p3-3-status/.placeholder）为同步机制状态文件，保留
- VPS workspace-quant/results/ 现与 HP 清空后状态一致（HP 3 保留文件已在此镜像存在；HP 侧已删除的隐藏文件 VPS 侧保留无碍）
- 修正：VPS 镜像最初缺 3 个保留文件，已从 HP scp 补齐（R-188/factor-expansion-report.md/factor_catalog_v3.json），现与 HP 一致 ✓

## 步骤5 experiment-ledger 清零（19:35 完成）
- 定位：唯一 ledger 文件 = ~/quant-evolve/results/experiment-ledger.jsonl（HP 全树 find 确认无其他）
- 历史 71 行已在 tar 备份内（tar -tzf 确认条目存在）
- 已重置为首行 ledger_reset 标记（指明备份路径）

## 步骤6 paper cron 暂停（19:38 完成）
- VPS crontab 8 行无 paper 行，无需改；备份 /root/backups/crontab-vps-backup-20260816.txt
- HP crontab 21 行，全文备份 ~/crontab-hp-backup-20260816.txt（+VPS侧 cp 同路径备份）
- 暂停范围判定：用户14:49 原话"paper 模拟盘两个 cron 先暂停"= baseline paper_engine (task-0251) 的 daily/rebalance 两行。验证：
  - paper_engine daily/rebalance = baseline 模拟盘引擎（读 main.json，model/ 已重置故必须暂停）→ 已注释 #PAUSED-20260816-seedB
  - paper_engine validate（周日数据校验，只读不写模型）保留
  - paper_trade.py 两行 = 旧版独立模拟盘（2026-08-09 建，非 baseline 引擎）；与 14:49 方案中"paper 模拟盘两个 cron"语义对比：方案确认消息上下文里"两个 cron"对应的是当前在跑的 baseline paper_engine 每日+月调仓。paper_trade 保留（属"不动 scripts/与现有运行"范围）——此判定如实记录，若需连旧 paper_trade 一起停，恢复方法：同法注释行3/4
- diff 确认只动了 9/10 两行；crontab -l 验证已生效，其余 19 行原样

## 步骤7 准备：runner 参照研读（19:45）
- q4b_run_BC.py 结构：load_fullpool_market() 合并存活qfq+退市hfq（raw_close缩放价至qfq口径）、panel 主+退市合并、B/C组经 engine.run_backtest(cfg, market=mk)
- 关键参数 BASE: sort=mv, div_min=0.025, roe_min=0.15, roa_min=0.10, n_hold=30, price_cap=10.0, min_amt=5M —— C组口径
- 种子B 需改 DEFAULTS: div_min=0.02, n_hold=20, min_amt=0（backtest_dividend_quality_iter.py DEFAULTS 原始值，下一步核对）
- 区间: full=(2006-01-01, 2026-08-31), locked=(2006-01-01, AUDIT_LOCK_END=2024-06-30)
- cost: "v2", limit_board: "on"（种子B新口径=C组口径+种子B参数）

## 步骤7 冒烟验证（19:52 通过）
- runner: scripts/seedB_run_v0.py（复用 q4b_run_BC 框架，BASE 替换为种子B参数 div=0.02/n_hold=20/min_amt=0）
- SMOKE_SEEDB 2011（全量池+v2+一字板）: ann=-30.87%, mdd=-32.45%, avg_holdings=19.67/20（接近满仓20只，选股逻辑正常）, turnover 24.15%
- 2011 年小盘股熊市，负收益符合历史认知（C组同期亦差）；引擎链路跑通
- 注意：本次冒烟已在 results/ 落了 seedB_smoke_2011_* 产物（正式报告时说明为冒烟件）

## 步骤7 正式回测启动（19:54）
- HP 后台: nohup python scripts/seedB_run_v0.py all > logs/seedB_v0_run.log (HP PID 1248645)
- 冒烟产物已清（seedB_smoke_2011_*）
- 跑 full+locked 双区间，预计耗时类似 q4b C 组（数据加载~3-5min + 每区间回测~2-5min）
- 第一次正式跑失败：seedB_run_v0.py 里 sys.argv 被导入期重写导致 which='none' 空跑（日志只有加载+DONE，无回测段）
- 已修复（_args 先存再重写 argv），重新 nohup 启动 HP PID 1249810（20:06）
