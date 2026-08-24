# task-0479 可转债去相关第四轮 V6/V7 过程笔记
启动: 2026-08-24 18:25 CST

## 步骤日志（边查边写）

## 环境核验（18:26-18:31）
- e3_backtest.py / e3_gates_result.json / e3_capacity_monthly.csv(99行) / e3_ic_filtered_universe.csv(103行) 在位；/tmp/r281(csi_cb_index基准+compute_ic.py) 与 /tmp/r286_daily(376券日频) 缓存存活。
- V2_G0 锚目标 = e3_gates_result.json V2_G0 corr 0.5829611184870819（78月重叠 2018-01..2024-06，报告口径称77月）。
- G5 口径（R-288 §2.2 冻结）：Cap_m = Σ当月全部持有券 10%×ADV(月末前20交易日日均成交额)，volume×close 近似成交额，主窗中位数≥2000万；e3_capacity_monthly.csv 为 V3 全持仓口径（列 ym,cap,got,n_hold）。
- IC 监控口径 = /tmp/r281/compute_ic.py（信用过滤后 universe，E1 口径），锚：dual_low 0.0451 / price 0.0966。
- R-289 §6 已复读：corr 源头=低价/小市值维度，发行规模静态代理对真实流通规模表征弱 → 本轮换正股总市值。
- 数据源测试：akshare 1.18.94 无 stock_a_lg_indicator；改用 stock_zh_valuation_baidu(总市值,全部)——日线级采样(中位间隔9-11天，新券2天)，亿元，退市正股(002072搜特)仍有历史。PIT 说明：百度总市值=历史收盘×历史总股本→时变股本内生，优于当前快照；披露采样近似(月内最后观测)。
- 18:31 启动 885 正股采集（fetch_mktcap.py 后台，限频0.5s/重试2/1200s时限/可续传）→ /tmp/r474_mktcap/ + work/r474/stock_mktcap_monthly.parquet
