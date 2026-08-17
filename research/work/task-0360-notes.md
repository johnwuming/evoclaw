# task-0360 过程笔记：择时v2数据底座一次性历史采集（NMTAP两融/PCR期权/QVIX）

任务：task-0360，产出 R-232 采集核验报告。前置：R-230（采集范围）、task-0354-notes（接口实调证据）。

## 0. 环境与通道（2026-08-18 07:31-07:40 GMT+8）

- SSH：`ssh -i ~/.ssh/id_hp -p 2222 noname@10.12.192.174` key 免密 OK（`hp-quant` 别名 DNS 解析失败，直接用 IP+key）。HP 时区 UTC，磁盘 30G 可用。
- HP：~/quant-evolve/data/derived 已存在（本任务唯一写入目录）；python=/home/noname/miniconda3/envs/quant/bin/python；akshare 1.18.83 / pandas 2.3.3 / pyarrow OK。
- 不改 crontab / 采集循环 / evolution_pipeline / registry：本任务只写 data/derived/ 新文件 + 脚本放 data/derived/fetch_timing_v2_base.py（同目录，避免污染 scripts/）。

## 1. 接口签名实测（07:35）

- `option_daily_stats_sse(date="YYYYMMDD")`：20260814 返回 5 行；列含 合约标的代码/名称、合约数量、总成交额、总成交量、认购成交量、认沽成交量、认沽/认购 …（完整列清单落最终核验）。
- `stock_margin_sse(start,end)`：20260810-17 返回 6 行，列=信用交易日期/融资余额/融资买入额/融券余量/融券余量金额/融券卖出量/融资融券余额。与 task-0354 记录一致。

## 2. 采集设计（写入 HP 脚本）

- margin：按年分段 2010-2026（2010 段 start=20100331），失败重试≤3 次后跳过记日志；年度 checkpoint tmp_margin_done.json。
- option：交易日历 ak.tool_trade_date_hist_sina 一次缓存落盘，区间 2015-02-09~2026-08-17（昨日，收盘完整日）；逐日 ≥1.05s 限速；每 50 天落 tmp partial parquet；checkpoint tmp_option_checkpoint.json（done/failed 日期），重跑跳过 done。
- QVIX：index_option_50etf_qvix() 一次全量。
- 日志：data/derived/fetch_timing_v2.log；nohup 后台；预计 option ~2800 次 ≈ 50-70 分钟。

## 3. 执行记录（边跑边记）

- 07:36 脚本 scp 上传 HP（2222 端口 sftp 子系统未开，scp 加 -O 走传统协议）；py_compile OK；07:37 nohup 启动（fetch_nohup.out + fetch_timing_v2.log）。
- **QVIX 完成**（07:37）：qvix_series.parquet 72KB，2,791 行，字段 date/open/high/low/close，与 task-0354 实测 2791 行完全一致 ✓。零重试。
- **两融完成**（07:37）：margin_sse_daily.parquet 236KB，FINAL 3,979 行，2010-03-31~2026-08-17，零重试零失败。年度明细：2010=185（3/31 起步）/2011-2025 每年 238-245/2026=150（至 8/17）。去重键=信用交易日期。字段：信用交易日期/融资余额/融资买入额/融券余量/融券余量金额/融券卖出量/融资融券余额。
- **期权进行中**（07:38 起）：目标 2,799 个交易日（交易日历 tool_trade_date_hist_sse 缓存 tmp_trade_calendar.parquet），速率实测 25 天/33 秒（约 1.3s/次），预计 ~61 分钟。每 25 天落一个 tmp_option_part_*.parquet，checkpoint tmp_option_checkpoint.json。
