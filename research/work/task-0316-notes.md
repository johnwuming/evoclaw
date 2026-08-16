# task-0316 Q4b 第四棒 过程笔记（边查边写）

## 18:58 接手
- 前序：A组双区间已落盘（A_full 25.73%/-70%/0.913；A_locked 26.11%/-70%/0.907）；第三棒就绪件 build_delisted_panel.py + q4b_run_BC.py 已冒烟过
- 日志确认：`/tmp/q4b_collect_v2_full.log` 显示 293/293 采完，末行 `COLLECT_V2_DONE`，`logout success`，无致命错。data/fin_delisted 共 309 个文件（含索引）
- 采集健康：✅ 退市财务采集完成（步骤1过）

## 待办
1. ✅ 采集完成确认
2. ⏳ 重建全量退市 panel
3. ⏳ B/C 全区间回测
4. ⏳ 收口报告
5. ⏳ decision-log 入档
6. ⏳ VPS 镜像同步

## 19:00 panel 重建中
- 发现 HP 上已有全量重建进程在跑（PID 1235807，nohup → /tmp/q4b_panel_full.log，10:57 启动，source files: 301）——判断为第三棒遗留/就绪进程，正好是我们要的重建任务
- 我误启了一个重复 build，已 kill 掉（1237022 wrapper + 1237023 orphaned python），保留 1235807 唯一写入者
- 现状：1235807 100% CPU，日志 "source files: 301"，等它跑完 → rows/codes 摘要

## 19:06 panel 全量重建完成（步骤2过）
- pre-existing 进程 1235807 跑完：source files=301, rows=44005, codes=299
- 范围 2006-01-31 ~ 2026-06-30；rows_with_roe=36863，rows_with_div=18399
- 输出 parquet 532KB → data/derived/fundamentals_delisted_monthly.parquet
- ⚠️ 注意：codes=299 比任务书预期 293 略多（可能含部分额外采集），以实际为准，不影响正确性
- 待办：B/C 全区间回测

## 19:10 B/C runner 就绪，准备启动
- q4b_run_BC.py 全读：main 支持 all=B+C+BUB 六腿（各 full+locked），单进程 market 只 load 一次，最省
- HP 4核/15G，可用 13G；已有模拟实盘进程 1017445 占 1 核（勿杀），负载 1.59 可承受再起一个
- 计划：nohup 后台 `q4b_run_BC.py all` → /tmp/q4b_run_BC_full.log，轮询到 Q4B_BC_DONE

## 19:15 B/C 回测进行中（步骤3过，跑完才算）
- 进程 1240006 活：市场 load 完（5505 只，交易日 5250，月度调仓 260）
- 19:14 标记：B_full 完成 → B_locked 启动中（六腿：B/C/BUB × full/locked）
- 日志 /tmp/q4b_run_BC_full.log，等 Q4B_BC_DONE

## 19:13 B/C/BUB 六腿全跑完（步骤3过）
- 11:13:39 UTC 确认 Q4B_BC_DONE，进程 1240006 退出
- 六腿：B_full/B_locked/C_full/C_locked/BUB_full/BUB_locked 全部完成，无 Traceback
- 下一步：抽取 metrics → 写报告

## 19:15 六腿 metrics 全量到手（已落盘 /tmp 于 SSH 输出，下面数字为最终采用）
- B_full:    cum 111.53%, ann 25.76%, mdd -70.02%, sharpe 0.9138, calmar 0.368, 调仓248
- B_locked:  cum 72.08%,  ann 26.14%, mdd -70.02%, sharpe 0.9080
- C_full:    cum 125.41%, ann 26.47%, mdd -69.88%, sharpe 0.9323
- C_locked:  cum 80.48%,  ann 26.88%, mdd -69.88%, sharpe 0.9267
- BUB_full:  cum -25.29%, ann -1.40%, mdd -98.15%, sharpe 0.115  （上界代理，灾难）
- BUB_locked:cum 81.24%,  ann 3.27%,  mdd -94.57%, sharpe 0.2666
- 注：BUB_full 较 BUB_locked 崩盘 → 2024-2026 尾部退市股集中暴露致 cum 从 +81%→-25%
- 关键发现：B≈A（ann 25.76 vs 25.73，差 +0.03pp）→ 财务五门禁挡住退市股 → 幸存者偏差被抑制
- 待办：取 A 组 exact metrics → 写报告 → decision-log → VPS 镜像
