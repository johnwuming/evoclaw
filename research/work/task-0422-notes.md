# task-0422 过程笔记：csad 波动率中性化残差 IC 裁决（R-260）

- 预登记裁决门槛（不可改）：残差 |ICIR| ≥ 0.25 → csad 有独立信息，建议登记 E2 预注册；< 0.25 → 定性波动率族替代表达，归档。主裁决用双中性化版（vol20+vol120），单版（vol20）作参照。
- 报告编号确认：05-量化投资/ 目录最大编号 R-259（R-258 行业轮动E2预注册、R-259 多引擎实施方案），本报告用 **R-260**。

## 核验点记录

1. [16:42] r0419 产物在位：csad_sigma20_monthly.csv（596,523 行=596,522 数据+表头，ym/code/feat_csad_sigma20，首月 2005-08）、ic_monthly.csv、xs_corr_monthly.csv、r0419_summary.json、build.log。均 HP ~/quant-evolve/results/r0419/。
2. [16:43] r0419 脚本口径确认（r0419_csad.py 243 行）：
   - 数据加载：data/all_stocks_qfq/*.parquet 取 date/close/amount/outstanding_share，len<120 剔除，sort+dedup(date)。
   - 月末：cal（close 索引）按 to_period("M") groupby max → me_dates。
   - 次月收益：me_close.pct_change().shift(-1)。
   - IC 池 mask：上市≥120（listed_cnt）& 月末 close 非 NaN & 有下月收益；MIN_OBS=20。
   - 预处理 cross_proc：dropna→quantile 1%/99% clip→zscore；IC=spearman(Fp, Rn)。
   - 分组：qcut(Fp.rank(method="first"), 5) Q1 低→Q5 高，组内 Rn 均值。
   - 五分段：n5=len//5，前 4 段各 n5，末段含余数。
   - vol120（r0419 内部版，未落盘）：月末前 120d ret，市场收益非 NaN 日 mask（okm），个股 NaN→0，std。spearman(F, vol120) 记录在 xs_corr_monthly.csv。
   - 基准数字（R-257 报告）：主口径 251 月 IC −0.0920 / ICIR −0.796 / t −12.61 / IC<0 80.5%；xs_corr vol120 ρ 均值 0.442（p90 0.574）。
3. [16:45] r0419 的 vol120 只在内存计算未落盘 → 需重算 vol20/vol120 月度截面。idio_vol 生产因子截面未在 r0419 落盘；按任务书预登记：双中性化即近似替代，另补 idio120 代理（120d 市场回归残差 std，szzs 已在 r0419 加载路径）作第三参照版，注明口径差异。

## 结果记录（HP results/work/r0422/r0422_summary.json, md5 见 md5.txt）

4. [16:47] 主计算完成（64 秒，months=252，mean_n=2350 与 r0419 一致）。验证三条全过：
   - raw IC vs r0419 ic_monthly 序列相关 = **1.000**；raw 主口径 IC −0.09195/ICIR −0.796/t −12.61/IC<0 80.5%，与 R-257 报告数字逐位一致。
   - ρ(F, vol120) mean 0.439 / p90 0.568 vs r0419 xs_corr 的 0.442/0.574（微差来自 winsorize 口径，可接受）。
   - ρ(F, vol20) mean 0.725（高于 vol120，印证与短窗波动更亲）。
5. [16:48] 裁决数字（主口径 251 月，剔 2026-07 部分月）：
   - **v2 双中性化（主裁决）：IC −0.0528 / ICIR −0.601 / t −9.53 / IC<0 71.7% → |ICIR|=0.601 ≥ 0.25 → csad 有独立信息**
   - v1 单中性化 vol20：IC −0.0461 / ICIR −0.464 / t −7.34 / IC<0 63.7%
   - v3 三代理（+idio120）：n=243，IC −0.0513 / ICIR −0.624 / t −9.72 / IC<0 73.7%
   - 回归 R² 均值：v1 0.585 / v2 0.599 / v3 0.652（波动率族解释 csad 方差约 6 成，但 IC 信息残留 6 成以上）
6. [16:50] 修 bug：quintile spread 统计因长表 pivot 对齐错误重算（组均值列本就正确）；修复脚本 r0422_fix_qstats.py，md5 已入档。修复后：
   - v2 分组 Q1 2.19% → Q5 0.86%（单调降），Q5−Q1 = −1.33%/月，t=−7.21，67.9% 月份负
   - v1：Q1 2.11% → Q5 0.88%，−1.23%/月，t=−6.34；v3：Q1 2.17% → Q5 1.00%，−1.18%/月，t=−6.75
7. [16:51] 残差 IC 序列 vs 在役因子 IC 序列相关（诊断）：res_v2 vs volatility_20d 0.402、vs idiosyncratic_vol 0.236（原始因子为 −0.833/−0.846）→ 中性化后时序冗余大幅下降但仍非零。
8. [16:52] v3 分段（弱尾段警示）：seg4 2018-04~2022-03 ICIR −0.430；seg5 2022-04~2026-06 ICIR −0.238（IC<0 60.8%）——近四年残差信息明显衰减，报告必须披露。

## 方法决策（披露）

- vol20：月末截断 trailing 20 交易日日收益 std，min_periods=15（不足 NaN）。
- vol120：完全复刻 r0419 内部口径（okm mask + NaN→0 + std），以便对拍 ρ≈0.442。
- idio120（补充参照）：trailing 120d，市场收益（szzs→cal 对齐）非 NaN 日，NaN→0，beta=cov/var，残差 std。与生产 idiosyncratic_vol 因子口径差异：生产版引擎内实现未公开细节，本代理为标准 CAPM 残差波动近似。
- 中性化回归：逐月截面 OLS，回归前对 F 与 vol 代理各做 1%/99% winsorize（OLS 残差对回归量的线性重标不变，zscore 与否不影响残差，只 winsorize 即可）；残差 e 再 winsorize 1%/99% + zscore 后做 spearman IC（spearman 秩基础，主要防极端值扰动分组）。
- 验证设计：先复现 r0419 原始 IC（应得 −0.0920/−0.796/251 月）+ 复现 ρ(F,vol120)≈0.442，两条通过才信残差结果。

## 待办
- [ ] 单月独立抽验
- [ ] R-260 报告 + README 更新 + completions
