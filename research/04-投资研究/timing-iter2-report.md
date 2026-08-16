# 择时层迭代v2 报告：PE估值信号（分位数+绝对值）+ 去行业化（task-0258）

> 报告由 `scripts/generate_timing_report_iter2.py` 依据 HP 实跑产物自动生成 · 生成时间 2026-08-13 18:47:58
> 数据基础：V2_d25_n30_p10（股息率≥2.5% + N=30 + 股价≤10 小盘等权），2006-2026 全区间
> 基线参照：task-0257 最优变体 p3_trendvol 年化16.19% / 最大回撤-39.07% / 2015股灾段回撤-39.07%（未达标≤-30%）

## 0. 估值数据落地核验

- ✅ `data/macro/index_valuation.parquet` 存在：5188 行，指数 ['hs300']，2005-04-08 ~ 2026-08-13
  - ✅ 估值历史覆盖 2010 前（可验证 2015 股灾段滚动分位）
- ⚠️ 全市场估值未落地（去行业化 Tier-1b 不可用）
- ⚠️ 行业估值未落地（去行业化将降级 Tier-1/Tier-1b 中位数PE）
- `fetch_log.json`：拉取时间 2026-08-13 18:37:08
    ⚠️ funddb 沪深300 失败: module 'akshare' has no attribute 'index_value_hist_funddb'
    ✅ 沪深300: 主源=lg, 5188 行, 2005-04-08 ~ 2026-08-13, pe 7.9~50.8
    ⚠️ funddb 中证500 失败: module 'akshare' has no attribute 'index_value_hist_funddb'
    ⚠️ 中证500: 全部数据源失败
    ✅ index_valuation.parquet: 5188 行, ('hs300', Timestamp('2005-04-08 00:00:00')) ~ ('hs300', Timestamp('2026-08-13 00:00:00'))
    ⚠️ 全市场估值不可得（去行业化 Tier-1b 不可用）
    ⚠️ 申万成分股拉取不足，尝试巨潮行业分类
    ⚠️ 巨潮行业分类失败: '证监会行业分类'
    ⚠️ 无行业映射，去行业化降级 Tier-1（用指数中位数PE）

## 1. f_val 估值信号（不再恒 1.0 的验证）

> task-0257 现状：f_val 恒为 1.0（估值数据源未拉到，信号空转）。
> 迭代v2：落地 PE 数据后计算 `f_val_q3/f_val_q5`（滚动分位）、`f_val_abs`（绝对水平）、`f_val_deind`（去行业化）。

- `timing_signals_iter2.csv`：248 个月
  - f_val_q3: mean=1.000 min=1.000 n_low(降仓月)=0 → ❌ 变化不足(近恒1.0)
  - f_val_q5: mean=1.000 min=1.000 n_low(降仓月)=0 → ❌ 变化不足(近恒1.0)
  - f_val_abs: mean=0.936 min=0.600 n_low(降仓月)=145 → ✅ 有真实变化
  - f_val_deind: mean=1.000 min=1.000 n_low(降仓月)=0 → ❌ 变化不足(近恒1.0)

## 2. 全变体回测对比（控制变量：只动总仓位）

| 组别 | 变体 | 说明 |
|---|---|---|
| 基线 | i2_base | trendvol（复现 task-0257 p3_trendvol） |
| 加估值 | i2_val_q3 / i2_val_q5 / i2_val_abs / i2_val_q5abs | 在基线上乘估值因子 |
| 加估值+去行业化 | i2_deind / i2_full | 去行业化估值信号（Tier-2 跨行业中位数 / Tier-1 指数中位数PE） |

| 变体 | 说明 | 年化 | 累计 | 最大回撤 | 夏普 | Calmar | 月胜率 |
|---|---|---|---|---|---|---|---|
| i2_base | 基线 trendvol | 16.19% | 2096.48% | -39.07% | 0.9052 | 0.4144 | 58.30% |
| i2_val_q3 | +PE分位3年 | 16.19% | 2096.48% | -39.07% | 0.9052 | 0.4144 | 58.30% |
| i2_val_q5 | +PE分位5年 | 16.19% | 2096.48% | -39.07% | 0.9052 | 0.4144 | 58.30% |
| i2_val_abs | +PE绝对 | 14.64% | 1566.71% | -36.80% | 0.8891 | 0.3979 | 58.30% |
| i2_val_q5abs | +分位5年×绝对 | 14.64% | 1566.71% | -36.80% | 0.8891 | 0.3979 | 58.30% |
| i2_deind | +去行业化 | 16.19% | 2096.48% | -39.07% | 0.9052 | 0.4144 | 58.30% |
| i2_full | +分位×绝对×去行业化 | 14.64% | 1566.71% | -36.80% | 0.8891 | 0.3979 | 58.30% |

## 3. 危机段最大回撤（2008 / 2015股灾 / 2018）

| 变体 | 2008熊市段 | 2015股灾段(2015-06~2016-02) | 2018熊市段 |
|---|---|---|---|
| i2_base | -35.96% | -39.07% | -13.13% |
| i2_val_q3 | -35.96% | -39.07% | -13.13% |
| i2_val_q5 | -35.96% | -39.07% | -13.13% |
| i2_val_abs | -30.73% | -36.80% | -12.48% |
| i2_val_q5abs | -30.73% | -36.80% | -12.48% |
| i2_deind | -35.96% | -39.07% | -13.13% |
| i2_full | -30.73% | -36.80% | -12.48% |

**2015股灾段改善判定**：基线 -39.07% → 迭代v2最佳(i2_val_q3) -39.07%，目标 ≤ -30%。
→ ❌ 未达标。

## 4. Walk-forward 样本外（OOS）

| 窗口 | OOS区间 | 训练最优参数 | OOS年化 | OOS回撤 | OOS夏普 | OOS Calmar |
|---|---|---|---|---|---|---|
| WF1 | 2011-01-01~2015-12-31 | win756_abs0 | 22.39% | -36.80% | 1.0073 | 0.6084 |
| WF2 | 2016-01-01~2020-12-31 | win756_abs0 | 3.77% | -25.18% | 0.3246 | 0.1496 |
| WF3 | 2021-01-01~2026-12-31 | win756_abs0 | 10.79% | -20.97% | 0.8817 | 0.5144 |

**OOS 汇总**：回撤均值 -27.65%，年化均值 12.32%
- 2015股灾段所在 WF1 OOS 回撤：-36.80%

## 5. 迭代v2 验收判定（task-0258）

最佳变体（按 Calmar，非基线）：**i2_val_q3**

| 验收项 | 目标 | 实测（最佳变体） | 判定 |
|---|---|---|---|
| annual_return | 年化 ≥ 6.0% | 16.19% | ✅ |
| year2015_dd | 2015股灾段(2015-06~2016-02)回撤 ≤ -30% | -39.07% | ❌ |
| year2008 | 2008 熊市段回撤 ≥ -40% | -35.96% | ✅ |
| year2018 | 2018 熊市段回撤 ≥ -10% | -13.13% | ❌ |

## 6. 去行业化方案说明

### 6.1 为什么需要去行业化

- 指数（如沪深300）PE 为**市值加权**，被权重行业（尤其金融/银行，长期低PE）主导：
  - 银行权重高 + PE 低 → 指数 PE 被拉低，看起来「便宜」，掩盖其他行业高估；
  - 或某一高估行业权重暴涨（如2015杠杆牛非银/科技）→ 指数 PE 被拉高，触发过度降仓。
- 单一估值信号会被行业结构「绑架」，导致误判（过早/过晚降仓）。

### 6.2 怎么做（三级降级，诚实报告实际生效级别）

| 级别 | 方法 | 数据 | 是否行业中性 |
|---|---|---|---|
| Tier-2（优先） | 各申万一级行业PE滚动分位因子取**中位数**（跨行业中性：一半以上行业偏贵才降仓） | 行业月度中位数PE | ✅ 完全中性 |
| Tier-1（降级） | 指数**中位数/等权PE**滚动分位（剔除市值权重，不被低PE金融权重拉低） | 指数估值含中位数PE | ⚠️ 弱中性 |
| Tier-1b（再降级） | 全市场 A股 PE(TTM) **中位数** 滚动分位（横截面中位数天然不被单行业权重绑架） | 全市场A股估值（乐咕 2005+） | ⚠️ 弱中性 |

- 计算链路：`fetch_valuation_data.py` 拉指数PE（乐咕 `stock_index_pe_lg` 2005+，含中位数/等权）
  + 行业映射(申万一级)→行业月度中位数PE → `f_val_deind`；行业不可得→自动降级 Tier-1/Tier-1b。
- **task-0258 根因修复**：上一轮 COL_MAP 未收录乐咕列名（滚动市盈率/滚动市盈率中位数），
  导致主源 fallback 到 `stock_market_pe_lg`（仅2019+），分位信号覆盖不到 2015 股灾。
  本轮补全列名映射 → 使用乐咕 `stock_index_pe_lg`（2005+）→ 分位信号可覆盖 2015。
- 若指数/全市场估值均不可达（如实记录于 fetch_log.json），自动降级 `f_val_deind=1.0`，报告会标注。

### 6.3 效果对比（去行业化前后）

| 对比 | f_val 基准 | 说明 |
|---|---|---|
| 加估值(未去行业化) | i2_val_q5abs | 市值加权PE分位×绝对 |
| 加估值+去行业化 | i2_deind / i2_full | Tier-2/Tier-1 中性化估值 |

> ⚠️ 具体数字待实跑回填，见 §2/§3 表。
## 7. 结论与建议

> 回测数字来自真实运行（timing_iter2_metrics.csv / _segments.csv / _walkforward_oos.csv）。

## 8. 运行手册（可复现）

```bash
# 1) 落地估值数据（多源，失败如实记录 fetch_log.json）
ssh noname@10.12.192.174 'source ~/miniconda3/etc/profile.d/conda.sh && conda activate quant && cd ~/quant-evolve && \
  python3 scripts/fetch_valuation_data.py'
# 2) 信号 + 全变体回测 + walk-forward
ssh noname@10.12.192.174 'source ~/miniconda3/etc/profile.d/conda.sh && conda activate quant && cd ~/quant-evolve && \
  python3 scripts/backtest_macro_timing_iter2.py --stage all'
# 3) 自动生成报告
ssh noname@10.12.192.174 'source ~/miniconda3/etc/profile.d/conda.sh && conda activate quant && cd ~/quant-evolve && \
  python3 scripts/generate_timing_report_iter2.py'
# 4) 回传 VPS
rsync -avz noname@10.12.192.174:~/quant-evolve/results/{timing-iter2-report.md,timing_iter2_metrics.csv,timing_iter2_segments.csv,timing_iter2_walkforward_oos.csv,timing_signals_iter2.csv} /root/.openclaw/workspace-quant/results/
```

## 9. 数据产物字典

| 文件 | 内容 | 状态 |
|---|---|---|
| `data/macro/index_valuation.parquet` | 沪深300/中证500 PE/PB(+等权/中位数) | §0 核验 |
| `data/macro/market_valuation.parquet` | 全市场 A股PE(TTM)中位数/等权（乐咕2005+，去行业化 Tier-1b） | §0 核验 |
| `data/macro/industry_pe_monthly.parquet` | 行业月度中位数PE（Tier-2去行业化） | §0 核验 |
| `data/macro/fetch_log.json` | 各数据项成败日志 | §0 核验 |
| `results/timing_signals_iter2.csv` | f_val_q3/q5/abs/deind 月度序列 | §1 核验 |
| `results/timing_iter2_metrics.csv` | 7 变体指标 | §2 |
| `results/timing_iter2_segments.csv` | 危机段最大回撤 | §3 |
| `results/timing_iter2_walkforward_oos.csv` | WF 3窗 OOS | §4 |
