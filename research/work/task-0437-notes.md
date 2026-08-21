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
- 22:03 脚本部署 HP（scp 拒连 → ssh 管道传输，md5 574021d30728be7a6932f1e3b422ed00 两端一致）；nohup 启动 pid 661644，142s 完成，零报错（空切片 warning 为全 NaN 月正常现象）
- 22:07 独立抽验：2010-06/2017-01/2024-06 × EP/BP 共 6 个 IC 从 factor_monthly.parquet 重算与 ic_monthly.csv 逐位一致（n=1406/2471/4858）✓

## 三、A 线计算结果（主口径 2006-07→2026-06，240 月；前 6 月因上市天数预热宇宙为空，如实计入）

### 3.1 主表（IC 均值 / ICIR / t / IC>0 占比 / 五段符号）

| 因子 | IC | ICIR | t | pos | 五段 | 分组 Q1→Q5（月均） | Q5−Q1 价差 |
|---|---|---|---|---|---|---|---|
| EP | +0.028 | +0.223 | +3.45 | 0.61 | 全正 | 1.61→1.94% | +0.33pp t=1.32 胜率 58% |
| BP | +0.061 | +0.565 | +8.75 | 0.74 | 全正 | 0.86→2.32% | **+1.50pp t=5.74 胜率 72%** |
| DP | +0.027 | +0.261 | +4.04 | 0.60 | 全正 | 1.27→1.96% | +0.20pp t=0.82 |
| SP | +0.039 | +0.417 | +6.47 | 0.65 | 全正 | 1.13→2.04% | +0.91pp t=4.19 胜率 63% |
| **EP_stab** | +0.025 | **+0.297** | +4.60 | 0.62 | 全正 | 1.89→1.88% | **−0.02pp t=−0.07（≈0）** |
| EP_impr | −0.003 | −0.047 | −0.73 | 0.45 | 段3 微正余负 | 混乱 n=88 月 | +0.64pp t=1.63（覆盖差） |
| EP_dz | +0.015 | +0.125 | +1.94 | 0.55 | 段2 微负 | — | — |
| BP_dz | +0.036 | +0.282 | +4.37 | 0.58 | 全正 | — | — |
| DP_dz | +0.025 | +0.256 | +3.96 | 0.60 | 全正 | — | — |
| SP_dz | +0.016 | +0.145 | +2.24 | 0.54 | — | — | — |

单调月占比（Q1≤Q2≤…≤Q5 严格不降的月份占比；随机≈0.8%）：BP 19% > EP 14% ≈ SP 13% > DP 5% >> EP_stab 1%（≈随机）、EP_impr 0%。

### 3.2 达线判定（对照预登记 P1/P2/P3）

- EP_stab：P1 ✓（0.297≥0.25）P2 ✓（五段全正）P3 ✓（0.297>0.223 同号）→ **形式达线**
- EP_impr：P1 ✗（−0.047）→ 死
- 预登记条款判定=达线；但如实披露矛盾证据：**EP_stab 的 IC 增量不转化为多空价差**（Q5−Q1≈0、单调月占比≈随机）——增量全在排序中段，组合级（买尾卖头）拿不到。R-269 采用 R-257 先例「达线+硬性前置」框架，综合建议=暂缓 E2、以负结果倾向归档（详见报告 §五）

### 3.3 冗余（截面 spearman 月均，p90；IC 序列相关另计）

| 新因子 | log_mv | amt20 | pb_inv | roe_ttm | 判定 |
|---|---|---|---|---|---|
| EP | −0.14 | +0.01 | −0.50 | **+0.69** | 与 roe 超线冗余 |
| BP | −0.37 | −0.25 | **−1.00** | −0.09 | 与 pb_inv 完全同源（预期内） |
| DP | +0.02 | +0.02 | −0.34 | +0.34 | 干净 |
| SP | −0.28 | −0.15 | **−0.62** | +0.27 | 与 pb_inv 临界超线 |
| EP_stab | +0.08 | +0.03 | −0.19 | +0.22 | **干净**（二值化打破机械相关） |
| EP_impr | +0.13 | +0.12 | +0.05 | +0.40 | 干净但无信息 |

IC 序列相关（时序维度）：EP~roe_ttm +0.86、DP~roe_ttm +0.73、SP~pb_inv（自查面板内）——估值因子族的月度 IC 景气与 roe 因子同步涨落。csad_sigma20 IC 相关：见 summary.json（弱，未超线，详见报告）。

### 3.4 在役四因子自查 IC（同口径参照，面板正确性 sanity）

log_mv −0.054/−0.314、amt20 −0.104/−0.675、pb_inv −0.061/−0.565、roe_ttm −0.011/−0.085——方向与量级与 R-251 同期口径（circ_mv 0.269 等）量级一致（窗口不同不逐位对表），面板可信。

### 3.5 敏感性 2026-07 部分月（次月收益仅到 08-10，单月）

全估值族深负（EP −0.32/BP −0.41/SP −0.35/EP_stab −0.28）——7 月动量延续、价值回撤月；单月不改变主口径结论，如实存档。

### 3.6 产物与 md5（HP results/work/r0437/）

- ic_monthly.csv 27358ba721b3342944c1c8dd0cf22141；summary.json 33df6a1b5aa18da2303b38cc563f5b35
- factor_monthly.parquet（43MB，留 HP 不镜像）b41eea57f0ff646376b8e611c653aff6
- quintile_monthly.csv / xs_corr_monthly.csv / build.log 同目录；脚本 scripts/r0437_valuation_quality.py（md5 与 VPS /tmp 同 574021d3…）

## 四、B 线（R-270）

- 22:04 R-270 写入 shared/results/05-量化投资/R-270-风格轮动E2预注册.md（6.3KB）：六段式结构，S1 主信号+拥挤辅助确认（不作协同门，n=6 样本过小）、引擎间权重切换与 R-233 边界四条、网格 X∈{30%,50%}+G0+T3 敏感性=计账 ≤4、四门（G1 危机 MDD≥2pp/G2 全窗损耗≤1pp/G3 分段>−1pp/G4 holdout 披露）、代理源前置（自算微盘等权 PE 秩相关 ≥0.6 或换源）、停止规则与激活人工门
- 全部数字引自 R-268/R-252，零新计算 ✓
