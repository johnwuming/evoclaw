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

## 预注册取证（18:35）
- R-298 md 落盘 18:35 前；e4_prereg.json sha256=58f4d28e565507eaeffd1313113bafe5cc2719b448d693a78ced0fbae77958ff（mtime 18:30:04 系统 UTC+8 校验）
- 试验冻结：V6(正股总市值 MC_pct 残差化替换 issue_sz) / V7(V6+close≥105) / S1(110) / S2(−0.2·P·(1−MCp) 交叉降权)，n_trials=4
- G0 锚 = 0.5829611184870819（|Δ|<1e-9）；G1-G5 沿 R-288；G6 = a13 重叠窗 corr<0.5
## 口径复刻验证（18:38）
- G5 容量公式验证通过：Cap_m=Σ 0.1×mean20d(close×volume)，无 ×100（2018-01 重建 14179.8万 vs csv 14179.8万 逐位一致；2020-06 一致；2018-06/2024-06 差~2%系 trades 重建 holdings 误差→e4 改为回测内直接 dump e4_holdings_*.jsonl 消除该误差源）
- IC 监控口径：信用过滤后 universe（filter_universe 无价格门）逐月 rank IC of f_dual_low / −close vs fwd_ret，n≥30
- e4_backtest.py 已写（py_compile OK）：G0→V6/V7/S1/S2→IC→结合表（仅 G6 PASS 触发）

## 正股市值采集完成（18:43）
- 885/885 全成功、0 fail、725.4s；月度面板 stock_mktcap_monthly.parquet：425月(1991-04..2026-08)×885股，回测窗覆盖见 md5+coverage 校验输出（补记于下）
