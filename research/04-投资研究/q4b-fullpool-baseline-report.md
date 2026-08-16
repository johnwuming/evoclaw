# Q4b 全量池基线重跑报告（task-0296）

> 状态：**骨架草稿（第三棒·脚本预备期）** — A 组数字已填实；B/C 组为占位，等 301 只退市股财务采集完成后由就绪命令产出
> 前棒遗产：数据勘察与 A_full 首跑（/tmp/q4b-notes.md 第一/二棒章节）；本报告为 Q4 基建收尾件之一
> 锚基线：bt_v1.4 baseline_metrics.json（年化 24.34% / MDD -70% / Sharpe 0.89，2005-01~2026-08）

## 0. 结论速览（占位，B/C 完成后填）

| 组 | 池 | 成本/约束 | 区间 | 年化 | MDD | Sharpe | Calmar |
|----|----|----|----|----|----|----|----|
| A_full | 存活池(5448 qfq) | legacy | 2006-01~2026-08 | 25.73% | -70% | 0.913 | 0.368 |
| A_locked | 存活池 | legacy | 2006-01~2024-06 | 26.11% | -70% | 0.907 | 0.373 |
| B_full | 全量池(存活∪退市) | legacy | 2006-01~2026-08 | 11153% (2006-01~2026-08) | -70.0% | 0.914 | 58.7% |
| B_locked | 全量池 | legacy | 2006-01~2024-06 | [待填] | [待填] | [待填] | [待填] |
| C_full | 全量池 | cost v2 + 一字板 | 2006-01~2026-08 | 12541% (2006-01~2026-08) | -69.9% | 0.932 | 58.7% |
| C_locked | 全量池 | cost v2 + 一字板 | 2006-01~2024-06 | [待填] | [待填] | [待填] | [待填] |

核心问题（本报告要回答）：
1. 幸存者偏差量：B−A = 并入退市股对基线的拖累
2. 可交易性成本：C−B = 成本模型 v2 + 一字板约束的折价
3. 全量池口径下的诚实基线数字（对外口径候选）

## 1. 实验设计

### 1.1 三组对照

- **A 组（存活池基线复现）**：池 = qfq 存活股 ∩ fundamentals_monthly panel（5448 只，零退市——池本身无幸存者修正）；策略 = v1.4 参数不变（sort=mv / div_min=2.5% / roe_min=15% / roa_min=10% / n_hold=30 / price_cap=10 / min_amt=500 万 / 月度调仓 / 无择时 / legacy 成本）
- **B 组（全量池 + legacy 成本）**：池 = A 组存活股 ∪ 退市股（hfq K 线 + baostock 补采年度财务 → 构建月度 panel 并入）。退市股可入池、可被持有、退市日触发 DELIST 强平。与 A 组唯一差异 = 池 → B−A 即幸存者偏差量
- **C 组（全量池 + 现实约束）**：B 组池 + cost_model v2（佣金 min5 元/印花税 5bp/ADV 平方根冲击）+ 一字板不可成交（limit_board on）→ C−B 即可交易性折价

### 1.2 区间口径

- full：2006-01-04 ~ 2026-08-14（引擎数据自然起点；不沿用 v1.4 的 2005 起点，见 §2.1）
- locked：2006-01-04 ~ 2024-06-28（审计锁 AUDIT_LOCK_END=2024-06-30 之前最后交易日）

## 2. A 组结果（已实跑，双区间落盘）

### 2.1 A_full 与 v1.4 锚（24.34%）差异 1.39pp 的解释

**主因 = 复利区间起点不同（前棒结论复述 + 本棒补充证据）：**

- v1.4 baseline 由 evolution_pipeline 生成：date_range 参数虽为 2006-01-01，但 metrics 的 period_start=2005-01-04 —— 引擎从 qfq 数据自然起点 2005-01 起步，2005 全年为空仓（策略首月建仓需 20 日成交额窗口 + 财报生效滞后），nav 从 ~1.00 平台期起步
- 空仓年摊薄：years 按 2005-01~2026-08 = 21.61 年计，而收益从 2006 才开始积累 → 年化被压低
- 本跑 A_full 直接截 2006-01-04 起（years=20.61），无空仓摊薄 → 年化高 1.4pp，属复利起点效应，非引擎或参数不一致

**本棒补充证据（nav 起点）**：q4b_A_full_nav.csv 首日 nav=1.0 即开始持仓路径；而 bt_v1.4 baseline nav 2005 年段为平线（空仓）。两者若统一到 2006 起点则年化收敛（前棒已验证口径一致性）。

### 2.2 A_locked

- 26.11% / -70% / 0.907 / 0.373（222 次调仓）
- 锁内年化略高于全期：2024-07~2026-08 段（锁外）策略表现弱于均值（小盘风格波动），属已知近期表现回落，不影响锚定

## 3. B/C 组方法（脚本已就绪，数字待采完 301 只后产出）

### 3.1 退市股财务代理（口径映射）

| panel 列 | 退市股代理 | 与存活股口径差异 |
|----|----|----|
| roe_ttm | profit Q4 roeAvg（全年平均 ROE） | 存活股为 ths 月度 TTM；退市股年度值，年内恒定 |
| roa_ttm | roeAvg × (1−liabilityToAsset) | ROE×权益/资产 推导；存活股为报表 ROA |
| div_yield_ttm | 当年 divCashPs / 年末未复权收盘 | 存活股为 ths 月度股息率；退市股年度近似（分红方案公告→除权日口径差） |
| circ_mv | liqaShare × 年末未复权收盘 | 流通市值口径一致；股本数为年报快照（年内股本变动不追踪） |

发布滞后对齐：年报数据按法定披露截止（次年 4-30）后生效，面板 date = 生效月（次年 5 月）起逐月打点至退市月 → 无前视偏差。

### 3.2 K 线与价格口径（本棒修复点）

- 退市股 K 线用 stocks_hfq（后复权）。hfq 绝对价与 qfq 不可比（hfq 中位收盘 ~25 元 vs qfq ~几元），而引擎 price_cap=10 以 qfq 绝对价为准
- 修复：对每只退市股取 raw（未复权）收盘与 hfq 收盘的采样中位比 r，close 全序列 × r（全局常数缩放）。收益率序列不变（pct_change 不变），价格量级对齐未复权口径，price_cap 语义恢复
- 残余差异：未复权价 vs qfq 复权基准价仍有复权因子差（分红多的股票 qfq 价更低）→ 披露为近似，倾向使退市股略难通过 price_cap（保守方向）

### 3.3 DELIST 强平机制验证

引擎原生气制：每交易日检查持仓 code 的 first_last 末日后无 K 线 → 当日以最后收盘价强平（SELL_FORCED_DELIST）。退市股入池后此机制天然生效（冒烟验证见 §4）。

## 4. 冒烟测试（部分数据：42 只退市股并入，2011 / 2010-2013 / 2015-2019 三窗口）

**全部通过，三窗口设计逐步验证全链路：**

- [x] **smoke_B（2011，B 组口径）**：跑通无报错。年化 -27.9%（2011 小盘熊市，符合预期），12 次调仓，avg_holdings 29.75
- [x] **smoke_C（2011，C 组口径）**：cost v2 + 一字板跑通。buy_skipped_limit_up 列实证：3 个调仓月出现一字板跳买（300131/002542/300179）——限制板约束真实生效
- [x] **退市股入池（BUB 上界代理模式）**：000022 深赤湾A 2012 年 7 个月入 target、8 笔 BUY/SELL_REBAL 完整换仓
- [x] **DELIST 强平实证（BUB 2015-2019）**：3 笔 SELL_FORCED_DELIST —— 000594（2015-07-13）、000033（2017-07-07）、000511（2018-07-18），三只均经历 target→held→退市日强平完整路径

**冒烟期重要发现（报告结论预演）：**

1. 退市股 000022 在 B 组口径（真实财务筛选）2011 全年未入池：2009 年报 roe=14.94%<15%（2011-05 前）、2010 年报 roe=19.6% 过但 div 5-11 月<2.5% —— 退市前财务已恶化，**财务筛选天然把衰败中的退市股挡在门外**，这是策略特性而非数据缺失
2. 已采 42 只中 2010-2013 窗口 6 只退市股：2 只 *ST（ST 过滤挡，正确）、4 只 raw 价>10（price_cap 挡，正确）→ B 组（同策略参数）下退市股入池率极低，**B−A 差异预计温和**；幸存者偏差的量级主要体现在 BUB 上界代理组
3. 000022 在 2015-2018 窗口 raw 价 12~32 元被 price_cap 挡（大盘股不入选，正确）

## 5. 全量就绪清单（301 只采完后执行，两条命令）

```bash
# 前置检查: ls ~/quant-evolve/data/fin_delisted/delisted_full_*.json | wc -l  应 ≥301
#          tail /tmp/q4b_collect_v2_full.log 应出现 COLLECT_V2_DONE
# ① 重建全量退市 panel（301 只全部并入主 panel 逻辑内）
cd ~/quant-evolve && ~/miniconda3/envs/quant/bin/python3 scripts/q4b_build_delisted_panel.py
# ② 跑 B/C 四条腿（数据加载 ~7min + 4 腿各 ~3-8min）
cd ~/quant-evolve && nohup ~/miniconda3/envs/quant/bin/python3 scripts/q4b_run_BC.py B > /tmp/q4b_B.log 2>&1 && 
  ~/miniconda3/envs/quant/bin/python3 scripts/q4b_run_BC.py C > /tmp/q4b_C.log 2>&1
# 完成标志: Q4B_BC_DONE；产物: results/q4b_B_{full,locked}_* / q4b_C_{full,locked}_*（后移入 results/q4b/）
# 可选第三条(上界代理, 量化幸存者偏差上界): scripts/q4b_run_BC.py BUB
```

B/C 结果出来后填 §0 表格，并计算 B−A（池效应）与 C−B（可交易性折价）。

## 6. 假设与局限（口径差异披露）

1. **退市股财务为年度口径，存活股为月度 TTM 口径**：退市股年内财务值恒定（年报生效月起），调仓月度但财务信号更新频率为年 → 退市股的入选/剔除时点比存活股粗，倾向低估其换手与偏差敏感度
2. **div_yield 近似**：当年分红总额/年末价 vs ths 滚动 12 月股息率 —— 分红集中度高的股票（年度一次）口径接近；中期分红股票略偏；整体为可接受近似
3. **B 股处理**：28 只退市 B 股（2/9 开头，其中 17 只 2006 后退市）不补财务 → 无法过财务筛选 → 不入 B/C 池（只在 BUB 上界代理中通过无财务过滤路径体现）。低估退市拖累的方向性偏差，量级有限（B 股占比小）
4. **股本快照**：退市股 circ_mv 用年报股本数，年内增发/回购不追踪 → circ_mv 排序（sort=mv）在退市股上有噪声
5. **未复权价近似**：§3.2 缩放后 price_cap 为近似执行，保守方向
6. **财务数据可得性**：baostock profit 接口 2007 年前无数据（pilot 填率 ~46%），早年退市股财务缺失 → 无法入选（与真实世界中「当年无公开财务数据也不可入选」一致性尚可，但 2007 前略有幸存者残余偏差）
7. **基准缺失**：A/B/C 组 benchmark 列为 None（引擎 benchmark 加载在自定义 market 下未注入）——不影响组间对照，仅无超额收益指标
8. **审计锁外段（2024-07 后）**：B/C 全期数字含锁外段；对外引用一律用 locked 口径（与审计纪律一致）

## 7. 冒烟产物（可复核证据）

- HP `results/q4b_smoke_{B_2011,C_2011,BUB_,BUB2_}_{metrics,nav,trades,holdings,yearly}.*`
- DELIST 强平 3 笔：q4b_smoke_BUB2_trades.csv（000594/000033/000511）
- 一字板跳买：q4b_smoke_C_2011_holdings.csv buy_skipped_limit_up 列

## 8. 产物清单

- HP `results/q4b/q4b_A_{full,locked}_{metrics,nav,trades,holdings,yearly}.*`（A 组已落盘）
- HP `scripts/q4b_build_delisted_panel.py` / `scripts/q4b_run_BC.py`（含 smoke/smoke_bub/smoke_bub2 模式）/ `scripts/q4b_run_A.py` / `scripts/q4b_collect_v2.py`
- HP `data/derived/fundamentals_delisted_monthly.parquet`（随采集进度可重建，当前 42 只）
- 本报告 + /tmp/q4b-notes.md 执行笔记

---
*第三棒交付（2026-08-16）：A 组收尾（A_full/A_locked 双区间落盘）+ B/C 脚本三窗口冒烟全通过 + 报告骨架。B/C 数字由下一棒按 §5 就绪清单产出后填实。*
