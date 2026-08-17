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
