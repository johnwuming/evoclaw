# task-0330 ST历史区间回补 笔记
## 阶段0 勘察
- 引擎 ST_CSV=data/stock_info/stock_info.csv（300行，is_st全False，无start/end列）→ load_st_flags() 实际返回空 dict → **当前回测引擎 ST 排除=0 生效**（比任务书诊断的"206只全程标记"更严重：st_history.parquet 根本没接入引擎）
- st_history.parquet (206行, code/name/is_star/snapshot_date=2026-08-15) 仅是 W6 快照产物，无区间结构
- 宇宙：data/all_stocks_qfq 5448 个 parquet（回测宇宙）；qfq 列: date/open/high/low/close/volume/amount/outstanding_share/turnover，**无名称列** → 需外部源
- 退市索引 stocks_hfq_delisted_index.json：dict，365 只
- akshare 1.18.83 可用；引擎 st_flag 构建：L200-211，按区间 [s,e] 布尔化到交易日索引
## 阶段0b 关键发现（续）
- 宇宙：all_stocks_qfq 5448 只（SZ≈2894 / SH≈2310 / BJ≈242）；退市股不在 qfq 目录（0 overlap）
- 源A（SZ精确日期）: ak.stock_info_sz_change_name("简称变更") → 7462 行带 变更日期，覆盖 000/001/002/003/300/301
- 源B（baostock 逐日名称）: bs.query_all_stock(day) → code/tradeStatus/code_name，名称 as-of-day（2021-07-01 有265个含ST/*名称，含已退市股如*ST宋都→非当前名，证明是历史名）
- 源C sina per-stock: 只返回名称序列无日期（弃）
- 东财 F10 RPT_F10_NAME_CHANGE: 报表不存在
- baostock 不覆盖 BJ（bj rows:0）；SZSE bulk 精确日期验证通过（000005: ST 2003-05-09→*ST→GST→ST→2008-06-25世纪星源→2021-05-06再ST）
- 计划：SZ=SZSE bulk精确；SH=baostock月网格+边界细化；BJ=待定(eastmoney F10/其他)
- sina stock_info_change_name 对 BJ 也返回名称序列（bj920023→*ST田野），但无日期
- BJ 方案：待测 eastmoney datacenter F10
## 阶段1 采集策略定稿
- SZ(000/001/002/003/300/301): SZSE bulk 简称变更 7462行 精确日期 → 源A
- SH(600/601/603/605/688): baostock query_all_stock 月度网格(2005-01~2026-08, 每月首个交易日) + 过渡月日级细化 → 源B
- BJ(920/8xx/4xx 242只): sina名称序列无日期; 待定(东财F10报告名未知)
- 需要: 当前ST快照(206只)作兜底; 但任务要求修复"206只全程标记"失真→避免对无日期的当前ST股全程标记
## 阶段1 定稿（2026-08-16 续）
- 引擎代码格式：KLINE_DIR 文件名 "000001_daily_qfq.parquet" → code 6位数字；st_history_ranges.csv 需用 6位 code 匹配
- SZSE bulk(简称变更) 7462行精确日期，覆盖SZ含退市
- SH: baostock query_all_stock(day) 全市场逐日名称（含ST），月网格+过渡月细化
- BJ: baostock无覆盖(0)；sina名称序列无日期；eastmoney F10报表名未找到 → BJ用 sina序列+首K线日下限+现快照上限，报告注明局限
- 关键事实：当前 ST_CSV=stock_info.csv 仅300行全 is_st=False → **现役回测 ST 排除实际为0**；st_history.parquet 未接入引擎
## 阶段4 收口
- 最终 st_history_ranges.csv: 1006 行/767 码/725 在宇宙 (szse_bulk 908 + retire 11 + snapshot 84 + bj 3)
- 对照回测(locked≤2024-06-30): v0_seed +0.20pp 年化/+0.44pp Sharpe; v2b_trr +0.20pp/+0.43pp; MDD 不变 → <1pp, 现役数字无需修订
- 关键修正: 引擎原 ST 排除实际为0(stock_info.csv 300行全False, st_history.parquet 未接入)
- baostock query_all_stock code_name=最终名非当日名 → 弃用; SH 历史区间用快照兜底(2026-08后)
