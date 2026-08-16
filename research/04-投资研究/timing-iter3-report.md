# 择时层迭代v3 报告：估值信号权重调优（更强估值权重 + 信号叠加）（task-0259）

> 报告由 `scripts/generate_timing_report_iter3.py` 依据 HP 实跑产物自动生成 · 生成时间 2026-08-14 13:29:39
> 数据基础：V2_d25_n30_p10（股息率≥2.5% + N=30 + 股价≤10 小盘等权），2006-2026 全区间
> 基线参照：task-0258 实测 i2_base 年化16.19%/-39.07%，i2_val_abs 年化14.64%/-36.80%

## 0. 估值数据落地核验（沿用 task-0258）

- ✅ `data/macro/index_valuation.parquet`：5188 行，指数 ['hs300']，2005-04-08 ~ 2026-08-13
  - ✅ 覆盖 2010 前（可验证 2015 股灾段滚动分位）
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

## 1. 调优方案说明

### 1.1 迭代v2 遗留问题（本迭代要解决的）
- task-0258 实测：唯一有效信号为 `f_val_abs`（绝对PE分段线性），145/248 个月降仓，
  2015股灾段 -39.07% → -36.80%，**未达 ≤-30%**，年化代价 16.19%→14.64%（-1.55pp）。
- `f_val_q3/q5`（滚动 min-max 分位）20 年从未触发：2007 年 PE 峰值 50.8 长期压制 rolling max，
  当前 PE 的 min-max 分位上穿不了 70%。

### 1.2 迭代v3 三个方向

**① 更强估值权重（绝对值网格 + 幂次放大）**：
- 绝对值网格：对 `f_val_abs` 的阈值/仓位映射做 5 档网格（ABS_GRID），
  在 trendvol 基线上乘 `f_val_abs_{key}`：

| key | anchors (PE→仓位系数) | floor | 设计意图 |
|---|---|---|---|
| v2 | `[(8,1.0),(12,1.0),(18,0.85),(25,0.70),(35,0.60)] floor0.60` | 0.60 | task-0258 实测基线（对照） |
| s1 | `[(10,1.0),(18,0.88),(25,0.75),(35,0.65),(45,0.55)] floor0.55` | 0.55 | 温和增强，低年化代价 |
| s2 | `[(10,1.0),(16,0.85),(20,0.70),(28,0.55),(35,0.45)] floor0.45` | 0.45 | 中强：28→0.55 直击2015中段 |
| s3 | `[(10,1.0),(15,0.80),(18,0.65),(22,0.50),(28,0.40),(35,0.35)] floor0.35` | 0.35 | 激进：18-22 一刀切 0.50 |
| s4 | `[(10,1.0),(15,0.90),(18,0.75),(21,0.55),(25,0.45),(30,0.40)] floor0.40` | 0.40 | 泡沫带聚焦：18-22 陡降，少误伤低估区 |

- 幂次放大：`(f_val_abs_{key})^power`，power∈{1,1.5,2,3}（0.85²=0.72，0.7³=0.343），
  直击 task「调大 f_val_abs 降仓强度」；实跑回测主用 power∈{1,2} 两档控过拟合。

**② 叠加其他信号（组合仓位系数）**：在 `abs_s4` 基础上叠加
- `f_mom_comp`（指数动量，来自 base 信号层）
- `f_breadth`（全市场上涨家数占比，市场宽度）
- `f_val_q5r`（修复后的分位秩信号，见下）

**③ 分位信号修复（附赠，非 task 强求）**：rolling min-max → rolling **百分位秩**（rank-based），对极端历史值更鲁棒；若实跑后仍不触发，报告如实标注。

### 1.2b 关于更早一次 task-0259 尝试（如实说明）
- 2026-08-14 更早一次尝试（memory 有记录）曾设计 steepB/steepC 锚点集 + min/geomean 组合算子；其文件未在磁盘留存（仅 memory 部分描述），为不引入猜测性重建，不再单独实现。
- 等价调优意图已由 ABS_GRID 的 s3（激进）/s4（泡沫带聚焦）与 power 幂次维度覆盖；
  实跑结果可直接检验该思路是否奏效，若相关变体未达标会在 §7 如实标注。

### 1.3 控制变量
- 只动**总仓位**（`timing_pos`），不动选股池/排序/调仓频率/交易规则
- 复用引擎双层防御 `eff_ret = day_ret × pos_ratio × timing_ratio`（task-0257 机制）

### 1.4 信号合成公式
```
w = f_trend_comp × f_vol_comp × (f_val_abs_{key})^power × [f_mom_comp] × [f_breadth] × [f_val_q5r]
pos = clip(ewm(w, α=0.3), w_min=0.3, 1.0)
```

## 2. 信号变化核验（不得恒 1.0）

  - f_val_abs: mean=0.936 min=0.600 n_low(降仓月)=145 → ✅ 有真实变化
  - f_val_abs_v2: mean=0.936 min=0.600 n_low(降仓月)=145 → ✅ 有真实变化
  - f_val_abs_s1: mean=0.930 min=0.550 n_low(降仓月)=223 → ✅ 有真实变化
  - f_val_abs_s2: mean=0.887 min=0.450 n_low(降仓月)=223 → ✅ 有真实变化
  - f_val_abs_s3: mean=0.837 min=0.350 n_low(降仓月)=223 → ✅ 有真实变化
  - f_val_abs_s4: mean=0.882 min=0.400 n_low(降仓月)=223 → ✅ 有真实变化
  - f_val_q5r: mean=1.000 min=1.000 n_low(降仓月)=0 → ❌ 变化不足(近恒1.0)
  - f_mom_comp: mean=0.665 min=0.400 n_low(降仓月)=177 → ✅ 有真实变化
  - f_breadth: mean=0.943 min=0.661 n_low(降仓月)=158 → ✅ 有真实变化

## 3. 全变体回测对比

| 变体 | 说明 | 年化 | 累计 | 最大回撤 | 夏普 | Calmar | 月胜率 |
|---|---|---|---|---|---|---|---|
| i3_base | 基线 trendvol | 16.19% | 2096.48% | -39.07% | 0.9052 | 0.4144 | 58.30% |
| i3_abs_v2 | +abs_v2（v2实测基线） | 14.64% | 1566.71% | -36.80% | 0.8891 | 0.3979 | 58.30% |
| i3_abs_v2_p2 | +abs_v2²（幂次放大） | 13.63% | 1289.16% | -34.69% | 0.8719 | 0.3930 | 58.30% |
| i3_abs_s1 | +abs_s1 温和 | 14.78% | 1608.23% | -36.85% | 0.8970 | 0.4011 | 58.30% |
| i3_abs_s2 | +abs_s2 中强 | 13.80% | 1332.94% | -35.25% | 0.8784 | 0.3916 | 58.30% |
| i3_abs_s3 | +abs_s3 激进 | 12.97% | 1131.95% | -32.75% | 0.8676 | 0.3961 | 58.30% |
| i3_abs_s4 | +abs_s4 泡沫带聚焦 | 13.40% | 1231.26% | -35.36% | 0.8599 | 0.3789 | 58.30% |
| i3_abs_s4_p2 | +abs_s4²（幂次放大） | 12.40% | 1010.62% | -32.06% | 0.8439 | 0.3869 | 58.30% |
| i3_abs_s4_mom | +abs_s4 × 动量 | 13.35% | 1220.71% | -35.27% | 0.8983 | 0.3787 | 58.30% |
| i3_abs_s4_breadth | +abs_s4 × 市场宽度 | 13.07% | 1155.11% | -35.16% | 0.8563 | 0.3718 | 58.30% |
| i3_abs_s4_stack | +abs_s4 × 动量×宽度 | 13.18% | 1178.44% | -35.07% | 0.8958 | 0.3757 | 58.30% |
| i3_abs_s4_q5r | +abs_s4 × 分位秩5年 | 13.40% | 1231.26% | -35.36% | 0.8599 | 0.3789 | 58.30% |

## 4. 危机段最大回撤（2008 / 2015股灾 / 2018）

| 变体 | 2008熊市段 | 2015股灾段(2015-06~2016-02) | 2018熊市段 |
|---|---|---|---|
| i3_base | -35.96% | -39.07% | -13.13% |
| i3_abs_v2 | -30.73% | -36.80% | -12.48% |
| i3_abs_v2_p2 | -28.68% | -34.69% | -11.87% |
| i3_abs_s1 | -30.41% | -36.85% | -12.37% |
| i3_abs_s2 | -29.18% | -35.25% | -11.86% |
| i3_abs_s3 | -28.67% | -32.75% | -11.61% |
| i3_abs_s4 | -28.72% | -35.36% | -12.10% |
| i3_abs_s4_p2 | -28.63% | -32.06% | -11.62% |
| i3_abs_s4_mom | -28.66% | -35.27% | -10.37% |
| i3_abs_s4_breadth | -28.71% | -35.16% | -11.61% |
| i3_abs_s4_stack | -28.66% | -35.07% | -10.35% |
| i3_abs_s4_q5r | -28.72% | -35.36% | -12.10% |

**2015股灾段改善判定**：基线 -39.07% → 迭代v3最佳(i3_abs_s1) -36.85%，目标 ≤ -30%。
→ ❌ 未达标。

## 5. Walk-forward 样本外（OOS）

> 训练窗网格选参（abs_key s2/s3/s4 × power 1/2 × mom 0/1 × breadth 0/1 = 24 组合，
按训练窗 Calmar 选最优），OOS 固定参数，杜绝前视。

| 窗口 | OOS区间 | 训练最优参数 | OOS年化 | OOS回撤 | OOS夏普 | OOS Calmar | 2015段OOS回撤 |
|---|---|---|---|---|---|---|---|
| WF1 | 2011-01-01~2015-12-31 | abs_s2_p1_mom1_bd0 | 20.31% | -35.15% | 1.0242 | 0.5777 | — |
| WF2 | 2016-01-01~2020-12-31 | abs_s3_p2_mom1_bd0 | 2.71% | -13.23% | 0.3222 | 0.2045 | — |
| WF3 | 2021-01-01~2026-12-31 | abs_s3_p2_mom1_bd0 | 7.09% | -16.63% | 0.8363 | 0.4265 | — |

**OOS 汇总**：回撤均值 -21.67%，年化均值 10.04%

## 6. 迭代v3 验收判定

最佳变体（按 Calmar，非基线）：**i3_abs_s1**

| 验收项 | 目标 | 实测（最佳变体） | 判定 |
|---|---|---|---|
| annual_return | 年化 ≥ 6.0% | 14.78% | ✅ |
| year2015_dd | 2015股灾段(2015-06~2016-02)回撤 ≤ -30% | -36.85% | ❌ |
| year2008 | 2008 熊市段回撤 ≥ -40% | -30.41% | ✅ |
| year2018 | 2018 熊市段回撤 ≥ -10% | -12.37% | ❌ |

## 7. 相对 task-0258 的改善与代价

> 由 §3/§4 实测表自动对比（见下，实跑后回填数字）。

| 指标 | task-0258 i2_val_abs | task-0259 最佳(见§6) | 改善幅度 |
|---|---|---|---|
| 年化 | 14.64%（i2_val_abs） | 待实跑 | — |
| 2015股灾段回撤 | -36.80% | 待实跑 | 目标压到 ≤-30% |
| 2008段回撤 | -30.73% | 待实跑 | — |
| 年化代价 | 相对 i2_base -1.55pp | 待实跑 | 要求不显著下降（保 6%+） |

## 8. 诚实标注：未生效/降级的信号

> 依据 §2 信号核验表与 fetch_log 自动标注。

## 9. 运行手册（可复现）

```bash
# 0) 同步脚本到 HP（含 v2 依赖 macro_timing_layer*.py）
rsync -avz /root/.openclaw/workspace-quant/scripts/macro_timing_layer_iter3.py \
          /root/.openclaw/workspace-quant/scripts/backtest_macro_timing_iter3.py \
          /root/.openclaw/workspace-quant/scripts/generate_timing_report_iter3.py \
          noname@10.12.192.174:~/quant-evolve/scripts/
# 1) 信号 + 全变体回测 + walk-forward（估值数据沿用 task-0258 已落地的 index_valuation.parquet）
ssh noname@10.12.192.174 'source ~/miniconda3/etc/profile.d/conda.sh && conda activate quant && cd ~/quant-evolve && \
  python3 scripts/backtest_macro_timing_iter3.py --stage all'
# 2) 自动生成报告
ssh noname@10.12.192.174 'source ~/miniconda3/etc/profile.d/conda.sh && conda activate quant && cd ~/quant-evolve && \
  python3 scripts/generate_timing_report_iter3.py'
# 3) 回传 VPS
rsync -avz noname@10.12.192.174:~/quant-evolve/results/{timing-iter3-report.md,timing_iter3_metrics.csv,timing_iter3_segments.csv,timing_iter3_walkforward_oos.csv,timing_iter3_signal_stats.csv,timing_signals_iter3.csv} /root/.openclaw/workspace-quant/results/
```

## 10. 数据产物字典

| 文件 | 内容 | 状态 |
|---|---|---|
| `results/timing_signals_iter3.csv` | f_val_abs_{v2,s1,s2,s3,s4}/f_val_q5r/mom/breadth 月度序列 | §2 核验 |
| `results/timing_iter3_signal_stats.csv` | 各信号 nunique/n_low 统计 | §2 |
| `results/timing_iter3_metrics.csv` | 10 变体指标 | §3 |
| `results/timing_iter3_segments.csv` | 危机段最大回撤 | §4 |
| `results/timing_iter3_walkforward_oos.csv` | WF 3窗 OOS（含2015段） | §5 |
