# task-0437 工作笔记：估值×质量交互因子 E1 画像（R-269）+ 风格轮动 E2 预注册（R-270）

- 日期：2026-08-21 21:42 开工 | 任务中心 task-0437 已置 running
- 纪律：零回测（A 全程 IC 画像；B 纯文档）；零引擎/registry/paper_engine/crontab 改动；HP 已跑进程不动；计算 nohup

## 一、预登记（2026-08-21 21:58 写定，先于任何因子计算，禁止事后调线）

### 1.1 因子族定义（口径固定）

数据（全部 HP 在库，PIT）：
- ths_ttm_panel.parquet（code/report_date/avail_date/net_profit_ttm/equity/roe_ttm/roa_ttm/debt，235,170 行，1997 起）：净利 TTM、净资产、roe_ttm 季度史，自有 as-of 对齐（avail_date ≤ 月末取最新）
- fundamentals_monthly.parquet（code/date/div_yield_ttm/circ_mv/roe_ttm/roa_ttm，2006-01→2026-08，5032 只）：市值、股息率（引擎在役面板同源，R-241 pb 先例同款）
- fin_panel（factor_registry_financial_panel.parquet，PIT 月度化，构建处已核 avail_date≤月末取最新）：net_profit_margin（SP 近似用）
- all_stocks_merged.parquet（2006-01-04 起，14.6M 行 qfq 日线）：月末收盘、次月收益、amt20、上市天数

因子（月末截面）：
- EP = net_profit_ttm(as-of) / circ_mv
- BP = equity(as-of) / circ_mv
- DP = div_yield_ttm（面板直取）
- SP = (net_profit_ttm / net_profit_margin) / circ_mv，仅 net_profit_margin>0.02 时有效；TTM 净利×报告期净利率的近似，如实披露
- EP_stab = EP × 1[std8 ≤ 0.05]；std8=过去 8 季季报 roe_ttm 的 std（as-of 月末 avail≤），≥6/8 非缺失才计，否则 NaN
- EP_impr = EP × 1[mean4 ≥ mean8]；mean4=近 4 季 roe_ttm 均值（≥3/4 非缺失），mean8=近 8 季（≥6/8 非缺失）；设计意图=排除盈利脉冲见顶票（task-0435 九安医疗教训：3 年 ROE 高均值≈脉冲刚见顶）

三口径：
- a) 原始：EP/BP/DP/SP
- b) 中性化：**行业分类在库不存在（面板无行业列；akshare eastmoney 板块接口 Connection refused，与 R-268 eastmoney 不可得一致）→ 申万映射不可得，如实标注**。替代口径=市值十分位哑变量中性化残差（EP_dz/BP_dz/DP_dz/SP_dz），明确标注这是**替代口径非行业中性**，作用轴=最强混淆变量（市值）
- c) 质量交互：EP_stab / EP_impr（原始值，不叠加中性化）

### 1.2 画像口径（W1 一致，R-251/R-257 复刻）

- IC[m] = spearman(F_m, R_{m→m+1})，月频全市场，min_obs=20
- 股票池：merged qfq 在市、上市满 120 交易日（以 merged 起点计数，2006 年内新股有高估预热期偏差，披露）、当月有交易、有次月收益
- 截面预处理：去极值 1%/99% + zscore（中性化回归在 zscore 后做）
- 主口径评估窗：因子月 2006-01→2026-06（次月收益完整到 2026-07-31）；2026-07（次月收益仅到 08-10，部分月）仅作敏感性附录
- 五分段：评估窗等分 5 段，每段 IC 均值/ICIR/符号
- 分组：月度五分位等权次月收益 Q1..Q5 + Q5−Q1 月均价差、t、胜率
- 冗余：①对新四因子（log_mv/amt20/pb_inv=circ_mv÷equity 同式复刻/roe_ttm）月度截面 spearman（均值+p90）；②IC 序列相关 vs factor_ic_monthly.csv 在役因子 + r0419 csad_sigma20 IC（csad_resid 月度文件未落盘，用家族代表 sigma20，如实标注）

### 1.3 达线判定（预登记，三条件全过才建议 E2 预注册）

判定对象：EP 族（EP 及 EP_stab/EP_impr）。BP/DP/SP 画像完备性输出，不参与达线（BP 与 pb_inv 同源可预期）。

- P1 信息量：候选交互因子 |ICIR| ≥ 0.25（主口径）
- P2 稳定性：该候选五分段符号与全样本一致（无方向翻转）
- P3 交互增量：max(ICIR(EP_stab), ICIR(EP_impr)) > ICIR(EP)（严格大于，同号）
- 存在 f∈{EP_stab, EP_impr} 同时过 P1+P2+P3 → 建议进 E2 预注册；否则负结果归档
- 冗余门（披露不判死）：|ρ|>0.6 在役即标冗余；BP~pb_inv 同源属预期，如实报

### 1.4 B 线（R-270）框架预登记

纯文档，无计算。判胜门槛数字在 R-270 内论证并预登记（危机窗 MDD 改善 ≥2pp、全窗年化损耗 ≤1pp、稳健门、holdout 披露），引用 R-268 实测数字，不新拉数据。

## 二、执行日志（边查边写）

- 21:42 任务置 running ✓
- 21:43-21:57 参考文档读完：R-268（S1 达线四线全过、t=0.94 弱功效、当前 S1=0.742 激活 13 个月、中证2000 两源不可得、中证1000 代理）、R-257（W1 IC 画像结构、达线 |ICIR|≥0.25 先例）、R-252（E2 预注册结构：假设/信号/形态/网格/判胜门/停止规则）、task-0435（九安医疗盈利脉冲教训）
- 21:52 HP 数据核验：ths_ttm_panel 8 列含 avail_date ✓；fundamentals_monthly 2006-01→2026-08 ✓；fin_panel PIT 月度化确认（factors_ext.build_financial_panel：取披露日≤月末最新一期）✓；merged 14.6M 行 2006-01-04 起 ✓
- 21:54 行业数据：面板无行业列；akshare stock_board_industry_name_em → Connection refused（与 R-268 eastmoney 记录一致）→ 口径 b 改市值十分位替代，如实标注
- 21:56 csad_resid 月度文件未落盘（find results 无 *resid*）→ 冗余检查用 r0419 csad_sigma20 ic_monthly.csv 家族代表，标注
- 21:58 本预登记写定 → 开写计算脚本
- （后续计算结果见下节，计算完成前不回改本节）
