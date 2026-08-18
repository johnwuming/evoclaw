# task-0362 过程笔记：择时v2 E2 结构 A/B 组合回测（REB/NMTAP/超跌C）

任务：task-0362，产出 R-233。E2 结构 A/B 回测。

## 0. 前置输入摘要（已读 10:05）
- R-230 §六 E2：同信号集下乘法合成(现役 macro_timing_layer 式) vs 优先级覆盖(华福式 底部/危机>顶部>均线)，n_trials=2；口径=A9微盘等权/月频调仓+日频信号闸门/成本v2+一字板(同R-222)；locked=2006-01~2024-06，full至2026-08，holdout=2024-07~2026-08。
- 任务书(user 2026-08-18 指示)把 E2 A/B 具体化为：A=REB 单信号门(底部入场)，B=REB+NMTAP+超跌C 组合门(底部三重确认近似)；顶部可加 FLOW/SPREAD 走弱作退出。剔除期权维度(PCR/QVIX 不用)。
- R-231 E1 关键结论：REB 97次/76.3%(唯一强信号，与超跌族正交)；SPREAD 顶部构造性失效(0.85 不可达) → 顶部退出用 FLOW 走弱或 MA15，不用 SPREAD；C 危机通道需加"首日反转"限定(前5日无触发)；B1 超跌单独 53%，作 B 必要条件。
- 数据缺口规则(R-230)：NMTAP 2010-03 前恒不触发；禁止回填；分段披露。
- R-222 基准：v6a_def=MA15_on_f0 (locked 14.63%/-24.67%)；成本 v2+一字板。


## 1. 数据勘察（10:0x）
- HP `data/derived/margin_sse_daily.parquet`：3979 行 × 7 列，2010-03-31~2026-08-17，列=[信用交易日期,融资余额,融资买入额,融券余量,融券余量金额,融券卖出量,融资融券余额]。两融 2010-03-31 启动 ✅（R-230 预期）。
- VPS `/root/tv2data/out/signal_series.parquet`（E1 产物副本，同 HP results/timing_v2/）：5003 行 × 24 列，含 M/M_micro_ew/breadth/SPREAD×3/REB/FLOW/FLOW_MA3/dd60/dd250/dev15/rsi14/ret1 + 全部触发 flag（含 flag_REB_bottom、flag_B1_oversold、flag_C_crisis、flag_FLOW_pos_cross）。✅ E2 所需底表齐备。
- VPS python：/opt/finworker/bin/python（pandas 3.0.5 / pyarrow 25.0.1 / numpy 2.5.2）✅（E1 同款 venv，路径已确认）。
- HP 内存仍紧张（free: 可用 129MB、swap 0），继续 VPS 计算、产物回写 HP 的路径。

### 待办
- [ ] 读 R-226 确认 P1 纪律措辞
- [ ] margin 数据单位核对（融资余额 2010≈582万 vs 2026≈1.36万亿，疑单位不一致，须核实后统一）
- [ ] 计算全市场成交额（merged 流式 Σamount/日）
- [ ] NMTAP_t = MA5[(融资买入−融资偿还)/全市场成交额]，偿还=余额_{t-1}+买入−余额_t；2010 前恒不触发
- [ ] 搭 E2 回测：v6a_def(MA15_on_f0) 基准 / A=REB单信号门 / B=REB×NMTAP×超跌C 三重确认+C 危机通道快道；FLOW 走弱作顶部退出；n_trials=2
- [ ] 分段披露 2006-2016/2016-2026/locked/full/holdout
- [ ] 写 R-233 + 更新 README + 写 .task-completions.jsonl

