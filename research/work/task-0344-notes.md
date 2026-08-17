# task-0344 量化流水线人为约束全量盘点 — 过程笔记

任务：审计量化流水线所有人为约束，分类 A/B/C/D，产出 R-219 报告（只盘点不改代码）。
分类口径：
- A类·评估流程约束：门禁/activate/locked窗口/战役目标
- B类·策略内硬约束：闸门/护栏/剔除/地板（可权重化）
- C类·市场现实约束：一字板/T+1/成本/停牌（物理现实）
- D类·数据正确性约束：PIT对齐/审计锁/防作弊基建

## 阶段0：环境确认
- [2026-08-17 13:12] VPS 侧确认 R-218 为现有最大编号，本任务用 R-219。
- HP 访问：ssh -i /root/.ssh/id_hp -p 2222 noname@10.12.192.174

## 阶段1：代码级盘点（HP: ~/quant-evolve）

### 1.1 evolution_pipeline.py（55KB）— 五门禁 g1-g6
- GATE_CONFIG（L56-64）：
  - g1 icir_is_min=0.5：IS全样本复合ICIR年化下限
  - g2 oos_p_min=0.05：OOS相对IS劣化单侧t检验 p>0.05（不显著劣于才过）；oos_split_ym=2021-01（OOS起始月）
  - g3 max_corr_max=0.7：与在役因子最高|ρ|上限
  - g4 dsr_min=0.95：Deflated Sharpe Ratio 下限；n_trials=HISTORICAL_TRIAL_OFFSET=34+台账backtest计数（多重检验校正）
  - g5_logic：logic 字段非空（文档性门禁）
  - g6 mdd_vs_parent_max_pp=2.0：MDD较父版本恶化≤2pp，一票否决（E3修复task-0292）
- 判定逻辑（L751-753）：decisive=状态为PASS/FAIL的门禁集合；任一FAIL→REJECT；全PASS→PASS；无decisive→N/A
- FAIL后果（L846-848 _do_activate）：verdict∉(PASS, legacy-grandfathered) 且无 --force → 拒绝激活。activate 需人工确认（Step7 注释 L1136：activate 为人工确认操作，不自动激活）
- HISTORICAL_TRIAL_OFFSET=34（registry化前历史试验数，L54）

### 1.2 audit_lock.py（1.5KB）— 审计锁
- AUDIT_LOCK_END="2024-06-30"：2024-06-30之后为锁定审计段，所有OOS/评估窗口不得穿透（R-213评审确认，task-0292/E6修复）
- clamp_date/clamp_ym/breaches_lock 统一工具；gate_icir 中 oos_mask 强制 ym<=2024-06
- 历史：v1.4及之前 gate-report OOS穿透是历史事实，不回改

### 1.3 backtest_dividend_quality_iter.py（36KB）— 基线回测引擎（q4b/a5/a7 系列共用底座）
DEFAULTS（L54-71）：
- sort=mv（默认按流通市值升序=小市值优先）；score_weights=[0.4,0.3,0.3,0.3]（div+roe+roa-mv z-score 加权）
- div_min=0.02 / roe_min=0.15 / roa_min=0.10（v2b 四闸门之三）
- n_hold=20；price_cap=10.0（qfq口径）；min_amt=0.0
- drawdown_control=0, dd_thresh=0.20, dd_reduce=0.5, dd_recover=0.05（V3回撤控制层，默认关）
- cost_rate=0.001（legacy成本7.5bp两倍？待核）；limit_up_pct=0.098
- cost_model="legacy"|"v2"; limit_board="off"|"on"; capital_base=1e7（v2成本佣金min5元折算本金）
- WF_PARAM_GRID：div_min{0.020,0.025}×n_hold{20,30} 4格

选股过滤（L386-424，每月调仓日）：
1. div_yield_ttm 缺失或 < div_min → 剔除
2. roe_ttm 缺失或 <= roe_min → 剔除
3. roa_ttm 缺失或 <= roa_min → 剔除
4. price >= price_cap 或 <=0 → 剔除（qfq绝对价）
5. ST（st_history_ranges.csv 精确区间表 task-0330）→ 剔除；持仓中变ST → 强制卖出
6. 停牌 → 剔除/当日不计收益；持仓停牌 → 顺延
7. 未上市 → 剔除
8. min_amt>0 时：20日均成交额 < min_amt（需≥10有效日）→ 剔除
9. 退市日 → 强制卖出（DELIST）
组合规则：
- 月度调仓（每月第一个交易日 rebalance_dates）
- 等权（weights 均分）
- top n_hold
- 回撤控制层（默认关）：NAV回撤>dd_thresh→仓位×dd_reduce，恢复到峰值-dd_recover→满仓
- 宏观择时层（timing_pos 叠加）：eff_ret = day_ret × pos_ratio × timing_ratio（双层防御 task-0255）
- 一字板约束（limit_board=on）：买入遇一字涨停 skip，卖出遇一字跌停顺延

### 1.4 cost_model_v2.py（9KB）— 成本模型v2 + 一字板判定
- COMM_BPS=2.5（最低5元）；STAMP_BPS_SELL=5.0；IMPACT_K=10.0（ADV平方根冲击 k*sqrt(order/ADV20)，保守值可调）
- is_untradeable：O==H==L==C（1e-6相对容差）且涨跌幅达板块阈值-0.1%容差 → 一字板不可成交
- 板块阈值分段：主板10%；科创板688=20%（2019-07-22起）；创业板300/301 10%→20%（2020-08-24起）；ST 5%（主板）/20%（双创注册制）；北交所30%
- direction="buy"仅一字涨停不可买，"sell"仅一字跌停不可卖

### 1.5 a5_runner.py / a7_runner.py（/tmp，task-0333/0338 系列）— 补丁引擎
A5 候选（成长×质量复合排序+E1护栏+G1加强+PEG过滤×v2b择时）：
- e1_guard：ret120 < -30% 剔除（买入时深跌股剔除）
- G1 加强（g1_boost）：dist250h>-10%（接近年高点）且 ret120>0 → 加分 g1_bonus=0.5
- peg_max=2.0（PEG过滤）
- gq_weights=[0.6,0.4]（成长×质量权重）
- 择时：q3z × EW-MA200 双信号：EW组合净值>MA200月线 → 1.0，破位 → 0.6；q3z_tr=q3z×trend_f
- vt_target/vt_floor=0.3（波动率目标层）、dd_trigger/dd_cut=0.5（回撤触发减仓）、inv_vol（反波动加权）、rank_buffer（排名缓冲带）

A7 候选（外部流动性因子 low_amount/amihud/amount_cv × E1 骨架）：
- v5g limup_max=3.0：近20日涨停(≥9.8%)计数>3天剔除
- v5h xsub_days=365：上市<365天剔除（次新股）
- v5f calendar_months=[1,4] calendar_factor=0.5：1/4月日历效应仓位减半
- v5a-c ext_weights 流动性因子权重梯度；v5d amihud；v5e amount_cv
- **active 版本 = v5h_xsub**：sort=ext(low_amount 权重1.0) + e1_guard + xsub_days=365，timing=q3z_tr

### 1.6 macro_timing_layer_iter4.py — 宏观择时层
- 合成：w = f_trend_comp × f_vol_comp × f_val(type_key)，clip [0.3,1.0]，EWM(α=0.3)平滑
- q3z 规格：win=36月, minp=12, zscore, hi=1.0σ, max_cut=0.40（PE z>1σ 开始线性降仓，最多降40%）
- SPECS 网格：q3r60/r70、q5r60/r70、q3m60、q5m60、q3z、q5z、q8r60（96月）
- ITER4_DEFAULTS：ma_window=120, target_vol=0.25, vol_floor=0.5, w_min=0.3, smooth_alpha=0.3
- 双红灯=估值层0.6底 × w_min 0.3地板 = 0.18（18%）
- CRISIS_SEGMENTS：2008熊/2015股灾/2018熊（校准段）

### 1.7 registry 版本史（43版）
v0_seed→v1a-v1k（排序/流动性/波动/逆波动/缓冲/q3z/vt18/q5z）→v2a-v2f（深度价值/三闸门trr/vt13/dd/dvt/lv）→v3a-v3f（peg/glm/组合）→v4a-v4e（gq/e1/mfu/trr）→v5a-v5i（低流动性因子/日历/涨停/次新/组合）

## 阶段2：流程级盘点

### 2.1 战役目标（a7b-iteration-report.md）
- locked 口径：年化≥25% / MDD≤20% / Sharpe≥1.2（微盘增强档位B）
- a7b 结论：40%现金档 ann=7.20% 距25%目标 -17.8pt；基线 v4b_mve1 ann=12.42%/MDD-28.99%/Sharpe0.84 → 差距 +12.6pt/+8.99pt/+0.36
- 事前杠杆不推动前沿；当前框架内不可达 → a7b 建议换赛道或下调目标（R-217 即换赛道调研）

### 2.2 activate/回退规则（evolution_pipeline.py）
- verdict 必须 PASS 或 legacy-grandfathered 才能 activate；否则需 --force（人工强制）
- activate 为人工确认操作，cycle Step7 不自动激活
- rollback：--to 指定回退版本；切换冻结旧 active main.json 字节快照；switch_log/history/decision-log 全程记录 md5
- 状态机：candidate→(PASS)→pending→(人工activate)→active→sota→retired

### 2.3 台账与审计（ledger 实例证据）
- experiment-ledger.jsonl：每次 backtest 记 run_id/params_hash/data_snapshot(hash)/metrics{full,locked}/n_trials_cum；DSR 用 n_trials 累计（现 69+）
- gates 实战样例：v5b_amt55 g2_icir_oos FAIL（p=0.0389<0.05，OOS IC 0.072 vs IS 0.120 劣化）→ REJECT；v5g_lim 规则层候选 g1/g2 N/A 以回测归因
- IT 编号：IT-A7-02..08；评估口径 locked=2006-01-01~2024-06-30

### 2.4 CLAUDE.md 遗留"回测参数（不可变）"段
- 初始资金10万/持仓20/月频/双边千一/候选池市值最小500只/2016起 —— 系 v0 seed 旧口径，与现行引擎（1e7/成本v2）不一致，属文档遗留（登记为流程约束-文档类）

### 2.5 运行层（paper/cron/override）
- paper_engine.py：自有选股参数 price_cap=10/n_hold=20（快照与 main.json 同步）；cron 月度调仓=每月最后一个工作日16:30（⚠️ 与回测引擎"每月首个交易日"口径不一致，登记待确认）
- override 机制：temp_override.json TTL 临时覆盖（--timing-off 等），过期自动忽略；decision_log 记录
- 防漂移守卫 guard_override_and_drift（task-0275）：main.json↔registry[active] 同口径比对，漂移写 drift-alert.json
- data_validator.py 六检查：K线新鲜度≤3天 / 面板覆盖≥0.95 / 持仓K线 / 价格区间0.01-100000 / 分红连续性回看365天 / 选股≥5只；Step0 FAIL→cycle fail-fast
- cron_paper_rebalance 同步产物到 VPS 04-投资研究（旧目录）

### 2.6 数据正确性基建（D类证据）
- PIT：fund = panel[panel["date"] <= d]（as-of 取数，无前视）
- 幸存者偏差：宇宙5205只含退市股（first_last 字段；backfill_delisted.py / collect_delisted_hfq.py 补数）
- 数据快照哈希：data_snapshot{hash, kline_as_of}（W6 内容hash bcf45e9...）写进 ledger，防"改数据不报告"
- ST 精确区间：st_history_ranges.csv（task-0330，替代静态 is_st 列）
- 审计锁 audit_lock.py（2024-06-30）统一 clamp，防评估穿透锁定段
- 等价校验：a5/a7 runner patched vs 原引擎 nav 逐位一致才放行
- 命名/呈现约束：R-编号报告 + README 顶部变更记录（Dashboard 消费约定）

### 2.7 数值影响锚点（交叉引用）
- E1护栏：压MDD 0.87pp（-29.86→-28.99）、年化-2.7pp、Sharpe-0.096、DSR 0.936→0.971（a5报告 IT-A5-02）
- E1 postmortem：砍20.8%尾部亏损、误杀12.1%赢家；G1加强：avg+21.2%/胜率78.4%（task-0331）
- 次新剔除v5h：+3.32pp年化、MDD持平、Sharpe+0.158、换手0.616→0.320（a7报告）
- 涨停剔除v5g：+2.32pp年化；日历降仓v5f：+1.41pp；低成交额族：+1.8~2.1pp、MDD恶化~1.8pp、换手-35%
- 现役 v5h_xsub locked：15.74%/-29.80%/0.998/Calmar0.528；战役目标差距 +9.3pp年化/+9.8pp MDD/+0.2 Sharpe
- v2b_trr（cost v2+一字板后现役参照）locked 15.15%/-29.86%/0.936
- a7b：40%现金档 ann=7.2%；事前杠杆不推动前沿（Calmar不变式）

## 阶段4：交付自检（全过）
- R-219 报告落盘：shared/results/05-量化投资/R-219-量化流水线人为约束审计.md（约10.8KB）
- 47 条约束（A13/B21/C5/D8），每条含分类/作用/数值影响/建议/勾选栏
- README.md 变更记录已更新（修复过一次重复行，现唯一 R-219 条目）
- 最关键3条：#7一票否决制（权重机制核心改造点，a7批5/9被拒）、#10 locked窗口≤2024-06-30（评估口径最大未使用信息，建议保留）、#14-17 v2b四闸门（宇宙定义，建议保留）
- 任务书"38条"系初稿计数，最终清单 47 条（更全）
