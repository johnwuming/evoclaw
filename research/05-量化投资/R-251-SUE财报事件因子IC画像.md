# R-251 SUE 财报事件因子 IC 画像（task-0409 / R-249 方向五）

- 日期：2026-08-21
- 任务：task-0409（proj-0003，research）
- 结论一句话：**SUE 两口径月频全市场 ICIR 0.115 / 0.074，未达线（R-200 门槛 0.4，在役最高 circ_mv 0.269）；但披露后 0-2 月新鲜窗 ICIR 0.261 达到在役水平，且与 roe_ttm 冗余 ρ=0.60 / IC 序列相关 0.886，增量信息有限 → 不建议引擎级立项，负结果记录归档。**

## 一、背景与目标

R-249 方向五提出：SUE（标准化未预期盈余）作为第 5 排序因子候选或 E1 同族惩罚项（利空财报惩罚）的月频因子形态评估。本任务为方向五的 E1 前置——IC 画像（factor_ic_monthly 通道，W1 面板现成），ICIR 达线才进入引擎级评估。数据零新增采集：全部基于既有 ths_ttm_panel（PIT 面板）与 K 线库。

## 二、方法与数据来源

### 2.1 SUE 构造（两口径，均 PIT 对齐）

- **sue_std（Foster 型标准化）**：`SUE_q = (E_q − E_{q−4}) / std(ΔE_{q−7..q}, min_periods=5)`，E = net_profit_ttm，事件级 clip ±15。分母为过去 8 个季度同比差的标准差，是学术界 PEAD 研究的标准构造。
- **sue_pct（变化率型）**：`SUE_q = (E_q − E_{q−4}) / max(|E_{q−4}|, 1e7)`，clip ±10。分母对零/微小基期做 1000 万地板值保护，防爆炸。
- 季度对齐：report_date → Period("Q")，ΔE 严格取 q−4 同季值（缺失则 NaN，不插值不 ffill 事件层）。

### 2.2 PIT 对齐说明（防前视，本节为口径核心）

**因子值仅用披露日之后的信息**：每条财报事件携带 avail_date（实际披露日），月度因子值 = 满足 `avail_date ≤ 月末` 的最新一期事件的 SUE，经 `ym_avail = avail_date 所在月` as-of 映射 + 同月多次披露取最新 + 按月 ffill 得到（与 W1 通道财务因子 `fin.reindex(ym).ffill()` 同机制）。**严禁** report_date 直接 join——ths 面板披露滞后分布：中位 62 天，年报/三季报约 120 天（25%/50%/75% 分位 = 31/62/120 天），报告期直接对齐会产生最长 4 个月前视。抽查样例（000001，2016 年）：Q1 报 avail 2016-04-30、Q4 年报 avail 2017-04-30，as-of 映射正确（见 results/r251/sue_events.parquet）。

### 2.3 IC 口径（W1 复刻）

- IC[m] = spearman(F_m, R_{m→m+1})，月频全市场，min_obs=20（与 factor_expansion_v3ak.compute_monthly_ic 一致）
- 股票池：全 A（qfq），上市满 120 交易日（v3ak MIN_LISTED_DAYS），当月有成交；月均覆盖 sue_std 2521 只 / sue_pct 2778 只（合格池月均约 2845 只）
- 截面预处理：去极值 1%/99% + zscore（隔离测试证明该处理不改变秩 IC，三态 -0.0166 一致）
- 参照线：在役 a13_rsraw_e1f10dz（ranksum4：log_mv/amt20/pb_inv/roe）中 catalog 可得因子的同期 W1 ICIR

### 2.4 样本覆盖

ths_ttm_panel 235,170 行 × 5,174 股（1997–2026 报告期，2010 起季度披露标准、66 个季度、中位 3,136 行/季度）；K 线匹配 5,020 只；IC 窗口 2006-01 ~ 2026-07 共 247 个月，有效 IC 月 240（sue_std 覆盖率：事件层 66.9%——std 口径需 5 季度同比差历史；sue_pct 84.2%）。

## 三、核心发现（按重要性排序）

### 1. 全样本判定：未达线（负结果）

| 因子 | IC 均值 | ICIR | t 值 | IC>0 占比 | 门槛（R-200） | 在役参照 |
|---|---|---|---|---|---|---|
| sue_std | 0.0117 | **0.115** | 1.78 | 50.8% | IC≥0.025 ✗ | circ_mv 0.269 |
| sue_pct | 0.0063 | **0.074** | 1.15 | 51.2% | ICIR≥0.4 ✗ | div_yield 0.261 |

月频全市场形态下 SUE 无有效选股力：IC 均值不到门槛一半，ICIR 仅为在役最高因子的 43%，t<2 不显著。**不进入引擎级评估。**

### 2. 新鲜度分解：真实但快速衰减的事件效应

| 披露后月数 | sue_std IC | ICIR | sue_pct IC | ICIR |
|---|---|---|---|---|
| 0–2 月 | **0.0266** | **0.261**（t≈3.3） | 0.0179 | 0.209 |
| 3–5 月 | −0.0045 | −0.037 | −0.0084 | −0.070 |
| 6 月+ | −0.0066 | −0.078 | −0.0049 | −0.062 |

PEAD（盈余公告后漂移）在 A 股存在但半衰期 ≤1 个季度：新鲜窗 ICIR 0.261 恰好达到在役因子水平，但陈旧窗转负——**SUE 本质是事件窗信号，不是持久排序因子**；月频 ffill 形态把事件信息稀释到噪声水平。

### 3. 冗余检查（g3 预判）：与 roe 高度重叠

- 横截面秩相关：sue_std vs roe_ttm 均值 ρ=**0.599**（p90 0.648，恰在 0.6 冗余门槛）；vs net_profit_yoy 仅 0.193
- IC 序列相关：sue_std IC 与 roe_ttm IC 相关系数 **0.886**——SUE 的月度预测信息近九成与 ROE 水平因子同源；与 net_profit_yoy 0.675、div_yield 0.617、circ_mv −0.276
- 两口径互相 ρ=0.79，口径选择不改变结论

### 4. 年度稳定性：不稳定的符号翻转

21 个年度中 12 正 9 负：强年 2006(+0.100)/2017(+0.077)/2013(+0.051)/2020(+0.051)，弱年 2021(−0.042)/2014(−0.029)/2016(−0.025)/2023(−0.022)；近三年（2023–2025）−0.022/+0.031/−0.009 无趋势性改善。

## 四、结论与建议

1. **不达线，负结果交付归档**：SUE 月频因子形态 ICIR 0.115 远低于 0.4 门槛与在役参照线，R-249 方向五按预设判定终止于 E1 前置阶段，不进入引擎级（评分制+g3）评估。
2. **E1 惩罚项的有限证据**：若未来重启，唯一有数据支撑的形态是"披露后 ≤2 月的强负惊喜惩罚"（IC 0.027/ICIR 0.261），但与 roe_ttm 冗余 ρ=0.60、IC 序列相关 0.886 表明增量信息大部分已被 ROE 评分吸收，预期边际收益低——建议仅在 E1 同族惩罚框架下作为打破平手规则的软惩罚试点，且须先做净增量 IC（leave-one-out）验证。
3. **方法论收获**：本次验收复算发现并修复了收益配对错位 bug（F[m] 误配 m+1→m+2 收益），修复后独立复算 3 个月份 IC 与落盘完全一致（见下）；建议后续所有画像任务保留"落盘+外部重算"双通道验收。
4. **对 R-249 地图的影响**：方向五结论=关闭（除非 E1 惩罚场景重启）；迭代优先级维持 R-250 建议的方向一（小市值本体）为主。

## 五、来源清单（关键数字溯源）

| 数字 | 数据文件 | 计算脚本 |
|---|---|---|
| IC/ICIR/t/覆盖（表三-1、三-2、三-3） | HP:~/quant-evolve/results/r251/sue_summary.json | HP:~/quant-evolve/scripts/r251_sue_profile.py |
| 逐月 IC 序列（年度分解、复算抽查） | HP:~/quant-evolve/results/r251/sue_ic_monthly.csv | 同上 |
| SUE 事件表（PIT 抽查 000001/2016） | HP:~/quant-evolve/results/r251/sue_events.parquet | 同上 |
| 月度因子值样本 2018+（复算输入） | HP:~/quant-evolve/results/r251/sue_monthly_values_sample.parquet | 同上 |
| 在役参照 ICIR（circ_mv .269 / div_yield .261 / roe_ttm −.092 / np_yoy −.209） | HP:~/quant-evolve/results/factor_ic_monthly.csv（2006-01~2026-07，247 月） | 由 scripts/a2_ic_data.py 生成（W1 通道） |
| 底层面板 | HP:~/quant-evolve/data/derived/ths_ttm_panel.parquet（235,170×8）；data/all_stocks_qfq/*.parquet | — |
| 独立复算验证（2019-04/2021-10/2025-06 三月 ic 与 n 全等） | HP:/tmp/r251_verify2.log | HP:~/quant-evolve/scripts/r251_verify2.py |
| 复算隔离测试（winsorize/zscore 不改秩 IC） | HP:/tmp/r251_isolate.log | HP:~/quant-evolve/scripts/r251_isolate.py |

运行日志：HP:~/quant-evolve/results/r251/run.log（R251_DONE 118.8s）。未修改 registry / evolution_pipeline.py / paper_engine / crontab；HP 既有进程未动。
