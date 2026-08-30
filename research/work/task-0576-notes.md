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

## 4. 运行结果（产物=HP work_tmp_task0576/t0576_*.json|csv，已镜像本目录）
### 4.1 RV 门重叠度检验（预注册第 1 步）——通过，非 RV 再derive
- 复现锚：P(RVhigh|dd20)=0.853 与 R-250 完全一致；dd20=197 日吻合
- 候选 risk-off（rep=micro MA20 K=2 tri）与 RV high：P=0.303/Jaccard 0.261/corr 0.124 —— 结构不同于 RV 门（RV 门对 dd20 是 0.853 的同步伴随）
- 候选 vs dd20：P(dd20|ro)=0.05、Jaccard 0.049 —— 非回撤追随型
- 与 q3z 代理互补：q3z 高仓（上 1/3）时候选仍降仓比例 46.4%；ro 日 q3z 均值 0.449 vs 非 ro 日 0.518
- 注：与 r250/rv_monthly.csv 月末状态逐月一致率仅 71%（口径漂移），但危机边际（dd20 重叠 85.3%）精确复现，参照系可用；ro_hard 定义滑点（tri 映射下=ro_any），硬降仓用 zero_pos_pct 代替
### 4.2 全期网格（48 组合，t0576_grid_full.csv）
- Calmar：min 0.396 / med 0.716 / max 1.188（raw=0.667）；31/48 超 raw
- 结构：MA20 med 0.803 >> MA60 0.621；zz500 0.757 > micro 0.614；bin_half 0.856 > floor 0.728 > tri 0.672；K: 0/1(0.784) > 2(0.752) > 3(0.643)
- **反直觉**：帖子的「微盘指数 MA」不是最强变体（zz500 更稳）；帖子的「2 日确认」被证据否定（K 越大越差，micro|60|K2/3 MDD −35.5%/−37.6% 比 raw −33.55% 还差）
- 成本（15bp/单位换手）：comb-only med 2.09pp/年、max 3.74pp/年 —— 单独使用净值经济性弱，价值在叠加
### 4.3 基线（全期，t0576_baselines.json）
- raw: ann 22.39%/MDD −33.55%/Calmar 0.667（MDD 与 registry 逐位吻合=验证器通过）
- q3z 代理(MA15_base): 12.45%/−17.32%（保守代理，真 a15 实际 ann 19.02%/−25.33%）
- sim ddc(raw): 20.22%/−22.89%，9 次触发——引擎语义复刻合理
- stack_base(q3z代理×ddc15): 12.12%/−16.20%/0.748
### 4.4 叠加组合（t0576_stack_comb.json；**全期 top5 为样本内选择，只作参考**）
- micro|20|0|bin_half 叠加：ann 25.06%/MDD −5.04%/Calmar 4.97；vs stack_base Δann +12.9pp/ΔMDD −11.2pp
- zz500|20|0|bin_half 叠加：23.32%/−8.92%/2.615；五痛段全部改善：E2015 −2.25%(基线−14.68)、E201412 −8.92%(−10.02)、E2020style −2.79%(−6.65)、E2024Q1 −0.30%(−2.36)、E2026 −2.52%(−6.45)
- PIT 抽查通过：翻转日次日成立完整承担（如 2006-03-01 翻满仓次日 −2.21% 全额计入）；series 本地复算逐位一致
- 空仓占比（zz500 best）：E2024Q1 70.3%、E2026 56.9%、E2015 52.2%、E2020style 52.4%
### 4.5 Walk-forward（判门核心证据，t0576_wf.json）
- 两窗同选 zz500|20|0|bin_half（IS Calmar 选择，选择稳定）
- OOS1 2016-2021：stack_comb 16.34%/−3.43%/4.76 vs stack_base 3.97%/−8.25%/0.48 vs raw 8.45%/−18.26% → Δann +12.4pp、ΔMDD −4.8pp
- OOS2 2022-2026.8：stack_comb 10.84%/−4.29%/2.53 vs stack_base 6.69%/−9.14%/0.73 vs raw 12.32%/−16.13% → Δann +4.2pp、ΔMDD −4.9pp
### 4.6 与真实在役对照（a15_ddc15 实际 nav）
- a15（自带 q3z×EW-MA200）残余痛点：E2015 −23.14%、E2020style −12.44%、E2026 −12.73% —— 与 R-373「真无防御痛段」一致
- 组合闸恰对此三段有效（叠加后 −2~−9%）→ 对真实在役件的互补性定性成立

## 5. 竞态与编号处置（2026-08-30 11:4x）
- 发现同任务竞态重复运行（R-371 先例重演）：A 线已交付 `05-量化投资/R-374-微盘P2闸设计E1画像.md`（10:49）并写入 completions；本线（B）报告原取 R-374（spawn 时实查空闲）→ 重号
- 处置：B 线报告改名 `R-376-大小盘价差动量x微盘MA趋势闸组合增量E1画像.md`（R-375 已被 task-0577 占用），文内加编号说明与 A 线交叉引用
- 互相印证核验：A 线 README 摘要关键数字与本线一致——zz500 MA20 组合闸单腿 MDD −15.51%（逐位同）、dd20=197 天、动量闸独立判负、月频形态判负、判门同为有条件进 E2；互补增量：本线 RV 门信号级重叠检验（0.303/Jaccard 0.261）、q3z 代理×ddc15 叠加态 WF 双窗 OOS（ΔMDD −4.8/−4.9pp 且 Δann 为正）、40bp 成本敏感性、E2 条件细化；A 线独有：月频执行形态全负、MA60 coverage 86.8% 同构降级分析
- 注：本笔记文件现仅含 B 线证据链；A 线证据在其报告与 HP p2gate_task0576_* 产物（若 A 线曾写本文件，已被 B 线首写覆盖，以 A 线报告为准）
