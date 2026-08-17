# A5/task-0333 第五批模型迭代报告：成长×质量排序 + 动量护栏 + 价值降级过滤 + v2b 择时血统（5候选，2 PASS 留 pending，0 activate）

> 2026-08-17 · 状态：已完成（战役目标 25%/-20%/1.2 **全部未达**；成长×质量复合 IC 为负结论再证；2 候选六门全 PASS 留 pending，0 activate，现役仍 v2b_trr）
> 父本系：v2b_trr（q3z×MA200 趋势择时，现役）/ v0_seed（裸选股）
> 基建口径：全量池+成本v2+一字板+审计锁+ST区间表（AUDIT_LOCK_END=2024-06-30）；等价校验：原引擎 vs patched 开关全关 **逐位一致**（full/locked nav exact，EQUIV_OK）

## 0. 批次结论速览

| 项 | 结果 |
|---|---|
| 候选数 | 5（v4a_gqe1 / v4b_mve1 / v4c_gqpeg / v4d_gqg1 / v4e_gqg1x） |
| 五门禁 | **v4b_mve1、v4d_gqg1 六门全 PASS**；v4a/v4c/v4e REJECT（g4_dsr FAIL） |
| 战役目标 | 25%/-20%/1.2 全部未达；最优 v4b_mve1 12.42%/-28.99%/0.840 |
| activate | **0**（PASS 候选均不严格优于现役 v2b_trr 15.15%/-29.86%/0.936） |
| 核心结论 | 成长×质量复合在质量小盘宇宙无 alpha（IC 预检+回测双重验证）；E1 动量护栏单加可略压 MDD（-29.86→-28.99）但年化/Sharpe 双降；**当前宇宙+择时框架下 25%/-20%/1.2 前沿无交点，需换赛道** |

## 1. 批次设计逻辑（三报告证据链）

- **a4d 报告（task-0328）**：质量小盘宇宙内价值指标 IC 全负（pb/peg/neff/pe ICIR -1.3~-1.7）→ 价值不能当排序主键；alpha 由小市值+成长主导；buf_quality 是唯一近零可用价值锚（+0.0035/+0.091）。→ A5 排序主键转向「成长×质量」，价值降级为过滤（PEG<2）。
- **holdings-postmortem（task-0331）**：跌深组=高股息陷阱+接飞刀（非基本面烂）；**E1（买入时 ret120<-30% 排除）砍 20.8% 尾部亏损/误杀仅 12.1% 赢家**；**G1（接近年高点 dist250h>-10% 且 ret120>0）avg+21.2%/胜率78.4%**；微盘尾排除不可用（误杀64%赢家）。→ A5 加 E1 动量护栏 + G1 加强加分项。
- **a2c 报告（task-0327）**：Calmar 不变式——纯择时/风控到不了 25%+20%，需选股层真 alpha；v2b_trr 双信号择时（q3z×EW-MA200）是现役最优风控底座。→ A5 全部保留 v2b 择时血统（除归因对照 v4e）。

**阶段1 IC 预检（a5_gq_ic_monthly.csv，W1 口径，248月）**：方法学验证 buf_quality 全市场 IC +0.0035/+0.091 与 a4d 完全一致（口径可复现）；成长×质量复合（grw=营收/利润yoy+加速度，qly=buf_quality+cf_np_ratio）在宇宙内 mean_IC -0.0265 / ICIR -0.62（**为负**），未确认 > 纯 mv 增量空间。故候选设计 mv 主权重 > gq 权重，主机制押注 E1/G1 动量护栏（postmortem 实证，不依赖 gq IC）。

## 2. 阶段0 基线核对

- v2b_trr locked（a2c 重跑文件）：**15.15% / -29.86% / 0.936**，与任务书一致，基线 OK
- 对照：v0_seed（裸选股）26.26%/-69.49%/0.885；v2d_dd 9.51%/-19.98%/0.857

## 3. 候选设计（5个，单维度可归因）

| IT | 版本 | parent | 组件改动（唯一维度） | 机制假设/预期贡献 |
|---|---|---|---|---|
| IT-A5-01 | v4a_gqe1 | v2b_trr | 排序 mv→gq 复合（0.6mv+0.4gq）+E1 护栏 | 成长×质量拉年化（a4d 说成长主导）+E1 砍尾部亏损；任务骨架 a |
| IT-A5-02 | v4b_mve1 | v2b_trr | 仅加 E1 护栏（纯 mv 排序） | 纯护栏增量验证（对照）；postmortem E1 实证最强 |
| IT-A5-03 | v4c_gqpeg | v2b_trr | a 基础 + PEG<2 软过滤 | 价值降级为过滤（a4d 证排序无 alpha，试过滤）；接飞刀防护 |
| IT-A5-04 | v4d_gqg1 | v2b_trr | gq 三维混合（0.5mv+0.5gq）+E1+G1 加分 | G1 加强（postmortem avg+21.2%/胜率78.4%）；任务骨架 d |
| IT-A5-05 | v4e_gqg1x | v0_seed | d 的裸选股版（无择时） | 归因对照：量化择时对 MDD 的贡献；任务骨架 e |

## 4. 阶段3 正式回测结果（locked=2006-01~2024-06 正式口径；full 补充）

| IT | 版本 | locked 年化/MDD/Sharpe | full 年化/MDD/Sharpe | 判读 |
|---|---|---|---|---|
| IT-A5-01 | v4a_gqe1 | 10.74% / −31.31% / 0.744 | 10.79% / −31.31% / 0.755 | gq blend 未增 alpha（IC 预检一致） |
| IT-A5-02 | v4b_mve1 | 12.42% / **−28.99%** / 0.840 | 12.31% / −28.99% / 0.843 | E1 压 MDD 0.87pp 但年化 -2.7pp |
| IT-A5-03 | v4c_gqpeg | 10.36% / −33.68% / 0.723 | 10.37% / −33.68% / 0.730 | PEG 过滤反而恶化 MDD（价值过滤无益） |
| IT-A5-04 | v4d_gqg1 | 11.59% / −29.67% / 0.796 | 11.55% / −29.67% / 0.802 | G1 加分略优于 v4a 但仍低于纯 mv+E1 |
| IT-A5-05 | v4e_gqg1x | 19.09% / **−71.69%** / 0.751 | 19.35% / −71.69% / 0.769 | 无择时年化升但 MDD 崩（Calmar 不变式再证） |

等价校验：EQUIV_OK（原引擎 vs patched 开关全关，full+locked nav 逐位一致，diffs={}）。

## 5. 阶段4 五门禁（n_trials 61→67，扩展 IC：a5_ic_monthly_ext.csv）

| 候选 | g1_icir_is | g2_icir_oos | g3_max_corr | g4_dsr | g5_logic | g6_mdd_vs_parent | 裁决 |
|---|---|---|---|---|---|---|---|
| v4a_gqe1 | PASS 3.20 | PASS 0.140 | PASS | FAIL 0.9338 | PASS | PASS | REJECT |
| v4b_mve1 | PASS 3.20 | PASS 0.140 | PASS | **PASS 0.9710** | PASS | PASS | **PASS→pending** |
| v4c_gqpeg | PASS 3.20 | PASS 0.140 | PASS | FAIL 0.9228 | PASS | FAIL | REJECT |
| v4d_gqg1 | PASS 5.05 | PASS 0.238 | PASS | **PASS 0.9579** | PASS | PASS | **PASS→pending** |
| v4e_gqg1x | PASS 5.05 | PASS 0.238 | PASS | FAIL 0.5472 | PASS | FAIL | REJECT |

- 关键：g1/g2/g3 全过（动量/成长因子 IC 为正或近零、相关性未超限）；分水岭在 g4_dsr——E1 护栏（v4b）与 G1 加强（v4d）把 DSR 抬过线（0.971/0.958 vs 阈值≈0.95），说明动量护栏/加强显著改善收益分布形态（削尾部亏损→负偏改善）。
- v4a/v4c/v4e REJECT 根因：gq 选股不带护栏时尾部亏损仍在（DSR 0.93），PEG 过滤与裸选股使 MDD 恶化（g6 FAIL）。

## 6. 战役目标对照（locked 口径，目标 25% / -20% / 1.2）

| 版本 | ann 差距(pp) | MDD 差距(pp) | Sharpe 差距 | 严格优于现役 v2b_trr？ |
|---|---|---|---|---|
| v4a_gqe1 | +14.26 | +11.31 | +0.456 | 否 |
| v4b_mve1 | +12.58 | +8.99 | +0.360 | 否（MDD -28.99 略优于 -29.86，但 ann/SR 双降） |
| v4c_gqpeg | +14.64 | +13.68 | +0.477 | 否 |
| v4d_gqg1 | +13.41 | +9.67 | +0.404 | 否 |
| v4e_gqg1x | +5.91 | +51.69 | +0.449 | 否 |

- **全部未达战役目标**；PASS 候选（v4b/v4d）不严格优于现役 → 0 activate，留 pending（Dashboard 可回退兜底）。
- decision-log：D-20260816-043 a5_batch_closeout（0 activate）；registry v4a-v4e 候选入库；ledger IT-A5-01~05（带 features 字段，n_trials_cum 57→67）。

## 7. 结论与下一批方向（含目标可达性定量判断）

1. **成长×质量复合排序在本宇宙无 alpha（双重验证）**：IC 预检 univ ICIR -0.62 + 回测 v4a(10.74%) < v4b(12.42%)——a4d 的"成长主导"在质量小盘过滤后并不成立于线性 IC，尾部小市值效应才是主 alpha 源。
2. **E1 动量护栏 = 本批唯一有效机制**：v4b 相对 v2b_trr 压 MDD 0.87pp（-29.86→-28.99）且 DSR 抬升（0.936→0.971），但年化 -2.73pp、Sharpe -0.096——护栏改善风险分布但不增收益，方向正确但幅度不足以改变战役结果。
3. **Calmar 不变式第三次验证**：v4e 裸选股 19.09%/-71.69% vs v4d 择时 11.59%/-29.67%——择时贡献 +42pp MDD 改善换 -7.5pp 年化；含现役全部候选前沿：MDD≤-20% 一侧年化最高 9.5%（v2d_dd），年化≥25% 一侧 MDD 均 ≤-69%。**MDD≤20% 与 ann≥25% 在当前宇宙+择时框架下无交点（已实证 30+ 候选）**。
4. **建议换赛道（新立项）**：(a) 期权对冲/尾部保险层（-20% MDD 约束下保住 25% 年化的唯一数学路径）；(b) 可转债-小盘轮动（不同风险预算的资产类）；(c) 现金增强（打新/逆回购收益增厚 Sharpe）；(d) 降低目标至可达前沿（如 15%/-25%/0.9，v4b 方向继续叠 E1+精选护栏）。现役 v2b_trr 维持。
5. **技术备注**：HP quant env 曾现 scipy.linalg ABI 损坏（numpy 2.4.6/scipy 1.17.1 swap_c_and_f_layout signature mismatch）与间歇性 glibc heap 报错（a5_ic_ext 进程退出时），已通过重试规避；建议后续任务前 `python -c "from scipy import stats"` 自检。
