# task-0361 过程笔记：择时v2信号画像第一批（E1：SPREAD/回流广度/FLOW/超跌包）

任务：task-0361，产出 R-231。纯分析画像，参数冻结（华福原参数+R-230 固定参数），不做遍历、不做策略回测。n_trials=3（SPREAD w∈{5,10,20}）。

## 0. 前置输入摘要（已读，2026-08-18 07:3x）

- R-230（唯一公式来源）：SPREAD_t = MA{w}(全市场上涨家数占比) w∈{5,10,20}；REB_t = 微盘池内 vol/vol_MA5>1.2 且收涨家数占比；FLOW_t = Σ(上涨股成交额−下跌股成交额)/Σ成交额（微盘池）；超跌包基于微盘等权指数 M_t。
- 固定参数（画像冻结）：B1 超跌释放 = dd60<−10% 且 dev15<−3pp 且 RSI14≤45；B2 部分条件 = REB≥55% 且 (REB_t−REB_{t−5})≥5pp 且 FLOW_MA3>0；危机通道 C = dd250<−35% 且单日收益>+5%；顶部 SPREAD = 20日 SPREAD 曾达≥0.85 且 5日内回落≥0.05。
- 数据：HP `results/breadth.parquet`（2006-2026 上涨家数占比，可直接作 SPREAD 底表）；`data/all_stocks_merged.parquet`（304MB/5,447只，严禁整读，OOM exit 137 实测）。
- 微盘池口径：A9 引擎现有口径（每日市值排序后 20%），不引入第二口径；微盘等权指数口径与 v6a_def/A9 一致（R-222）。
- 输出位置：HP `~/quant-evolve/results/timing_v2/`（新目录，禁改生产文件）。

## 1. HP 实查记录（边查边写，2026-08-18 07:3x-07:5x）

### 1.1 连接与数据布局
- SSH：`ssh -p 22 noname@10.12.192.174` key 认证可用（hp-quant 别名不可解析，直连 22 口）。
- `results/breadth.parquet`：5003 行×1 列（index=date, col=breadth），2006-01-05~2026-08-10，≈任务预期 ~5000 日频。直接作 SPREAD 底表（任务书指定）。
- `data/all_stocks_merged.parquet`：schema=[date,code,open,close,high,low,volume,amount]，14 row groups × 1,048,576 行 = 14,613,191 行，按 code（内按 date）排序。5,447 codes = 5,206 qfq 存活 + 241 退市（q4b 口径池，无 outstanding_share 列）。
- `data/all_stocks_qfq/`：5,448 文件 / 5,206 唯一 code，列 [date,open,high,low,close,volume,amount,outstanding_share,turnover] → 微盘池市值=mcap=close×outstanding_share 可算。
- `data/stocks_hfq/`：5,569 文件（全市场 hfq），列 [date,code,open,high,low,close,volume,amount,turn]（**无 outstanding_share**）；退市索引 `stocks_hfq_delisted_index.json` post-2006 退市 301 只。

### 1.2 口径考古（关键决策）
- **微盘池定义（REB/FLOW 用）**：`collect_crowding.py` 是体系内唯一现成实现——"每日全市场按总市值（close×outstanding_share）排序后 20%"，MICRO_PCT=0.20，numpy lexsort+bincount 流式实现（memory-safe 模板，直接照抄方法）。**该实现只读 qfq 池（不含退市 hfq）**，退市股无 outstanding_share 无法入池 → REB/FLOW 池= qfq 口径（与 crowding 一致），偏差=早期退市小盘缺席，报告披露。复用 lexsort(rank<(n*0.2)) 保证与现有实现逐位同构。
- **微盘等权指数 M_t（超跌包载体）**：v6a_def/A9 的趋势锚在 `a9_common.py::build_timing` = `ew_ret = mean(全池 rets)`（q4b 全池=merged 5,447 只）→ `ew_idx=cumprod(1+ew_ret.fillna(0))`。故 M_t 用 merged 流式复算（row-group 逐块读 date/code/close，pct_change 同码连续行），与引擎同构；同期复算 up-share 与 breadth.parquet 交叉验证。
- breadth.parquet 生成口径（macro_timing_layer.load_breadth）：ret=close.pct_change() 按码分组，up=ret>0 占比——与我的 Part A 同构。

### 1.4 执行环境突变与处置（07:5x）
- HP 内存耗尽：MemAvailable 57MB，SwapFree 164KB（4GB swap 几乎满）；259 进程 sumRSS=14.7GB，其中 106 个 idle `openclaw-node`（每个 ~190MB，0% CPU）。按纪律**一律勿杀**，HP 无法承载本任务计算（峰值需 ~350MB+）。
- 处置：数据只读副本 rsync 到 VPS `/root/tv2data/`（qfq 池 1.1G + merged 290M + breadth.parquet），VPS venv（pandas 3.0.5 / pyarrow 25.0.1 / numpy 2.5.2）计算；口径完全不变；产物回写 HP `results/timing_v2/`。已在脚本头部与 summary.json 记录 compute_env 偏离。
- 内存安全重写：Part A 按 row group 流式+日桶增量聚合；Part B 按日期 5 块分块（块前扩 30 天上下文保 rolling5/pct_change），块内 numpy lexsort（与 crowding 同构），VPS 峰值 ~350MB（MemAvailable 584MB + swap 8GB）。
- SPREAD_w = breadth.rolling(w).mean()，w∈{5,10,20}（n_trials=3）。
- 顶部 SPREAD_top_w：`SPREAD_w.rolling(20).max()≥0.85`（T1 曾达高位）且 `max(SPREAD_w, t-5..t-1) − SPREAD_w(t) ≥ 0.05`（T2 5日内回落）。
- REB（B2 广度部分）：`REB≥0.55` 且 `REB−REB.shift(5)≥0.05`；REB=微盘池内(vol/vol_MA5>1.2 & vol>0 & ret>0)/（微盘池内有效成员：ret 非缺 & vol_MA5 有效 & vol>0）。
- FLOW = (Σamt_up−Σamt_dn)/Σamt（微盘池，amt>0）；FLOW_pos_cross = FLOW_MA3 上穿 0（转正事件，B2 资金条件）。
- 超跌包（载体 M_t）：dd60=M/rolling(60).max()−1（B1 条件1：<−10%）；dev15=M/rolling(15).mean()−1（条件2：<−3pp）；RSI14=Wilder（条件3：≤45）；B1=三条件同时；危机 C=dd250<−35% 且 日收益>+5%。
- 事件口径：episode=连续触发日段，事件日=段首日；fwd15=M.shift(−15)/M−1；底向信号 hit=fwd15>0，顶向(SPREAD_top) hit=fwd15<0。
- 重合度：日级 Jaccard 矩阵（触发日集合）。
- 覆盖检查：M 自身 dd<−15% 的主要回撤段（数据驱动，不预设日期），±10 交易日内是否有信号触发。
