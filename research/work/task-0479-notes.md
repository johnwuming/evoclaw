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
- 885/885 全成功、0 fail、725.4s；月度面板 stock_mktcap_monthly.parquet：425月(1991-04..2026-08)×885股，md5=1311ef16cabbad45ed40b430de6c616f；窗102月，覆盖率均值89.3%、最低66.7%@2018-01(早期)、末月99.2%；fillna 0.5 兜底

## e4 核心回测结果（18:47 首跑完成，e4_run.log + e4_gates_result.json）
- **G0 PASS 逐位一致**：V2 复现 corr=0.5829611184870819（=锚，|Δ|=0）→ 环境零漂移
- **V6**（正股市值中性化）：G1 超额 +2.49pp FAIL（V2 基线 +5.33）；G2 -9.19% PASS / G3 前+2.20后+2.81 PASS / G4 15.8% PASS；**G6 corr(a13,78月)=0.5068 FAIL（边际）**；i3_base 102月 0.5916
- **V7**（V6+P≥105）：G1 +1.23pp FAIL；G2 -9.36% / G3 +1.43/+1.02 / G4 12.5% PASS；**G6 corr=0.5240 FAIL**；i3_base 0.6336
- **S1**（110 下限）：G1 +0.53pp FAIL；G6 corr=0.5225 FAIL → 价格下限越高超额越死、corr 几乎不动（0.524→0.522）
- **S2**（交叉降权）：G1 +2.37pp FAIL；**G6 corr=0.4908 PASS（唯一<0.5）**——但判胜需 G1-G6 全过，S2 仅敏感性
- **裁决：V6/V7 双主试验 G1+G6 双 FAIL → 负结果**。机制终证：超额与 corr 同源（低价/小市值维度），中性化/过滤在压 corr 的同时等比例杀超额（+5.33→+2.5→+1.2→+0.5），无免费午餐
- 结合表：预注册规定仅 V6/V7 任一 G6<0.5 才补 → 均未达标，跳过（合规）

## E4 执行启动（18:44）
- 18:43 sha256 复验 e4_prereg.json = 58f4d28e...58ff（与冻结一致）；mktcap 面板 (425,885) 可读
- 18:44 nohup 启动 e4_backtest.py → work/r474/e4_run.log；流程 G0(锚 0.5829611184870819, |Δ|<1e-9) → G0_FAIL 则 sys.exit 不进判门

## E4 核心回测完成（18:46，耗时约 2 分钟）
- G0 对拍 PASS：corr=0.5829611184870819，与锚 0.5829611184870819 完全一致（Δ=0<1e-9），无环境漂移
- 主窗 102 月（2018-02..2026-07），基准年化 6.09%；a13 重叠 78 月（2018-01..2024-06）
- V6(市值中性化)：G1 超额 +2.49pp FAIL；G2 MDD −9.19% PASS；G3 前后窗 +2.20/+2.81pp PASS；G4 换手 15.8% PASS；G6 corr=0.5068 FAIL（差 0.0068 临界）
- V7(V6+close≥105)：G1 +1.23pp FAIL；G2 −9.36% PASS；G3 +1.43/+1.02pp PASS；G4 12.5% PASS；G6 corr=0.5240 FAIL
- S1(110)：G1 +0.53pp FAIL；G2 −8.48% PASS；G3 +0.16/+0.93pp PASS；G4 10.9% PASS；G6 corr=0.5225 FAIL
- S2(交叉降权)：G1 +2.37pp FAIL；G2 −9.56% PASS；G3 +1.99/+2.78pp PASS；G4 15.9% PASS；G6 corr=0.49075 PASS（四轮唯一 <0.5）
- IC 监控（信用过滤 universe）：见 gates JSON dual_low_mean/price_mean
- 结合表：V6/V7 G6 均 FAIL → comb={} 空（符合预注册仅 G6 PASS 触发条件）
- 初步判门：无变体六门全过（S2 过 G6 但 G1 差 2.6pp）；四试验 = 2 正结果失败 + 负结果归档方向
