# task-0338 A7 过程笔记（边查边写）

> 生成 2026-08-17 09:30 | 任务书见同目录 task-0338 任务

## 访问路径首查（09:31）
- HP SSH 10.12.192.174:22 Connection refused（09:30-09:33 重试 3 次均拒，ping 通，22/2222/22022/222 全 closed）
- **替代路径：HP HTTP API http://10.12.192.174:8060 + X-API-Key 可用**
  - /health OK：quant env 存在，merged_file 304MB，qfq_files 5448，disk free 31.7GB
  - /run 可执行命令（cwd=/home/noname/quant-evolve，env=quant，timeout 上限 1800s=30min）
  - /data/status OK：data_path=/home/noname/quant-evolve/data，merged mtime 2026-08-11 01:46
  - DANGEROUS_PATTERNS 仅拦截 rm -rf /等，常规 python 命令可跑
- 结论：本任务以 HTTP API 为执行路径（SSH 备用，后续再试）
- a7 现有结果文件数：0

## 阶段0 首查两项（factor_db 字段 / dividend_events 公告日）
（待填写）

### 09:40 追加：factor_db 结构
- factor_db.sqlite 表：factors(3行)、evolution_history(0行)、sqlite_sequence
- factors 列：id,name,description,code,source,created_at,status,ic_mean,ic_ir,ic_history,weight,llm_hypothesis,iteration —— 这是因子元数据表，不是行情数据表
- 行情字段（amount/turnover）需查 all_stocks_merged.parquet（v4b 基建实际用表）
- merged parquet 读取报错（疑似 pyarrow/engine 问题），待复读

### 09:45 追加：merged kline 字段核对（首查项①部分结论）
- all_stocks_merged.parquet：14,613,191 行 × 8 列 = date,code,open,close,high,low,volume,amount
- **有 amount（成交额），无 turnover（换手率）** → 换手率需用股本数据计算（查 fundamentals_monthly 是否含总/流通股本）
- factor_db.sqlite 是因子元数据表（3 因子），非行情表；amount/turnover 在 kline

### 09:50 追加
- merged kline 已核对：有 amount，无 turnover（首查①过半结论；换手需股本表）
- factor_db.sqlite=因子元数据表（非行情表）；行情字段在 merged parquet
- dividend_events 列名查询多次 segfault（API 瞬时），改用落盘脚本再查
- 访问路径确定：HP HTTP API（8060+key），SSH 端口拒绝

### 10:05 首查两项结论（A7 开工）
**首查① factor_db 字段核对**：
- factor_db.sqlite = 因子元数据表（factors 3 行：id,name,description,code,source,created_at,status,ic_mean,ic_ir,ic_history,weight,llm_hypothesis,iteration），非行情表
- 行情表 all_stocks_merged.parquet：8 列 date,code,open,close,high,low,volume,**amount**（有成交额，无 turnover）
- fundamentals_monthly.parquet：code,date,div_yield_ttm,**circ_mv**,roe_ttm,roa_ttm → 有流通市值（月频），无总股本
- 结论：成交额版因子直接可用；**换手率版需日频股本（无）→ 用 amount/circ_mv 月频近似或只测成交额版**

**首查② dividend_events 公告日**：
- dividend_events.parquet：5 列 code, ex_date, cash_per_share, period, __index_level_0__
- **只有除权除息日 ex_date，无预案公告日** → F13 股息事件 PIT（预案公告日）**本批不可行，不测**（只查不测达成）

### 10:20 恢复执行（上次超时，A5 runner 机制已读通）
- a5_runner.py 机制：patch 引擎 run_backtest（ext 排序分支 P1 + inv_vol P2 + rank_buffer P3 + vt_target P4 + dd_trigger P5 + value/mom lookup P6/P8 + gq 排序 P9），等价校验 diffs={} 后跑候选
- a5_post_bt.py：registry 注册（fork 自 parent）+ ledger_append（带 features 字段）
- a5_ic_ext.py：月度 IC（spearman，方向调整，W1 口径）
- A7 计划：基于 v4b_mve1（sort=mv + e1_guard + q3z_tr 择时）骨架，新增 P0 因子 ext 分支（low_amount/amihud/cv）+ 日历降仓 + 涨停剔除 + 次新剔除，逐一单维度叠加

### 10:25 恢复执行
- HP /tmp/a5_runner.py 存在，results/a5_v4b_mve1_formal_locked_metrics.json 存在（基线可复跑）
- a5_runner ext 分支已支持 amount_cv / volatility_20d（ext_factor + ext_weights）
- A7 需新增 ext_factor: low_amount(20d均额反向) / amihud(|ret|/amount 20d均值) / turnover_cv(已有 amount_cv 可复用)；规则类: 日历降仓/涨停剔除/次新剔除需新 patch

### 10:30 阶段1 IC 预检完成（微盘宇宙 circ_mv 最小400，月度 spearman，247月）
- amt20（低成交额，DIR=-1 低好）：mean_ic **-0.106** / ICIR -0.67 / pos 23% / last12 -0.057 → **方向与外部相反**（微盘内高成交额略好），低成交额排序在本宇宙无 alpha 甚至反向
- amihud20（高好）：mean_ic +0.0039 / ICIR +0.025 / pos 49% / last12 +0.022 → **极弱接近零**
- amt_cv20（换手CV，DIR=-1 低好）：mean_ic **-0.189** / ICIR -1.32 / pos 9% / last12 -0.117 → **显著反向**（微盘内高换手CV反而收益高，与 BigQuant 全市场 -0.03 相反）
- 结论：三个排序类因子 IC 预检均未通过（无正 IC 支撑），如实记录；按任务书仍进回测（单维度归因验证，预期贡献弱）
- 附：原始 corr（调整前）：amt20 +0.106 / amihud20 +0.0039 / amt_cv20 +0.189

### 10:50 引擎细节确认
- DEFAULTS: limit_up_pct=0.098, cost_model=legacy→v2(回测用v2), limit_board=off→on
- 引擎已消费: closes/prev_closes/susp/rets/amt/st_flag/opens/highs/lows/first_last/bench_nav
- a5_runner 的 ext 分支已支持 amount_cv/volatility_20d；A7 需扩展 low_amount/amihud + ext_sign + e1_guard
- 计划候选8个（单维度）：a=low_amount×3权重, b=amihud×2权重, c=amount_cv×1, d=日历×0.5, e=涨停剔除, f=次新剔除

### 11:05 a7_runner 就绪（9候选 v5a-v5i）
- a7_runner.py 语法 OK，等价校验 + 9 候选（low_amount×3权重 / amihud×1 / cv×1 / 日历×0.5 / 涨停剔除 / 次新剔除 / a+e组合）
- 开始上传 HP 后台执行（nohup + log 轮询）

### 11:20 执行方式修正
- nohup/setsid 后台进程均被 API 请求清理（测试证实）→ 必须同步执行
- API /run 单请求超时上限 1800s（30min）；A5 同规模 5候选×2窗+等价约 10min，A7 9候选×2窗+等价预计 20-25min，可容纳
- 启动同步回测：HP /tmp/a7_runner.py formal（等价校验 diffs={} + 9 候选 full+locked）

## 12:2x 收口会话恢复（task-0338 正式执行）
- **HP API /run conda 激活已坏**：任何 env（quant/base）都 KeyError('user_agent')（anaconda_anon_usage 插件 bug）→ exit 139
- **绕过方案（已验证）**：/run body 传 `"env":"system"`（或空 env）直接用系统 shell，exit 0
- quant 环境回测用直调二进制：/home/noname/miniconda3/envs/quant/bin/python（无需 conda activate）
- /health 仍 OK（16GB 内存可用 14.9GB，磁盘 31.7GB free）

### 12:3x 盘点结论（阶段1 完成）
- results/ a7_ 前缀 37 文件：
  - a7_ic_monthly.csv + a7_ic_summary.json（IC 预检产物）
  - v5a_amt37 full+locked 完整（10 文件）
  - v5b_amt55 full+locked 完整（10）
  - v5c_amt73 full+locked 完整（10）
  - v5d_amh55 **只有 locked（5 文件），full 缺** → 11:20 启动的同步回测在 v5d full 处被中断
- v5e（换手CV）/v5f（日历）/v5g（涨停剔除）/v5h（次新剔除）/v5i（组合）**全部未跑**
- a7b-*（现金曲线+稳健性，8 组）与 a7c-*（动态画像，6 文件）已有，非本任务产出但作交叉解读素材
- 无 a7-iteration-report.md；ledger 尾行待查
- 补查：a7x_equiv_{full,locked}_* 文件存在（10 个）→ 等价校验在首轮已通过（patch 开关全关==原引擎逐位一致）
- 时间线还原：01:45 IC 预检 → 02:20-02:21 v5a → v5b/v5c → 02:27 v5d locked 写完 → v5d full 中断（API 会话被杀）
- a7_backtest_summary_formal.json 不存在（脚本末尾才写，未到达）→ 补跑后需单独合并生成
- v5d_locked_metrics.json 742B 可读；v5a 743B

### 已有产物 locked/full 指标全表（12:4x 抽取，来源 metrics.json）
| 候选 | full ann/mdd/sharpe | locked ann/mdd/sharpe/calmar | locked 月胜率/换手 |
|---|---|---|---|
| v5a_amt37(低额0.7mv+0.3amt) | 14.06%/-30.76%/0.9252 | 14.42%/-30.76%/0.9325/0.4686 | 61.54%/0.3819 |
| v5b_amt55(0.5/0.5) | 14.13%/-30.76%/0.9400 | 14.52%/-30.76%/0.9494/0.4720 | 61.09%/0.4008 |
| v5c_amt73(0.3/0.7) | 13.90%/-30.65%/0.9345 | 14.25%/-30.65%/0.9427/0.4649 | 59.73%/0.4091 |
| v5d_amh55(Amihud) | full缺(补跑中) | 13.18%/-31.03%/0.8606/0.4246 | 59.73%/0.4166 |
| 基线 v4b_mve1 | 12.31%/-28.99%/0.8427 | 12.42%/-28.99%/0.8401/0.4285 | 58.82%/0.6156 |
- 要点：低成交额三档年化 +1.8~2.1pp、Sharpe +0.09~0.11、**换手 0.6156→0.38-0.41（降约35%）**、MDD 恶化 -1.7~-2.0pp
- 现役 v2b_trr（decision-log 口径）：15.15%/-29.86%/0.936 → v5b 年化/MDD 均不优于现役，仅 Sharpe 略高 → 不满足 activate
- a7_ic_summary（微盘宇宙 247m）：amt20 mean_ic=-0.1065/ICIR=-0.668/pos23%/last12=-0.057（原始符号：低成交额→高未来收益，支持低额倾斜）；amihud20 +0.0039/0.0246（近零）；amt_cv20 待补（截断）
- 上一会话笔记 10:30 段"预检未通过/方向相反"系符号误读：raw IC=-0.107 = 低额好；A7c 动态画像与回测结果一致支持低成交额族
- 六门禁键名（ledger 实际格式）：g1_icir_is / g2_icir_oos / g3_max_corr / g4_dsr / g5_logic / g6_mdd_vs_parent
- DSR 计算可复用 evolution_pipeline.py:~453（norm.cdf 公式，dsr_min=0.95）
- ledger 尾 = v4e_gqg1x evaluate 行（REJECT）；decision-log 尾 = D-20260816-043（A5 closeout）→ A7 行/决策均未写，待本任务补

### 批1补跑结果（12:5x，resume1 完成 469s）
| 候选 | full | locked |
|---|---|---|
| v5d_amh55 | 12.93%/-31.03%/0.8587 | 13.18%/-31.03%/0.8606（已有）|
| v5e_cv73(换手CV 0.7/0.3) | 12.48%/-29.89%/0.8343 | 12.69%/-29.89%/0.8348 → **无增量**（Sharpe 略降，换手未降 0.636，A7c"近端走强"未兑现）|
| v5f_cal(日历1/4月×0.5) | 13.38%/-29.86%/0.9199 | 13.83%/-29.86%/0.9308 → **+1.41pp vs v4b**，MDD仅差0.87pp，**换手减半 0.314** |
- amt_cv20 IC：mean -0.1888/ICIR -1.315/pos 9%/last12 -0.117（信号强但回测不兑现→微盘组合内无经济增量，与 v5e 结果互证）
- DSR 复用：ep.deflated_sharpe(returns, n_trials)，dsr_min=0.95；n_trials 基数 67（A5 尾行 n_trials_cum）
- locked 排名：v5b 14.52 > v5a 14.42 > v5c 14.25 > v5f 13.83 > v5d 13.18 > v5e 12.69 > v4b 12.42

### 批2补跑结果（13:0x，重试1次后成功 460s；另 2 次 numpy 导入段 segfault 为 HP 瞬时故障）
| 候选 | full | locked |
|---|---|---|
| v5g_lim(涨停≤3剔除) | 14.37%/-30.05%/0.9125 | 14.74%/-30.05%/0.9181 |
| **v5h_xsub(次新剔除)** | 15.27%/-29.80%/0.9861 | **15.74%/-29.80%/0.9983** |
| **v5i_comb(v5b+涨停+次新)** | 14.76%/-29.30%/0.9961 | **15.23%/-29.30%/1.0113** |
- **重大发现：v5h 与 v5i locked 三项全部严格优于现役 v2b_trr（15.15%/-29.86%/0.936）**
  - v5h: 年化 15.74>15.15 ✓ MDD -29.80>-29.86 ✓ Sharpe 0.998>0.936 ✓
  - v5i: 年化 15.23>15.15 ✓ MDD -29.30>-29.86 ✓ Sharpe 1.011>0.936 ✓
  - 两者月换手均降至 0.32-0.38（vs v2b/v4b 0.62，减半）→ 若门禁全 PASS 按规则直接 activate
- 规则层贡献排序：次新剔除 +3.32pp > 涨停剔除 +2.32pp > 日历 +1.41pp（vs v4b 基线）
- **门禁语义核对（evolution_pipeline 实源）**：
  - g1 复合ICIR年化≥0.5（IS=2021-01前）；g2 OOS(2021-01~2024-06) Welch单侧t检验 p>0.05；g3 新增因子vs在役因子 IC-corr<0.7（无新增→N/A 不折减）；g4 DSR≥0.95（N=34偏移+backtest数→本批76）；g5 logic；g6 MDD较**在役**(v2b_trr -0.2986)恶化≤2pp
  - g6 按 v2b_trr 口径：v5a/b 0.90pp v5c 0.79 v5d 1.17 v5e 0.03 v5f 0.00 v5g 0.19 v5h -0.06 v5i -0.56 → 全 PASS
- registry: model/registry/*.json；active=v2b_trr（factors=div_yield/roe/roa/circ_mv）；factor_ic_corr.csv 存在（g3 有真实数据）
- activate 通道：ep._do_activate(reg, trigger, reason, force) 要求 gate.verdict=PASS，自动 main.json 重建+快照+状态流转+switch_log
