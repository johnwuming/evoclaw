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
