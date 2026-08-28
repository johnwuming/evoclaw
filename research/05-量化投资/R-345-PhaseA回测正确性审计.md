# R-345 Phase A 回测正确性六项审计报告

- 任务号：task-0537 ｜ 日期：2026-08-28 ｜ 性质：只读审计（零修复、零既有文件改动、不改 evolution_pipeline/registry/paper_engine/crontab/engines）
- 审计依据：R-336 v1.4 §5（审计项清单 A1–A6、三板斧、处置语义）+ §8 Phase A 动作 1
- 在役审计对象（model/registry/engines.json，3 引擎）：**A**（active，微盘选股 a13_rsraw_e1f10dz + q3z×EW-MA200 择时内化）、**A2**（shadow，a14_crowdf2 w=0.5 叠加于 A）、**gold_trend_sma200**（active，slot B，SMA200×波动目标10%×月频×现金增强）
- 过程笔记：`shared/results/work/task-0537-phase-a-audit-notes.md`

## 〇、总结论（先行）

| # | 审计项 | 判定 | 一句话依据 |
|---|---|---|---|
| A1 | 前视偏差 | **PASS**（附 1 项 Phase B 前强制补验） | pb join 真 as-of(avail_date)；四族信号 shift(1) 核验无恙；唯 fundamentals_monthly→roe/roa/div 过滤通道构建器未能在预算内核验 |
| A2 | 复权口径 | **PASS** | gold sleeve 157 月重放 md5 逐位一致（diff=0bp）；513100 拆分悬崖 qfq 修正实证（−80.45%→无悬崖） |
| A3 | 退市股处理 | **PASS** | 引擎宇宙=stocks_hfq+退市索引(365)+退市基本面面板，全量池「含退市」语义在代码与数据两层落实 |
| A4 | 涨跌停掩码贯穿 | **PASS**（附卖出侧缺口披露） | 回测层 limit_board=on；paper 层 is_limit_up 禁买闸 8/8 笔实测零违规；卖出侧无显式跌停闸（历史 0 笔卖出，未行使） |
| A5 | 滑点/冲击成本 | **PASS**（不阻塞项） | paper 真实费用三件套在账；R-333 三情态结论引用成立；参与率 0.002–0.07% 平方根冲击豁免成立 |
| A6 | 分红除息 | **PASS**（记录在案，无现实异常） | paper 持有窗口内分红事件=0（4 个代码级命中全在窗口外）；DIV_EVENTS 未接线属潜伏缺口，修复另行立项 |

**总裁决：六项无 FAIL，A1/A2 两个绝对阻塞项均 PASS → 放行 Phase B。**
附加条件三条（详见 §九）：①Phase B 影子层消费 a13 因子面板前，必须完成 fundamentals_monthly 构建器 PIT 补验（本审计唯一未尽事项）；②paper_engine 卖出侧跌停闸与分红入账两处缺口立修复项（不阻塞、不自动修）；③三套成本口径（回测 10bp/R-333 中间态 11.5bp/金假设 13bp）在 gate spec v1 落库时统一归一到 11.5bp/边基线。

## 一、审计执行方式

- HP 侧：`/tmp/audit_0537.py`（第一轮六项扫描）+ `/tmp/audit_0537_f3.py`（定向补验），只读 + 输出仅写新目录 `~/quant-evolve/results/phase_a_audit_0537/`（audit_findings.json、followup3.json）；python 均为 `/home/noname/miniconda3/envs/quant/bin/python`。
- 本地侧：gold 回测确定性重放（r483 复制到 `/tmp/r483replay/`，OUT 重定向，原件零触碰）；513100 复权对比（work/r323/raw 双源）。
- 三板斧对齐：①锚点单测（R-317 md5 引用在案 + gold 全历史重放）②月度对账（gold=全 157 月逐位；A股 paper=state/NAV 一致性核验）③R-333 引用不重做。
- 审计窗口内 HP 在役 cron（周日 20:00 refresh、日 16:30 paper daily）均不落在窗口内，无并发污染。

## 二、A1 前视偏差（PIT 对齐）——PASS

**方法**：逐 join 键核查 + 锚点断言 + 引用 R-343（task-0531，2026-08-28 同日出具的逐行代码核验）。

**证据**：
1. **pb/equity join 为真 PIT as-of**：`scripts/a9_common.py` L237–249 `merge_pb_into_panel`：`pd.merge_asof(p, ths.sort_values("avail_date"), by="code", left_on="date", right_on="avail_date", direction="backward")`——equity 只取披露日 ≤ 当日的最近值，无报告期直 join。R-328「000001 滞后 371 天」类缺陷在此路径结构性不可能。
2. **披露日映射健康**：`data/derived/ths_ttm_panel.parquet` 235,170 行，`avail_date − report_date` 中位 62 天 / 最小 30 天 / **负值 0 行**（无披露日早于报告期的脏数据进入）。
3. **信号对齐（四族核验，引用 R-343 §二/§三 + 本次复验）**：黄金族 r482/analyze.py L60、r483/e2_backtest.py L47/74/99 均真 shift(1)；择时 v2 族 `timing_layer_prod.py` shift(1)（本次 grep 命中）+「只允许 as_of_date 上月末及更早信号」；HP 在役 `paper_engine_gold.py` prev_me×12、PIT×2（信号取上一完整月末冻结）；A股 IC/截面 E1 族（12 份）「月末因子×次月收益」结构天然免疫同月对齐。
4. **QDII E1 前视缺陷（analyze3/analyze2 同月对齐）已由 R-341/R-343 定位并隔离**：该缺陷属已终止链路（E2 判门 FAIL 归档），非在役引擎，不在本审计阻塞面内；其标准污染（R-330 观察线 0.35 标定依据被击穿）R-343 已披露，属 G3 口径重冻结范畴，与在役三引擎上岗依据无关。
5. **锚点断言（三板斧①）**：R-317 四锚点 PIT 断言（2015-06=FULL/2015-07=REDUCE/2020-06=REDUCE/2020-07=FULL）与 F1 基线 md5 `915e446388…` 的逐位复现记录在案（R-317 L9：task-0492 于 /tmp 副本重跑，三输出文件 md5 逐位一致，原目录零改动）。注：该脚本本体随 /tmp 清理已不在盘，本审计引用该在案记录并如实标注。
6. **残留补验项（唯一未竟）**：`data/derived/fundamentals_monthly.parquet`（roe_ttm/roa_ttm/div_yield_ttm 过滤通道，a13 因子含 roe 0.3 权重）的构建器 `scripts/fetch_valuation_data.py` 中未见显式披露滞后关键词（grep lag/shift/avail/as_of 命中 0）；panel 本身无 avail_date 列。**未发现前视证据**（该通道可能天然按可得月份构建），但本审计未能在预算内完成其构建语义逐行核验，不得默证为安全。

**判定**：PASS。已核验通道全部干净；残留 1 项为「未完成核验」而非「发现缺陷」，列为 Phase B 影子层消费 a13 因子面板前的强制补验项（见 §九条件①）。

## 三、A2 复权口径——PASS

**方法**：全 sleeve 净值重算 diff + ETF 拆分案例实证（R-336 §5.1 A2 方法逐条）。

**证据**：
1. **gold sleeve 全历史重放逐位一致**：`work/r483/e2_backtest.py`（确定性脚本，无随机数）复制至 /tmp 重放，输出 `e2_nav_monthly.csv` md5 = `18bdf07bc3353f3884765fce2692cd49`，与原件及 md5.txt 在案值**逐位一致**（157 个月，2013-08 起全部月度净值/仓位/锚序列复现，diff=0bp ≤ 1bp 标准）；`e2_gates_result.json` 重放差异仅 `run_at` 时间戳与 NaN 比较伪差异两项，全部业务字段一致。该项同时覆盖三板斧②对 gold sleeve 的月度对账（强于抽 3 个月要求）。
2. **513100 拆分反例实证（R-330 F4 反例闭环）**：本地 r323/raw 双源对比——未复权 sina 序列单日最小收益 **−80.45%**（拆分悬崖，即 R-330 假 MDD −85% 之源）；qfq（tx）序列单日区间 [−9.59%, +11.19%]，**无悬崖**，符合 QDII ETF ±10% 涨跌停域。qfq 唯一口径在数据源层成立。
3. **双轨复权体系澄清**：引擎回测宇宙用 `data/stocks_hfq/`（后复权，5569 文件，保留分红再投资语义）+ paper/监控标记用 `all_stocks_qfq/{code}_daily_qfq.parquet`（前复权，当前价=真实价）。两轨各司其职（回测收益含分红、paper 标记贴近真实成交价），未发现混用导致的净值扭曲。
4. **A股 paper sleeve 净值一致性**：paper-state.json（cash=40393.0，持仓 0 只）与 baseline-paper-nav.csv 末值（2026-08-26 nav=0.9974，基资金额换算一致）对账相符。

**判定**：PASS。A2 绝对阻塞项解除。

## 四、A3 退市股处理——PASS

**方法**：股票池含退市股清单 diff + 幸存者偏差检验（数据层与代码层双向）。

**证据**：
1. **退市数据三层在位**：`data/delisted_pool.parquet` 361 只（code/name/exchange/delist_date/pause_date）；`data/stocks_hfq_delisted_index.json` **365 条**退市价格索引；`data/derived/fundamentals_delisted_monthly.parquet` 退市基本面月度面板在位。
2. **引擎宇宙显式含退市**：`scripts/paper_engine.py` L520–527 注释「语义逐行对齐 a9_common.patch_engine(PA/PB/PC/PD) + **q4b 全量池(含退市)宇宙**」，并直接引用 PANEL_DEL/HFQ_DIR/DELISTED_IDX 三数据源；`backfill_delisted.py`、`q4b_build_delisted_panel.py`、`w6_collect_delisted.py` 构建链完备。
3. **澄清一个反向疑点**：`data/all_stocks_qfq/`（6089 文件，qfq 目录）中退市股覆盖为 0——经追查该目录是 paper 标记/监控的现役标的行情源，**不是**回测宇宙源（回测走 stocks_hfq）；不构成幸存者偏差通道。
4. **残留披露**：361×hfq 按逐 code 精确对账因 hfq 文件名含交易所前缀约定未及归一，未完成到逐只配平；索引数(365)≈池数(361)已给出量级一致性。列为 Phase B 首月例行核查项（非缺陷）。

**判定**：PASS（历史各期股票池含退市股的机制在位；组合级历史结论可采信）。

## 五、A4 涨跌停可交易掩码贯穿性——PASS（附卖出侧缺口披露）

**方法**：三层（Data→Backtest 撮合→paper）各抽查；paper 全部真实成交逐笔复算。

**证据**：
1. **回测层**：a13 引擎 BASE 配置 `limit_board="on"`、`limit_up_pct=0.098`（a13_run.py L60）；limit_board 实现散布于 a11_rules/a8_bucket/a10_v6a_formal 等引擎文件（grep 定位 8 文件），一字板日不成交机制在回测撮合内生效。
2. **paper 层**：`paper_engine.py` L949 `is_limit_up`（pct ≥ 阈−1e-4，ST 分阈）+ L1251 买入前硬闸。**全部 8 笔真实买单逐笔复算：0 笔涨停日违规**。
3. **现实层（R-333 引用）**：300862 四连一字板实际不可成交已在 paper 真实成本对账中实证，paper 执行层与Reality一致。
4. **缺口披露（不阻塞，未行使）**：paper 卖出侧无显式跌停禁卖闸（grep limit_down 命中 0）；截至审计日 paper 历史 **0 笔卖出**，缺口从未被行使，无已发生的失真。修复另行立项（§九条件②）。

**判定**：PASS（paper→live 毕业门不被阻塞；卖出侧闸门列入修复项跟踪）。

## 六、A5 滑点/冲击成本模型——PASS（R-336 语义：不阻塞迁移）

**方法**：paper 实际费用参数核验 + 回测成本配置核验 + R-333 实测结论引用（三板斧③，不重做）。

**证据**：
1. **paper 真实费用三件套在账**：COST_BUY=万2.5（0.00025）、COST_SELL_COMM=万2.5、STAMP_DUTY=千1（0.001，卖出）、MIN_COMMISSION=5 元（paper_engine.py L93–95）；trades.csv 8 笔 cost 字段无缺失。
2. **回测成本**：a13 BASE `cost_model="v2"`、`cost_rate=0.001`（10bp/边，含买卖）。
3. **R-333 在案结论（直接引用）**：两代引擎 18 笔逐笔对账——记账滑点恒 0（dev_bp≡0）、实测三情态 4.0/11.5/15.7bp/边；R-336 指定可实现中间态 **11.5bp/边为门禁基线**；当前实测参与率 0.002–0.07% « 0.1%，平方根冲击项（Almgren-Chriss 简化式）**豁免成立**。
4. **口径归一提示**：回测 10bp / R-333 基线 11.5bp / 金引擎假设 13bp（R-304 v2）三数并存；按 R-336，G-S4/G-L3 门禁必须用校准后成本（11.5bp 基线）——归一动作属 Phase A 动作 2（gate spec v1）范畴，列入附加条件③。
5. Phase B paper 实测滑点回填校准机制已在 R-336 §8 Phase B 动作中排定，本审计确认其前置（本项）无阻塞。

**判定**：PASS（不阻塞迁移；门禁成本归一到 11.5bp/边列入 gate spec 条件）。

## 七、A6 分红除息处理——PASS（记录在案，无现实异常）

**方法**：抽样除息日对账（R-336 要求 3 个分红事件人工核对；实际做了全量事件×持有窗口扫描）。

**证据**：
1. **数据在位**：`data/derived/dividend_events.parquet` 48,081 行（code/ex_date/cash_per_share/period），2026-05 以来 3,470 条。
2. **持有窗口全量扫描 = 0 命中**：paper 全部 8 笔买入的 [买入日, 卖出日/审计日] 持有窗口与分红事件求交，**0 个除息日落在持有窗口内**。此前按代码匹配出的 4 个疑似事件（300009 05-29/0.25、600867 06-05/0.30、603551 06-09/0.55、601600 08-14/0.147）经窗口复核全部不享有：买入发生在除息日之后或除息日当日（601600 恰于除息日当天买入，买入方不享有该次分红）。**paper NAV 至今无分红口径失真**。
3. **回测侧语义正确**：回测宇宙用 hfq（后复权）价格，分红已通过复权因子保留在收益序列中，回测净值不因除息跳空失真。
4. **潜伏缺口（记录在案，修复另行立项）**：`paper_engine.py` L61 定义 `DIV_EVENTS` 但全文件仅此 1 处引用（**加载未接线**）——一旦未来持仓跨除息日，现金分红将不入账、paper NAV 会低估真实收益。当前零影响，风险敞口为「下一只跨除息日持仓」。列入 §九条件②修复项。

**判定**：PASS（异常才阻塞；本项无异常，缺口已记录并立项跟踪）。

## 八、三板斧执行对照

| 板斧 | R-336 要求 | 本审计执行 | 结果 |
|---|---|---|---|
| ①锚点单测 | R-317 PIT 四锚点 + F1 md5 逐位复现；每 sleeve ≥2 锚点 | R-317 复现在案记录引用（task-0492，逐位一致；脚本已随 /tmp 清理，如实标注）；gold sleeve 以 157 月全历史重放逐位一致覆盖（远超 2 锚点）；A股 paper sleeve 以 state/NAV/trades 三方一致性核验覆盖 | 达成（gold 超额；R-317 引用在案） |
| ②随机样本月度对账 | 随机抽 3 个月重算，diff ≤1bp | gold=157 月全重放 diff=0bp；A股 paper 当前满仓为 0（全部清算后 cash 态），无独立月度持仓可重算，以三方一致性替代并如实披露 | gold 达成；paper 以替代核验披露 |
| ③paper 真实成本对账 | 引用 R-333，不重做 | 引用其 18 笔逐笔对账结论（A5 §六.3） | 达成 |

## 九、附加条件（放行 Phase B 的三项非阻塞跟踪项）

1. **【Phase B 影子层消费 a13 因子面板前，强制】fundamentals_monthly 构建器 PIT 补验**：逐行核验 `fetch_valuation_data.py`/`prep_dividend_roa.py` 对 roe_ttm/roa_ttm/div_yield_ttm 的月份键是否按可得日（披露后）落位；若发现报告期直落，则 a13 因子 roe 通道历史结论需按 R-336 A1 语义重新定性（届时触发绝对阻塞复评）。补验预计 1 个子任务内完成。
2. **【修复项，另行立项，不自动修】paper_engine 两处缺口**：①卖出侧跌停禁卖闸缺失（现 0 笔卖出未行使）；②DIV_EVENTS 分红入账未接线（现 0 命中未触发）。
3. **【gate spec v1 落库时】成本口径归一**：回测 cost_rate 10bp / 门禁基线 11.5bp/边（R-333 中间态）/ 金引擎假设 13bp（R-304 v2）统一到 R-336 指定的 11.5bp/边基线，G-S4/G-L3 用校准后成本；Phase B 期间以 paper 实测滑点回填复核。

## 十、产物与零改动声明

**HP 产物（新目录）**：`~/quant-evolve/results/phase_a_audit_0537/`——audit_findings.json（第一轮六项扫描）、followup3.json（定向补验：grep 命中/分红窗口/NAV 尾）。
**HP 过程文件（/tmp）**：audit_0537.py、audit_0537_f3.py、audit_0537_run.log、audit_f2.log、audit_0537_before.txt（审计前 `find -newermt 23:00` 快照）。
**本地产物（/tmp）**：/tmp/r483replay/（重放副本，OUT 重定向至 /tmp/r483replay/out/，原件零触碰，重放后 work/r483 关键文件 md5 复验不变）。
**本审计未修复任何发现的问题**；未修改 evolution_pipeline.py / registry / paper_engine / crontab / engines；未杀任何在役进程（仅终止本审计自身启动的 f2 扫描进程）。零既有文件改动（HP/本地），README 更新日志行除外（任务书要求）。

## 附录 A：执行时间线（2026-08-28，Asia/Shanghai）

| 时刻 | 动作 |
|---|---|
| 23:05 | R-345 编号确认未占用；R-336 分段提取 §5/§8 审计条款；notes 骨架落盘 |
| 23:10 | HP 勘察：engines.json 三在役引擎锁定；paper_engine 费用/涨停闸定位 |
| 23:15 | 第一轮只读扫描脚本上 HP 后台跑（audit_0537.py） |
| 23:20 | 本地 r483 重放启动（OUT 重定向 /tmp）；发现 a13 BASE 配置含 limit_board/cost_model |
| 23:25 | gold 重放完成：nav md5 逐位一致；gates 仅 run_at 伪差异；HP 第一轮扫描完成 |
| 23:40 | 定向补验 f3：A1 grep 命中、A6 分红窗口=0、NAV 一致性 |
| 23:50 | 513100 双源复权实证（raw −80.45% vs qfq −9.59%）；A3 转向真实宇宙源（hfq+退市索引） |
| 00:05 | 最后定点核验（退市索引 365 条、load_kline=qfq 源）；终止自身 f2 进程；撰写报告 |
| 00:15 | 报告落盘、零改动自检、完成回报 |

## 附录 B：关键原始输出摘录（HP audit_findings.json / followup3.json）

```json
A1_ths_panel:      {rows:235170, lag_median:62, lag_min:30, neg_count:0}
A1_shift_timing:   {shift(1):1, 上一个月末:1}  (timing_layer_prod.py)
A1_shift_gold:     {prev_me:12, PIT:2}        (paper_engine_gold.py)
A3_delisted_pool:  {n:361}   + stocks_hfq_delisted_index.json n=365
A4_buy_on_limitup: {n_buys:8, n_viol:0}
A5_trades_fee:     {buy_rows:8, sell_rows:0, cost_na:0}
A6_div_events:     {rows:48081, n_since_202605:3470}
A6_holding_window: []  (0 命中；4 个代码级命中全在窗口外)
RECON_state:       {cash:40393.0, n_pos:0}   nav_tail: 2026-08-26 = 0.9974
```

本地重放：`md5(e2_nav_monthly.csv) = 18bdf07bc3353f3884765fce2692cd49`（重放=原件=md5.txt 在案值）；`md5(513100 raw 单日min) = −0.8045` vs `qfq 单日min = −0.0959`。

## 十二、审计局限性声明

1. 本审计为时间盒（≤40 分钟设计预算，实际跨零点）内的只读审计，A1 残留通道与 A3 逐只配平两处以「未完成核验」如实披露，未默证为安全。
2. A股 paper sleeve 历史仅 8 笔（2026-06 起）且审计时点为满现金态，月度对账的统计功效有限；待影子双轨积累后 Phase B 退出条件（vC-0 复现 R-317 md5 一致）将提供更强验证。
3. R-317 锚点复现引用 2026-08 在案记录而非本次重跑（脚本已不在盘）；gold sleeve 全历史重放提供了同量级的确定性复现证据。

## 十一、来源（续前）

- R-336 v1.4 §5/§8（审计语义）；R-342 §5（Phase A 与 W1–W3 并行关系确认）；R-343（前视缺陷影响面，代码级核验引用）；R-333（paper 真实成本，三板斧③引用）；R-330/R-323 raw（513100 双源）；R-317（md5 复现在案记录）；R-304/R-305（金引擎判门与重放路径）。
- HP 数据/代码：model/registry/engines.json；scripts/{a9_common,a13_run,paper_engine,paper_engine_gold,timing_layer_prod,fetch_valuation_data,q4b_run_BC}.py；data/{delisted_pool.parquet,stocks_hfq_delisted_index.json,fundamentals_delisted_monthly.parquet,ths_ttm_panel.parquet,derived/dividend_events.parquet}；results/{baseline-paper-trades.csv,baseline-paper-nav.csv,paper-state.json}。
