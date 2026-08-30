2026-08-30 10:22:52 task-0576 E1 画像启动：组合增量闸（微盘MA趋势闸×大小盘价差动量）vs 现役 q3z+ddc15。先读输入，后 HP 实查定义。

## 1. 输入锚点（已读全，2026-08-30）
- 对象：a13_rsraw_e1f10dz 全期 nav（HP results/a13_rsraw_e1f10dz_full_nav.csv，5008日，raw 无 ddc，ann22.02%/maxDD-33.55%）
- 判门：组合闸（微盘MA趋势状态闸 × 大小盘价差动量）相对【q3z 择时门 + ddc15】的增量
- 痛段（须覆盖）：2015型 maxDD(-33.6%)、2026-05~07(-16.1%未修复)、2024Q1(-9.9%缓冲)、风格段 2014-12(-10.9%)/2020-09~2021-01(-14.5%)
- 先例红线：R-222 纯趋势 MDD-38~-52%；R-250 RV门与dd20重叠85.3%/Jaccard0.12已冻结；R-284 ddc15 score0.8834 holdout MDD-15.78%待激活
- 四参数网格：MA标的/周期/仓位映射/确认期；确认期扫0/1/2/3；先做RV门重叠度检验（防冻结覆辙）
- 数据源线索：R-250 记 timing_v2/signal_series.parquet 有 M_micro_ew（微盘等权日指数 2006-01-05~2026-08-07）；a12_pos_micro.csv 有 MA15_base（q3z形日频仓位）→ 库内无中证2000/万得微盘官方指数，M_micro_ew 即微盘标的代理
- RV 参照系：HP results/r250/rv_monthly.csv（日频状态可按 R-250 公式复算：ln(M_micro_ew) 20日std×√252，trailing756日分位≥0.7=高）

### 扫描结果（日频执行，2026-08-30 跑通，HP results/p2gate_task0576_scan.csv 14 行）
- 校验：MDD raw −0.3355 精确吻合 registry −33.55%；dd20=197 天精确吻合 R-250/R-373；ann 复算 23.31% vs registry 22.02%（年化基数口径差：交易日年 vs 日历年，如实标注）
- MA 闸（zz500 标的）：MA20_c0_full ann 19.17%/MDD −15.51%/Sharpe 1.696/鞭打 25.9/年；MA20_c0_half ann 21.43%/MDD −20.43%；MA20_c2_full OOS MDD −11.47% 最优
- MA60 档 MDD 改善弱于 MA20 全部档；鞭打低（9.4-12.9/年）
- 价差动量闸独立：全面劣——L20 ann 14.42%(−8.9pp)/MDD −28.96%(仅+4.6pp)；L60 MDD −37.28% 反恶化；L120 持平 raw。独立不成立
- COMBO(MA20_c0_full+MOM_L20)：MDD −13.66%（比单 MA20 再+1.9pp）但 ann 12.85%（再−6.3pp），不划算
- DDC15 同 nav 同参数复算：MDD −25.29% vs R-284 报告 −25.33%（机制复算吻合✓），ann −1.06pp，鞭打 2.62/年
- 重叠检验（risk-off 天 vs dd20 天）：MA20 coverage 68.5%/precision 6.1%/Jaccard 0.059；MA60 coverage 86.8%（接近 RV 的 85.3%）→ MA60 与危机段高重叠疑似同构；MA20 coverage 低 31.5% 危机日在场（修复段回场），结构不同于 RV 同步伴随
- 关键缺口①：日频闸切换成本未计（25.9 次/年×整仓进出成本量级可观）→ 必须跑月频执行变体（搭 a13 月频调仓便车）
- 关键缺口②：2026 段/2015 段分段行为需从 scan CSV 取数核对

## 2. HP 实查（2026-08-30，全部只读）
- registry=model/main.json：timing.type=q3z_x_ew_trend_overlay；signal="EW指数月末<MA200 → ×0.6"；q_key=q3z(win36,zscore,hi1.0,cut0.40,w_min0.3)；ddc15 字样 0 命中（ddc 是回测参数非 registry 条目）
- ddc 引擎语义（scripts/backtest_dividend_quality_iter.py L536-543 实读）：cur_dd=nav/peak-1；pos_ratio>0.999 且 dd≤-thresh → pos=reduce(0.5)；pos<0.999 且 dd≥-recover(-0.05) → pos=1.0。a15_ddc15 metrics 实查：drawdown_control=1,dd_thresh=0.15,dd_reduce=0.5；全期 ann 0.1901/maxDD -0.2533/Sharpe 1.3669/Calmar 0.7506
- **a15_run.py L1-40 实读关键发现：a15 批（含 ddc15）自带 q3z×EW-MA200 择时（ma_window=200,floor=0.30,q3z_on=True）** → a15_ddc15 nav≈「q3z+ddc15」现役叠加态的实际回测产物，可直接作对照锚
- q3z 日频仓位代理=timing_v2/a12_pos_micro.csv 的 MA15_base 列（R-250 同款口径；2026-05-06≈0.677 → 2026-07-29≈0.450，2026 段确有降仓）；连续 0-1
- 微盘 MA 标的=signal_series.parquet M_micro_ew（微盘等权日指数，2006-01-05~2026-08-07）；价差=zz500/hs300（2006-01-01~2026-08-08）；库内无官方微盘指数（R-373 缺口口径不变，M_micro_ew 为代理）
- RV 参照系=results/r250/rv_monthly.csv（rv20/rv_state=high|low，月末粒度）
- a13dz nav 尾 2026-08-14=64.3096；a15_ddc15 尾=36.1354
- 工作副本目录 HP:~/quant-evolve/work_tmp_task0576/ 已建；不动任何在役文件

## 3. 设计定格（运行前预注册）
- 组合闸定义：S=MA标的收盘≥MA_n（确认K日；K∈{0,1,2,3}）；G=zz500/hs300 比率20日动量≥0；仓位映射三种：bin_half（S:1/0，G=0 时×0.5）、tri（S+G 计数 2/1/0→1.0/0.5/0.0）、floor（S:1/0.5，G=0 时×0.5→{1,0.5,0.25}）
- 网格：MA标的{micro_ew,zz500}×周期{20,60}×映射{3}×确认{4}=48 组合；价差窗固定20（最优组加60日敏感性）
- 基线：raw；q3z 代理（MA15_base）；ddc15 实际 nav（a15_ddc15_full）；ddc 模拟器按引擎语义复刻并在 raw 上验证；叠加基线 stack_base=pq×ddc_sim；叠加候选 stack_comb=pq×comb×ddc_sim
- WF：W1 IS 2006~2015→OOS 2016~2021；W2 IS 2006~2021→OOS 2022~2026-08；IS 内 Calmar 最大者入选
- 判门预注册标准：stack_comb 相对 stack_base 全期+OOS MDD 改善≥3pp 且 ann 代价≤3pp，且 2026 段/风格段有实质覆盖，且与 RV 门重叠结构不同（非 RV 再derive）；任一不满足→不建议进 E2 或降级为条件建议
- PIT：全部信号 t 收盘可得，pos.shift(1) 施加于 r(t+1)；暖机期 MA 未就绪→中性满仓；闸换仓成本另报（Σ|Δpos|×15bp，约 ann 拖累）
